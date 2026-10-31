"""Business-system connectors. Demo connectors read the local synthetic source tables.

In a real deployment, replace each adapter with an API/warehouse connector and
store credentials in a secrets manager. Keep the connector contract stable.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
import pandas as pd
from sqlalchemy import select, func

from .db import SessionLocal
from .models import Campaign, Customer, Lead, SalesOrder, SupportTicket


class BusinessConnector(Protocol):
    name: str
    def count_records(self) -> int: ...


@dataclass
class CRMConnector:
    name: str = "CRM"
    def count_records(self) -> int:
        with SessionLocal() as db:
            return db.query(Customer).count()
    def customers(self) -> pd.DataFrame:
        with SessionLocal() as db:
            rows = db.execute(select(Customer)).scalars().all()
            return pd.DataFrame([{c.name: getattr(row, c.name) for c in Customer.__table__.columns} for row in rows])
    def leads(self) -> pd.DataFrame:
        with SessionLocal() as db:
            rows = db.execute(select(Lead)).scalars().all()
            return pd.DataFrame([{c.name: getattr(row, c.name) for c in Lead.__table__.columns} for row in rows])


@dataclass
class LeadGenerationConnector:
    name: str = "Lead Generation"
    def count_records(self) -> int:
        with SessionLocal() as db:
            return db.query(Lead).count()
    def leads(self) -> pd.DataFrame:
        with SessionLocal() as db:
            rows = db.execute(select(Lead)).scalars().all()
            return pd.DataFrame([{c.name: getattr(row, c.name) for c in Lead.__table__.columns} for row in rows])


@dataclass
class CommerceConnector:
    name: str = "ERP / Commerce"
    def count_records(self) -> int:
        with SessionLocal() as db:
            return db.query(SalesOrder).count()
    def orders(self) -> pd.DataFrame:
        with SessionLocal() as db:
            rows = db.execute(select(SalesOrder)).scalars().all()
            return pd.DataFrame([{c.name: getattr(row, c.name) for c in SalesOrder.__table__.columns} for row in rows])


@dataclass
class SupportConnector:
    name: str = "Customer Support"
    def count_records(self) -> int:
        with SessionLocal() as db:
            return db.query(SupportTicket).count()
    def tickets(self) -> pd.DataFrame:
        with SessionLocal() as db:
            rows = db.execute(select(SupportTicket)).scalars().all()
            return pd.DataFrame([{c.name: getattr(row, c.name) for c in SupportTicket.__table__.columns} for row in rows])


@dataclass
class MarketingConnector:
    name: str = "Marketing Automation"
    def count_records(self) -> int:
        with SessionLocal() as db:
            return db.query(Campaign).count()
    def campaigns(self) -> pd.DataFrame:
        with SessionLocal() as db:
            rows = db.execute(select(Campaign)).scalars().all()
            return pd.DataFrame([{c.name: getattr(row, c.name) for c in Campaign.__table__.columns} for row in rows])


CONNECTORS: list[BusinessConnector] = [CRMConnector(), LeadGenerationConnector(), CommerceConnector(), SupportConnector(), MarketingConnector()]


def systems_status() -> list[dict]:
    return [{"system": connector.name, "status": "connected", "records": connector.count_records(),
             "mode": "synthetic local adapter"} for connector in CONNECTORS]


def _finite_float(value):
    """Convert a pandas scalar to a JSON-safe finite float."""
    if pd.isna(value):
        return None
    number = float(value)
    return number if pd.notna(number) and abs(number) != float("inf") else None


def data_profile(frame: pd.DataFrame, source: str) -> dict:
    """Return a compact EDA report safe to serialize through the API."""
    if frame.empty:
        return {"source": source, "rows": 0, "columns": 0, "missing_cells": 0,
                "duplicate_rows": 0, "fields": [], "top_numeric_correlations": []}
    fields = []
    for col in frame.columns:
        series = frame[col]
        item = {
            "name": str(col), "type": str(series.dtype),
            "missing": int(series.isna().sum()),
            "unique": int(series.nunique(dropna=True)),
            "sample": [str(v) for v in series.dropna().head(3).tolist()],
        }
        if pd.api.types.is_numeric_dtype(series) and not pd.api.types.is_bool_dtype(series):
            clean = series.dropna()
            item["summary"] = {
                "kind": "numeric",
                "min": _finite_float(clean.min()) if not clean.empty else None,
                "mean": _finite_float(clean.mean()) if not clean.empty else None,
                "median": _finite_float(clean.median()) if not clean.empty else None,
                "std": _finite_float(clean.std()) if len(clean) > 1 else None,
                "max": _finite_float(clean.max()) if not clean.empty else None,
            }
        elif pd.api.types.is_datetime64_any_dtype(series):
            clean = series.dropna()
            item["summary"] = {
                "kind": "datetime",
                "earliest": str(clean.min()) if not clean.empty else None,
                "latest": str(clean.max()) if not clean.empty else None,
            }
        else:
            counts = series.value_counts(dropna=True).head(5)
            item["summary"] = {
                "kind": "categorical",
                "top_values": [{"value": str(value), "count": int(count)} for value, count in counts.items()],
            }
        fields.append(item)

    # Exclude database row IDs from the exploratory correlation summary.
    numeric_columns = [
        c for c in frame.select_dtypes(include=["number"]).columns
        if str(c).lower() not in {"id"} and not str(c).lower().endswith(("_id", "_ref"))
    ]
    correlations = []
    if len(numeric_columns) >= 2:
        corr = frame[numeric_columns].corr(numeric_only=True)
        for i, left in enumerate(numeric_columns):
            for right in numeric_columns[i + 1:]:
                value = _finite_float(corr.loc[left, right])
                if value is not None:
                    correlations.append({"field_a": str(left), "field_b": str(right), "correlation": round(value, 4)})
    correlations.sort(key=lambda x: abs(x["correlation"]), reverse=True)

    return {
        "source": source, "rows": int(len(frame)), "columns": int(len(frame.columns)),
        "missing_cells": int(frame.isna().sum().sum()), "duplicate_rows": int(frame.duplicated().sum()),
        "fields": fields, "top_numeric_correlations": correlations[:10],
        "correlation_note": "Pairwise numeric association only; correlation does not establish causation.",
    }


def profile_all_sources() -> list[dict]:
    crm, leadgen, commerce, support, marketing = CRMConnector(), LeadGenerationConnector(), CommerceConnector(), SupportConnector(), MarketingConnector()
    return [
        data_profile(crm.customers(), "CRM — customers"),
        data_profile(leadgen.leads(), "Lead Generation — prospects"),
        data_profile(commerce.orders(), "ERP / Commerce — orders"),
        data_profile(support.tickets(), "Customer Support — tickets"),
        data_profile(marketing.campaigns(), "Marketing Automation — campaigns"),
    ]


def business_system_summary() -> dict:
    profiles = profile_all_sources()
    return {
        "systems": systems_status(),
        "totals": {"rows": sum(p["rows"] for p in profiles), "tables": len(profiles)},
        "profiles": profiles,
    }
