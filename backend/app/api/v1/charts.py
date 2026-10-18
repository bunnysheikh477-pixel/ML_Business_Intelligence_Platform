
import logging

from fastapi import APIRouter, HTTPException, Query
from pymongo.errors import PyMongoError

from app.analytics.filters import apply_filters
from app.charts.plotly_charts import (
    CHART_BUILDERS,
    build_chart,
    build_charts_payload,
    resolve_chart_params,
)
from app.core.cache import TTLCache
from app.core.config import settings
from app.services.dataset_service import (
    dataset_file_signature,
    get_dataset,
    get_dataset_dataframe,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/charts", tags=["Charts"])

# Generated figures are reused while the dataset file and query are unchanged.
chart_cache = TTLCache(
    ttl_seconds=settings.CHART_CACHE_TTL_SECONDS, max_entries=64
)


def _filter_parameters(
    date_from,
    date_to,
    category_value,
    region_value,
):
    return {
        "date_from": date_from,
        "date_to": date_to,
        "category_value": category_value,
        "region_value": region_value,
    }


def _cache_key(dataset_id, signature, params):
    return (
        dataset_id,
        signature,
        tuple(sorted((key, value) for key, value in params.items() if value)),
    )


def _build_payload(dataset_id, document, df, chart_params, filters):
    columns = resolve_chart_params(df, chart_params)

    filtered, applied_filters, warnings = apply_filters(
        df,
        date_column=columns["date_column"],
        date_from=filters["date_from"],
        date_to=filters["date_to"],
        category_column=columns["category_column"],
        category_value=filters["category_value"],
        region_column=columns["region_column"],
        region_value=filters["region_value"],
    )

    if columns["sales_column"] is None:
        warnings.append(
            "No revenue/sales column could be detected; revenue charts are "
            "unavailable until a column is selected explicitly."
        )

    payload = build_charts_payload(
        filtered,
        columns,
        dataset={"id": dataset_id, "name": document["name"]},
        applied_filters=applied_filters,
        warnings=warnings,
    )

    return payload


@router.get("/{dataset_id}")
def dataset_charts(
    dataset_id: str,
    date_column: str | None = Query(default=None),
    sales_column: str | None = Query(default=None),
    category_column: str | None = Query(default=None),
    region_column: str | None = Query(default=None),
    profit_column: str | None = Query(default=None),
    product_column: str | None = Query(default=None),
    quantity_column: str | None = Query(default=None),
    date_from: str | None = Query(default=None),
    date_to: str | None = Query(default=None),
    category_value: str | None = Query(default=None),
    region_value: str | None = Query(default=None),
):
    try:
        document = get_dataset(dataset_id)

        if document is None:
            raise HTTPException(
                status_code=404,
                detail="Dataset not found. Check the dataset ID.",
            )

        chart_params = {
            "date_column": date_column,
            "sales_column": sales_column,
            "category_column": category_column,
            "region_column": region_column,
            "profit_column": profit_column,
            "product_column": product_column,
            "quantity_column": quantity_column,
        }
        filters = _filter_parameters(
            date_from, date_to, category_value, region_value
        )

        cache_key = _cache_key(
            dataset_id, dataset_file_signature(document), {**chart_params, **filters}
        )

        cached = chart_cache.get(cache_key)

        if cached is not None:
            return {"success": True, "cached": True, **cached}

        df = get_dataset_dataframe(document)
        payload = _build_payload(
            dataset_id, document, df, chart_params, filters
        )

        chart_cache.set(cache_key, payload)

        return {"success": True, "cached": False, **payload}

    except HTTPException:
        raise

    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="Dataset file not found on storage.",
        )

    except PyMongoError:
        raise HTTPException(
            status_code=503,
            detail="MongoDB is unavailable.",
        )


@router.get("/{dataset_id}/{chart_key}")
def single_chart(
    dataset_id: str,
    chart_key: str,
    date_column: str | None = Query(default=None),
    sales_column: str | None = Query(default=None),
    category_column: str | None = Query(default=None),
    region_column: str | None = Query(default=None),
    profit_column: str | None = Query(default=None),
    product_column: str | None = Query(default=None),
    quantity_column: str | None = Query(default=None),
    date_from: str | None = Query(default=None),
    date_to: str | None = Query(default=None),
    category_value: str | None = Query(default=None),
    region_value: str | None = Query(default=None),
):
    if chart_key not in CHART_BUILDERS:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Unknown chart '{chart_key}'. Available charts: "
                f"{', '.join(CHART_BUILDERS)}"
            ),
        )

    try:
        document = get_dataset(dataset_id)

        if document is None:
            raise HTTPException(
                status_code=404,
                detail="Dataset not found. Check the dataset ID.",
            )

        df = get_dataset_dataframe(document)
        columns = resolve_chart_params(df, {
            "date_column": date_column,
            "sales_column": sales_column,
            "category_column": category_column,
            "region_column": region_column,
            "profit_column": profit_column,
            "product_column": product_column,
            "quantity_column": quantity_column,
        })

        filtered, applied_filters, warnings = apply_filters(
            df,
            date_column=columns["date_column"],
            date_from=date_from,
            date_to=date_to,
            category_column=columns["category_column"],
            category_value=category_value,
            region_column=columns["region_column"],
            region_value=region_value,
        )

        chart = build_chart(chart_key, filtered, columns)

        return {
            "success": True,
            "dataset": {"id": dataset_id, "name": document["name"]},
            "detected_columns": columns,
            "filters": applied_filters,
            "warnings": warnings,
            "chart": chart,
        }

    except HTTPException:
        raise

    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="Dataset file not found on storage.",
        )

    except PyMongoError:
        raise HTTPException(
            status_code=503,
            detail="MongoDB is unavailable.",
        )
