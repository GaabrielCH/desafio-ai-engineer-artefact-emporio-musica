"""Ferramentas (Function Calling Tools) para consulta ao catálogo, pedidos, promoções e políticas."""

from __future__ import annotations

import json
import math
from datetime import date
from typing import Any

from src.config import settings
from src.database import StoreDatabase, db, digits_only, normalize_text
from src.policy_rag import PolicyRAG, policy_rag

ACCESSORY_KEYWORDS = [
    "encordoamento",
    "corda avulsa",
    "jogo de cordas",
    "palheta",
    "palhetas",
    "cabo",
    "cabos",
    "case",
    "cases",
    "capa",
    "bag",
    "pedal",
    "pedais",
    "pedaleira",
    "amplificador",
    "amplificadores",
    "cubo",
    "caixa amplificada",
    "correia",
    "capotraste",
    "suporte",
    "estante",
    "baqueta",
    "baquetas",
    "boquilha",
]


def calcular_opcoes_pagamento(
    preco_tabela: float,
    tem_promocao_ativa: bool = False,
    desconto_promocao_pct: int = 0,
) -> dict[str, Any]:
    """Calcula preços à vista, PIX e opções de parcelamento conforme Seções 3, 3.1 e 6.2 do Manual."""
    if tem_promocao_ativa and desconto_promocao_pct > 0:
        preco_vigente = round(preco_tabela * (1.0 - desconto_promocao_pct / 100.0), 2)
        # Regra 6.2: Promoções não são cumulativas; desconto PIX (5%) não se aplica sobre preço promocional
        preco_pix = preco_vigente
        regra_pix = (
            "Item já em promoção ativa; conforme Seção 6.2 do manual, o desconto de 5% no PIX "
            "não é cumulativo com preços promocionais."
        )
    else:
        preco_vigente = round(preco_tabela, 2)
        preco_pix = round(preco_tabela * 0.95, 2)
        regra_pix = "5% de desconto à vista no PIX sobre o preço de tabela (Seção 3)."

    # Regras de parcelamento (Seção 3.1):
    # - 1x a 3x sem juros: parcela mínima R$ 50,00 (ou 1x para qualquer valor)
    # - 4x a 6x sem juros: parcela mínima R$ 80,00
    # - 7x a 12x sem juros: parcela mínima R$ 100,00
    opcoes_parcelamento: list[dict[str, Any]] = []
    max_parcelas = 1
    for n in range(1, 13):
        valor_parcela = round(preco_vigente / n, 2)
        elegivel = False
        if n == 1:
            elegivel = True
        elif 2 <= n <= 3 and valor_parcela >= 50.0:
            elegivel = True
        elif 4 <= n <= 6 and valor_parcela >= 80.0:
            elegivel = True
        elif 7 <= n <= 12 and valor_parcela >= 100.0:
            elegivel = True

        if elegivel:
            max_parcelas = n
            opcoes_parcelamento.append(
                {
                    "parcelas": n,
                    "valor_parcela_brl": valor_parcela,
                    "sem_juros": True,
                }
            )

    valor_max_parcela = round(preco_vigente / max_parcelas, 2)
    permite_combinacao = preco_vigente > 2000.0

    return {
        "preco_tabela_brl": round(preco_tabela, 2),
        "preco_vigente_brl": preco_vigente,
        "tem_promocao_ativa": tem_promocao_ativa,
        "desconto_promocao_percent": desconto_promocao_pct if tem_promocao_ativa else 0,
        "preco_pix_brl": preco_pix,
        "economia_pix_brl": round(preco_tabela - preco_pix, 2),
        "regra_pix": regra_pix,
        "cartao_debito_brl": preco_vigente,
        "boleto_bancario_brl": preco_vigente,
        "max_parcelas_sem_juros": max_parcelas,
        "resumo_max_parcelamento": f"Até {max_parcelas}x de R$ {valor_max_parcela:.2f} sem juros no cartão de crédito",
        "permite_combinar_pagamentos": permite_combinacao,
        "regra_combinacao": (
            "Permitida combinação de formas de pagamento (ex.: PIX + cartão) pois o valor supera R$ 2.000,00 (Seção 3.1)."
            if permite_combinacao
            else "Combinação de pagamentos (PIX + cartão) permitida apenas para compras acima de R$ 2.000,00 (Seção 3.1)."
        ),
        "opcoes_parcelamento": opcoes_parcelamento,
    }


