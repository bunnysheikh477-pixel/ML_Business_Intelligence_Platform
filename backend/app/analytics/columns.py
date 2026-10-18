
from __future__ import annotations

import re
import unicodedata

import pandas as pd

# Candidate column names per logical role, checked in order.
# Names are compared after normalisation, so "Order Date", "order_date"
# and "ORDERDATE" are all treated as the same column.
CANDIDATES: dict[str, tuple[str, ...]] = {
    "date": (
        "date", "order date", "orderdate", "invoice date", "invoicedate",
        "purchase date", "purchase date", "transaction date", "created at",
        "createdat", "timestamp", "month", "period",
    ),
    "revenue": (
        "revenue", "sales", "total sales", "totalsales", "net sales",
        "amount", "total amount", "totalamount", "price", "turnover",
        "gross sales", "line total", "total",
    ),
    "order_id": (
        "order id", "orderid", "transaction id", "transactionid",
        "invoice no", "invoiceno", "invoice number", "receipt id",
        "order number",
    ),
    "category": (
        "category", "product category", "productcategory", "sub category",
        "subcategory", "segment", "department", "product line", "productline",
        "product group",
    ),
    "region": (
        "region", "country", "state", "market", "territory", "zone",
        "province", "area", "location", "city",
    ),
    "product": (
        "product", "product name", "productname", "item", "item name",
        "sku", "model", "description",
    ),
    "profit": (
        "profit", "net profit", "netprofit", "gross profit", "grossprofit",
        "margin", "profit margin", "income", "earnings",
    ),
    "quantity": (
        "quantity", "qty", "units", "units sold", "unitssold", "volume",
        "count",
    ),
    "cost": (
        "cost", "total cost", "totalcost", "cogs", "unit cost", "unitcost",
        "cost of goods",
    ),
}


def _normalize(value) -> str:
    """Lower-case, strip accents/punctuation and collapse whitespace."""
    text = unicodedata.normalize("NFKD", str(value))
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.lower().replace("&", " and ")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _compact(value) -> str:
    """Normalised form without spaces, used for fuzzy-free equality checks."""
    return _normalize(value).replace(" ", "")


def _column_maps(df: pd.DataFrame):
    exact: dict[str, object] = {}
    compact: dict[str, object] = {}

    for column in df.columns:
        exact.setdefault(_normalize(column), column)
        compact.setdefault(_compact(column), column)

    return exact, compact


def available_column_names(df: pd.DataFrame) -> list[str]:
    return [str(column) for column in df.columns]


def find_column(df, requested=None, candidates=()):
    """Resolve a column name requested by the client or a role candidate.

    Raises ValueError with the available column list when an explicitly
    requested column does not exist. Returns None when no candidate matches.
    """
    exact, compact = _column_maps(df)

    if requested:
        key = _compact(requested)

        if key in compact:
            return compact[key]

        if _normalize(requested) in exact:
            return exact[_normalize(requested)]

        raise ValueError(
            f"Column '{requested}' does not exist in this dataset. "
            f"Available columns: {', '.join(available_column_names(df))}"
        )

    normalized_candidates = [_compact(candidate) for candidate in candidates]

    for candidate in normalized_candidates:
        if candidate in compact:
            return compact[candidate]

    # Fall back to a substring match, preferring the shortest column name so
    # that "sales" matches "Sales" before "Sales Tax Adjustment".
    columns = list(df.columns)

    for candidate in normalized_candidates:
        if len(candidate) < 4:
            continue

        matches = [
            column for column in columns
            if candidate in _compact(column)
        ]

        if matches:
            return min(matches, key=lambda column: len(_compact(column)))

    return None


def find_requested_column(df, requested, role: str):
    """Resolve an explicitly requested column, with a role-aware error."""
    try:
        return find_column(df, requested)
    except ValueError as exc:
        raise ValueError(
            f"Unknown {role} column: {exc}"
        ) from exc


def resolve_columns(df, requested: dict | None = None) -> dict[str, str | None]:
    """Resolve every supported role for a dataset.

    Explicitly requested columns win; otherwise candidates are detected.
    """
    requested = requested or {}
    resolved: dict[str, str | None] = {}

    for role, candidates in CANDIDATES.items():
        explicit = requested.get(role)

        if explicit:
            resolved[role] = find_requested_column(df, explicit, role)
        else:
            resolved[role] = find_column(df, None, candidates)

    return resolved


def detect_columns(df) -> dict[str, str | None]:
    """Detect candidate columns for every supported role."""
    return resolve_columns(df, None)
