"""Interface de Linha de Comando (CLI) interativa para o Agente da Empório da Música."""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from typing import Any

from src.agent import EmporioMusicaAgent
from src.config import settings


def _ensure_utf8_stdio() -> None:
    """Garante codificação UTF-8 no terminal Windows/Linux/macOS para acentos e emojis."""
    for stream_name in ("stdout", "stderr", "stdin"):
        stream = getattr(sys, stream_name, None)
        if stream is not None and hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass


def _print_banner(provider: str, model: str, session_id: str) -> None:
    print("=" * 76)
    print(" 🎸 EMPÓRIO DA MÚSICA — Assistente Virtual de Atendimento (Campo Grande/MS)")
    print("    'Sua música começa aqui.' | Rua 14 de Maio, 3200 — Centro")
    print("=" * 76)
    print(f" Provedor ativo : {provider} ({model})")
    print(f" Sessão atual   : {session_id}")
    print(" Comandos úteis : /ajuda | /tools (exibir/ocultar tools) | /historico | /limpar | /sair")
    print("=" * 76)
    print()


def _format_tool_trace(tool_calls: list[dict[str, Any]]) -> str:
    if not tool_calls:
        return "  [Nenhuma ferramenta externa acionada neste turno]"
    lines = ["  ┌── 🛠️ Ferramentas acionadas pelo Agente:"]
    for idx, tc in enumerate(tool_calls, start=1):
        args_str = json.dumps(tc.get("arguments", {}), ensure_ascii=False)
        lines.append(f"  │ {idx}. {tc.get('tool')}({args_str})")
    lines.append("  └──")
    return "\n".join(lines)


def run_demo_scenarios(agent: EmporioMusicaAgent, show_tools: bool = True) -> None:
    """Executa uma demonstração rápida dos principais cenários do desafio no terminal."""
    demo_prompts = [
        "Quais opções de violões disponíveis custando até R$1000?",
        "Quanto custa o Takamine GD20? Ele está em promoção ou tem desconto no PIX?",
        "Qual o endereço e horário de funcionamento da loja?",
        "Oi, sou a Letícia Gonçalves Rocha! Me arrependi da minha compra do pedido #7, posso devolver?",
        "Vocês vendem encordoamento Elixir e amplificador para guitarra?",
    ]
    session_id = f"demo-{uuid.uuid4().hex[:6]}"
    print(f"\n▶ Executando {len(demo_prompts)} cenários de demonstração (sessão: {session_id})...\n")
    for idx, prompt in enumerate(demo_prompts, start=1):
        print(f"─── [Cenário {idx}/{len(demo_prompts)}] " + "─" * 52)
        print(f"👤 Cliente: {prompt}\n")
        resp = agent.chat(prompt, session_id=session_id)
        if show_tools and resp.tool_calls:
            print(_format_tool_trace(resp.tool_calls))
            print()
        print(f"🤖 Empório da Música:\n{resp.reply}\n")


def main(argv: list[str] | None = None) -> int:
    """Ponto de entrada principal da CLI."""
    _ensure_utf8_stdio()
    parser = argparse.ArgumentParser(
        description="Agente de Atendimento — Empório da Música (Desafio Técnico AI Engineer)"
    )
    parser.add_argument(
        "--session",
        type=str,
        default=f"sessao-{uuid.uuid4().hex[:6]}",
        help="ID da sessão para persistência do histórico de conversa.",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Executa automaticamente os cenários de demonstração no terminal e encerra.",
    )
    parser.add_argument(
        "--mensagem",
        "-m",
        type=str,
        default=None,
        help="Envia uma única mensagem ao agente, imprime a resposta e encerra.",
    )
    parser.add_argument(
        "--hide-tools",
        action="store_true",
        help="Oculta o log de chamadas de ferramentas (Function Calling) no terminal.",
    )
    args = parser.parse_args(argv)

    agent = EmporioMusicaAgent()
    provider = settings.resolve_provider()
    model = settings.resolve_model(provider)
    show_tools = not args.hide_tools

    if args.demo:
        _print_banner(provider, model, args.session)
        run_demo_scenarios(agent, show_tools=show_tools)
        return 0

    if args.mensagem:
        resp = agent.chat(args.mensagem, session_id=args.session)
        if show_tools and resp.tool_calls:
            print(_format_tool_trace(resp.tool_calls))
            print()
        print(resp.reply)
        return 0

    _print_banner(provider, model, args.session)
    print(
        "🤖 Empório da Música: Olá! Bem-vindo(a) à Empório da Música! 🎸\n"
        "Como posso ajudar você hoje? (Ex.: buscar instrumentos, consultar preços/promoções, "
        "rastrear pedido ou tirar dúvidas sobre trocas, frete e horários)\n"
    )

    while True:
        try:
            user_input = input("👤 Você: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nAté logo! 🎶 Empório da Música — Sua música começa aqui.")
            break

        if not user_input:
            continue

        cmd = user_input.lower()
        if cmd in {"/sair", "/exit", "/quit", "sair"}:
            print("\nAté logo! Foi um prazer atender você. 🎶 Empório da Música — Sua música começa aqui!")
            break
        if cmd == "/ajuda":
            print(
                "\nComandos disponíveis:\n"
                "  /tools     - Alterna a exibição das ferramentas acionadas pelo agente\n"
                "  /historico - Mostra o histórico salvo na sessão atual\n"
                "  /limpar    - Limpa o histórico da sessão atual\n"
                "  /demo      - Roda os 5 cenários de demonstração\n"
                "  /sair      - Encerra o atendimento\n"
            )
            continue
        if cmd == "/tools":
            show_tools = not show_tools
            print(f"\n[Exibição de ferramentas: {'ATIVADA' if show_tools else 'OCULTADA'}]\n")
            continue
        if cmd == "/limpar":
            agent.memory.clear_session(args.session)
            print("\n[Histórico da sessão limpo com sucesso!]\n")
            continue
        if cmd == "/historico":
            hist = agent.memory.get_history(args.session, limit=20)
            print(f"\n─── Histórico da Sessão ({args.session}) — {len(hist)} mensagens ───")
            for h in hist:
                role_label = "👤 Você" if h["role"] == "user" else "🤖 Agente"
                print(f"{role_label} ({h['created_at'][:19]}): {h['content'][:140]}...")
            print("─" * 60 + "\n")
            continue
        if cmd == "/demo":
            run_demo_scenarios(agent, show_tools=show_tools)
            continue

        resp = agent.chat(user_input, session_id=args.session)
        print()
        if show_tools and resp.tool_calls:
            print(_format_tool_trace(resp.tool_calls))
            print()
        print(f"🤖 Empório da Música:\n{resp.reply}\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
