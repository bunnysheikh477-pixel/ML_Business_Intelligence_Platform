import pandas as pd
import pytest

from app.analytics.aggregations import (
    category_sales,
    monthly_profit,
    monthly_revenue,
    region_sales,
    top_products,
)
from app.analytics.columns import detect_columns, find_column
from app.analytics.filters import apply_filters, build_facets
from app.analytics.kpis import calculate_kpis, data_quality_summary


def test_detect_columns_for_sample(sample_frame):
    detected = detect_columns(sample_frame)

    assert detected["date"] == "OrderDate"
    assert detected["revenue"] == "Sales"
    assert detected["order_id"] == "OrderID"
    assert detected["category"] == "Category"
    assert detected["region"] == "Region"
    assert detected["product"] == "Product"
    assert detected["profit"] == "Profit"
    assert detected["quantity"] == "Quantity"


def test_find_column_accepts_normalised_names(messy_frame):
    assert find_column(messy_frame, "order date") == "Order Date"
    assert find_column(messy_frame, "ORDERID", ("order id",)) == "Order ID"


def test_find_column_unknown_request_reports_available(messy_frame):
    with pytest.raises(ValueError) as error:
        find_column(messy_frame, "DoesNotExist")

    assert "DoesNotExist" in str(error.value)
    assert "Order Date" in str(error.value)


def test_detect_columns_without_date(no_date_frame):
    detected = detect_columns(no_date_frame)

    assert detected["date"] is None
    assert detected["revenue"] == "Sales"


def test_calculate_kpis_known_values(sales_frame):
    kpis = calculate_kpis(sales_frame)

    assert kpis["total_rows"] == 8
    assert kpis["total_columns"] == 8
    assert kpis["total_revenue"] == 1040.0
    assert kpis["total_orders"] == 7
    assert kpis["orders_count_method"] == "distinct_order_id"
    assert kpis["average_order_value"] == pytest.approx(148.57, abs=0.01)
    assert kpis["total_profit"] == 203.0
    assert kpis["profit_margin_percent"] == pytest.approx(19.52, abs=0.01)
    assert kpis["total_quantity"] == 16.0
    assert any("distinct values" in note for note in kpis["calculation_notes"])


def test_calculate_kpis_without_revenue_column(no_date_frame):
    frame = no_date_frame.rename(columns={"Sales": "Unrelated"})
    kpis = calculate_kpis(frame)

    assert kpis["total_revenue"] is None
    assert kpis["average_order_value"] is None
    assert kpis["orders_count_method"] == "distinct_order_id"
    assert any(
        "no revenue/sales column was detected" in note.lower()
        for note in kpis["calculation_notes"]
    )


def test_data_quality_summary(messy_frame):
    quality = data_quality_summary(messy_frame)

    assert quality["rows"] == 4
    assert quality["missing_cells"] == 6
    assert quality["empty_columns"] == ["Empty"]
    assert quality["columns_with_missing"][0]["name"] == "Empty"


def test_monthly_revenue_sums_and_sorts(sales_frame):
    rows = monthly_revenue(sales_frame)

    assert [row["month"] for row in rows] == [
        "2026-01", "2026-02", "2026-03",
        "2026-04", "2026-05", "2026-06",
    ]
    assert rows[0]["revenue"] == 150.0
    assert rows[-1]["revenue"] == 380.0


def test_monthly_profit_requires_profit_column(no_date_frame):
    assert monthly_profit(no_date_frame) == []


def test_category_and_region_aggregations(sales_frame):
    categories = category_sales(sales_frame)
    regions = region_sales(sales_frame)

    assert categories[0]["category"] == "Software"
    assert categories[0]["revenue"] == 590.0
    assert categories[0]["share_percent"] == pytest.approx(56.73, abs=0.01)

    assert regions[0]["region"] == "North"
    assert regions[0]["revenue"] == 600.0
    assert regions[0]["share_percent"] == pytest.approx(57.69, abs=0.01)


def test_top_products_includes_quantity(sales_frame):
    products = top_products(sales_frame)

    assert len(products) == 2
    by_name = {item["product"]: item for item in products}
    assert by_name["Gadget"]["quantity"] == 8.0
    assert by_name["Widget"]["revenue"] == 540.0
    assert products[0]["product"] == "Widget"


def test_apply_filters_date_range(sales_frame):
    filtered, applied, warnings = apply_filters(
        sales_frame, date_from="2026-03-01", date_to="2026-04-30"
    )

    assert warnings == []
    assert len(filtered) == 2
    assert applied["date_from"] == "2026-03-01"
    assert applied["date_to"] == "2026-04-30"
    assert applied["date_column"] == "OrderDate"


def test_apply_filters_invalid_date(sales_frame):
    with pytest.raises(ValueError):
        apply_filters(sales_frame, date_from="yesterday")


def test_apply_filters_category_and_region(sales_frame):
    filtered, applied, _ = apply_filters(
        sales_frame, category_value="hardware", region_value="North"
    )

    assert len(filtered) == 3
    assert applied["category_value"] == "hardware"
    assert applied["region_value"] == "North"


def test_apply_filters_warns_when_nothing_matches(sales_frame):
    filtered, _, warnings = apply_filters(
        sales_frame, category_value="Unknown Category"
    )

    assert len(filtered) == 0
    assert any("No rows match category" in warning for warning in warnings)


def test_build_facets(sales_frame):
    facets = build_facets(sales_frame)

    assert facets["category"] == ["Hardware", "Software"]
    assert facets["region"] == ["North", "South"]


def test_filters_handle_missing_values(messy_frame):
    filtered, _, warnings = apply_filters(
        messy_frame, category_value="A", region_value="North"
    )

    assert isinstance(filtered, pd.DataFrame)
    assert warnings
