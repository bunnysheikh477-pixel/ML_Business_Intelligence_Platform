
from __future__ import annotations

import pandas as pd

from app.analytics.columns import find_column

REVENUE_CANDIDATES = (
    "revenue", "sales", "total sales", "net sales",
    "amount", "total amount", "price", "turnover",
)


def _clean_frame(df, value_column: str, date_column: str | None = None):
    if date_column is None:
        data = pd.DataFrame({
            "value": pd.to_numeric(df[value_column], errors="coerce"),
        })
        data = data.dropna(subset=["value"])
        return data

    data = pd.DataFrame({
        "date": pd.to_datetime(df[date_column], errors="coerce"),
        "value": pd.to_numeric(df[value_column], errors="coerce"),
    })
    return data.dropna(subset=["date", "value"])


def _resolve_revenue(df, revenue_column=None):
    return find_column(df, revenue_column, REVENUE_CANDIDATES)


def monthly_revenue(
    df,
    revenue_column=None,
    date_column=None,
):
    """Sum revenue per calendar month, ordered chronologically."""
    revenue_column = _resolve_revenue(df, revenue_column)

    date_column = find_column(
        df,
        date_column,
        ("date", "order date", "orderdate", "created at", "timestamp",
         "invoice date", "purchase date"),
    )

    if revenue_column is None or date_column is None:
        return []

    data = _clean_frame(df, revenue_column, date_column)

    if data.empty:
        return []

    data["month"] = data["date"].dt.to_period("M").astype(str)

    result = (
        data.groupby("month")["value"]
        .sum()
        .sort_index()
    )

    return [
        {
            "month": str(month),
            "revenue": round(float(value), 2),
        }
        for month, value in result.items()
    ]


def monthly_profit(
    df,
    profit_column=None,
    date_column=None,
):
    """Sum profit per calendar month. Empty when no profit column exists."""
    profit_column = find_column(
        df,
        profit_column,
        ("profit", "net profit", "gross profit", "margin", "income"),
    )

    date_column = find_column(
        df,
        date_column,
        ("date", "order date", "orderdate", "created at", "timestamp",
         "invoice date", "purchase date"),
    )

    if profit_column is None or date_column is None:
        return []

    data = _clean_frame(df, profit_column, date_column)

    if data.empty:
        return []

    data["month"] = data["date"].dt.to_period("M").astype(str)

    result = data.groupby("month")["value"].sum().sort_index()

    return [
        {
            "month": str(month),
            "profit": round(float(value), 2),
        }
        for month, value in result.items()
    ]


def category_sales(
    df,
    revenue_column=None,
    category_column=None,
    limit: int = 10,
):
    """Sum revenue per category, highest first."""
    revenue_column = _resolve_revenue(df, revenue_column)

    category_column = find_column(
        df,
        category_column,
        (
            "category", "product category", "sub category",
            "segment", "department", "product", "product name",
        ),
    )

    if revenue_column is None or category_column is None:
        return []

    data = pd.DataFrame({
        "category": df[category_column].fillna("Unknown").astype(str).str.strip(),
        "revenue": pd.to_numeric(df[revenue_column], errors="coerce"),
    })
    data = data.dropna(subset=["revenue"])
    data = data[data["category"] != ""]

    if data.empty:
        return []

    result = (
        data.groupby("category")["revenue"]
        .sum()
        .sort_values(ascending=False)
        .head(limit)
    )

    total = float(result.sum())

    return [
        {
            "category": category,
            "revenue": round(float(value), 2),
            "share_percent": (
                round(value / total * 100, 2) if total else 0.0
            ),
        }
        for category, value in result.items()
    ]


def region_sales(
    df,
    revenue_column=None,
    region_column=None,
    limit: int = 10,
):
    """Sum revenue per region, highest first."""
    revenue_column = _resolve_revenue(df, revenue_column)

    region_column = find_column(
        df,
        region_column,
        ("region", "country", "state", "market", "territory", "zone",
         "province", "area", "location", "city"),
    )

    if revenue_column is None or region_column is None:
        return []

    data = pd.DataFrame({
        "region": df[region_column].fillna("Unknown").astype(str).str.strip(),
        "revenue": pd.to_numeric(df[revenue_column], errors="coerce"),
    })
    data = data.dropna(subset=["revenue"])
    data = data[data["region"] != ""]

    if data.empty:
        return []

    result = (
        data.groupby("region")["revenue"]
        .sum()
        .sort_values(ascending=False)
        .head(limit)
    )

    total = float(result.sum())

    return [
        {
            "region": region,
            "revenue": round(float(value), 2),
            "share_percent": (
                round(value / total * 100, 2) if total else 0.0
            ),
        }
        for region, value in result.items()
    ]


def top_products(
    df,
    revenue_column=None,
    product_column=None,
    quantity_column=None,
    limit: int = 10,
):
    """Rank products by revenue, with quantity sold when available."""
    revenue_column = _resolve_revenue(df, revenue_column)

    product_column = find_column(
        df,
        product_column,
        ("product", "product name", "item", "item name", "sku", "model",
         "description"),
    )

    quantity_column = find_column(
        df,
        quantity_column,
        ("quantity", "qty", "units", "units sold", "volume"),
    )

    if revenue_column is None or product_column is None:
        return []

    data = pd.DataFrame({
        "product": df[product_column].fillna("Unknown").astype(str).str.strip(),
        "revenue": pd.to_numeric(df[revenue_column], errors="coerce"),
    })

    if quantity_column is not None:
        data["quantity"] = pd.to_numeric(
            df[quantity_column], errors="coerce"
        )

    data = data.dropna(subset=["revenue"])
    data = data[data["product"] != ""]

    if data.empty:
        return []

    if quantity_column is not None:
        grouped = data.groupby("product").agg(
            revenue=("revenue", "sum"),
            quantity=("quantity", "sum"),
        )
    else:
        grouped = data.groupby("product").agg(revenue=("revenue", "sum"))

    grouped = grouped.sort_values("revenue", ascending=False).head(limit)
    total_revenue = float(grouped["revenue"].sum())

    results = []

    for product, row in grouped.iterrows():
        item = {
            "product": str(product),
            "revenue": round(float(row["revenue"]), 2),
            "share_percent": (
                round(float(row["revenue"]) / total_revenue * 100, 2)
                if total_revenue else 0.0
            ),
        }

        if quantity_column is not None:
            quantity = row["quantity"]
            item["quantity"] = (
                round(float(quantity), 2)
                if pd.notna(quantity) else None
            )

        results.append(item)

    return results
