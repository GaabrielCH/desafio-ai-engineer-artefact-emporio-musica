"""Módulo de RAG (Retrieval-Augmented Generation) para o Manual de Políticas da Loja (PDF)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pdfplumber
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from src.config import DATA_DIR
from src.database import normalize_text


@dataclass
class PolicyChunk:
    """Representa uma seção semântica extraída do manual de políticas."""

    section_id: str
    title: str
    content: str
    page_numbers: list[int]
    keywords: list[str]


class PolicyRAG:
    """Indexa o PDF de políticas da loja por seções semânticas e realiza busca híbrida."""

    TOPIC_SYNONYMS: dict[str, list[str]] = {
        "1": [
            "sobre",
            "empresa",
            "missao",
            "cnpj",
            "endereco",
            "rua",
            "localizacao",
            "onde fica",
            "campo grande",
            "telefone",
            "contato",
            "email",
            "fundacao",
            "acessorios",
            "cordas",
            "palhetas",
            "cabos",
            "cases",
            "pedais",
            "amplificadores",
            "escopo",
        ],
        "2": [
            "horario",
            "funcionamento",
            "abre",
            "fecha",
            "aberto",
            "sabado",
            "domingo",
            "feriado",
            "segunda",
            "sexta",
            "expediente",
        ],
        "3": [
            "pagamento",
            "formas de pagamento",
            "pix",
            "desconto",
            "cartao",
            "credito",
            "debito",
            "boleto",
            "parcelamento",
            "parcela",
            "sem juros",
            "12x",
            "3x",
            "6x",
            "combinacao",
        ],
        "4": [
            "troca",
            "trocas",
            "devolucao",
            "devolver",
            "arrependimento",
            "arrependi",
            "reembolso",
            "estorno",
            "defeito",
            "7 dias",
            "30 dias",
            "preferencia",
            "cor",
            "modelo",
            "boquilha",
            "liquidação",
            "setup",
        ],
        "5": [
            "frete",
            "entrega",
            "entregas",
            "envio",
            "prazo",
            "motoboy",
            "correios",
            "pac",
            "sedex",
            "jadlog",
            "rastreamento",
            "rastreio",
            "codigo",
            "seguro",
            "avaria",
            "outras cidades",
            "dourados",
            "tres lagoas",
            "corumba",
            "ponta pora",
        ],
        "6": [
            "promocao",
            "promocoes",
            "descontos",
            "black friday",
            "aniversario",
            "volta as aulas",
            "queima de estoque",
            "semana do musico",
            "cumulativo",
            "cumulatividade",
            "rain check",
        ],
        "7": [
            "whatsapp",
            "atendimento",
            "tom de voz",
            "fora de estoque",
            "indisponivel",
            "descontinuado",
            "promocao expirada",
            "vencida",
            "reclamacao",
            "ouvidoria",
            "acessorios",
        ],
        "8": [
            "garantia",
            "garantia legal",
            "cdc",
            "90 dias",
            "fabricante",
            "mau uso",
            "desgaste",
            "trastes",
        ],
        "9": [
            "privacidade",
            "lgpd",
            "dados pessoais",
            "exclusao",
            "protecao de dados",
            "marketing",
        ],
        "10": [
            "disposicoes finais",
            "gerencia",
            "manual",
            "versao",
        ],
    }

    def __init__(self, data_dir: Path = DATA_DIR) -> None:
        self.data_dir = Path(data_dir)
        self.pdf_path = self._find_pdf()
        self.raw_pages: list[tuple[int, str]] = []
        self.chunks: list[PolicyChunk] = []
        self._load_and_chunk_pdf()
        self._build_index()

    def _find_pdf(self) -> Path:
        matches = list(self.data_dir.glob("*.pdf"))
        if not matches:
            raise FileNotFoundError(f"Nenhum PDF de políticas encontrado em {self.data_dir}")
        return matches[0]

    def _load_and_chunk_pdf(self) -> None:
        """Extrai texto do PDF página a página e segmenta pelas 10 seções numeradas do manual."""
        full_text_with_pages: list[tuple[int, str]] = []
        with pdfplumber.open(self.pdf_path) as pdf:
            for idx, page in enumerate(pdf.pages, start=1):
                txt = page.extract_text() or ""
                # Remove cabeçalho/rodapé repetitivo das páginas internas
                txt = re.sub(
                    r"^Empório da Música Manual de Políticas e Procedimentos\s*",
                    "",
                    txt.strip(),
                )
                txt = re.sub(r"\s*Página \d+\s*$", "", txt.strip())
                full_text_with_pages.append((idx, txt))

        self.raw_pages = full_text_with_pages

        # Concatena marcando páginas para preservar rastreabilidade de página
        combined_lines: list[tuple[int, str]] = []
        for page_num, page_text in full_text_with_pages:
            for line in page_text.splitlines():
                if line.strip():
                    combined_lines.append((page_num, line.strip()))

        section_pattern = re.compile(r"^(\d{1,2})\.\s+([A-ZÀ-Ú].+)$")
        current_sec_id = "0"
        current_title = "Capa e Identificação da Loja"
        current_lines: list[str] = []
        current_pages: set[int] = set()
        raw_sections: list[PolicyChunk] = []

        for page_num, line in combined_lines:
            match = section_pattern.match(line)
            if match:
                if current_lines and current_sec_id != "0":
                    raw_sections.append(
                        PolicyChunk(
                            section_id=current_sec_id,
                            title=current_title,
                            content="\n".join(current_lines),
                            page_numbers=sorted(current_pages),
                            keywords=self.TOPIC_SYNONYMS.get(current_sec_id, []),
                        )
                    )
                current_sec_id = match.group(1)
                current_title = f"{current_sec_id}. {match.group(2)}"
                current_lines = [line]
                current_pages = {page_num}
            else:
                current_lines.append(line)
                current_pages.add(page_num)

        if current_lines:
            raw_sections.append(
                PolicyChunk(
                    section_id=current_sec_id,
                    title=current_title,
                    content="\n".join(current_lines),
                    page_numbers=sorted(current_pages),
                    keywords=self.TOPIC_SYNONYMS.get(current_sec_id, []),
                )
            )

        # Notas de reconciliação para ambiguidades conhecidas do documento
        reconciliation_notes = {
            "1": (
                "\n[Nota de Consistência Interna]: O manual informa (67) 3341-4444 na Seção 1.2 "
                "(Telefone/WhatsApp geral da loja física) e (67) 3321-4500 na Seção 7 (Canal central "
                "de atendimento remoto via WhatsApp). O e-mail oficial é contato@emporiodamusica.com.br."
            ),
            "3": (
                "\n[Nota de Consistência Interna]: A tabela 3 resume 'Até 12x sem juros (parcela mínima R$ 100)', "
                "enquanto a Seção 3.1 detalha o escalonamento exato por faixa: "
                "1x a 3x sem juros com parcela mínima de R$ 50,00; "
                "4x a 6x sem juros com parcela mínima de R$ 80,00; "
                "7x a 12x sem juros com parcela mínima de R$ 100,00. "
                "Combinação de formas de pagamento (ex.: PIX + cartão) é permitida para compras acima de R$ 2.000,00."
            ),
            "7": (
                "\n[Nota de Consistência Interna]: Canal central WhatsApp remoto: (67) 3321-4500; "
                "Telefone/WhatsApp da loja física (Seção 1.2): (67) 3341-4444."
            ),
        }

        for chunk in raw_sections:
            if chunk.section_id in reconciliation_notes:
                chunk.content += reconciliation_notes[chunk.section_id]

        self.chunks = raw_sections

    def _build_index(self) -> None:
        """Constrói índice híbrido TF-IDF de palavras e n-gramas de caracteres."""
        corpus = [
            normalize_text(f"{c.title} {' '.join(c.keywords)} {c.content}") for c in self.chunks
        ]
        self.word_vectorizer = TfidfVectorizer(ngram_range=(1, 2))
        self.char_vectorizer = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5))
        self.word_matrix = self.word_vectorizer.fit_transform(corpus)
        self.char_matrix = self.char_vectorizer.fit_transform(corpus)

    def search(self, query: str, top_k: int = 3) -> list[dict[str, Any]]:
        """Busca as seções mais relevantes do PDF combinando TF-IDF e boost semântico."""
        q_norm = normalize_text(query)
        if not q_norm:
            return []

        w_vec = self.word_vectorizer.transform([q_norm])
        c_vec = self.char_vectorizer.transform([q_norm])

        w_scores = cosine_similarity(w_vec, self.word_matrix).flatten()
        c_scores = cosine_similarity(c_vec, self.char_matrix).flatten()
        combined = 0.65 * w_scores + 0.35 * c_scores

        # Boost por palavras-chave de domínio mapeadas para cada seção
        for idx, chunk in enumerate(self.chunks):
            matches = sum(1 for kw in chunk.keywords if kw in q_norm)
            if matches > 0:
                combined[idx] += 0.25 * min(matches, 3)

        ranked_indices = np.argsort(combined)[::-1][:top_k]
        results: list[dict[str, Any]] = []
        for idx in ranked_indices:
            score = float(combined[idx])
            if score <= 0.01 and len(results) > 0:
                continue
            chunk = self.chunks[int(idx)]
            results.append(
                {
                    "section_id": chunk.section_id,
                    "title": chunk.title,
                    "pages": chunk.page_numbers,
                    "score": round(score, 4),
                    "content": chunk.content,
                }
            )
        return results


policy_rag = PolicyRAG()
