
from __future__ import annotations

import json
import logging

import pandas as pd
import plotly.graph_objects as go

from app.analytics.aggregations import (
    category_sales,
    monthly_profit,
    monthly_revenue,
    region_sales,
    top_products,
)
from app.analytics.columns import available_column_names, resolve_columns
from app.analytics.kpis import data_quality_summary

logger = logging.getLogger(__name__)

FONT_FAMILY = "Manrope, DM Sans, Arial, sans-serif"
COLORS = {
    "primary": "#7C6CF2",
    "secondary": "#25B8A7",
    "accent": "#F4B860",
    "danger": "#F07D75",
    "muted": "#9AA1B2",
}

# Parameter name used by the API mapped to the detected column role.
PARAM_ROLES = {
    "date_column": "date",
    "sales_column": "revenue",
    "category_column": "category",
    "region_column": "region",
    "profit_column": "profit",
    "product_column": "product",
    "quantity_column": "quantity",
}

CHART_ORDER = (
    "monthly_revenue",
    "sales_by_category",
    "sales_by_region",
    "top_products",
    "profit_vs_revenue",
    "missing_values",
)


def resolve_chart_params(
    df: pd.DataFrame,
    requested: dict | None = None,
) -> dict:
    """Resolve requested/detected columns for chart generation.

    Raises ValueError when an explicitly requested column does not exist.
    """
    requested = requested or {}
    role_request = {
        role: requested.get(param)
        for param, role in PARAM_ROLES.items()
        if requested.get(param)
    }

    detected = resolve_columns(df, role_request)

    return {
        param: (
            str(detected[role]) if detected.get(role) else None
        )
        for param, role in PARAM_ROLES.items()
    }


def serialize_figure(fig: go.Figure) -> dict:
    """Convert a Plotly figure into a JSON-safe dict.

    ``fig.to_json()`` already converts NumPy scalars, pandas timestamps and
    non-finite values into JSON-compatible primitives (NaN/Inf become null).
    """
    return json.loads(fig.to_json())


def _base_layout(fig: go.Figure, height: int = 340) -> go.Figure:
    fig.update_layout(
        template="plotly_white",
        font=dict(family=FONT_FAMILY, size=11.5, color="#5f6578"),
        height=height,
        margin=dict(l=52, r=22, t=26, b=46, pad=4),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        hoverlabel=dict(
            bgcolor="#171927",
            font=dict(color="#ffffff", size=11),
            bordercolor="rgba(0,0,0,0)",
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0,
            bgcolor="rgba(0,0,0,0)",
        ),
        bargap=0.28,
    )
    fig.update_xaxes(
        showgrid=False,
        zeroline=False,
        linecolor="#E7E9F1",
        tickfont=dict(size=10.5, color="#8b91a4"),
        title_font=dict(size=11, color="#8b91a4"),
    )
    fig.update_yaxes(
        gridcolor="#EEF0F5",
        zeroline=False,
        tickformat=",.0f",
        tickfont=dict(size=10.5, color="#8b91a4"),
        title_font=dict(size=11, color="#8b91a4"),
    )
    return fig


def _monthly_revenue_chart(df, columns):
    revenue_column = columns.get("sales_column")
    date_column = columns.get("date_column")

    if not revenue_column or not date_column:
        return None, (
            "A date column and a revenue/sales column are required "
            "for the monthly revenue trend."
        )

    rows = monthly_revenue(
        df,
        revenue_column=revenue_column,
        date_column=date_column,
    )

    if not rows:
        return None, "No parseable dates and numeric revenue values found."

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=[row["month"] for row in rows],
        y=[row["revenue"] for row in rows],
        mode="lines+markers",
        name="Revenue",
        line=dict(color=COLORS["primary"], width=2.6),
        marker=dict(size=5),
        fill="tozeroy",
        fillcolor="rgba(124,108,242,0.10)",
        hovertemplate="%{x}<br>%{y:,.2f}<extra>Revenue</extra>",
    ))

    profit_rows = monthly_profit(
        df,
        profit_column=columns.get("profit_column"),
        date_column=date_column,
    )

    if profit_rows:
        profit_by_month = {row["month"]: row["profit"] for row in profit_rows}
        shared = [row for row in rows if row["month"] in profit_by_month]

        if shared:
            fig.add_trace(go.Scatter(
                x=[row["month"] for row in shared],
                y=[profit_by_month[row["month"]] for row in shared],
                mode="lines+markers",
                name="Profit",
                line=dict(color=COLORS["secondary"], width=2.2),
                marker=dict(size=4),
                hovertemplate=(
                    "%{x}<br>%{y:,.2f}<extra>Profit</extra>"
                ),
            ))

    fig.update_layout(
        xaxis=dict(
            title="Month",
            tickangle=-45 if len(rows) > 12 else 0,
            dtick=1 if len(rows) > 18 else None,
            type="category",
        ),
        yaxis=dict(title=f"Revenue ({revenue_column})"),
        hovermode="x unified",
    )
    _base_layout(fig, height=350)
    return fig, None


