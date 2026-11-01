"""Suíte de testes automatizados para banco de dados, RAG de políticas, tools e agente."""

from __future__ import annotations

from datetime import date

from src.agent import EmporioMusicaAgent
from src.database import StoreDatabase
from src.memory import ConversationMemory
from src.policy_rag import PolicyRAG
from src.tools import AgentToolkit, calcular_opcoes_pagamento


def test_database_ingestion_and_data_quality() -> None:
    db = StoreDatabase()
    products = db.execute_query("SELECT * FROM products")
    assert len(products) == 65

    # Produto 96 (Giannini GF-3D) é 'active' mas tem stock_quantity=0 -> out_of_stock
    prod_96 = db.execute_query("SELECT * FROM products WHERE product_id = 96")[0]
    assert prod_96["availability"] == "out_of_stock"

    # Produto 136 (Ibanez Bass 2X) tem stock=13 mas status='discontinued' -> discontinued
    prod_136 = db.execute_query("SELECT * FROM products WHERE product_id = 136")[0]
    assert prod_136["availability"] == "discontinued"

    # Produto 94 (Taylor 110e) tem promoção ativa de 8% (is_active=1)
    prod_94 = db.execute_query("SELECT * FROM products WHERE product_id = 94")[0]
    assert prod_94["has_active_promo"] == 1
    assert prod_94["promo_discount_percent"] == 8
    assert prod_94["effective_price_brl"] == 5519.08
    # Não cumulatividade do PIX em item promocional (Política 6.2)
    assert prod_94["pix_price_brl"] == 5519.08


def test_policy_rag_chunks_and_retrieval() -> None:
    rag = PolicyRAG()
    assert len(rag.chunks) == 10

    res_troca = rag.search("Me arrependi da minha compra, posso devolver meu pedido?", top_k=2)
    assert res_troca[0]["section_id"] == "4"

    res_horario = rag.search("Qual o horário de funcionamento aos sábados e domingos?", top_k=2)
    assert any(r["section_id"] == "2" for r in res_horario)

    res_frete = rag.search("Qual o valor do frete para Campo Grande e Dourados?", top_k=2)
    assert res_frete[0]["section_id"] == "5"


def test_payment_and_installment_rules() -> None:
    # Caso 1: Takamine GD20 (R$ 2.199,00 sem promoção ativa)
    pgto_gd20 = calcular_opcoes_pagamento(2199.0, tem_promocao_ativa=False)
    assert pgto_gd20["preco_pix_brl"] == 2089.05
    assert pgto_gd20["max_parcelas_sem_juros"] == 12
    assert pgto_gd20["permite_combinar_pagamentos"] is True

    # Caso 2: Ukulele Kala KA-15S (R$ 199,90 -> até 3x de R$ 66,63, pois 4x daria R$ 49,98 < R$ 80)
    pgto_uku = calcular_opcoes_pagamento(199.9, tem_promocao_ativa=False)
    assert pgto_uku["max_parcelas_sem_juros"] == 3
    assert pgto_uku["permite_combinar_pagamentos"] is False

    # Caso 3: Violão Tagima Memphis AC-39 (R$ 429,90 -> 5x de R$ 85,98 >= R$ 80; 6x daria R$ 71,65 < R$ 80)
    pgto_ac39 = calcular_opcoes_pagamento(429.9, tem_promocao_ativa=False)
    assert pgto_ac39["max_parcelas_sem_juros"] == 5


def test_toolkit_catalog_and_orders() -> None:
    tk = AgentToolkit(reference_date=date(2026, 2, 20))

    # Violões disponíveis até R$ 1.000 (exclui Giannini GF-3D sem estoque e Shelby SN-7C descontinuado)
    violoes = tk.buscar_produtos(categoria="Violões", preco_max=1000.0, apenas_disponiveis=True)
    assert violoes["total_encontrado"] == 12
    nomes = [p["nome"] for p in violoes["produtos"]]
    assert "Giannini GF-3D Dreadnought Sunburst" not in nomes
    assert "Shelby SN-7C 7 Cordas Nylon Natural" not in nomes

    # Detalhar Takamine GD20 (promoção 12% expirada is_active=0)
    gd20 = tk.detalhar_produto_e_pagamento("Takamine GD20")
    assert gd20["encontrado"] is True
    assert gd20["disponibilidade"] == "available"
    assert len(gd20["promocoes_ativas"]) == 0
    assert len(gd20["promocoes_expiradas"]) == 1

    # Consultar Pedido #7 (entregue em 2026-02-17; em 2026-02-20 está a 3 dias da entrega -> elegível a arrependimento!)
    ped7 = tk.consultar_pedido("7")
    assert ped7["encontrado"] is True
    analise = ped7["pedidos"][0]["analise_troca_e_devolucao"]
    assert analise["direito_arrependimento_7_dias"]["elegivel_na_data_referencia"] is True


def test_agent_end_to_end_conversations() -> None:
    mem = ConversationMemory(":memory:")
    agent = EmporioMusicaAgent(memory=mem)

    # 1. Consulta de catálogo
    r1 = agent.chat("Quais opções de violões disponíveis custando até R$1000?", session_id="s1")
    assert any(tc["tool"] == "buscar_produtos" for tc in r1.tool_calls)
    assert "Yamaha C40" in r1.reply
    assert "Tagima Woodstock" in r1.reply

    # 2. Consulta de preço + promoção expirada
    r2 = agent.chat("Quanto custa o Takamine GD20?", session_id="s1")
    assert any(tc["tool"] == "detalhar_produto_e_pagamento" for tc in r2.tool_calls)
    assert "2.199,00" in r2.reply
    assert "2.089,05" in r2.reply

    # 3. Fora de escopo: acessórios
    r3 = agent.chat("Vocês vendem encordoamento e palhetas?", session_id="s1")
    assert "exclusivamente com instrumentos musicais" in r3.reply

    # 4. Fora de escopo: off-topic geral
    r4 = agent.chat("Qual a receita de bolo de cenoura?", session_id="s1")
    assert len(r4.tool_calls) == 0
    assert "Empório da Música" in r4.reply
