import json

import pandas as pd
import pytest

from app.charts.plotly_charts import (
    CHART_BUILDERS,
    build_chart,
    build_charts,
    build_forecast_figure,
    resolve_chart_params,
    serialize_figure,
)
from app.ml.sales_forecasting import forecast_sales


def test_all_charts_ready_for_sample(sample_frame):
    columns = resolve_chart_params(sample_frame)
    charts = build_charts(sample_frame, columns)

    assert {chart["key"] for chart in charts} == set(CHART_BUILDERS)

    by_key = {chart["key"]: chart for chart in charts}

    assert by_key["monthly_revenue"]["status"] == "ready"
    assert by_key["sales_by_category"]["status"] == "ready"
    assert by_key["sales_by_region"]["status"] == "ready"
    assert by_key["top_products"]["status"] == "ready"
    assert by_key["profit_vs_revenue"]["status"] == "ready"

    for chart in charts:
        if chart["status"] != "ready":
            continue

        assert chart["title"]
        assert chart["type"] in {"line", "bar", "scatter"}
        assert chart["figure"]["data"], chart["key"]
        assert chart["figure"]["layout"]


def test_chart_payload_is_json_serializable(sample_frame, messy_frame):
    columns = resolve_chart_params(sample_frame)

    for chart in build_charts(sample_frame, columns):
        assert json.dumps(chart)

        if chart["status"] == "ready":
            json.dumps(chart["figure"])

    # NaT dates and non-numeric text must not break serialization.
    messy_columns = resolve_chart_params(messy_frame)
    for chart in build_charts(messy_frame, messy_columns):
        assert json.dumps(chart)


def test_serialize_figure_handles_numpy_and_nan():
    import plotly.graph_objects as go

    fig = go.Figure(go.Bar(x=[1, 2, 3], y=[float("nan"), 2.0, 3.0]))
    payload = serialize_figure(fig)

    assert isinstance(payload, dict)
    json.dumps(payload)
    assert payload["data"][0]["y"][0] is None


def test_charts_degrade_when_columns_missing(no_date_frame):
    frame = no_date_frame[["OrderID", "Sales"]]
    columns = resolve_chart_params(frame)
    charts = {chart["key"]: chart for chart in build_charts(frame, columns)}

    assert charts["monthly_revenue"]["status"] == "unavailable"
    assert "date column" in charts["monthly_revenue"]["reason"].lower()
    assert charts["profit_vs_revenue"]["status"] == "unavailable"
    assert charts["sales_by_category"]["status"] == "unavailable"
    assert charts["sales_by_region"]["status"] == "unavailable"
    assert charts["top_products"]["status"] == "unavailable"
    assert charts["missing_values"]["status"] == "unavailable"


def test_unknown_chart_key_is_reported(no_date_frame):
    chart = build_chart("does_not_exist", no_date_frame, {})

    assert chart["status"] == "unavailable"
    assert "Unknown chart" in chart["reason"]


def test_resolve_chart_params_rejects_unknown_column(sample_frame):
    with pytest.raises(ValueError):
        resolve_chart_params(sample_frame, {"sales_column": "Nope"})


def test_chart_filters_are_applied(sample_frame):
    columns = resolve_chart_params(sample_frame)
    filtered = sample_frame[sample_frame["Region"] == "Lahore"]
    chart = build_chart("sales_by_region", filtered, columns)

    regions = chart["figure"]["data"][0]["x"]

    assert list(regions) == ["Lahore"]


def test_build_forecast_figure(sample_frame):
    result = forecast_sales(sample_frame, periods=3)
    figure = build_forecast_figure(result)

    json.dumps(figure)

    names = [trace.get("name") for trace in figure["data"]]

    assert "Actual" in names
    assert "Forecast" in names
    assert figure["layout"]["xaxis"]["type"] == "category"


def test_charts_are_deterministic(sample_frame):
    columns = resolve_chart_params(sample_frame)
    first = build_chart("monthly_revenue", sample_frame, columns)
    second = build_chart("monthly_revenue", sample_frame, columns)

    assert first["figure"] == second["figure"]


def test_charts_dont_crash_on_single_row():
    frame = pd.DataFrame({
        "OrderDate": ["2026-01-01"],
        "Sales": [10.0],
        "Category": ["A"],
        "Region": ["North"],
        "Profit": [2.0],
    })
    columns = resolve_chart_params(frame)

    for chart in build_charts(frame, columns):
        assert chart["status"] in {"ready", "unavailable"}
        assert json.dumps(chart)
