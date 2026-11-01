"""Gera os 5 arquivos de exemplo de conversação em examples/*.md executando o Agente real."""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.agent import EmporioMusicaAgent
from src.memory import ConversationMemory
from src.tools import AgentToolkit


def render_conversation_md(
    title: str,
    scenario_description: str,
    turns: list[str],
    reference_date: date = date(2026, 3, 23),
) -> str:
    """Executa uma conversa multi-turno com o agente e formata em Markdown com trace de tools."""
    tk = AgentToolkit(reference_date=reference_date)
    mem = ConversationMemory(":memory:")
    agent = EmporioMusicaAgent(agent_toolkit=tk, memory=mem)
    session_id = "exemplo-sessao"

    lines: list[str] = [
        f"# {title}",
        "",
        f"> **Cenário demonstrado:** {scenario_description}",
        f"> **Data de referência do sistema:** `{reference_date.isoformat()}`",
        "",
        "---",
        "",
    ]

    for idx, user_msg in enumerate(turns, start=1):
        resp = agent.chat(user_msg, session_id=session_id)
        lines.append(f"## Turno {idx}")
        lines.append("")
        lines.append(f"### 👤 Cliente")
        lines.append(f"> {user_msg}")
        lines.append("")

        if resp.tool_calls:
            lines.append("<details>")
            lines.append(
                f"<summary>🛠️ <b>Ferramentas acionadas pelo Agente ({len(resp.tool_calls)} call{'s' if len(resp.tool_calls) > 1 else ''})</b></summary>"
            )
            lines.append("")
            for tc in resp.tool_calls:
                args_str = json.dumps(tc["arguments"], ensure_ascii=False)
                lines.append(f"- **`{tc['tool']}({args_str})`**")
            lines.append("")
            lines.append("</details>")
            lines.append("")

        lines.append("### 🤖 Agente (Empório da Música)")
        lines.append("")
        lines.append(resp.reply)
        lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def main() -> None:
    examples_dir = BASE_DIR / "examples"
    examples_dir.mkdir(parents=True, exist_ok=True)

    scenarios = [
        (
            "01_catalogo_violoes_ate_1000.md",
            "Exemplo 1 — Consulta ao Catálogo de Produtos e Tratamento de Indisponibilidade",
            (
                "Cliente busca violões disponíveis até R$ 1.000,00 e, em seguida, pergunta especificamente "
                "sobre o Giannini GF-3D (que custa R$ 799,90 mas está com estoque zero) e o Shelby SN-7C "
                "(descontinuado), demonstrando a aplicação rigorosa da Seção 7.3 do Manual."
            ),
            [
                "Oi, meu nome é Lucas! Quais opções de violões disponíveis custando até R$1000?",
                "Eu vi em um anúncio antigo o violão Giannini GF-3D e o Shelby SN-7C de 7 cordas. Vocês têm eles em estoque?",
            ],
            date(2026, 3, 23),
        ),
        (
            "02_preco_promocoes_e_pagamento_takamine.md",
            "Exemplo 2 — Consulta de Preço, Promoções (Ativas vs Expiradas) e Regras de Pagamento",
            (
                "Cliente consulta o preço do Takamine GD20 (R$ 2.199,00), verifica se uma promoção antiga ainda vale "
                "(Seção 7.3 — promoção expirada), simula pagamento no PIX (5%) e parcelamento sem juros (Seção 3.1), "
                "e pergunta quais violões/ukuleles estão em promoção ativa agora (Seção 6.2 — não cumulatividade do PIX)."
            ),
            [
                "Olá! Quanto custa o Takamine GD20? Como ficam as opções de pagamento no PIX e parcelado no cartão?",
                "E quais instrumentos estão em promoção ativa hoje na loja? O desconto do PIX acumula com a promoção do Taylor 110e?",
            ],
            date(2026, 3, 23),
        ),
        (
            "03_devolucao_arrependimento_e_rastreio_pedidos.md",
            "Exemplo 3 — Situação Não-Trivial: Políticas de Devolução + Consulta de Pedidos em Tempo Real",
            (
                "Cliente pergunta sobre devolução por arrependimento (Seção 4.1) e consulta o Pedido #7 (entregue em "
                "2026-02-17) e o Pedido #8 (em trânsito), cruzando dados reais de orders.csv, customers.csv e "
                "order_items.csv com as regras do Código de Defesa do Consumidor e do Manual de Políticas."
            ),
            [
                "Me arrependi da minha compra, posso devolver meu pedido?",
                "Sou a Letícia Gonçalves Rocha, meu pedido é o #7. Recebi há poucos dias, consigo devolver? E se tivesse vindo com defeito?",
                "Aproveitando, minha irmã Ana Carolina Ferreira fez o pedido #8. Qual o status e o código de rastreio dele?",
            ],
            date(2026, 2, 20),  # Data 3 dias após a entrega do pedido #7 (2026-02-17) para demonstrar elegibilidade dentro dos 7 dias!
        ),
        (
            "04_informacoes_gerais_frete_e_horario.md",
            "Exemplo 4 — Informações Gerais da Loja, Horário de Funcionamento e Cálculo de Frete",
            (
                "Cliente solicita endereço, horário de funcionamento, contatos de WhatsApp e consulta regras e "
                "custos de entrega para Campo Grande/MS (motoboy próprio / frete grátis acima de R$ 500) e Dourados/MS "
                "(PAC, SEDEX e Jadlog — Seção 5)."
            ),
            [
                "Qual o endereço da loja, telefone de contato e o horário de funcionamento durante a semana e no sábado?",
                "Quanto fica o frete para entregar um violão de R$ 600 aqui em Campo Grande? E se eu pedir para entregar na casa do meu primo em Dourados?",
            ],
            date(2026, 3, 23),
        ),
        (
            "05_fora_de_escopo_acessorios_e_off_topic.md",
            "Exemplo 5 — Guardrails de Escopo: Solicitação de Acessórios e Perguntas Off-Topic",
            (
                "Cliente pede acessórios (encordoamento, palhetas e amplificador — fora do escopo conforme Seções 1 e 7.1, "
                "pois a loja vende exclusivamente instrumentos musicais) e depois faz uma pergunta fora do domínio "
                "(receita culinária), demonstrando redirecionamento educado e manutenção da persona."
            ),
            [
                "Vocês têm encordoamento Elixir 0.10, palhetas e amplificador para guitarra?",
                "Haha entendi! E você sabe me passar uma receita de bolo de cenoura com cobertura de chocolate?",
            ],
            date(2026, 3, 23),
        ),
    ]

    for filename, title, desc, turns, ref_dt in scenarios:
        md_content = render_conversation_md(title, desc, turns, reference_date=ref_dt)
        out_path = examples_dir / filename
        out_path.write_text(md_content, encoding="utf-8")
        print(f"Gerado: {out_path.relative_to(BASE_DIR)} ({len(md_content)} bytes)")


if __name__ == "__main__":
    main()
