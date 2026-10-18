import json

import pandas as pd
import pytest

from app.ml.sales_forecasting import (
    evaluate_sales_forecast,
    forecast_sales,
)


def test_forecast_on_sample_dataset(sample_frame):
    result = forecast_sales(
        sample_frame, date_column="OrderDate", sales_column="Sales", periods=3
    )

    assert result["model"] == "LinearRegression"
    assert result["frequency"] == "monthly"
    assert result["historical_months"] == 21
    assert len(result["history"]) == 21
    assert len(result["forecasts"]) == 3

    months = [row["month"] for row in result["history"]]
    assert months == sorted(months), "history must be chronological"
    assert months[-1] not in {row["month"] for row in result["forecasts"]}

    for row in result["forecasts"]:
        assert row["predicted_sales"] >= 0
        assert "raw_prediction" in row


def test_forecast_reports_chronological_holdout_metrics(sample_frame):
    result = forecast_sales(sample_frame, periods=2)
    evaluation = result["evaluation"]

    assert evaluation["status"] == "evaluated"
    assert evaluation["method"] == "chronological_holdout"
    assert evaluation["test_months"] >= 1
    assert evaluation["train_months"] + evaluation["test_months"] == 21

    model_metrics = evaluation["model_metrics"]
    assert model_metrics["mae"] >= 0
    assert model_metrics["rmse"] >= model_metrics["mae"]

    baseline = evaluation["baseline"]
    assert baseline["name"] == "naive_last_value"
    assert baseline["metrics"]["mae"] >= 0

    comparison = evaluation["comparison"]
    assert isinstance(comparison["model_better_than_baseline"], bool)
    assert len(evaluation["actual_vs_predicted"]) == evaluation["test_months"]

    for row in evaluation["actual_vs_predicted"]:
        assert {"month", "actual", "predicted", "baseline_prediction"} <= set(row)


def test_forecast_never_trains_on_future_months():
    rows = []
    for index in range(10):
        month = 1 + index
        rows.append({
            "OrderDate": f"2026-{month:02d}-05",
            "Sales": 100.0 + index * 10,
        })

    result = forecast_sales(pd.DataFrame(rows), periods=1)

    assert result["evaluation"]["train_months"] == 8
    assert result["evaluation"]["test_months"] == 2


def test_forecast_clamps_negative_predictions():
    rows = []
    for index in range(8):
        rows.append({
            "OrderDate": f"2026-{index + 1:02d}-05",
            "Sales": 1000.0 - index * 140,
        })

    result = forecast_sales(pd.DataFrame(rows), periods=3)

    assert all(row["predicted_sales"] >= 0 for row in result["forecasts"])
    assert any(
        row["raw_prediction"] < 0 for row in result["forecasts"]
    )
    assert any("negative" in warning.lower() for warning in result["warnings"])


def test_forecast_six_months_uses_single_holdout(sales_frame):
    result = forecast_sales(sales_frame, periods=2)

    assert result["historical_months"] == 6
    assert result["evaluation"]["status"] == "evaluated"
    assert result["evaluation"]["test_months"] == 1
    assert result["evaluation"]["train_months"] == 5


def test_forecast_requires_three_months():
    frame = pd.DataFrame({
        "OrderDate": ["2026-01-01", "2026-02-01"],
        "Sales": [10.0, 20.0],
    })

    with pytest.raises(ValueError) as error:
        forecast_sales(frame, periods=1)

    assert "3 distinct months" in str(error.value)


def test_forecast_rejects_unknown_columns(sample_frame):
    with pytest.raises(ValueError) as error:
        forecast_sales(sample_frame, date_column="Nope", periods=2)

    assert "Nope" in str(error.value)
    assert "Available columns" in str(error.value)


@pytest.mark.parametrize("periods", [0, -1, 13])
def test_forecast_validates_horizon(sample_frame, periods):
    with pytest.raises(ValueError):
        forecast_sales(sample_frame, periods=periods)


def test_forecast_rejects_non_integer_periods(sample_frame):
    with pytest.raises(ValueError):
        forecast_sales(sample_frame, periods=2.5)


def test_forecast_detects_case_insensitive_usage(sample_frame):
    frame = sample_frame.rename(
        columns={"OrderDate": "order date", "Sales": "sales"}
    )
    result = forecast_sales(frame, date_column="order date", sales_column="sales")

    assert result["historical_months"] == 21


def test_evaluate_sales_forecast_insufficient_data(sales_frame):
    result = evaluate_sales_forecast(sales_frame, test_months=6)

    assert result["status"] == "insufficient_data"
    assert result["available_months"] == 6
    assert result["required_months"] == 7


def test_evaluate_sales_forecast_metrics(sample_frame):
    result = evaluate_sales_forecast(sample_frame, test_months=3)

    assert result["status"] == "evaluated"
    assert result["model_metrics"]["mae"] >= 0
    assert result["model_metrics"]["rmse"] >= result["model_metrics"]["mae"]
    assert result["note"]


def test_forecast_drops_invalid_rows_and_notes():
    rows = [
        {"OrderDate": "2026-01-01", "Sales": "100"},
        {"OrderDate": "2026-02-01", "Sales": "not-a-number"},
        {"OrderDate": "invalid", "Sales": "30"},
        {"OrderDate": "2026-02-15", "Sales": "200"},
        {"OrderDate": "2026-03-15", "Sales": "300"},
    ]

    result = forecast_sales(pd.DataFrame(rows), periods=1)

    assert result["historical_months"] == 3
    assert any("excluded" in note for note in result["notes"])


def test_forecast_zero_sales_mape_note():
    rows = []
    for index in range(8):
        rows.append({
            "OrderDate": f"2026-{index + 1:02d}-05",
            "Sales": 0.0 if index == 6 else 100.0 + index,
        })

    result = forecast_sales(pd.DataFrame(rows), periods=1)
    evaluation = result["evaluation"]

    assert evaluation["status"] == "evaluated"
    assert evaluation["mape_note"] is not None
    assert "zero" in evaluation["mape_note"].lower()


def test_forecast_result_is_json_serializable(sample_frame):
    result = forecast_sales(sample_frame, periods=3)
    json.dumps(result)
