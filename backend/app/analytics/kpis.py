
from __future__ import annotations

import pandas as pd

from app.analytics.columns import (
    available_column_names,
    find_column,
    resolve_columns,
)

__all__ = [
    "find_column",
    "calculate_kpis",
    "data_quality_summary",
    "resolve_columns",
]


def _numeric(series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def data_quality_summary(df: pd.DataFrame) -> dict:
    """Missing-value and structural quality indicators for a dataset."""
    rows = int(len(df))
    columns = int(len(df.columns))
    total_cells = rows * columns
    missing_cells = int(df.isna().sum().sum())

    per_column = []

    for column in df.columns:
        missing = int(df[column].isna().sum())

        if missing:
            per_column.append({
                "name": str(column),
                "missing_values": missing,
                "missing_percentage": round(missing / rows * 100, 2)
                if rows else 0.0,
            })

    per_column.sort(key=lambda item: item["missing_values"], reverse=True)

    empty_columns = [
        str(column) for column in df.columns
        if rows and df[column].isna().all()
    ]

    return {
        "rows": rows,
        "columns": columns,
        "total_cells": total_cells,
        "missing_cells": missing_cells,
        "missing_percentage": (
            round(missing_cells / total_cells * 100, 2)
            if total_cells else 0.0
        ),
        "columns_with_missing": per_column[:15],
        "columns_missing_count": len(per_column),
        "empty_columns": empty_columns,
        "duplicate_rows": int(df.duplicated().sum()),
    }


def calculate_kpis(
    df: pd.DataFrame,
    revenue_column=None,
    order_id_column=None,
    profit_column=None,
    quantity_column=None,
) -> dict:
    """Calculate core BI metrics with explicit column detection.

    Every value is derived from the uploaded dataset only. Column roles that
    cannot be detected are reported as ``None`` together with an explanatory
    note, instead of inventing numbers.
    """
    columns = resolve_columns(df, {
        "revenue": revenue_column,
        "order_id": order_id_column,
        "profit": profit_column,
        "quantity": quantity_column,
    })

    resolved_revenue = columns["revenue"]
    resolved_order_id = columns["order_id"]
    resolved_profit = columns["profit"]
    resolved_quantity = columns["quantity"]

    notes: list[str] = []

    revenue = None
    revenue_values = None

    if resolved_revenue is not None:
        revenue_values = _numeric(df[resolved_revenue])
        revenue = round(float(revenue_values.sum()), 2)
        notes.append(
            f"Total revenue is the sum of column '{resolved_revenue}' "
            f"({int(revenue_values.notna().sum())} numeric values, "
            "non-numeric cells ignored)."
        )
    else:
        notes.append(
            "Total revenue is unavailable: no revenue/sales column was "
            "detected. Pass a revenue column explicitly."
        )

    if resolved_order_id is not None:
        total_orders = int(df[resolved_order_id].nunique(dropna=True))
        orders_method = "distinct_order_id"
        notes.append(
            f"Total orders counts distinct values of "
            f"'{resolved_order_id}', so multi-line orders are not "
            "double-counted."
        )
    else:
        total_orders = int(len(df))
        orders_method = "row_count"
        notes.append(
            "No order identifier column was detected, so total orders falls "
            "back to the row count. Multi-line orders may be over-counted."
        )

    average_order_value = (
        round(revenue / total_orders, 2)
        if revenue is not None and total_orders > 0
        else None
    )

    if revenue is not None and average_order_value is not None:
        notes.append(
            "Average order value = total revenue / total orders."
        )

    total_profit = None
    profit_margin = None

    if resolved_profit is not None:
        profit_values = _numeric(df[resolved_profit])
        total_profit = round(float(profit_values.sum()), 2)
        notes.append(
            f"Total profit is the sum of column '{resolved_profit}'."
        )

        if revenue:
            profit_margin = round(total_profit / revenue * 100, 2)
            notes.append(
                "Profit margin = total profit / total revenue * 100."
            )
    else:
        notes.append(
            "Profit metrics are unavailable: no profit column was detected."
        )

    total_quantity = None

    if resolved_quantity is not None:
        quantity_values = _numeric(df[resolved_quantity])
        total_quantity = round(float(quantity_values.sum()), 2)
        notes.append(
            f"Quantity sold is the sum of column '{resolved_quantity}'."
        )

    quality = data_quality_summary(df)

    if quality["missing_cells"]:
        notes.append(
            f"{quality['missing_cells']} missing values "
            f"({quality['missing_percentage']}% of all cells) were found; "
            "metrics ignore cells that cannot be parsed."
        )

    return {
        "total_rows": int(len(df)),
        "total_columns": int(len(df.columns)),
        "total_revenue": revenue,
        "total_orders": total_orders,
        "orders_count_method": orders_method,
        "average_order_value": average_order_value,
        "total_profit": total_profit,
        "profit_margin_percent": profit_margin,
        "total_quantity": total_quantity,
        "revenue_column": (
            str(resolved_revenue) if resolved_revenue is not None else None
        ),
        "order_id_column": (
            str(resolved_order_id) if resolved_order_id is not None else None
        ),
        "profit_column": (
            str(resolved_profit) if resolved_profit is not None else None
        ),
        "quantity_column": (
            str(resolved_quantity) if resolved_quantity is not None else None
        ),
        "available_columns": available_column_names(df),
        "data_quality": quality,
        "calculation_notes": notes,
    }
