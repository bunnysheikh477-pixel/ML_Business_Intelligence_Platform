
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error

MIN_MONTHS_TO_FORECAST = 3
MIN_MONTHS_FOR_EVALUATION = 6
MAX_PERIODS = 12
BASELINE_NAME = "naive_last_value"


def _available_columns(dataframe: pd.DataFrame) -> str:
    return ", ".join(str(column) for column in dataframe.columns)


def _validate_columns(dataframe: pd.DataFrame, date_column: str, sales_column: str):
    if date_column not in dataframe.columns:
        raise ValueError(
            f"Date column '{date_column}' was not found. "
            f"Available columns: {_available_columns(dataframe)}"
        )

    if sales_column not in dataframe.columns:
        raise ValueError(
            f"Sales column '{sales_column}' was not found. "
            f"Available columns: {_available_columns(dataframe)}"
        )


def _prepare_monthly(
    dataframe: pd.DataFrame,
    date_column: str,
    sales_column: str,
) -> tuple[pd.Series, int]:
    """Aggregate individual transactions into a monthly sales series."""
    _validate_columns(dataframe, date_column, sales_column)

    work = dataframe[[date_column, sales_column]].copy()
    work["date"] = pd.to_datetime(work[date_column], errors="coerce")
    work["sales"] = pd.to_numeric(work[sales_column], errors="coerce")

    invalid_dates = int(work["date"].isna().sum())
    invalid_sales = int(work["sales"].isna().sum())

    work = work.dropna(subset=["date", "sales"])

    if work.empty:
        raise ValueError(
            "No valid dates and numeric sales values were found in the "
            "selected columns."
        )

    work["month"] = work["date"].dt.to_period("M")
    monthly = work.groupby("month")["sales"].sum().sort_index()

    dropped = invalid_dates + invalid_sales
    return monthly, dropped


def _metrics(actual: np.ndarray, predicted: np.ndarray) -> dict:
    mae = float(mean_absolute_error(actual, predicted))
    rmse = float(np.sqrt(mean_squared_error(actual, predicted)))

    nonzero = actual != 0
    mape = None

    if nonzero.any():
        mape = float(
            np.mean(
                np.abs(
                    (actual[nonzero] - predicted[nonzero])
                    / actual[nonzero]
                )
            )
            * 100
        )

    return {
        "mae": round(mae, 2),
        "rmse": round(rmse, 2),
        "mape_percent": round(mape, 2) if mape is not None else None,
    }


def _holdout_evaluation(monthly: pd.Series, test_months: int) -> dict:
    """Chronological holdout evaluation of the trend model vs a baseline."""
    train = monthly.iloc[:-test_months]
    test = monthly.iloc[-test_months:]

    model = LinearRegression()
    train_x = np.arange(len(train)).reshape(-1, 1)
    model.fit(train_x, train.to_numpy())

    test_positions = np.arange(
        len(train), len(train) + len(test)
    ).reshape(-1, 1)
    predictions = model.predict(test_positions)

    # Baseline: repeat the last observed training value (persistence).
    baseline_predictions = np.full(
        shape=len(test), fill_value=float(train.iloc[-1])
    )

    actual = test.to_numpy(dtype=float)

    model_metrics = _metrics(actual, predictions)
    baseline_metrics = _metrics(actual, baseline_predictions)

    baseline_mae = baseline_metrics["mae"]
    mae_improvement = None

    if baseline_mae > 0:
        mae_improvement = round(
            (baseline_mae - model_metrics["mae"]) / baseline_mae * 100, 2
        )

    mape_note = (
        "MAPE is only meaningful for non-zero sales; months with zero "
        "actual sales were excluded."
        if (actual == 0).any() else None
    )

    return {
        "status": "evaluated",
        "method": "chronological_holdout",
        "train_months": int(len(train)),
        "test_months": int(len(test)),
        "model_metrics": model_metrics,
        "baseline": {
            "name": BASELINE_NAME,
            "description": (
                "Repeats the most recent training month's sales for every "
                "future month."
            ),
            "metrics": baseline_metrics,
        },
        "comparison": {
            "model_better_than_baseline": (
                model_metrics["mae"] < baseline_metrics["mae"]
            ),
            "mae_improvement_percent": mae_improvement,
        },
        "actual_vs_predicted": [
            {
                "month": str(month),
                "actual": round(float(actual_value), 2),
                "predicted": round(float(predicted_value), 2),
                "baseline_prediction": round(float(baseline_value), 2),
            }
            for month, actual_value, predicted_value, baseline_value
            in zip(test.index, actual, predictions, baseline_predictions)
        ],
        "mape_note": mape_note,
        "note": (
            "Metrics come from a small chronological holdout. Treat them as "
            "indicative; more history gives more reliable accuracy."
        ),
    }