def _sales_by_category_chart(df, columns):
    revenue_column = columns.get("sales_column")
    category_column = columns.get("category_column")

    if not revenue_column or not category_column:
        return None, "No category column was detected in this dataset."

    rows = category_sales(
        df,
        revenue_column=revenue_column,
        category_column=category_column,
        limit=12,
    )

    if not rows:
        return None, "No categorical revenue data is available."

    rows = list(reversed(rows))
    fig = go.Figure(go.Bar(
        x=[row["revenue"] for row in rows],
        y=[row["category"] for row in rows],
        orientation="h",
        name="Revenue",
        marker=dict(
            color=COLORS["primary"],
            cornerradius=4,
        ),
        customdata=[[row["share_percent"]] for row in rows],
        hovertemplate=(
            "%{y}<br>%{x:,.2f} (%{customdata[0]:.1f}%)"
            "<extra></extra>"
        ),
    ))

    fig.update_layout(
        xaxis=dict(title="Revenue"),
        yaxis=dict(title="Category"),
    )
    _base_layout(fig, height=350)
    return fig, None


def _sales_by_region_chart(df, columns):
    revenue_column = columns.get("sales_column")
    region_column = columns.get("region_column")

    if not revenue_column or not region_column:
        return None, "No region column was detected in this dataset."

    rows = region_sales(
        df,
        revenue_column=revenue_column,
        region_column=region_column,
        limit=12,
    )

    if not rows:
        return None, "No regional revenue data is available."

    fig = go.Figure(go.Bar(
        x=[row["region"] for row in rows],
        y=[row["revenue"] for row in rows],
        name="Revenue",
        marker=dict(color=COLORS["secondary"], cornerradius=5),
        customdata=[[row["share_percent"]] for row in rows],
        hovertemplate=(
            "%{x}<br>%{y:,.2f} (%{customdata[0]:.1f}%)"
            "<extra></extra>"
        ),
    ))

    fig.update_layout(
        xaxis=dict(title="Region", tickangle=-30),
        yaxis=dict(title="Revenue"),
    )
    _base_layout(fig, height=330)
    return fig, None


def _top_products_chart(df, columns):
    revenue_column = columns.get("sales_column")
    product_column = columns.get("product_column")

    if not revenue_column or not product_column:
        return None, "No product column was detected in this dataset."

    rows = top_products(
        df,
        revenue_column=revenue_column,
        product_column=product_column,
        quantity_column=columns.get("quantity_column"),
        limit=10,
    )

    if not rows:
        return None, "No product-level revenue data is available."

    rows = list(reversed(rows))
    fig = go.Figure(go.Bar(
        x=[row["revenue"] for row in rows],
        y=[row["product"] for row in rows],
        orientation="h",
        name="Revenue",
        marker=dict(color=COLORS["accent"], cornerradius=4),
        hovertemplate="%{y}<br>%{x:,.2f}<extra></extra>",
    ))

    fig.update_layout(
        xaxis=dict(title="Revenue"),
        yaxis=dict(title="Product"),
    )
    _base_layout(fig, height=350)
    return fig, None


