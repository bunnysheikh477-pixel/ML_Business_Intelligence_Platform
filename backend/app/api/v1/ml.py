
import logging

from fastapi import APIRouter, HTTPException, Query

from app.analytics.columns import resolve_columns
from app.charts.plotly_charts import build_forecast_figure
from app.ml.sales_forecasting import forecast_sales
from app.services.dataset_service import (
    get_dataset,
    get_dataset_dataframe,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/ml",
    tags=["Machine Learning"],
)


@router.post("/{dataset_id}/forecast")
def create_sales_forecast(
    dataset_id: str,
    date_column: str | None = Query(default=None),
    sales_column: str | None = Query(default=None),
    periods: int = Query(default=3, ge=1, le=12),
):
    """Generate a monthly sales forecast for an uploaded dataset."""
    try:
        dataset = get_dataset(dataset_id)

        if dataset is None:
            raise HTTPException(
                status_code=404,
                detail="Dataset not found. Upload the dataset first.",
            )

        dataframe = get_dataset_dataframe(dataset)

        columns = resolve_columns(dataframe, {
            "date": date_column,
            "revenue": sales_column,
        })

        available = ", ".join(str(column) for column in dataframe.columns)

        if columns["date"] is None:
            raise HTTPException(
                status_code=400,
                detail=(
                    "No date column could be detected. Select a date column "
                    f"explicitly. Available columns: {available}"
                ),
            )

        if columns["revenue"] is None:
            raise HTTPException(
                status_code=400,
                detail=(
                    "No sales column could be detected. Select a numeric "
                    f"sales column explicitly. Available columns: {available}"
                ),
            )

        result = forecast_sales(
            dataframe=dataframe,
            date_column=str(columns["date"]),
            sales_column=str(columns["revenue"]),
            periods=periods,
        )

        return {
            "success": True,
            "dataset_id": dataset_id,
            "dataset": {"id": dataset_id, "name": dataset["name"]},
            "columns": {
                "date_column": str(columns["date"]),
                "sales_column": str(columns["revenue"]),
            },
            "data": result,
            "figure": build_forecast_figure(result),
        }

    except HTTPException:
        raise

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="Dataset file not found on storage.",
        )

    except Exception as exc:
        logger.exception("Forecast generation failed for %s", dataset_id)
        raise HTTPException(
            status_code=500,
            detail="Unable to generate forecast. Check backend logs.",
        ) from exc