def _choose_test_months(months: int) -> int:
    if months < MIN_MONTHS_FOR_EVALUATION:
        return 0

    return min(3, max(1, months // 4))


def forecast_sales(
    dataframe: pd.DataFrame,
    date_column: str = "OrderDate",
    sales_column: str = "Sales",
    periods: int = 3,
) -> dict:
    """Aggregate monthly sales, validate a trend model and forecast ahead."""
    if not isinstance(periods, int) or isinstance(periods, bool):
        raise ValueError("Periods must be a whole number.")

    if periods < 1 or periods > MAX_PERIODS:
        raise ValueError(
            f"Periods must be between 1 and {MAX_PERIODS}."
        )

    monthly, dropped_rows = _prepare_monthly(
        dataframe, date_column, sales_column
    )

    if len(monthly) < MIN_MONTHS_TO_FORECAST:
        raise ValueError(
            f"At least {MIN_MONTHS_TO_FORECAST} distinct months of sales "
            f"data are required. Found {len(monthly)}."
        )

    warnings: list[str] = []
    notes: list[str] = []

    if dropped_rows:
        notes.append(
            f"{dropped_rows} row(s) were excluded because their date or "
            "sales value could not be parsed."
        )

    # Fit the production model on the full history.
    positions = np.arange(len(monthly)).reshape(-1, 1)
    model = LinearRegression()
    model.fit(positions, monthly.to_numpy(dtype=float))

    test_months = _choose_test_months(len(monthly))
    evaluation = None

    if test_months:
        evaluation = _holdout_evaluation(monthly, test_months)

        if not evaluation["comparison"]["model_better_than_baseline"]:
            warnings.append(
                "The trend model did not beat the naive baseline on the "
                "holdout period; treat these forecasts with caution."
            )
    else:
        evaluation = {
            "status": "insufficient_data",
            "available_months": int(len(monthly)),
            "required_months": MIN_MONTHS_FOR_EVALUATION,
            "message": (
                "At least "
                f"{MIN_MONTHS_FOR_EVALUATION} months of history are needed "
                "for a chronological holdout evaluation. No accuracy "
                "metrics are reported."
            ),
        }
        warnings.append(
            f"Only {len(monthly)} months of history: no holdout evaluation "
            "could be performed, so no accuracy metrics are reported."
        )

    # Forecast future monthly periods.
    future_positions = np.arange(
        len(monthly), len(monthly) + periods
    ).reshape(-1, 1)
    raw_predictions = model.predict(future_positions)

    clamped = int((raw_predictions < 0).sum())
    last_month = monthly.index[-1]

    forecasts = []

    for offset, raw_prediction in enumerate(raw_predictions, start=1):
        future_month = last_month + offset
        raw_value = float(raw_prediction)

        forecasts.append({
            "month": str(future_month),
            "predicted_sales": round(max(0.0, raw_value), 2),
            "raw_prediction": round(raw_value, 2),
        })

    if clamped:
        warnings.append(
            f"{clamped} raw prediction(s) were negative and were clamped to "
            "0 for display. A linear trend on declining sales can produce "
            "negative values that are not valid business outcomes; add more "
            "recent history or a different model before acting on them."
        )

    if len(monthly) < 12:
        notes.append(
            f"Only {len(monthly)} monthly points: the model captures a "
            "straight-line trend, so seasonal patterns are not modelled."
        )

    history = [
        {
            "month": str(month),
            "actual_sales": round(float(sales), 2),
        }
        for month, sales in monthly.items()
    ]

    return {
        "model": "LinearRegression",
        "baseline": BASELINE_NAME,
        "target": sales_column,
        "date_column": date_column,
        "frequency": "monthly",
        "historical_months": int(len(monthly)),
        "history": history,
        "forecasts": forecasts,
        "evaluation": evaluation,
        "warnings": warnings,
        "notes": notes,
        # Kept for backwards compatibility with the original response shape.
        "warning": warnings[0] if warnings else None,
    }


def evaluate_sales_forecast(
    dataframe: pd.DataFrame,
    date_column: str = "OrderDate",
    sales_column: str = "Sales",
    test_months: int = 2,
) -> dict:
    """Evaluate the trend model on a chronological holdout."""
    if not isinstance(test_months, int) or isinstance(test_months, bool):
        raise ValueError("test_months must be a whole number.")

    if test_months < 1:
        raise ValueError("test_months must be at least 1.")

    monthly, _ = _prepare_monthly(dataframe, date_column, sales_column)

    if len(monthly) <= test_months:
        return {
            "status": "insufficient_data",
            "available_months": int(len(monthly)),
            "required_months": test_months + 1,
            "message": (
                "Need more distinct monthly observations than the number of "
                "test months."
            ),
        }

    return _holdout_evaluation(monthly, test_months)
