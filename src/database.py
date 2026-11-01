"""Camada de ingestão, higienização, tratamento de dados e banco relacional SQLite."""

from __future__ import annotations

import json
import re
import sqlite3
import unicodedata
from pathlib import Path
from typing import Any

import pandas as pd

from src.config import DATA_DIR


def normalize_text(text: Any) -> str:
    """Remove acentos, converte para minúsculas e normaliza espaços para busca."""
    if text is None or (isinstance(text, float) and pd.isna(text)):
        return ""
    raw = str(text).strip().lower()
    nfkd = unicodedata.normalize("NFKD", raw)
    no_accents = "".join(c for c in nfkd if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", no_accents)


def digits_only(text: Any) -> str:
    """Extrai apenas dígitos numéricos (útil para telefone/WhatsApp)."""
    if text is None or (isinstance(text, float) and pd.isna(text)):
        return ""
    return re.sub(r"\D+", "", str(text))


class StoreDatabase:
    """Gerencia o carregamento, limpeza dos CSVs e consultas estruturadas via SQLite."""

    def __init__(self, data_dir: Path = DATA_DIR) -> None:
        self.data_dir = Path(data_dir)
        self.conn = sqlite3.connect(":memory:", check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.data_quality_notes: list[str] = []
        self._load_and_sanitize()

    def _find_csv(self, suffix: str) -> Path:
        """Localiza arquivo CSV com ou sem prefixo 'desafio_tecnico_ai_eng - '."""
        direct = self.data_dir / f"{suffix}.csv"
        if direct.exists():
            return direct
        prefixed = self.data_dir / f"desafio_tecnico_ai_eng - {suffix}.csv"
        if prefixed.exists():
            return prefixed
        matches = list(self.data_dir.glob(f"*{suffix}.csv"))
        if matches:
            return matches[0]
        raise FileNotFoundError(f"Arquivo CSV para '{suffix}' não encontrado em {self.data_dir}")

    def _load_and_sanitize(self) -> None:
        """Carrega os 6 CSVs, aplica regras de higienização e cria tabelas no SQLite."""
        categories_df = pd.read_csv(self._find_csv("categories"))
        customers_df = pd.read_csv(self._find_csv("customers"))
        orders_df = pd.read_csv(self._find_csv("orders"))
        order_items_df = pd.read_csv(self._find_csv("order_items"))
        products_df = pd.read_csv(self._find_csv("products"))
        promotions_df = pd.read_csv(self._find_csv("promotions"))

        # 1. Tratamento de Categories
        categories_df["name_norm"] = categories_df["name"].apply(normalize_text)
        cat_map = dict(zip(categories_df["category_id"], categories_df["name"]))

        # 2. Tratamento de Promotions (separando ativas vs expiradas)
        promotions_df["is_active"] = promotions_df["is_active"].astype(int)
        active_promos = (
            promotions_df[promotions_df["is_active"] == 1]
            .sort_values("discount_percent", ascending=False)
            .drop_duplicates(subset=["product_id"], keep="first")
            .set_index("product_id")
        )

        # 3. Tratamento de Products + parse de JSON specs + disponibilidade real
        spec_strings_list: list[str] = []
        spec_electronics_list: list[str] = []
        spec_color_list: list[str] = []
        spec_top_list: list[str] = []
        availability_list: list[str] = []
        has_active_promo_list: list[int] = []
        promo_discount_list: list[int] = []
        promo_desc_list: list[str] = []
        final_price_list: list[float] = []
        pix_price_list: list[float] = []
        search_blob_list: list[str] = []
        data_anomaly_list: list[str] = []

        for _, row in products_df.iterrows():
            pid = int(row["product_id"])
            price = float(row["price_brl"])
            stock = int(row["stock_quantity"])
            status = str(row["status"]).strip().lower()
            cat_id = int(row["category_id"])
            cat_name = cat_map.get(cat_id, "")

            # Parse specs JSON safely
            raw_specs = row.get("specs", "{}")
            try:
                specs = json.loads(raw_specs) if isinstance(raw_specs, str) else {}
            except json.JSONDecodeError:
                specs = {}

            strings_val = str(specs.get("strings", "")).lower()
            elec_val = str(specs.get("electronics", "")).lower()
            color_val = str(specs.get("color", ""))
            top_val = str(specs.get("top", specs.get("body", specs.get("shells", ""))))

            spec_strings_list.append(strings_val)
            spec_electronics_list.append(elec_val)
            spec_color_list.append(color_val)
            spec_top_list.append(top_val)

            # Regra de negócio (Seção 7.3 do Manual):
            # - status == 'discontinued' -> descontinuado (mesmo se stock_quantity > 0, ex: id 136)
            # - status == 'coming_soon' -> em breve / pré-lançamento (ex: id 130)
            # - status == 'active' e stock == 0 -> fora de estoque (ex: id 96)
            # - status == 'active' e stock > 0 -> disponível
            if status == "discontinued":
                availability = "discontinued"
                if stock > 0:
                    self.data_quality_notes.append(
                        f"Produto ID {pid} ({row['name']}) possui status='discontinued' com stock_quantity={stock}; tratado como descontinuado conforme Política 7.3."
                    )
            elif status == "coming_soon":
                availability = "coming_soon"
            elif status == "active" and stock <= 0:
                availability = "out_of_stock"
            else:
                availability = "available"
            availability_list.append(availability)

            # Detecção de inconsistência textual nos produtos sintéticos (IDs 135-144)
            anomaly = ""
            name_str = str(row["name"])
            desc_str = str(row["description"])
            for brand in ["Fender", "Ibanez", "Pearl", "Tama", "Roland", "Yamaha"]:
                if brand.lower() in desc_str.lower() and brand.lower() not in name_str.lower():
                    anomaly = (
                        f"Divergência cadastral entre título ('{name_str}') e descrição ('{desc_str[:55]}...'). "
                        "Priorizar nome oficial do catálogo."
                    )
                    self.data_quality_notes.append(f"Produto ID {pid}: {anomaly}")
                    break
            data_anomaly_list.append(anomaly)

            # Promoções ativas e Regra 6.2 (PIX 5% NÃO é cumulativo com preço promocional)
            if pid in active_promos.index:
                disc = int(active_promos.loc[pid, "discount_percent"])
                pdesc = str(active_promos.loc[pid, "description"])
                final_p = round(price * (1.0 - disc / 100.0), 2)
                # PIX não acumula 5% extra em item já promocional (Política 6.2)
                pix_p = final_p
                has_active_promo_list.append(1)
                promo_discount_list.append(disc)
                promo_desc_list.append(pdesc)
            else:
                final_p = round(price, 2)
                pix_p = round(price * 0.95, 2)
                has_active_promo_list.append(0)
                promo_discount_list.append(0)
                promo_desc_list.append("")

            final_price_list.append(final_p)
            pix_price_list.append(pix_p)

            blob = normalize_text(
                f"{row['name']} {cat_name} {row['description']} {strings_val} {color_val} {top_val}"
            )
            search_blob_list.append(blob)

        products_df["category_name"] = products_df["category_id"].map(cat_map)
        products_df["name_norm"] = products_df["name"].apply(normalize_text)
        products_df["spec_strings"] = spec_strings_list
        products_df["spec_electronics"] = spec_electronics_list
        products_df["spec_color"] = spec_color_list
        products_df["spec_top"] = spec_top_list
        products_df["availability"] = availability_list
        products_df["has_active_promo"] = has_active_promo_list
        products_df["promo_discount_percent"] = promo_discount_list
        products_df["promo_description"] = promo_desc_list
        products_df["effective_price_brl"] = final_price_list
        products_df["pix_price_brl"] = pix_price_list
        products_df["search_blob"] = search_blob_list
        products_df["data_anomaly"] = data_anomaly_list

        # Verificar categorias sem produtos cadastrados
        present_cats = set(products_df["category_id"].unique())
        for _, crow in categories_df.iterrows():
            if int(crow["category_id"]) not in present_cats:
                self.data_quality_notes.append(
                    f"Categoria ID {crow['category_id']} ('{crow['name']}') consta em categories.csv mas possui 0 produtos em products.csv."
                )

        # 4. Tratamento de Customers
        customers_df["name_norm"] = customers_df["name"].apply(normalize_text)
        customers_df["phone_digits"] = customers_df["phone"].apply(digits_only)
        customers_df["email_norm"] = customers_df["email"].apply(
            lambda x: str(x).strip().lower() if pd.notna(x) else ""
        )
        customers_df["city_norm"] = customers_df["city"].apply(normalize_text)

        # Verificar e-mails duplicados em customers.csv
        dup_emails = customers_df[customers_df.duplicated(subset=["email_norm"], keep=False)]
        if not dup_emails.empty:
            for email_val, group in dup_emails.groupby("email_norm"):
                ids = ", ".join(f"{r['customer_id']} ({r['name']})" for _, r in group.iterrows())
                self.data_quality_notes.append(
                    f"E-mail '{email_val}' compartilhado por múltiplos registros em customers.csv: {ids}."
                )

        # 5. Tratamento de Orders
        orders_df["tracking_code"] = orders_df["tracking_code"].fillna("").astype(str).str.strip()
        orders_df["estimated_delivery"] = (
            orders_df["estimated_delivery"].fillna("").astype(str).str.strip()
        )
        orders_df["notes"] = orders_df["notes"].fillna("").astype(str).str.strip()
        orders_df["status"] = orders_df["status"].fillna("").astype(str).str.strip().str.lower()

        # Persistir tabelas no SQLite em memória
        categories_df.to_sql("categories", self.conn, index=False, if_exists="replace")
        customers_df.to_sql("customers", self.conn, index=False, if_exists="replace")
        orders_df.to_sql("orders", self.conn, index=False, if_exists="replace")
        order_items_df.to_sql("order_items", self.conn, index=False, if_exists="replace")
        products_df.to_sql("products", self.conn, index=False, if_exists="replace")
        promotions_df.to_sql("promotions", self.conn, index=False, if_exists="replace")

    def execute_query(self, sql: str, params: tuple[Any, ...] | list[Any] = ()) -> list[dict[str, Any]]:
        """Executa uma query SQL read-only e retorna lista de dicionários."""
        cur = self.conn.cursor()
        cur.execute(sql, params)
        return [dict(row) for row in cur.fetchall()]


# Singleton default para reutilização rápida
db = StoreDatabase()
