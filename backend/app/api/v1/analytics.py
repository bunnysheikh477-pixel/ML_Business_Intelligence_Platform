
from fastapi import APIRouter, HTTPException, Query
from pymongo.errors import PyMongoError

from app.analytics.aggregations import (
    category_sales,
    monthly_revenue,
    region_sales,
    top_products,
)
from app.analytics.columns import resolve_columns
from app.analytics.filters import apply_filters, build_facets
from app.analytics.kpis import calculate_kpis
from app.services.dataset_service import (
    get_dataset,
    get_dataset_dataframe,
)

router = APIRouter(
    prefix="/analytics",
    tags=["BI Analytics"],
)


@router.get("/{dataset_id}/overview")
def analytics_overview(
    dataset_id: str,
    revenue_column: str | None = Query(default=None),
    sales_column: str | None = Query(default=None),
    order_id_column: str | None = Query(default=None),
    date_column: str | None = Query(default=None),
    category_column: str | None = Query(default=None),
    region_column: str | None = Query(default=None),
    profit_column: str | None = Query(default=None),
    quantity_column: str | None = Query(default=None),
    product_column: str | None = Query(default=None),
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

        df = get_dataset_dataframe(document)

        columns = resolve_columns(df, {
            "revenue": revenue_column or sales_column,
            "order_id": order_id_column,
            "date": date_column,
            "category": category_column,
            "region": region_column,
            "profit": profit_column,
            "quantity": quantity_column,
            "product": product_column,
        })

        warnings: list[str] = []

        if columns["revenue"] is None:
            warnings.append(
                "No revenue/sales column could be detected, so revenue "
                "based KPIs and charts are unavailable. Select a column "
                "explicitly to continue."
            )

        filtered, applied_filters, filter_warnings = apply_filters(
            df,
            date_column=columns["date"],
            date_from=date_from,
            date_to=date_to,
            category_column=columns["category"],
            category_value=category_value,
            region_column=columns["region"],
            region_value=region_value,
        )

        warnings.extend(filter_warnings)

        kpis = calculate_kpis(
            filtered,
            revenue_column=columns["revenue"],
            order_id_column=columns["order_id"],
            profit_column=columns["profit"],
            quantity_column=columns["quantity"],
        )

        return {
            "success": True,
            "dataset": {
                "id": dataset_id,
                "name": document["name"],
            },
            "kpis": kpis,
            "monthly_revenue": monthly_revenue(
                filtered,
                revenue_column=columns["revenue"],
                date_column=columns["date"],
            ),
            "category_sales": category_sales(
                filtered,
                revenue_column=columns["revenue"],
                category_column=columns["category"],
            ),
            "region_sales": region_sales(
                filtered,
                revenue_column=columns["revenue"],
                region_column=columns["region"],
            ),
            "top_products": top_products(
                filtered,
                revenue_column=columns["revenue"],
                product_column=columns["product"],
                quantity_column=columns["quantity"],
            ),
            "detected_columns": columns,
            "available_columns": [
                str(column) for column in df.columns
            ],
            "filters": applied_filters,
            "facets": build_facets(
                df,
                category_column=columns["category"],
                region_column=columns["region"],
            ),
            "rows_analyzed": int(len(filtered)),
            "warnings": warnings,
        }

    except HTTPException:
        raise

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

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
