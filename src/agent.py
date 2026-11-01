"""Motor principal do Agente de Atendimento da Empório da Música (ReAct + Function Calling)."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any

import requests

from src.config import Settings, settings
from src.database import normalize_text
from src.memory import ConversationMemory
from src.prompts import SYSTEM_PROMPT
from src.tools import ACCESSORY_KEYWORDS, AgentToolkit, toolkit


@dataclass
class AgentResponse:
    """Resposta estruturada retornada pelo agente a cada turno de conversa."""

    reply: str
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    provider: str = "local"
    model: str = "emporio-react-local-v1"
    session_id: str = "default"


class EmporioMusicaAgent:
    """Agente híbrido com Function Calling multi-provedor (Gemini, OpenAI, Groq, Ollama) e motor ReAct local."""

    OFF_TOPIC_KEYWORDS = [
        "receita de bolo",
        "bolo de cenoura",
        "lasanha",
        "previsao do tempo",
        "quem ganhou o jogo",
        "campeonato brasileiro",
        "futebol",
        "codigo em python",
        "script em javascript",
        "investir em bitcoin",
        "criptomoeda",
        "eleicao",
        "presidente",
        "capital da franca",
        "equacao de segundo grau",
        "horoscopo",
        "piada",
    ]

    KNOWN_MODELS = [
        "takamine gd20",
        "takamine gc5ce",
        "takamine gn51ce",
        "takamine gc1ce",
        "yamaha c40",
        "yamaha c70",
        "yamaha f310",
        "yamaha fg800",
        "yamaha ntx1",
        "yamaha apx600",
        "yamaha cg162s",
        "martin d-28e",
        "martin d-28",
        "taylor 110e",
        "taylor 214ce",
        "giannini gn-15",
        "giannini gf-1r",
        "giannini gf-3d",
        "giannini gnf-3",
        "giannini gwne-7",
        "tagima memphis ac-39",
        "tagima dallas",
        "tagima woodstock",
        "tagima classical",
        "tagima vegas",
        "tagima tw-7",
        "rozini rc-104",
        "rozini rv-174",
        "rozini rv-175",
        "shelby sn-100",
        "shelby sgd-195e",
        "shelby sn-7c",
        "shelby su-21s",
        "crafter ht-100",
        "crafter d-8",
        "crafter ce-15",
        "kala ka-15s",
        "kala ka-c",
        "kala ka-smhce",
        "kala ka-t",
        "kala ka-srt-ctg",
        "kala ka-b",
        "kala ka-abp-ctg",
        "ohana sk-10",
        "ohana ck-20",
        "ohana tk-35g",
        "ohana bk-35e",
        "kalani kal-300s",
        "kalani kal-500c",
        "kalani kal-700t",
        "fender stratocaster",
        "fender telecaster",
        "gibson les paul",
        "ibanez rg550",
        "prs se custom 24",
        "music man bass 1x",
        "ibanez bass 2x",
        "yamaha bass 3x",
        "music man bass 4x",
        "nord synth 2 pro",
        "korg synth 1 pro",
        "roland synth 3 pro",
    ]

    def __init__(
        self,
        agent_settings: Settings = settings,
        agent_toolkit: AgentToolkit = toolkit,
        memory: ConversationMemory | None = None,
    ) -> None:
        self.settings = agent_settings
        self.toolkit = agent_toolkit
        self.memory = memory or ConversationMemory()

    def chat(self, user_message: str, session_id: str = "default") -> AgentResponse:
        """Processa uma mensagem do cliente, mantendo contexto e executando ferramentas."""
        history = self.memory.get_history(session_id=session_id, limit=12)
        self.memory.add_message(session_id=session_id, role="user", content=user_message)

        provider = self.settings.resolve_provider()
        model = self.settings.resolve_model(provider)

        if provider in {"gemini", "openai", "groq", "ollama"}:
            try:
                response = self._run_api_function_calling(
                    user_message=user_message,
                    history=history,
                    provider=provider,
                    model=model,
                    session_id=session_id,
                )
                self.memory.add_message(
                    session_id=session_id,
                    role="assistant",
                    content=response.reply,
                    tool_calls=response.tool_calls,
                )
                return response
            except Exception as exc:
                # Fallback resiliente para o motor ReAct local caso a chave expire ou haja erro de rede
                fallback_resp = self._run_local_react(
                    user_message=user_message,
                    history=history,
                    session_id=session_id,
                )
                fallback_resp.provider = f"local (fallback from {provider}: {type(exc).__name__})"
                self.memory.add_message(
                    session_id=session_id,
                    role="assistant",
                    content=fallback_resp.reply,
                    tool_calls=fallback_resp.tool_calls,
                )
                return fallback_resp

        local_resp = self._run_local_react(
            user_message=user_message,
            history=history,
            session_id=session_id,
        )
        self.memory.add_message(
            session_id=session_id,
            role="assistant",
            content=local_resp.reply,
            tool_calls=local_resp.tool_calls,
        )
        return local_resp

    def _get_api_endpoint_and_headers(self, provider: str) -> tuple[str, dict[str, str]]:
        """Retorna URL e headers compatíveis com o padrão Chat Completions + Tools."""
        if provider == "gemini":
            url = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.settings.gemini_api_key}",
                "Content-Type": "application/json",
            }
            return url, headers
        if provider == "groq":
            url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.settings.groq_api_key}",
                "Content-Type": "application/json",
            }
            return url, headers
        if provider == "ollama":
            base = self.settings.openai_base_url or "http://localhost:11434/v1"
            url = f"{base.rstrip('/')}/chat/completions"
            headers = {"Content-Type": "application/json"}
            if self.settings.openai_api_key:
                headers["Authorization"] = f"Bearer {self.settings.openai_api_key}"
            return url, headers

        base = self.settings.openai_base_url or "https://api.openai.com/v1"
        url = f"{base.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.settings.openai_api_key}",
            "Content-Type": "application/json",
        }
        return url, headers

    def _run_api_function_calling(
        self,
        user_message: str,
        history: list[dict[str, Any]],
        provider: str,
        model: str,
        session_id: str,
    ) -> AgentResponse:
        """Executa o loop de Function Calling via endpoint compatível com OpenAI."""
        url, headers = self._get_api_endpoint_and_headers(provider)
        messages: list[dict[str, Any]] = [{"role": "system", "content": SYSTEM_PROMPT}]
        for h in history:
            if h["role"] in {"user", "assistant"}:
                messages.append({"role": h["role"], "content": h["content"]})
        messages.append({"role": "user", "content": user_message})

        tools_schema = self.toolkit.get_openai_tools_schema()
        executed_tools: list[dict[str, Any]] = []

        for _ in range(4):
            payload: dict[str, Any] = {
                "model": model,
                "messages": messages,
                "tools": tools_schema,
                "tool_choice": "auto",
                "temperature": self.settings.temperature,
            }
            resp = requests.post(url, headers=headers, json=payload, timeout=35)
            resp.raise_for_status()
            data = resp.json()
            choice = data["choices"][0]["message"]

            tool_calls = choice.get("tool_calls")
            if not tool_calls:
                final_text = choice.get("content") or ""
                return AgentResponse(
                    reply=final_text.strip(),
                    tool_calls=executed_tools,
                    provider=provider,
                    model=model,
                    session_id=session_id,
                )

            messages.append(choice)
            for tc in tool_calls:
                fn_name = tc["function"]["name"]
                raw_args = tc["function"].get("arguments", "{}")
                try:
                    parsed_args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
                except json.JSONDecodeError:
                    parsed_args = {}

                tool_output = self.toolkit.dispatch(fn_name, parsed_args)
                executed_tools.append(
                    {
                        "tool": fn_name,
                        "arguments": parsed_args,
                        "output": tool_output,
                    }
                )
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "name": fn_name,
                        "content": json.dumps(tool_output, ensure_ascii=False),
                    }
                )

        # Solicita síntese final após esgotar iterações de ferramentas
        resp = requests.post(
            url,
            headers=headers,
            json={"model": model, "messages": messages, "temperature": self.settings.temperature},
            timeout=35,
        )
        resp.raise_for_status()
        final_text = resp.json()["choices"][0]["message"].get("content") or ""
        return AgentResponse(
            reply=final_text.strip(),
            tool_calls=executed_tools,
            provider=provider,
            model=model,
            session_id=session_id,
        )

    def _run_local_react(
        self,
        user_message: str,
        history: list[dict[str, Any]],
        session_id: str,
    ) -> AgentResponse:
        """Motor ReAct local determinístico: roteia intenções, aciona tools reais e sintetiza a resposta na persona."""
        q_norm = normalize_text(user_message)
        executed_tools: list[dict[str, Any]] = []
        sections_reply: list[str] = []

        def call_tool(name: str, args: dict[str, Any]) -> dict[str, Any]:
            out = self.toolkit.dispatch(name, args)
            executed_tools.append({"tool": name, "arguments": args, "output": out})
            return out

        # Extrair nome do cliente se ele se apresentou na mensagem atual ou no histórico
        customer_first_name = self._extract_customer_greeting_name(user_message, history)
        greeting_prefix = f"Olá, {customer_first_name}! Tudo bem? 🎸\n\n" if customer_first_name else "Olá! Tudo bem? Bem-vindo(a) à **Empório da Música**! 🎸\n\n"
        if history:
            # Em turnos seguintes da mesma conversa, usar transição natural sem repetir "Bem-vindo"
            greeting_prefix = f"Claro, {customer_first_name}!\n\n" if customer_first_name else ""

        # 1. Guardrail: Perguntas totalmente fora do escopo da loja (Off-topic)
        if self._is_off_topic(q_norm):
            reply = (
                f"{greeting_prefix}Haha, adoraria bater esse papo, mas meu ouvido é afinado exclusivamente "
                "para instrumentos musicais! 🎶\n\n"
                "Aqui na **Empório da Música** eu consigo te ajudar a escolher violões, guitarras, baixos, "
                "ukuleles, baterias e teclados, além de consultar preços, promoções, frete, status do seu pedido "
                "ou nossas políticas de troca e garantia.\n\n"
                "Posso te ajudar a encontrar algum instrumento hoje?"
            )
            return AgentResponse(reply=reply, tool_calls=executed_tools, session_id=session_id)

        # 2. Guardrail: Pedido de acessórios (cordas avulsas, palhetas, cabos, cases, pedais, amplificadores)
        matched_acc = self._detect_accessory_request(q_norm)
        if matched_acc:
            pol_out = call_tool(
                "consultar_politicas_loja",
                {"pergunta": f"escopo da loja sobre acessórios como {matched_acc}"},
            )
            _ = pol_out
            sections_reply.append(
                f"Sobre **{matched_acc}**: aqui na **Empório da Música** nós trabalhamos **exclusivamente com instrumentos musicais** "
                "(violões, guitarras, baixos, baterias, teclados, instrumentos de sopro, cordas orquestrais e ukuleles).\n\n"
                "Por política da loja, **não comercializamos acessórios** como encordoamentos/cordas avulsas, palhetas, cabos, "
                "cases, capas, pedais ou amplificadores. Para esses itens, recomendamos procurar lojas parceiras de acessórios musicais aqui no Centro de Campo Grande!\n\n"
                "Mas se você também estiver de olho em algum instrumento novo ou quiser conferir nossas ofertas, é só me falar!"
            )

        # 3. Intenção: Consulta de Pedido / Rastreamento / Troca ou Devolução associada a pedido
        order_identifier = self._extract_order_identifier(user_message, history)
        wants_return_or_exchange = any(
            kw in q_norm
            for kw in [
                "arrependi",
                "arrependimento",
                "devolver",
                "devolucao",
                "trocar",
                "troca",
                "reembolso",
                "estorno",
                "defeito",
                "quebrado",
                "garantia",
            ]
        )
        wants_order_status = any(
            kw in q_norm
            for kw in [
                "pedido",
                "rastreio",
                "rastreamento",
                "status",
                "minha compra",
                "meu pedido",
                "onde esta",
                "ja foi enviado",
                "entrega do pedido",
            ]
        )

        if order_identifier and (wants_order_status or wants_return_or_exchange or order_identifier.startswith("id:")):
            clean_ident = order_identifier.removeprefix("id:")
            ord_res = call_tool("consultar_pedido", {"identificador": clean_ident})
            if wants_return_or_exchange:
                call_tool(
                    "consultar_politicas_loja",
                    {"pergunta": "política de trocas e devoluções direito de arrependimento defeito garantia"},
                )
            sections_reply.append(self._format_order_response(ord_res, wants_return_or_exchange, q_norm))
        elif wants_return_or_exchange:
            # Pergunta sobre troca/devolução/arrependimento sem número de pedido ainda
            pol_res = call_tool(
                "consultar_politicas_loja",
                {"pergunta": "política de trocas e devoluções direito de arrependimento defeito garantia"},
            )
            sections_reply.append(self._format_return_policy_response(q_norm, pol_res))
        elif wants_order_status:
            sections_reply.append(
                "Para eu consultar o status certinho do seu pedido em tempo real, você pode me informar o "
                "**número do pedido** (ex.: `#7`), o seu **nome completo**, **e-mail** ou o **código de rastreamento**?"
            )

        # 4. Intenção: Detalhamento de Produto Específico (ex.: "Quanto custa o Takamine GD20?", "E o Giannini GF-3D?")
        specific_models = self._extract_specific_models(q_norm, history)
        for model_name in specific_models:
            prod_detail = call_tool("detalhar_produto_e_pagamento", {"nome_ou_id_produto": model_name})
            sections_reply.append(self._format_product_detail_response(prod_detail, q_norm))

        # 5. Intenção: Busca de Catálogo com Filtros (ex.: "Quais opções de violões disponíveis custando até R$1000?")
        catalog_filters = self._extract_catalog_search_filters(q_norm) if not matched_acc else None
        if catalog_filters and not specific_models:
            search_res = call_tool("buscar_produtos", catalog_filters)
            sections_reply.append(self._format_catalog_search_response(search_res, catalog_filters))

        # 6. Intenção: Promoções e Descontos Gerais
        wants_promos = any(
            kw in q_norm
            for kw in ["promocao", "promocoes", "desconto", "oferta", "ofertas", "black friday", "liquidacao", "queima de estoque"]
        )
        if wants_promos and not specific_models and not catalog_filters:
            include_exp = any(k in q_norm for k in ["black friday", "inverno", "pascoa", "aniversario", "semana do musico", "expirada"])
            promo_res = call_tool("listar_promocoes", {"incluir_expiradas": include_exp})
            call_tool("consultar_politicas_loja", {"pergunta": "regras de promoções e descontos cumulatividade pix"})
            sections_reply.append(self._format_promotions_response(promo_res, q_norm))

        # 7. Intenção: Frete e Prazos de Entrega por Cidade
        freight_info = self._extract_freight_query(q_norm)
        if freight_info:
            f_res = call_tool("calcular_frete_e_entrega", freight_info)
            sections_reply.append(self._format_freight_response(f_res))

        # 8. Intenção: Informações Gerais da Loja (Endereço, Horário, Contatos, Formas de Pagamento, LGPD)
        general_policy_topics = self._extract_general_policy_topics(q_norm)
        if general_policy_topics and not wants_return_or_exchange:
            pol_res = call_tool("consultar_politicas_loja", {"pergunta": general_policy_topics})
            sections_reply.append(self._format_general_policy_response(q_norm, pol_res))

        # 9. Caso nenhuma intenção específica tenha disparado, faz uma busca aberta ou saudação consultiva
        if not sections_reply:
            if any(
                g in q_norm
                for g in ["oi", "ola", "bom dia", "boa tarde", "boa noite", "tudo bem", "ajuda", "atendimento"]
            ):
                sections_reply.append(
                    "Sou o consultor virtual da **Empório da Música** aqui de Campo Grande/MS! "
                    "Posso te ajudar a:\n"
                    "- 🎸 **Buscar instrumentos** por categoria, faixa de preço ou estilo (violões, guitarras, baixos, ukuleles, baterias e teclados);\n"
                    "- 💰 **Consultar preços, estoque em tempo real, promoções ativas** e simular parcelamento sem juros ou desconto no PIX;\n"
                    "- 📦 **Rastrear pedidos** e verificar prazos de entrega, trocas ou devoluções;\n"
                    "- 📍 **Tirar dúvidas** sobre endereço, horário de funcionamento, garantia e frete.\n\n"
                    "O que você está procurando hoje?"
                )
            else:
                pol_res = call_tool("consultar_politicas_loja", {"pergunta": user_message})
                sections_reply.append(self._format_general_policy_response(q_norm, pol_res))

        body = "\n\n---\n\n".join(s for s in sections_reply if s.strip())
        closing = "\n\nFicou com alguma dúvida ou quer que eu compare algum outro modelo para você? 😊"
        full_reply = f"{greeting_prefix}{body}{closing}"

        return AgentResponse(
            reply=full_reply.strip(),
            tool_calls=executed_tools,
            provider="local",
            model=self.settings.resolve_model("local"),
            session_id=session_id,
        )

    def _extract_customer_greeting_name(
        self, user_message: str, history: list[dict[str, Any]]
    ) -> str | None:
        patterns = [
            r"(?:meu nome e|sou o|sou a|aqui e o|aqui e a|me chamo)\s+([A-ZÀ-Úa-zà-ú]+)",
        ]
        for text in [user_message] + [h["content"] for h in reversed(history) if h["role"] == "user"]:
            for pat in patterns:
                m = re.search(pat, text, flags=re.IGNORECASE)
                if m:
                    candidate = m.group(1).strip(" .,!?")
                    if candidate.lower() not in {"cliente", "musico", "comprador"} and len(candidate) > 2:
                        return candidate.capitalize()
        return None

    def _is_off_topic(self, q_norm: str) -> bool:
        if any(kw in q_norm for kw in self.OFF_TOPIC_KEYWORDS):
            return True
        return False

    def _detect_accessory_request(self, q_norm: str) -> str | None:
        for acc in ACCESSORY_KEYWORDS:
            if re.search(rf"\b{re.escape(acc)}\b", q_norm):
                if acc in {"corda", "cordas"} and any(
                    inst in q_norm for inst in ["violao", "violoes", "7 cordas", "nylon", "aco"]
                ):
                    continue
                return acc
        # Caso peça "cordas para violão" / "encordoamento"
        if re.search(r"\b(comprar cordas|jogo de cordas|cordas avulsas|cordas elixir|cordas daddario)\b", q_norm):
            return "cordas avulsas / encordoamento"
        return None

    def _extract_order_identifier(
        self, user_message: str, history: list[dict[str, Any]]
    ) -> str | None:
        q_norm = normalize_text(user_message)

        # Código de rastreio padrão BR...BR
        m_track = re.search(r"\b(BR[A-Z0-9]{7,11}BR)\b", user_message, flags=re.IGNORECASE)
        if m_track:
            return m_track.group(1).upper()

        # Número do pedido explícito: "pedido 7", "pedido #7", "#19", "número 12"
        m_ord = re.search(
            r"(?:pedido\s*(?:n[ºo°]?|numero|#)?\s*|#\s*)(\d{1,2})\b",
            q_norm,
        )
        if m_ord:
            return f"id:{m_ord.group(1)}"

        # E-mail na mensagem
        m_email = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", user_message)
        if m_email:
            return m_email.group(0)

        # Nome de clientes conhecidos na mensagem
        customer_rows = self.toolkit.db.execute_query("SELECT name, name_norm FROM customers")
        for c in customer_rows:
            c_norm = c["name_norm"]
            parts = c_norm.split()
            if c_norm in q_norm or (len(parts) >= 2 and f"{parts[0]} {parts[1]}" in q_norm):
                return c["name"]

        # Se a pergunta atual fala em "esse pedido", "meu pedido" e houve pedido citado no histórico
        if any(k in q_norm for k in ["meu pedido", "esse pedido", "minha compra", "ele foi", "posso devolver"]):
            for h in reversed(history):
                h_norm = normalize_text(h["content"])
                m_prev = re.search(r"(?:pedido\s*(?:n[ºo°]?|numero|#)?\s*|#\s*)(\d{1,2})\b", h_norm)
                if m_prev:
                    return f"id:{m_prev.group(1)}"
                for c in customer_rows:
                    parts = c["name_norm"].split()
                    if c["name_norm"] in h_norm or (len(parts) >= 2 and f"{parts[0]} {parts[1]}" in h_norm):
                        return c["name"]

        return None

    def _extract_specific_models(
        self, q_norm: str, history: list[dict[str, Any]]
    ) -> list[str]:
        found: list[str] = []
        for model in self.KNOWN_MODELS:
            if model in q_norm:
                found.append(model)
        # Busca também por códigos de modelo curtos (ex.: "gd20", "c40", "c70", "f310", "fg800", "gf-3d", "110e", "214ce", "d-28", "rg550", "ka-15s", "ck-20")
        if not found:
            short_codes = {
                "gd20": "Takamine GD20",
                "gc5ce": "Takamine GC5CE",
                "gn51ce": "Takamine GN51CE",
                "gc1ce": "Takamine GC1CE",
                "c40": "Yamaha C40",
                "c70": "Yamaha C70",
                "f310": "Yamaha F310",
                "fg800": "Yamaha FG800",
                "ntx1": "Yamaha NTX1",
                "apx600": "Yamaha APX600",
                "cg162s": "Yamaha CG162S",
                "d-28e": "Martin D-28E",
                "d-28": "Martin D-28",
                "110e": "Taylor 110e",
                "214ce": "Taylor 214ce",
                "gn-15": "Giannini GN-15",
                "gf-1r": "Giannini GF-1R",
                "gf-3d": "Giannini GF-3D",
                "gnf-3": "Giannini GNF-3",
                "gwne-7": "Giannini GWNE-7",
                "ac-39": "Tagima Memphis AC-39",
                "dallas": "Tagima Dallas Tuner",
                "woodstock": "Tagima Woodstock",
                "rc-104": "Rozini RC-104",
                "rv-174": "Rozini RV-174",
                "rv-175": "Rozini RV-175",
                "sn-100": "Shelby SN-100",
                "sgd-195e": "Shelby SGD-195E",
                "sn-7c": "Shelby SN-7C",
                "su-21s": "Shelby SU-21S",
                "ht-100": "Crafter HT-100",
                "d-8": "Crafter D-8",
                "ce-15": "Crafter CE-15",
                "ka-15s": "Kala KA-15s",
                "sk-10": "Ohana SK-10",
                "ck-20": "Ohana CK-20",
                "tk-35g": "Ohana TK-35G",
                "kal-700t": "Kalani KAL-700T",
                "rg550": "Ibanez RG550",
                "stratocaster": "Fender Stratocaster",
                "telecaster": "Fender Telecaster",
                "les paul": "Gibson Les Paul",
            }
            for code, full_name in short_codes.items():
                if re.search(rf"\b{re.escape(code)}\b", q_norm):
                    found.append(full_name)

        # Resolução de correferência ("e se eu pagar no pix?", "como fica o parcelamento dele?", "ele está em promoção?")
        if not found and any(
            pron in q_norm
            for pron in ["dele", "desse modelo", "esse violao", "esse instrumento", "no pix", "parcelar ele", "promocao dele"]
        ):
            for h in reversed(history):
                h_norm = normalize_text(h["content"])
                for model in self.KNOWN_MODELS:
                    if model in h_norm:
                        found.append(model)
                        break
                if found:
                    break

        # Remove duplicatas preservando a ordem
        unique: list[str] = []
        for item in found:
            if item.lower() not in [u.lower() for u in unique]:
                unique.append(item)
        return unique[:3]

    def _extract_catalog_search_filters(self, q_norm: str) -> dict[str, Any] | None:
        cat_map = {
            "Violões": ["violao", "violoes", "7 cordas", "dreadnought", "folk"],
            "Ukuleles": ["ukulele", "ukuleles", "soprano", "concert", "tenor", "baritono"],
            "Guitarras": ["guitarra", "guitarras"],
            "Baixos": ["baixo", "baixos", "contrabaixo", "contrabaixos"],
            "Baterias": ["bateria", "baterias", "percussao"],
            "Teclados": ["teclado", "teclados", "piano", "pianos", "sintetizador"],
            "Sopro": ["saxofone", "flauta", "clarinete", "trompete", "trombone", "sopro"],
            "Cordas Orquestrais": ["violino", "violoncelo", "viola de arco", "cordas orquestrais"],
        }
        detected_cat: str | None = None
        for cat_label, terms in cat_map.items():
            if any(re.search(rf"\b{re.escape(t)}\b", q_norm) for t in terms):
                detected_cat = cat_label
                break

        # Extrair limite de preço (ex.: "até R$1000", "até 1.000", "abaixo de 800", "menos de R$ 600")
        preco_max: float | None = None
        m_max = re.search(
            r"(?:ate|abaixo de|menos de|no maximo|custando ate)\s*(?:r\$\s*)?(\d{1,3}(?:\.\d{3})+|\d+)(?:,\d{2})?",
            q_norm,
        )
        if m_max:
            raw_num = m_max.group(1).replace(".", "")
            preco_max = float(raw_num)

        preco_min: float | None = None
        m_min = re.search(
            r"(?:acima de|a partir de|mais de|no minimo)\s*(?:r\$\s*)?(\d{1,3}(?:\.\d{3})+|\d+)(?:,\d{2})?",
            q_norm,
        )
        if m_min:
            raw_num = m_min.group(1).replace(".", "")
            preco_min = float(raw_num)

        tipo_corda: str | None = None
        if "nylon" in q_norm:
            tipo_corda = "nylon"
        elif re.search(r"\b(aco|steel)\b", q_norm):
            tipo_corda = "steel"

        eletrico: str | None = None
        if any(w in q_norm for w in ["eletroacustico", "eletrico", "com captacao"]):
            eletrico = "sim"
        elif "acustico" in q_norm and "eletroacustico" not in q_norm:
            eletrico = "nao"

        termo_busca: str | None = None
        for kw in ["7 cordas", "soprano", "concert", "tenor", "baritono", "yamaha", "tagima", "giannini", "takamine", "rozini", "shelby", "crafter", "kala", "ohana", "kalani", "fender", "gibson", "ibanez"]:
            if kw in q_norm:
                termo_busca = kw
                break

        if not detected_cat and not preco_max and not preco_min and not termo_busca:
            return None

        apenas_disp = any(w in q_norm for w in ["disponiveis", "disponivel", "em estoque", "pronta entrega"])
        return {
            "termo_busca": termo_busca,
            "categoria": detected_cat,
            "preco_max": preco_max,
            "preco_min": preco_min,
            "tipo_corda": tipo_corda,
            "eletrico": eletrico,
            "apenas_disponiveis": apenas_disp,
        }

    def _extract_freight_query(self, q_norm: str) -> dict[str, Any] | None:
        if not any(w in q_norm for w in ["frete", "entrega", "entregam", "envio", "enviar", "motoboy", "sedex", "pac", "jadlog"]):
            return None
        cities = [
            "Campo Grande",
            "Dourados",
            "Três Lagoas",
            "Corumbá",
            "Ponta Porã",
            "São Paulo",
            "Curitiba",
            "Cuiabá",
            "Brasília",
        ]
        chosen_city = "Campo Grande"
        for c in cities:
            if normalize_text(c) in q_norm:
                chosen_city = c
                break
        m_val = re.search(r"r\$\s*(\d{1,3}(?:\.\d{3})+|\d+)", q_norm)
        val = float(m_val.group(1).replace(".", "")) if m_val else None
        grande = any(g in q_norm for g in ["bateria", "piano", "contrabaixo", "baixo"])
        return {
            "cidade": chosen_city,
            "valor_pedido_brl": val,
            "instrumento_grande_porte": grande,
        }

    def _extract_general_policy_topics(self, q_norm: str) -> str | None:
        topics: list[str] = []
        if any(w in q_norm for w in ["endereco", "onde fica", "localizacao", "rua", "loja fisica", "cep", "cnpj"]):
            topics.append("endereço localização dados da empresa")
        if any(w in q_norm for w in ["horario", "funcionamento", "abre", "fecha", "sabado", "domingo", "feriado", "expediente"]):
            topics.append("horário de funcionamento segunda a sábado domingo")
        if any(w in q_norm for w in ["telefone", "whatsapp", "contato", "email", "falar com"]):
            topics.append("telefone whatsapp e-mail de contato")
        if any(w in q_norm for w in ["formas de pagamento", "como posso pagar", "aceita pix", "aceita cartao", "boleto", "parcelamento", "parcela minima"]):
            topics.append("formas de pagamento pix cartão regras de parcelamento")
        if any(w in q_norm for w in ["lgpd", "privacidade", "dados pessoais", "excluir meus dados"]):
            topics.append("privacidade e proteção de dados lgpd")
        return " ".join(topics) if topics else None

    def _format_catalog_search_response(
        self, search_res: dict[str, Any], filters: dict[str, Any]
    ) -> str:
        if search_res.get("fora_de_escopo_acessorio"):
            return search_res["mensagem_politica"]
        if search_res.get("categoria_sem_itens_no_catalogo"):
            return (
                f"Consultei nosso sistema aqui: {search_res['mensagem']}\n\n"
                "No momento, temos pronta entrega nas categorias de **Violões**, **Ukuleles**, **Guitarras**, "
                "**Baixos**, **Baterias** e **Teclados/Sintetizadores**. Gostaria de ver opções em alguma delas?"
            )

        prods = search_res.get("produtos", [])
        if not prods:
            return (
                "Consultei nosso estoque agora mesmo, mas não encontrei nenhum instrumento que combine exatamente "
                "com todos esses filtros. Quer que eu amplie a faixa de preço ou busque modelos equivalentes?"
            )

        disponiveis = [p for p in prods if p["disponibilidade"] == "available"]
        indisponiveis = [p for p in prods if p["disponibilidade"] != "available"]

        cat_title = filters.get("categoria") or "Instrumentos"
        price_suffix = f" até **R$ {filters['preco_max']:,.2f}**".replace(",", "X").replace(".", ",").replace("X", ".") if filters.get("preco_max") else ""

        lines: list[str] = [
            f"Consultei nosso catálogo em tempo real! Encontrei **{len(disponiveis)} opções de {cat_title.lower()} disponíveis em estoque**{price_suffix}:"
        ]

        # Separar por tipo de corda se for Violões para facilitar a escolha do cliente
        nylon_list = [p for p in disponiveis if p.get("cordas") == "nylon"]
        steel_list = [p for p in disponiveis if p.get("cordas") == "steel"]

        def fmt_item(p: dict[str, Any]) -> str:
            preco_str = f"R$ {p['preco_vigente_brl']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            pix_str = f"R$ {p['preco_pix_brl']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            elet_tag = " | Eletroacústico" if p.get("eletroacustico") else ""
            promo_tag = ""
            if p.get("promocao_ativa"):
                orig_str = f"R$ {p['preco_tabela_brl']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                promo_tag = f" 🔥 *(Em promoção: de {orig_str} por {preco_str} — {p['promocao_ativa']['desconto_percent']}% OFF!)*"
            return (
                f"- **{p['nome']}**{promo_tag}: **{preco_str}** "
                f"(ou **{pix_str}** à vista no PIX | {p['parcelamento_max']}){elet_tag} — *{p['estoque']} un. em estoque*"
            )

        if nylon_list and steel_list and len(disponiveis) > 4:
            lines.append("\n**Cordas de Nylon** *(mais macias, ideais para iniciantes, clássico, MPB e choro)*:")
            for p in nylon_list:
                lines.append(fmt_item(p))
            lines.append("\n**Cordas de Aço** *(som mais brilhante e encorpado, ótimo para pop, folk, rock e sertanejo)*:")
            for p in steel_list:
                lines.append(fmt_item(p))
        else:
            lines.append("")
            for p in disponiveis:
                lines.append(fmt_item(p))

        if indisponiveis:
            lines.append("\n> ⚠️ **Observação de transparência sobre o catálogo:**")
            for u in indisponiveis:
                u_price = f"R$ {u['preco_vigente_brl']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                if u["disponibilidade"] == "out_of_stock":
                    lines.append(
                        f"> - O modelo **{u['nome']}** ({u_price}) consta no catálogo nessa faixa, porém está **temporariamente sem estoque (0 unidades)** no momento."
                    )
                elif u["disponibilidade"] == "discontinued":
                    lines.append(
                        f"> - O modelo **{u['nome']}** ({u_price}) foi **descontinuado** e não faz mais parte do catálogo ativo."
                    )
                elif u["disponibilidade"] == "coming_soon":
                    lines.append(
                        f"> - O modelo **{u['nome']}** ({u_price}) está em pré-lançamento (**em breve**)."
                    )

        return "\n".join(lines)

    def _format_product_detail_response(self, detail: dict[str, Any], q_norm: str) -> str:
        if not detail.get("encontrado"):
            return detail.get("mensagem", "Produto não localizado no sistema.")

        nome = detail["nome"]
        disp = detail["disponibilidade"]
        estoque = detail["estoque"]
        pgto = detail["condicoes_pagamento"]
        specs = detail.get("especificacoes", {})

        preco_tab = f"R$ {pgto['preco_tabela_brl']:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")
        preco_vig = f"R$ {pgto['preco_vigente_brl']:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")
        preco_pix = f"R$ {pgto['preco_pix_brl']:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")
        econ_pix = f"R$ {pgto['economia_pix_brl']:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")

        lines: list[str] = [f"### 🎵 {nome} (`ID #{detail['product_id']}`)"]
        lines.append(f"- **Categoria:** {detail['categoria']}")
        lines.append(f"- **Descrição:** {detail['descricao']}")

        if specs:
            specs_formatted = ", ".join(f"{k}: `{v}`" for k, v in specs.items())
            lines.append(f"- **Especificações técnicas:** {specs_formatted}")

        # Status de estoque (Seção 7.3)
        if disp == "available":
            lines.append(f"- **Disponibilidade:** ✅ **Em estoque** ({estoque} {'unidade disponível' if estoque == 1 else 'unidades disponíveis'} para pronta entrega)")
        elif disp == "out_of_stock":
            lines.append(
                "- **Disponibilidade:** ⚠️ **Temporariamente Fora de Estoque (0 unidades)**.\n"
                "  *Seguindo nossa política de transparência, nunca confirmamos venda de item sem estoque físico.*"
            )
        elif disp == "discontinued":
            lines.append(
                "- **Disponibilidade:** 🚫 **Produto Descontinuado** (não faz mais parte do catálogo ativo da loja)."
            )
        elif disp == "coming_soon":
            lines.append("- **Disponibilidade:** ⏳ **Chegada em breve (Pré-lançamento)**.")

        # Promoções ativas ou expiradas (Seção 6.2 e 7.3)
        if detail.get("promocoes_ativas"):
            pr = detail["promocoes_ativas"][0]
            lines.append(
                f"\n#### 🔥 Promoção Ativa ({pr['campanha']} — {pr['desconto_percent']}% de desconto!)\n"
                f"- **Preço Original de Tabela:** ~~{preco_tab}~~\n"
                f"- **Preço Promocional Vigente:** **{preco_vig}**\n"
                f"- *(Nota sobre cumulatividade — Seção 6.2: como este instrumento já está com {pr['desconto_percent']}% de desconto promocional, o desconto de 5% do PIX não é cumulativo, mantendo-se **{preco_pix}** no PIX).*"
            )
        else:
            lines.append(
                f"\n#### 💰 Preço e Condições de Pagamento\n"
                f"- **Preço de Tabela:** **{preco_tab}**\n"
                f"- **À vista no PIX (5% de desconto):** **{preco_pix}** *(economia de {econ_pix})*\n"
                f"- **Cartão de Débito ou Boleto Bancário:** {preco_vig} à vista"
            )
            if detail.get("promocoes_expiradas"):
                exp_list = ", ".join(
                    f"{e['campanha']} ({e['desconto_percent_expirado']}%)"
                    for e in detail["promocoes_expiradas"]
                )
                lines.append(
                    f"- **Status de Promoções:** Verificando no sistema, a campanha anterior (*{exp_list}*) **já está encerrada (`inativa`)**. O valor vigente hoje é o de tabela com os 5% de desconto para pagamento via PIX."
                )

        # Parcelamento (Seção 3.1)
        lines.append(
            f"- **Cartão de Crédito sem juros:** **{pgto['resumo_max_parcelamento']}** "
            "(respeitando nossas faixas: até 3x com parcela mínima de R$ 50, 4x a 6x mín. R$ 80, e 7x a 12x mín. R$ 100)."
        )
        if pgto["permite_combinar_pagamentos"]:
            lines.append(
                "- **Combinação de Pagamento:** ✅ Como o valor supera R$ 2.000,00, você também pode **combinar formas de pagamento** (por exemplo, dar uma entrada no PIX e parcelar o restante no cartão)!"
            )

        # Sugestão de alternativas caso indisponível/descontinuado (Seção 7.3)
        if disp != "available" and detail.get("alternativas_disponiveis"):
            lines.append("\n#### 💡 Alternativas equivalentes disponíveis para pronta entrega:")
            for alt in detail["alternativas_disponiveis"]:
                alt_p = f"R$ {alt['preco_brl']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                lines.append(f"- **{alt['nome']}** — **{alt_p}** (*{alt['estoque']} un. em estoque*)")

        return "\n".join(lines)

    def _format_order_response(
        self, ord_res: dict[str, Any], wants_return_or_exchange: bool, q_norm: str
    ) -> str:
        if not ord_res.get("encontrado"):
            return ord_res.get("mensagem", "Pedido não encontrado.")

        lines: list[str] = []
        if ord_res.get("clientes_homonimos_detectados"):
            hom = ", ".join(
                f"{c['nome']} ({c['cidade']})" for c in ord_res["clientes_homonimos_detectados"]
            )
            lines.append(
                f"*(Nota: identifiquei cadastros com nomes semelhantes na base [{hom}]; abaixo estão os pedidos localizados)*\n"
            )

        for ped in ord_res["pedidos"]:
            cli = ped["cliente"]
            itens_str = ", ".join(
                f"{it['quantidade']}x **{it['produto']}** (R$ {it['preco_catalogo_brl']:,.2f})".replace(",", "X").replace(".", ",").replace("X", ".")
                for it in ped["itens"]
            )
            total_str = f"R$ {ped['valor_total_brl']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

            lines.append(f"### 📦 Pedido `#{ped['order_id']}` — Cliente: **{cli['nome']}** ({cli['cidade']})")
            lines.append(f"- **Data da compra:** `{ped['data_pedido']}`")
            lines.append(f"- **Status atual:** **{ped['status_descricao']}** (`{ped['status_codigo']}`)")
            lines.append(f"- **Itens do pedido:** {itens_str}")
            lines.append(f"- **Valor Total:** **{total_str}** (Forma de pagamento: `{ped['forma_pagamento']}`)")

            if ped.get("codigo_rastreamento"):
                lines.append(f"- **Código de Rastreamento:** `{ped['codigo_rastreamento']}`")
            if ped.get("previsao_ou_data_entrega"):
                label_dt = "Data de entrega registrada" if ped["status_codigo"] == "delivered" else "Previsão de entrega"
                lines.append(f"- **{label_dt}:** `{ped['previsao_ou_data_entrega']}`")
            if ped.get("observacoes"):
                lines.append(f"- **Observação no sistema:** *{ped['observacoes']}*")

            if wants_return_or_exchange:
                analise = ped["analise_troca_e_devolucao"]
                lines.append("\n#### 🔄 Análise de Elegibilidade para Troca / Devolução (Manual Seção 4 e 8):")
                if ped["status_codigo"] == "delivered":
                    arr = analise.get("direito_arrependimento_7_dias", {})
                    defeito = analise.get("troca_por_defeito_30_dias_loja", {})
                    gar = analise.get("garantia_legal_90_dias_cdc", {})
                    dias_ent = analise.get("dias_corridos_desde_entrega")
                    dias_comp = analise.get("dias_corridos_desde_compra")

                    lines.append(
                        f"1. **Direito de Arrependimento / Troca por Preferência (Seção 4.1 e 4.3 — até 7 dias corridos do recebimento):**\n"
                        f"   - Como o pedido foi entregue em `{ped['previsao_ou_data_entrega']}` ({dias_ent} dias corridos até a data de referência `{analise['data_referencia_sistema']}`): "
                        + (
                            "✅ **Está DENTRO do prazo de 7 dias corridos!** Você pode devolver sem necessidade de justificativa (desde que na embalagem original, sem sinais de uso e com acessórios/manuais). O **frete de devolução é por conta da Empório da Música** e o reembolso ocorre em até **10 dias úteis** na mesma forma de pagamento (`"
                            + ped["forma_pagamento"]
                            + "`)."
                            if arr.get("elegivel_na_data_referencia")
                            else "⚠️ **O prazo legal de 7 dias corridos após a entrega para devolução por simples arrependimento já foi ultrapassado** (se o pedido realmente foi entregue na data prevista de `"
                            + str(ped["previsao_ou_data_entrega"])
                            + "`). *Caso a entrega real tenha ocorrido há 7 dias ou menos, basta nos confirmar a data de recebimento dos Correios/transportadora que liberamos imediatamente a logística reversa gratuita!*"
                        )
                    )
                    lines.append(
                        f"2. **Troca por Defeito de Fabricação (Seção 4.2 e 8.1):**\n"
                        f"   - **Troca direta na loja (até 30 dias da compra):** {'✅ Elegível' if defeito.get('elegivel_na_data_referencia') else f'⚠️ Prazo de 30 dias da compra ({dias_comp} dias) encerrado para troca direta na loja'}.\n"
                        f"   - **Garantia Legal CDC (até 90 dias do recebimento) + Garantia do Fabricante (6 meses a 2 anos):** "
                        + (
                            "✅ **Coberto pela Garantia Legal de 90 dias e pela garantia do fabricante!** A Empório da Música pode intermediar todo o acionamento junto ao fabricante caso o instrumento apresente algum defeito."
                            if gar.get("elegivel_na_data_referencia")
                            else "Coberto pela garantia contratual do fabricante (6 meses a 2 anos conforme certificado do produto)."
                        )
                    )
                else:
                    lines.append(f"- {analise.get('orientacao', '')}")

        return "\n".join(lines)

    def _format_return_policy_response(self, q_norm: str, pol_res: dict[str, Any]) -> str:
        _ = pol_res
        return (
            "### 🔄 Política de Trocas, Devoluções e Garantia — Empório da Música\n\n"
            "Seguimos integralmente o Código de Defesa do Consumidor (Lei nº 8.078/90). Veja como funciona em cada caso:\n\n"
            "1. **Direito de Arrependimento — Compras Online (Seção 4.1):**\n"
            "   - **Prazo:** Até **7 (sete) dias corridos** contados a partir do **recebimento do produto**, sem necessidade de justificativa.\n"
            "   - **Condições:** O instrumento deve estar na **embalagem original, sem sinais de uso**, acompanhado de todos os manuais e itens originais.\n"
            "   - **Custo de Envio:** O **frete de devolução é 100% por conta da Empório da Música**.\n"
            "   - **Reembolso:** Realizado na **mesma forma de pagamento original em até 10 dias úteis**.\n\n"
            "2. **Troca por Preferência — Cor, Modelo ou Tamanho (Seção 4.3):**\n"
            "   - Permitida em até **7 dias corridos**, com o produto em perfeito estado e na embalagem original (eventuais diferenças de valor são cobradas ou reembolsadas).\n\n"
            "3. **Troca por Defeito de Fabricação e Garantia (Seções 4.2 e 8):**\n"
            "   - **Até 30 dias corridos após a compra:** Troca realizada diretamente com a Empório da Música.\n"
            "   - **Após 30 dias:** Você conta com a **Garantia Legal de 90 dias** (a partir do recebimento) e a **Garantia do Fabricante (6 meses a 2 anos)**, e nossa equipe pode intermediar o processo para você.\n"
            "   - *Nota:* Danos por mau uso, quedas, umidade excessiva ou modificações não autorizadas não são cobertos.\n\n"
            "4. **Itens Não Elegíveis para Troca (Seção 4.4):**\n"
            "   - Instrumentos com personalização ou regulagem/setup sob encomenda;\n"
            "   - Produtos comprados em liquidação com aviso explícito de *\"venda final\"*;\n"
            "   - Boquilhas de instrumentos de sopro (por questões de higiene).\n\n"
            "👉 **Quer que eu verifique o seu pedido agora mesmo?** Me informe o **número do pedido** ou o seu **nome completo / e-mail** que eu já consulto a data de entrega e o status para você!"
        )

    def _format_promotions_response(self, promo_res: dict[str, Any], q_norm: str) -> str:
        ativas = promo_res.get("promocoes_ativas", [])
        lines: list[str] = [
            f"### 🔥 Promoções Ativas no Sistema Agora ({len(ativas)} ofertas vigentes):"
        ]
        for p in ativas:
            orig = f"R$ {p['preco_original_brl']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            promo = f"R$ {p['preco_promocional_brl']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            lines.append(
                f"- **{p['produto']}** ({p['categoria']}) — Campanha *{p['campanha']}*:\n"
                f"  De ~~{orig}~~ por **{promo}** (**{p['desconto_percent']}% OFF!**) — *{p['estoque']} un. em estoque*"
            )
        lines.append(
            "\n> 📌 **Regras de Promoções (Seção 6.2 do Manual):**\n"
            "> - Promoções **não são cumulativas**: o desconto de 5% do PIX não se aplica sobre preços já promocionais.\n"
            "> - Ofertas válidas enquanto durar o estoque (sem reserva de preço / *rain check*)."
        )
        return "\n".join(lines)

    def _format_freight_response(self, f_res: dict[str, Any]) -> str:
        lines: list[str] = [f"### 🚚 Frete e Prazos de Entrega — {f_res['cidade_informada']}"]
        if "Motoboy" in str(f_res.get("modalidade", "")):
            lines.append(f"- **Região:** {f_res['regiao']}")
            lines.append("- **Frete Grátis:** Para todos os pedidos **acima de R$ 500,00**!")
            lines.append("- **Pedidos abaixo de R$ 500,00:** Taxa fixa de **R$ 35,00**.")
            lines.append(f"- **Prazo de entrega:** **{f_res['prazo_entrega']}** via **motoboy próprio** (nossa equipe entra em contato por telefone antes da entrega).")
        else:
            lines.append(f"- **Região:** {f_res['regiao']}")
            lines.append(f"- **Cálculo do frete:** {f_res['calculo_valor']}")
            lines.append("- **Modalidades e Prazos Estimados:**")
            for mod in f_res.get("modalidades_disponiveis", []):
                lines.append(
                    f"  - **{mod['modalidade']}:** {mod['prazo_estimado']} (Rastreamento + Seguro contra extravio/avaria inclusos)"
                )
            lines.append(f"- *{f_res['alerta_grande_porte']}*")
        return "\n".join(lines)

    def _format_general_policy_response(self, q_norm: str, pol_res: dict[str, Any]) -> str:
        _ = pol_res
        parts: list[str] = []

        if any(w in q_norm for w in ["endereco", "onde fica", "localizacao", "rua", "loja", "horario", "funcionamento", "abre", "fecha", "sabado", "domingo", "telefone", "whatsapp", "contato", "email"]):
            parts.append(
                "### 📍 Informações da Loja — Empório da Música\n"
                "- **Endereço:** Rua 14 de Maio, 3200 — Centro, Campo Grande – MS, CEP 79202-333\n"
                "- **Horário de Funcionamento (Loja Física e WhatsApp):**\n"
                "  - **Segunda a Sexta-feira:** 09:00 às 18:00\n"
                "  - **Sábado:** 09:00 às 13:00\n"
                "  - **Domingos e Feriados:** Fechado *(em datas especiais como Black Friday, Aniversário da Loja e Natal, o horário pode ser estendido)*\n"
                "- **Canais de Contato:**\n"
                "  - **WhatsApp Central de Atendimento:** `(67) 3321-4500`\n"
                "  - **Telefone / WhatsApp Loja Física:** `(67) 3341-4444`\n"
                "  - **E-mail:** `contato@emporiodamusica.com.br`\n"
                "- **CNPJ:** 12.345.678/0001-90"
            )

        if any(w in q_norm for w in ["pagamento", "pagar", "pix", "cartao", "boleto", "parcelamento", "parcela"]):
            parts.append(
                "### 💳 Formas de Pagamento e Parcelamento (Seção 3)\n"
                "- **PIX:** Pagamento à vista com **5% de desconto** sobre o preço de tabela *(não cumulativo com promoções ativas)*.\n"
                "- **Cartão de Débito:** À vista (todas as bandeiras).\n"
                "- **Boleto Bancário:** À vista (compensação em até 3 dias úteis).\n"
                "- **Cartão de Crédito (em até 12x sem juros):**\n"
                "  - **Até 3x sem juros:** parcela mínima de **R$ 50,00**\n"
                "  - **De 4x a 6x sem juros:** parcela mínima de **R$ 80,00**\n"
                "  - **De 7x a 12x sem juros:** parcela mínima de **R$ 100,00**\n"
                "- **Combinação de Pagamentos:** Permitida (ex.: PIX + cartão) para compras **acima de R$ 2.000,00**."
            )

        if any(w in q_norm for w in ["lgpd", "privacidade", "dados"]):
            parts.append(
                "### 🔒 Privacidade e Proteção de Dados — LGPD (Seção 9)\n"
                "Seguimos a Lei nº 13.709/2018. Seus dados (nome, telefone, e-mail e endereço) são usados exclusivamente para processamento/entrega de pedidos, avisos de rastreamento, obrigações fiscais e (apenas com seu consentimento explícito) envio de novidades. Não compartilhamos dados com terceiros para marketing, e você pode solicitar a exclusão a qualquer momento pelo nosso WhatsApp ou e-mail."
            )

        if not parts:
            # Fallback mostrando os trechos recuperados pelo RAG
            secoes = pol_res.get("secoes_encontradas", [])
            if secoes:
                top = secoes[0]
                parts.append(f"### 📋 {top['title']}\n\n{top['content']}")

        return "\n\n".join(parts)