class AgentToolkit:
    """Conjunto de ferramentas estruturadas expostas ao agente LLM via Function Calling."""

    def __init__(
        self,
        database: StoreDatabase = db,
        rag: PolicyRAG = policy_rag,
        reference_date: date | None = None,
    ) -> None:
        self.db = database
        self.rag = rag
        self.reference_date = reference_date or settings.reference_date

    def buscar_produtos(
        self,
        termo_busca: str | None = None,
        categoria: str | None = None,
        preco_max: float | None = None,
        preco_min: float | None = None,
        tipo_corda: str | None = None,
        eletrico: str | None = None,
        apenas_disponiveis: bool = False,
        limite: int = 15,
    ) -> dict[str, Any]:
        """Busca instrumentos no catálogo da loja com filtros de categoria, preço, corda, captação e estoque."""
        q_norm = normalize_text(termo_busca or "")
        cat_norm = normalize_text(categoria or "")

        # 1. Verificar se a busca é por acessórios fora do escopo da loja (Seções 1 e 7.1)
        combined_query = f"{q_norm} {cat_norm}".strip()
        for acc in ACCESSORY_KEYWORDS:
            if acc in combined_query:
                # Exceção: "violão 7 cordas" ou "cordas de nylon/aço" refere-se a violão
                if acc in {"corda avulsa", "jogo de cordas", "encordoamento"} or (
                    "violao" not in combined_query
                    and "violoes" not in combined_query
                    and "guitarra" not in combined_query
                    and "ukulele" not in combined_query
                    and "baixo" not in combined_query
                ):
                    return {
                        "fora_de_escopo_acessorio": True,
                        "termo_identificado": acc,
                        "mensagem_politica": (
                            "A Empório da Música trabalha exclusivamente com instrumentos musicais. "
                            "Não comercializamos acessórios como cordas avulsas, palhetas, cabos, cases, "
                            "pedais ou amplificadores (Seções 1 e 7.1 do Manual de Políticas)."
                        ),
                        "produtos_encontrados": [],
                    }

        # 2. Mapear categoria se informada no termo_busca ou no parâmetro categoria
        category_aliases: dict[int, list[str]] = {
            1: ["guitarra", "guitarras", "stratocaster", "les paul", "telecaster", "rg550", "prs"],
            2: ["baixo", "baixos", "contrabaixo", "contrabaixos", "bass"],
            3: ["bateria", "baterias", "percussao"],
            4: ["teclado", "teclados", "piano", "pianos", "sintetizador", "synth"],
            5: ["violao", "violoes", "dreadnought", "folk", "7 cordas"],
            6: ["sopro madeira", "flauta", "clarinete", "saxofone", "sax", "oboe"],
            7: ["sopro metal", "trompete", "trombone", "tuba", "trompa"],
            8: ["cordas orquestrais", "violino", "viola de arco", "violoncelo", "cello"],
            9: ["ukulele", "ukuleles", "soprano", "concert", "tenor", "baritono"],
        }

        target_cat_id: int | None = None
        if cat_norm:
            for cid, aliases in category_aliases.items():
                if any(a in cat_norm for a in aliases):
                    target_cat_id = cid
                    break
        elif q_norm:
            # Se o termo de busca for exatamente o nome de uma categoria
            for cid, aliases in category_aliases.items():
                if q_norm in aliases:
                    target_cat_id = cid
                    q_norm = ""  # Já filtrou pela categoria
                    break

        # Verificar categorias sem estoque cadastrado no CSV (6, 7, 8)
        if target_cat_id in {6, 7, 8}:
            cat_rows = self.db.execute_query(
                "SELECT * FROM categories WHERE category_id = ?", (target_cat_id,)
            )
            cat_info = cat_rows[0] if cat_rows else {"name": categoria}
            return {
                "categoria_sem_itens_no_catalogo": True,
                "categoria": cat_info.get("name"),
                "mensagem": (
                    f"A categoria '{cat_info.get('name')}' faz parte do portfólio da Empório da Música, "
                    "porém não há modelos com estoque ativo cadastrados no sistema no momento."
                ),
                "produtos_encontrados": [],
            }

        sql = "SELECT * FROM products WHERE 1=1"
        params: list[Any] = []

        if target_cat_id is not None:
            sql += " AND category_id = ?"
            params.append(target_cat_id)

        if preco_max is not None:
            # Considera tanto preço de tabela quanto preço promocional efetivo
            sql += " AND effective_price_brl <= ?"
            params.append(float(preco_max))

        if preco_min is not None:
            sql += " AND effective_price_brl >= ?"
            params.append(float(preco_min))

        if tipo_corda:
            tc_norm = normalize_text(tipo_corda)
            if "nylon" in tc_norm:
                sql += " AND spec_strings = 'nylon'"
            elif "aco" in tc_norm or "steel" in tc_norm:
                sql += " AND spec_strings = 'steel'"

        if eletrico:
            el_norm = normalize_text(eletrico)
            if el_norm in {"sim", "yes", "true", "1", "eletroacustico", "eletrico"}:
                sql += " AND spec_electronics = 'yes'"
            elif el_norm in {"nao", "no", "false", "0", "acustico"}:
                sql += " AND spec_electronics = 'no'"

        if apenas_disponiveis:
            sql += " AND availability = 'available'"

        sql += " ORDER BY effective_price_brl ASC"
        rows = self.db.execute_query(sql, params)

        # Filtragem por termos de busca (marca, modelo, características)
        if q_norm:
            stopwords = {
                "de",
                "da",
                "do",
                "para",
                "com",
                "sem",
                "um",
                "uma",
                "ate",
                "reais",
                "opcoes",
                "opcao",
                "disponiveis",
                "disponivel",
                "modelo",
                "modelos",
                "violao",
                "violoes",
                "ukulele",
                "ukuleles",
                "guitarra",
                "guitarras",
                "baixo",
                "baixos",
                "bateria",
                "baterias",
                "teclado",
                "teclados",
            }
            tokens = [t for t in q_norm.split() if t not in stopwords and len(t) > 1]
            # Se o usuário buscou apenas o nome da categoria (ex: "violões"), mantemos todos da categoria
            if tokens:
                scored_rows: list[tuple[int, dict[str, Any]]] = []
                for r in rows:
                    score = 0
                    name_n = r["name_norm"]
                    blob_n = r["search_blob"]
                    for tok in tokens:
                        if tok in name_n:
                            score += 3
                        elif tok in blob_n:
                            score += 1
                    if score > 0:
                        scored_rows.append((score, r))
                scored_rows.sort(key=lambda x: (-x[0], x[1]["effective_price_brl"]))
                rows = [r for _, r in scored_rows]

        formatted: list[dict[str, Any]] = []
        unavailable_found: list[dict[str, Any]] = []

        for r in rows[:limite]:
            pgto = calcular_opcoes_pagamento(
                preco_tabela=float(r["price_brl"]),
                tem_promocao_ativa=bool(r["has_active_promo"]),
                desconto_promocao_pct=int(r["promo_discount_percent"]),
            )
            item = {
                "product_id": r["product_id"],
                "nome": r["name"],
                "categoria": r["category_name"],
                "preco_tabela_brl": float(r["price_brl"]),
                "preco_vigente_brl": float(r["effective_price_brl"]),
                "preco_pix_brl": pgto["preco_pix_brl"],
                "promocao_ativa": (
                    {
                        "desconto_percent": int(r["promo_discount_percent"]),
                        "campanha": r["promo_description"],
                        "preco_original_brl": float(r["price_brl"]),
                        "preco_promocional_brl": float(r["effective_price_brl"]),
                    }
                    if r["has_active_promo"]
                    else None
                ),
                "parcelamento_max": pgto["resumo_max_parcelamento"],
                "estoque": int(r["stock_quantity"]),
                "status_catalogo": r["status"],
                "disponibilidade": r["availability"],
                "cordas": r["spec_strings"] or None,
                "eletroacustico": r["spec_electronics"] == "yes" if r["spec_electronics"] else None,
                "cor": r["spec_color"] or None,
                "descricao": r["description"],
                "alerta_cadastro": r["data_anomaly"] or None,
            }
            formatted.append(item)
            if r["availability"] != "available":
                unavailable_found.append(item)

        # Se algum produto retornado estiver sem estoque ou descontinuado, sugerir alternativas ativas (Seção 7.3)
        alternativas: list[dict[str, Any]] = []
        if unavailable_found:
            ref_item = unavailable_found[0]
            ref_cat_rows = self.db.execute_query(
                """
                SELECT product_id, name, price_brl, effective_price_brl, stock_quantity, spec_strings, spec_electronics
                FROM products
                WHERE category_name = ? AND availability = 'available' AND product_id != ?
                ORDER BY ABS(effective_price_brl - ?) ASC
                LIMIT 3
                """,
                (ref_item["categoria"], ref_item["product_id"], ref_item["preco_vigente_brl"]),
            )
            for alt in ref_cat_rows:
                alternativas.append(
                    {
                        "product_id": alt["product_id"],
                        "nome": alt["name"],
                        "preco_brl": float(alt["effective_price_brl"]),
                        "estoque": int(alt["stock_quantity"]),
                    }
                )

        return {
            "total_encontrado": len(rows),
            "exibindo": len(formatted),
            "filtros_aplicados": {
                "termo_busca": termo_busca,
                "categoria": categoria,
                "preco_max": preco_max,
                "preco_min": preco_min,
                "tipo_corda": tipo_corda,
                "eletrico": eletrico,
                "apenas_disponiveis": apenas_disponiveis,
            },
            "produtos": formatted,
            "alternativas_sugeridas_para_indisponiveis": alternativas,
        }

    def detalhar_produto_e_pagamento(
        self,
        nome_ou_id_produto: str,
    ) -> dict[str, Any]:
        """Retorna ficha completa de um produto, estoque, histórico de promoções e simulação de pagamento/parcelas."""
        q_raw = str(nome_ou_id_produto).strip()
        rows: list[dict[str, Any]] = []

        if q_raw.isdigit():
            rows = self.db.execute_query(
                "SELECT * FROM products WHERE product_id = ?", (int(q_raw),)
            )

        if not rows:
            q_norm = normalize_text(q_raw)
            all_prods = self.db.execute_query("SELECT * FROM products")
            tokens = [t for t in q_norm.split() if len(t) > 1]
            scored: list[tuple[int, dict[str, Any]]] = []
            for p in all_prods:
                score = 0
                if q_norm in p["name_norm"]:
                    score += 10
                for tok in tokens:
                    if tok in p["name_norm"]:
                        score += 3
                    elif tok in p["search_blob"]:
                        score += 1
                if score > 0:
                    scored.append((score, p))
            scored.sort(key=lambda x: -x[0])
            if scored:
                rows = [scored[0][1]]

        if not rows:
            # Verifica se é um acessório fora de escopo
            q_norm = normalize_text(q_raw)
            for acc in ACCESSORY_KEYWORDS:
                if acc in q_norm:
                    return {
                        "encontrado": False,
                        "fora_de_escopo_acessorio": True,
                        "mensagem": (
                            "A Empório da Música trabalha exclusivamente com instrumentos musicais "
                            "e não comercializa acessórios (cordas, palhetas, cabos, cases, pedais ou amplificadores)."
                        ),
                    }
            return {
                "encontrado": False,
                "mensagem": f"Nenhum produto encontrado para '{nome_ou_id_produto}'.",
            }

        prod = rows[0]
        pid = int(prod["product_id"])

        # Consultar promoções ativas e expiradas deste produto (Seção 6.2 e 7.3)
        promos = self.db.execute_query(
            "SELECT * FROM promotions WHERE product_id = ? ORDER BY is_active DESC, discount_percent DESC",
            (pid,),
        )
        promocoes_ativas = [
            {
                "promotion_id": pr["promotion_id"],
                "campanha": pr["description"],
                "desconto_percent": int(pr["discount_percent"]),
                "preco_original_brl": float(prod["price_brl"]),
                "preco_promocional_brl": round(
                    float(prod["price_brl"]) * (1.0 - int(pr["discount_percent"]) / 100.0), 2
                ),
            }
            for pr in promos
            if int(pr["is_active"]) == 1
        ]
        promocoes_expiradas = [
            {
                "promotion_id": pr["promotion_id"],
                "campanha": pr["description"],
                "desconto_percent_expirado": int(pr["discount_percent"]),
                "status": "expirada (is_active=0)",
            }
            for pr in promos
            if int(pr["is_active"]) == 0
        ]

        pgto = calcular_opcoes_pagamento(
            preco_tabela=float(prod["price_brl"]),
            tem_promocao_ativa=bool(prod["has_active_promo"]),
            desconto_promocao_pct=int(prod["promo_discount_percent"]),
        )

        # Se estiver indisponível ou descontinuado, buscar alternativas disponíveis na mesma categoria
        alternativas: list[dict[str, Any]] = []
        if prod["availability"] != "available":
            alt_rows = self.db.execute_query(
                """
                SELECT product_id, name, effective_price_brl, stock_quantity, description
                FROM products
                WHERE category_id = ? AND availability = 'available' AND product_id != ?
                ORDER BY ABS(effective_price_brl - ?) ASC
                LIMIT 3
                """,
                (prod["category_id"], pid, prod["effective_price_brl"]),
            )
            alternativas = [
                {
                    "product_id": a["product_id"],
                    "nome": a["name"],
                    "preco_brl": float(a["effective_price_brl"]),
                    "estoque": int(a["stock_quantity"]),
                }
                for a in alt_rows
            ]

        try:
            specs_dict = json.loads(prod["specs"]) if prod["specs"] else {}
        except json.JSONDecodeError:
            specs_dict = {}

        return {
            "encontrado": True,
            "product_id": pid,
            "nome": prod["name"],
            "categoria": prod["category_name"],
            "descricao": prod["description"],
            "especificacoes": specs_dict,
            "estoque": int(prod["stock_quantity"]),
            "status_catalogo": prod["status"],
            "disponibilidade": prod["availability"],
            "orientacao_atendimento_estoque": (
                "Produto disponível para pronta entrega."
                if prod["availability"] == "available"
                else (
                    "ATENÇÃO (Política 7.3): Produto temporariamente FORA DE ESTOQUE (estoque = 0). "
                    "Informar indisponibilidade com transparência e sugerir as alternativas disponíveis."
                    if prod["availability"] == "out_of_stock"
                    else (
                        "ATENÇÃO (Política 7.3): Produto DESCONTINUADO. Informar que não faz mais parte "
                        "do catálogo ativo e oferecer modelos equivalentes/sucessores."
                        if prod["availability"] == "discontinued"
                        else "Produto com status 'coming_soon' (pré-lançamento / chegada em breve)."
                    )
                )
            ),
            "promocoes_ativas": promocoes_ativas,
            "promocoes_expiradas": promocoes_expiradas,
            "orientacao_promocao": (
                "Apresentar sempre o preço original, o percentual de desconto e o preço promocional (Política 6.2)."
                if promocoes_ativas
                else (
                    "Este produto já teve promoção no passado, mas encontra-se EXPIRADA (is_active=0). "
                    "Conforme Política 7.3, informar com transparência que a promoção encerrou e apresentar o preço atual."
                    if promocoes_expiradas
                    else "Sem promoções registradas para este item."
                )
            ),
            "condicoes_pagamento": pgto,
            "alternativas_disponiveis": alternativas,
            "alerta_cadastro": prod["data_anomaly"] or None,
        }

    def listar_promocoes(self, incluir_expiradas: bool = False) -> dict[str, Any]:
        """Lista todas as promoções ativas no sistema (e opcionalmente as expiradas)."""
        sql = """
            SELECT
                pr.promotion_id,
                pr.product_id,
                pr.discount_percent,
                pr.description AS promo_campaign,
                pr.is_active,
                p.name AS product_name,
                p.category_name,
                p.price_brl AS original_price_brl,
                p.effective_price_brl,
                p.stock_quantity,
                p.availability
            FROM promotions pr
            JOIN products p ON pr.product_id = p.product_id
        """
        if not incluir_expiradas:
            sql += " WHERE pr.is_active = 1"
        sql += " ORDER BY pr.is_active DESC, pr.discount_percent DESC"

        rows = self.db.execute_query(sql)
        ativas: list[dict[str, Any]] = []
        expiradas: list[dict[str, Any]] = []

        for r in rows:
            orig = float(r["original_price_brl"])
            disc = int(r["discount_percent"])
            promo_price = round(orig * (1.0 - disc / 100.0), 2)
            entry = {
                "promotion_id": r["promotion_id"],
                "product_id": r["product_id"],
                "produto": r["product_name"],
                "categoria": r["category_name"],
                "campanha": r["promo_campaign"],
                "desconto_percent": disc,
                "preco_original_brl": orig,
                "preco_promocional_brl": promo_price,
                "estoque": int(r["stock_quantity"]),
                "disponibilidade": r["availability"],
            }
            if int(r["is_active"]) == 1:
                ativas.append(entry)
            else:
                expiradas.append(entry)

        return {
            "total_ativas": len(ativas),
            "promocoes_ativas": ativas,
            "regras_aplicaveis": [
                "Promoções não são cumulativas: o desconto de 5% no PIX não se aplica sobre preços já promocionais (Seção 6.2).",
                "Sempre apresentar o preço original junto com o percentual de desconto e o preço promocional (Seção 6.2).",
                "Promoções estão sujeitas à disponibilidade de estoque, sem direito a rain check (Seção 6.2).",
            ],
            "promocoes_expiradas": expiradas if incluir_expiradas else [],
        }

    def consultar_pedido(
        self,
        identificador: str,
    ) -> dict[str, Any]:
        """Consulta status de pedido, itens, rastreio e elegibilidade para troca/devolução por ID, cliente, e-mail, telefone ou código de rastreio."""
        raw = str(identificador).strip()
        q_norm = normalize_text(raw)
        q_digits = digits_only(raw)

        # Remover prefixos comuns como "pedido #", "pedido", "#"
        cleaned_id = q_norm.replace("pedido", "").replace("#", "").strip()

        matched_orders: list[dict[str, Any]] = []

        # 1. Busca por order_id exato
        if cleaned_id.isdigit():
            matched_orders = self.db.execute_query(
                """
                SELECT o.*, c.name AS customer_name, c.email, c.phone, c.city
                FROM orders o
                JOIN customers c ON o.customer_id = c.customer_id
                WHERE o.order_id = ?
                """,
                (int(cleaned_id),),
            )

        # 2. Busca por código de rastreamento (ex.: BRAB1234567BR)
        if not matched_orders and len(raw) >= 6:
            matched_orders = self.db.execute_query(
                """
                SELECT o.*, c.name AS customer_name, c.email, c.phone, c.city
                FROM orders o
                JOIN customers c ON o.customer_id = c.customer_id
                WHERE LOWER(o.tracking_code) = LOWER(?)
                """,
                (raw,),
            )

        # 3. Busca por e-mail, telefone ou nome de cliente
        ambiguous_customers: list[dict[str, Any]] = []
        if not matched_orders:
            customers = self.db.execute_query("SELECT * FROM customers")
            matched_cust_ids: list[int] = []
            for c in customers:
                if raw.lower() == c["email_norm"]:
                    matched_cust_ids.append(int(c["customer_id"]))
                elif q_digits and len(q_digits) >= 8 and q_digits in c["phone_digits"]:
                    matched_cust_ids.append(int(c["customer_id"]))
                elif q_norm and len(q_norm) >= 3 and (
                    q_norm in c["name_norm"]
                    or all(tok in c["name_norm"] for tok in q_norm.split() if len(tok) > 2)
                ):
                    matched_cust_ids.append(int(c["customer_id"]))
                    ambiguous_customers.append(
                        {
                            "customer_id": c["customer_id"],
                            "nome": c["name"],
                            "email": c["email"],
                            "cidade": c["city"],
                        }
                    )

            if matched_cust_ids:
                placeholders = ",".join("?" for _ in matched_cust_ids)
                matched_orders = self.db.execute_query(
                    f"""
                    SELECT o.*, c.name AS customer_name, c.email, c.phone, c.city
                    FROM orders o
                    JOIN customers c ON o.customer_id = c.customer_id
                    WHERE o.customer_id IN ({placeholders})
                    ORDER BY o.order_date DESC
                    """,
                    tuple(matched_cust_ids),
                )

        if not matched_orders:
            return {
                "encontrado": False,
                "identificador_buscado": identificador,
                "clientes_homonimos_sem_pedido": ambiguous_customers,
                "mensagem": (
                    f"Nenhum pedido encontrado para '{identificador}'. "
                    "Solicite ao cliente o número do pedido (1 a 20), nome completo, CPF/e-mail ou código de rastreio."
                ),
            }

        status_pt = {
            "delivered": "Entregue",
            "shipped": "Enviado / Em trânsito",
            "confirmed": "Confirmado (em separação para envio)",
            "pending": "Pendente (aguardando confirmação de pagamento/processamento)",
            "cancelled": "Cancelado",
        }

        detailed_orders: list[dict[str, Any]] = []
        for ord_row in matched_orders:
            oid = int(ord_row["order_id"])
            items = self.db.execute_query(
                """
                SELECT oi.quantity, p.product_id, p.name, p.price_brl, p.category_name
                FROM order_items oi
                JOIN products p ON oi.product_id = p.product_id
                WHERE oi.order_id = ?
                """,
                (oid,),
            )

            order_date = date.fromisoformat(str(ord_row["order_date"]))
            est_deliv_str = str(ord_row["estimated_delivery"]).strip()
            deliv_date = date.fromisoformat(est_deliv_str) if est_deliv_str else None

            dias_desde_compra = (self.reference_date - order_date).days
            dias_desde_entrega = (
                (self.reference_date - deliv_date).days if deliv_date else None
            )

            st = str(ord_row["status"]).lower()

            # Avaliação automática das políticas de troca/devolução (Seções 4.1, 4.2, 4.3, 8.1)
            analise_troca_devolucao: dict[str, Any] = {
                "data_referencia_sistema": self.reference_date.isoformat(),
                "dias_corridos_desde_compra": dias_desde_compra,
                "dias_corridos_desde_entrega": dias_desde_entrega,
            }

            if st == "delivered" and deliv_date is not None and dias_desde_entrega is not None:
                elegivel_arrependimento = 0 <= dias_desde_entrega <= 7
                elegivel_defeito_loja = 0 <= dias_desde_compra <= 30
                elegivel_garantia_legal = 0 <= dias_desde_entrega <= 90
                analise_troca_devolucao.update(
                    {
                        "direito_arrependimento_7_dias": {
                            "elegivel_na_data_referencia": elegivel_arrependimento,
                            "prazo_regra": "Até 7 dias corridos após o recebimento (Seção 4.1).",
                            "explicacao": (
                                f"Pedido entregue em {deliv_date.isoformat()} ({dias_desde_entrega} dias corridos até {self.reference_date.isoformat()}). "
                                + (
                                    "DENTRO do prazo de 7 dias corridos para devolução por arrependimento ou troca por preferência! "
                                    "Frete de devolução por conta da loja e reembolso em até 10 dias úteis na mesma forma de pagamento."
                                    if elegivel_arrependimento
                                    else "Prazo de 7 dias corridos para arrependimento/troca por preferência já encerrado desde a entrega registrada."
                                )
                            ),
                        },
                        "troca_por_defeito_30_dias_loja": {
                            "elegivel_na_data_referencia": elegivel_defeito_loja,
                            "prazo_regra": "Até 30 dias corridos após a compra diretamente na loja (Seção 4.2).",
                        },
                        "garantia_legal_90_dias_cdc": {
                            "elegivel_na_data_referencia": elegivel_garantia_legal,
                            "prazo_regra": "Até 90 dias corridos após o recebimento contra defeitos de fabricação (Seção 8.1), além da garantia do fabricante (6 meses a 2 anos, Seção 8.2).",
                        },
                    }
                )
            elif st in {"pending", "confirmed", "shipped"}:
                analise_troca_devolucao["orientacao"] = (
                    "O pedido ainda não foi entregue. Conforme Seção 4.1 do manual, o prazo de 7 dias corridos "
                    "para Direito de Arrependimento passa a contar a partir do recebimento do produto (ou o cliente pode solicitar cancelamento antes da entrega)."
                )
            elif st == "cancelled":
                analise_troca_devolucao["orientacao"] = (
                    f"Pedido já encontra-se cancelado. Motivo registrado: {ord_row['notes'] or 'Não informado'}."
                )

            detailed_orders.append(
                {
                    "order_id": oid,
                    "cliente": {
                        "customer_id": ord_row["customer_id"],
                        "nome": ord_row["customer_name"],
                        "email": ord_row["email"],
                        "telefone": ord_row["phone"],
                        "cidade": ord_row["city"],
                    },
                    "data_pedido": ord_row["order_date"],
                    "status_codigo": st,
                    "status_descricao": status_pt.get(st, st),
                    "valor_total_brl": float(ord_row["total_brl"]),
                    "forma_pagamento": ord_row["payment_method"],
                    "codigo_rastreamento": ord_row["tracking_code"] or None,
                    "previsao_ou_data_entrega": ord_row["estimated_delivery"] or None,
                    "observacoes": ord_row["notes"] or None,
                    "itens": [
                        {
                            "product_id": it["product_id"],
                            "produto": it["name"],
                            "categoria": it["category_name"],
                            "quantidade": int(it["quantity"]),
                            "preco_catalogo_brl": float(it["price_brl"]),
                        }
                        for it in items
                    ],
                    "analise_troca_e_devolucao": analise_troca_devolucao,
                }
            )

        return {
            "encontrado": True,
            "total_pedidos": len(detailed_orders),
            "clientes_homonimos_detectados": ambiguous_customers if len(ambiguous_customers) > 1 else [],
            "pedidos": detailed_orders,
        }

    def calcular_frete_e_entrega(
        self,
        cidade: str,
        valor_pedido_brl: float | None = None,
        instrumento_grande_porte: bool = False,
    ) -> dict[str, Any]:
        """Calcula custos, modalidades e prazos de frete conforme a cidade e o valor do pedido (Seção 5 do Manual)."""
        c_norm = normalize_text(cidade)
        is_cg = any(
            term in c_norm
            for term in ["campo grande", "regiao metropolitana", "terenos", "sidrolandia", "jaraguari"]
        )

        if is_cg:
            frete_gratis = valor_pedido_brl is not None and valor_pedido_brl >= 500.0
            custo = (
                0.0
                if frete_gratis
                else (35.0 if valor_pedido_brl is not None else "Grátis acima de R$ 500,00 ou taxa fixa de R$ 35,00 abaixo de R$ 500,00")
            )
            return {
                "regiao": "Região Metropolitana de Campo Grande/MS (Seção 5.1)",
                "cidade_informada": cidade,
                "valor_pedido_brl": valor_pedido_brl,
                "frete_gratis": frete_gratis,
                "custo_frete_brl": custo,
                "prazo_entrega": "1 a 3 dias úteis",
                "modalidade": "Motoboy próprio da Empório da Música (cliente é contactado por telefone antes da entrega)",
                "seguro_incluso": True,
            }

        return {
            "regiao": "Outras Cidades / Fora da Região Metropolitana de Campo Grande (Seção 5.2)",
            "cidade_informada": cidade,
            "valor_pedido_brl": valor_pedido_brl,
            "calculo_valor": "Calculado automaticamente com base no CEP de destino, peso e dimensões do produto.",
            "modalidades_disponiveis": [
                {
                    "modalidade": "SEDEX (Correios)",
                    "prazo_estimado": "2 a 5 dias úteis",
                    "rastreamento": "Sim (formato BR + 9 caracteres + BR)",
                    "seguro": "Incluído contra extravios e danos",
                },
                {
                    "modalidade": "Jadlog (.package)",
                    "prazo_estimado": "3 a 8 dias úteis",
                    "rastreamento": "Sim",
                    "seguro": "Incluído contra extravios e danos",
                },
                {
                    "modalidade": "PAC (Correios)",
                    "prazo_estimado": "5 a 12 dias úteis",
                    "rastreamento": "Sim",
                    "seguro": "Incluído contra extravios e danos",
                },
            ],
            "alerta_grande_porte": (
                "Instrumentos de grande porte (baterias acústicas, pianos digitais, contrabaixos) "
                "podem exigir frete especial com cotação individual (Seção 5.2)."
                if instrumento_grande_porte
                else "Nota: Baterias acústicas, pianos digitais e contrabaixos podem exigir cotação individual de frete."
            ),
            "orientacao_avaria": "Em caso de avaria no transporte, o cliente deve recusar o recebimento e contatar imediatamente a loja (Seção 5.2).",
        }

    def consultar_politicas_loja(self, pergunta: str) -> dict[str, Any]:
        """Busca trechos relevantes no Manual de Políticas e Procedimentos da Empório da Música (PDF)."""
        trechos = self.rag.search(pergunta, top_k=3)
        return {
            "pergunta": pergunta,
            "documento_fonte": "data/políticas_da_loja.pdf (Versão 2.1 — Junho de 2025)",
            "secoes_encontradas": trechos,
        }

    def get_openai_tools_schema(self) -> list[dict[str, Any]]:
        """Retorna as definições de ferramentas no formato JSON Schema (OpenAI / Groq / Gemini / Ollama)."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "buscar_produtos",
                    "description": (
                        "Busca instrumentos musicais no catálogo da Empório da Música filtrando por termo/modelo/marca, "
                        "categoria (Violões, Ukuleles, Guitarras, Baixos, Baterias, Teclados), preço máximo/mínimo, "
                        "tipo de corda (nylon ou steel/aço), captação elétrica e disponibilidade em estoque."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "termo_busca": {
                                "type": "string",
                                "description": "Termo livre: modelo, marca ou característica (ex.: 'Takamine', 'Yamaha', '7 cordas', 'dreadnought').",
                            },
                            "categoria": {
                                "type": "string",
                                "description": "Categoria do instrumento: 'Violões', 'Ukuleles', 'Guitarras', 'Baixos', 'Baterias', 'Teclados', 'Sopro', 'Cordas Orquestrais'.",
                            },
                            "preco_max": {
                                "type": "number",
                                "description": "Preço máximo em reais (R$). Ex.: 1000 para até R$ 1.000,00.",
                            },
                            "preco_min": {
                                "type": "number",
                                "description": "Preço mínimo em reais (R$).",
                            },
                            "tipo_corda": {
                                "type": "string",
                                "enum": ["nylon", "steel"],
                                "description": "Filtrar por tipo de corda ('nylon' ou 'steel' para aço).",
                            },
                            "eletrico": {
                                "type": "string",
                                "enum": ["sim", "nao"],
                                "description": "Filtrar por captação elétrica/eletroacústica ('sim' ou 'nao').",
                            },
                            "apenas_disponiveis": {
                                "type": "boolean",
                                "description": "Se true, retorna apenas produtos ativos com estoque > 0.",
                            },
                        },
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "detalhar_produto_e_pagamento",
                    "description": (
                        "Consulta detalhes completos de um instrumento específico (preço, estoque, especificações técnicas, "
                        "promoções ativas ou expiradas, valor com desconto no PIX e tabela de parcelamento sem juros)."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "nome_ou_id_produto": {
                                "type": "string",
                                "description": "Nome do modelo (ex.: 'Takamine GD20', 'Yamaha C40', 'Giannini GF-3D') ou product_id numérico.",
                            }
                        },
                        "required": ["nome_ou_id_produto"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "listar_promocoes",
                    "description": "Lista todos os instrumentos que estão em promoção ativa no momento (e opcionalmente promoções expiradas).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "incluir_expiradas": {
                                "type": "boolean",
                                "description": "Se true, inclui também o histórico de promoções encerradas (is_active=0).",
                            }
                        },
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "consultar_pedido",
                    "description": (
                        "Consulta informações de pedidos (status, código de rastreio, previsão/data de entrega, itens comprados "
                        "e análise automática de prazo para troca ou devolução por arrependimento/defeito) buscando por "
                        "número do pedido, nome do cliente, e-mail, telefone ou código de rastreamento."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "identificador": {
                                "type": "string",
                                "description": "Número do pedido (ex.: '7', '19'), nome do cliente (ex.: 'Letícia Gonçalves', 'Pedro Oliveira'), e-mail, telefone ou código de rastreio.",
                            }
                        },
                        "required": ["identificador"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "calcular_frete_e_entrega",
                    "description": "Consulta valor de frete, modalidades de envio (Motoboy, PAC, SEDEX, Jadlog) e prazo de entrega para uma cidade.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "cidade": {
                                "type": "string",
                                "description": "Nome da cidade de destino (ex.: 'Campo Grande', 'Dourados', 'Três Lagoas', 'Corumbá', 'São Paulo').",
                            },
                            "valor_pedido_brl": {
                                "type": "number",
                                "description": "Valor do pedido em R$ para verificar elegibilidade a frete grátis em Campo Grande (acima de R$ 500).",
                            },
                            "instrumento_grande_porte": {
                                "type": "boolean",
                                "description": "True se for bateria acústica, piano digital ou contrabaixo.",
                            },
                        },
                        "required": ["cidade"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "consultar_politicas_loja",
                    "description": (
                        "Consulta o Manual de Políticas e Procedimentos da Empório da Música (PDF) sobre endereço, "
                        "horário de funcionamento, contatos/WhatsApp, formas de pagamento, regras de parcelamento, "
                        "política de trocas e devoluções (arrependimento 7 dias, defeito 30 dias), garantia legal (90 dias), "
                        "frete, promoções, escopo (não vende acessórios) e LGPD."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "pergunta": {
                                "type": "string",
                                "description": "Pergunta ou tópico a buscar no manual de políticas (ex.: 'horário de funcionamento e endereço', 'regras de devolução por arrependimento').",
                            }
                        },
                        "required": ["pergunta"],
                    },
                },
            },
        ]

    def dispatch(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Executa uma ferramenta pelo nome com os argumentos fornecidos."""
        fn_map = {
            "buscar_produtos": self.buscar_produtos,
            "detalhar_produto_e_pagamento": self.detalhar_produto_e_pagamento,
            "listar_promocoes": self.listar_promocoes,
            "consultar_pedido": self.consultar_pedido,
            "calcular_frete_e_entrega": self.calcular_frete_e_entrega,
            "consultar_politicas_loja": self.consultar_politicas_loja,
        }
        if tool_name not in fn_map:
            return {"erro": f"Ferramenta '{tool_name}' desconhecida."}
        try:
            return fn_map[tool_name](**arguments)
        except TypeError as exc:
            return {"erro": f"Parâmetros inválidos para '{tool_name}': {exc}"}
        except Exception as exc:
            return {"erro": f"Falha ao executar '{tool_name}': {exc}"}


toolkit = AgentToolkit()