def _profit_vs_revenue_chart(df, columns):
    revenue_column = columns.get("sales_column")
    date_column = columns.get("date_column")
    profit_column = columns.get("profit_column")

    if not revenue_column or not date_column:
        return None, "A date column and a revenue column are required."

    if not profit_column:
        return None, "No profit column was detected in this dataset."

    revenue_rows = monthly_revenue(
        df,
        revenue_column=revenue_column,
        date_column=date_column,
    )
    profit_rows = monthly_profit(
        df,
        profit_column=profit_column,
        date_column=date_column,
    )

    if not revenue_rows or not profit_rows:
        return None, "Not enough monthly revenue/profit data to plot."

    profit_by_month = {row["month"]: row["profit"] for row in profit_rows}
    shared = [
        row for row in revenue_rows
        if row["month"] in profit_by_month
    ]

    if len(shared) < 2:
        return None, (
            "At least two months with both revenue and profit are required."
        )

    fig = go.Figure(go.Scatter(
        x=[row["revenue"] for row in shared],
        y=[profit_by_month[row["month"]] for row in shared],
        mode="markers",
        text=[row["month"] for row in shared],
        name="Month",
        marker=dict(
            size=11,
            color=[index for index in range(len(shared))],
            colorscale=[[0, COLORS["primary"]], [1, COLORS["secondary"]]],
            showscale=False,
            line=dict(width=1, color="#ffffff"),
        ),
        hovertemplate=(
            "%{text}<br>Revenue %{x:,.2f}<br>Profit %{y:,.2f}"
            "<extra></extra>"
        ),
    ))

    fig.update_layout(
        xaxis=dict(title=f"Revenue ({revenue_column})"),
        yaxis=dict(title=f"Profit ({profit_column})"),
        showlegend=False,
    )
    _base_layout(fig, height=340)
    return fig, None


def _missing_values_chart(df, columns):
    quality = data_quality_summary(df)
    missing = [
        column for column in quality["columns_with_missing"]
        if column["missing_values"] > 0
    ]

    if not missing:
        return None, "This dataset has no missing values."

    missing = list(reversed(missing[:12]))
    fig = go.Figure(go.Bar(
        x=[column["missing_values"] for column in missing],
        y=[column["name"] for column in missing],
        orientation="h",
        name="Missing values",
        marker=dict(color=COLORS["danger"], cornerradius=4),
        customdata=[[column["missing_percentage"]] for column in missing],
        hovertemplate=(
            "%{y}<br>%{x:,.0f} missing (%{customdata[0]:.1f}%)"
            "<extra></extra>"
        ),
    ))

    fig.update_layout(
        xaxis=dict(title="Missing cells"),
        yaxis=dict(title="Column"),
    )
    _base_layout(fig, height=330)
    return fig, None


CHART_BUILDERS = {
    "monthly_revenue": {
        "title": "Monthly revenue trend",
        "description": "Revenue aggregated by month from the selected "
                       "date and revenue columns.",
        "type": "line",
        "builder": _monthly_revenue_chart,
    },
    "sales_by_category": {
        "title": "Revenue by category",
        "description": "Top categories ranked by total revenue.",
        "type": "bar",
        "builder": _sales_by_category_chart,
    },
    "sales_by_region": {
        "title": "Revenue by region",
        "description": "Regional revenue distribution.",
        "type": "bar",
        "builder": _sales_by_region_chart,
    },
    "top_products": {
        "title": "Product performance",
        "description": "Best performing products by revenue.",
        "type": "bar",
        "builder": _top_products_chart,
    },
    "profit_vs_revenue": {
        "title": "Profit versus revenue",
        "description": "Monthly revenue and profit, plotted against "
                       "each other.",
        "type": "scatter",
        "builder": _profit_vs_revenue_chart,
    },
    "missing_values": {
        "title": "Missing data by column",
        "description": "Data-quality indicator: cells that are missing "
                       "per column.",
        "type": "bar",
        "builder": _missing_values_chart,
    },
}


