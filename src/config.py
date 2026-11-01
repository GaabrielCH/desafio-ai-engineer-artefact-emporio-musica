"""Configurações centralizadas do projeto Empório da Música."""

from __future__ import annotations

import os
from datetime import date
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"


class Settings:
    """Configurações carregadas do ambiente (.env) com valores padrão seguros."""

    def __init__(self) -> None:
        self.llm_provider: str = os.getenv("LLM_PROVIDER", "auto").strip().lower()
        self.llm_model: str = os.getenv("LLM_MODEL", "").strip()
        self.gemini_api_key: str = os.getenv("GEMINI_API_KEY", "").strip()
        self.openai_api_key: str = os.getenv("OPENAI_API_KEY", "").strip()
        self.groq_api_key: str = os.getenv("GROQ_API_KEY", "").strip()
        self.openai_base_url: str = os.getenv("OPENAI_BASE_URL", "").strip()
        self.temperature: float = float(os.getenv("LLM_TEMPERATURE", "0.2"))

        ref_date_str = os.getenv("REFERENCE_DATE", "2026-03-23").strip()
        try:
            self.reference_date: date = date.fromisoformat(ref_date_str)
        except ValueError:
            self.reference_date = date(2026, 3, 23)

        chat_db_env = os.getenv("CHAT_HISTORY_DB", "data/chat_history.db").strip()
        self.chat_history_db: Path = (
            Path(chat_db_env) if Path(chat_db_env).is_absolute() else BASE_DIR / chat_db_env
        )
        self.data_dir: Path = DATA_DIR

    def resolve_provider(self) -> str:
        """Determina o provedor ativo com base na configuração e nas chaves disponíveis."""
        if self.llm_provider in {"gemini", "openai", "groq", "ollama", "local"}:
            if self.llm_provider == "gemini" and not self.gemini_api_key:
                return "local"
            if self.llm_provider == "openai" and not self.openai_api_key and not self.openai_base_url:
                return "local"
            if self.llm_provider == "groq" and not self.groq_api_key:
                return "local"
            return self.llm_provider

        # Auto-detection order: Gemini -> OpenAI -> Groq -> Ollama (if base_url set) -> Local
        if self.gemini_api_key:
            return "gemini"
        if self.openai_api_key:
            return "openai"
        if self.groq_api_key:
            return "groq"
        if self.openai_base_url:
            return "ollama"
        return "local"

    def resolve_model(self, provider: str | None = None) -> str:
        """Retorna o nome do modelo para o provedor selecionado."""
        if self.llm_model:
            return self.llm_model
        active = provider or self.resolve_provider()
        defaults = {
            "gemini": "gemini-2.5-flash",
            "openai": "gpt-4o-mini",
            "groq": "llama-3.3-70b-versatile",
            "ollama": "llama3.1",
            "local": "emporio-react-local-v1",
        }
        return defaults.get(active, "emporio-react-local-v1")


settings = Settings()