def build_chart(key: str, df: pd.DataFrame, columns: dict) -> dict:
    """Build a single chart definition, never raising for unsupported data."""
    spec = CHART_BUILDERS.get(key)

    if spec is None:
        return {
            "key": key,
            "status": "unavailable",
            "reason": f"Unknown chart '{key}'.",
        }

    payload = {
        "key": key,
        "title": spec["title"],
        "description": spec["description"],
        "type": spec["type"],
    }

    try:
        fig, reason = spec["builder"](df, columns)
    except Exception:
        logger.exception("Chart '%s' failed for dataset", key)
        return {
            **payload,
            "status": "unavailable",
            "reason": "Chart could not be generated for this dataset.",
        }

    if fig is None:
        return {
            **payload,
            "status": "unavailable",
            "reason": reason or "Chart is not supported for this dataset.",
        }

    try:
        return {
            **payload,
            "status": "ready",
            "figure": serialize_figure(fig),
        }
    except (TypeError, ValueError):
        logger.exception("Chart '%s' failed to serialize", key)
        return {
            **payload,
            "status": "unavailable",
            "reason": "Chart output could not be serialized.",
        }


def build_charts(
    df: pd.DataFrame,
    columns: dict,
    keys: tuple[str, ...] = CHART_ORDER,
) -> list[dict]:
    """Build every requested chart; failures degrade to a status entry."""
    return [build_chart(key, df, columns) for key in keys]


def build_forecast_figure(result: dict) -> dict:
    """Actual vs predicted sales figure built from a forecast result."""
    history = result.get("history", [])
    forecasts = result.get("forecasts", [])
    evaluation = result.get("evaluation") or {}
    holdout = evaluation.get("actual_vs_predicted") or []

    fig = go.Figure()

    if history:
        fig.add_trace(go.Scatter(
            x=[row["month"] for row in history],
            y=[row.get("actual_sales") for row in history],
            mode="lines+markers",
            name="Actual",
            line=dict(color=COLORS["primary"], width=2.6),
            marker=dict(size=5),
            hovertemplate="%{x}<br>%{y:,.2f}<extra>Actual</extra>",
        ))

    if holdout:
        fig.add_trace(go.Scatter(
            x=[row["month"] for row in holdout],
            y=[row.get("predicted") for row in holdout],
            mode="markers",
            name="Model (holdout)",
            marker=dict(
                color=COLORS["accent"],
                size=9,
                symbol="diamond",
                line=dict(width=1, color="#ffffff"),
            ),
            hovertemplate="%{x}<br>%{y:,.2f}<extra>Model holdout</extra>",
        ))

        baseline = [
            row for row in holdout
            if row.get("baseline_prediction") is not None
        ]

        if baseline:
            fig.add_trace(go.Scatter(
                x=[row["month"] for row in baseline],
                y=[row["baseline_prediction"] for row in baseline],
                mode="markers",
                name="Baseline (naive)",
                marker=dict(
                    color=COLORS["muted"],
                    size=8,
                    symbol="x",
                ),
                hovertemplate=(
                    "%{x}<br>%{y:,.2f}<extra>Baseline</extra>"
                ),
            ))

    if forecasts:
        x_values = list(forecasts)
        y_values = [row["predicted_sales"] for row in forecasts]

        # Connect the forecast line to the last observed point.
        if history:
            x_values = [history[-1]["month"], *x_values]
            y_values = [history[-1].get("actual_sales"), *y_values]

        fig.add_trace(go.Scatter(
            x=x_values,
            y=y_values,
            mode="lines+markers",
            name="Forecast",
            line=dict(color=COLORS["secondary"], width=2.6, dash="dot"),
            marker=dict(size=6),
            hovertemplate="%{x}<br>%{y:,.2f}<extra>Forecast</extra>",
        ))

    fig.update_layout(
        xaxis=dict(title="Month", type="category", tickangle=-45),
        yaxis=dict(title=result.get("target", "Sales")),
        hovermode="x unified",
    )
    _base_layout(fig, height=360)
    return serialize_figure(fig)


def build_charts_payload(
    df: pd.DataFrame,
    columns: dict,
    *,
    dataset: dict,
    applied_filters: dict,
    warnings: list[str],
    keys: tuple[str, ...] = CHART_ORDER,
) -> dict:
    return {
        "dataset": dataset,
        "detected_columns": columns,
        "available_columns": available_column_names(df),
        "filters": applied_filters,
        "charts": build_charts(df, columns, keys),
        "warnings": warnings,
    }
