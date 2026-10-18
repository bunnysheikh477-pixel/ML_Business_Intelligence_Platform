
import pytest
from bson import ObjectId
from fastapi.testclient import TestClient

from app.api.v1 import analytics as analytics_api
from app.api.v1 import charts as charts_api
from app.api.v1 import datasets as datasets_api
from app.api.v1 import ml as ml_api
from app.main import app

DATASET_ID = str(ObjectId())


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def dataset_document(sample_frame, monkeypatch):
    """Patch every module that loads datasets to use an in-memory frame."""
    document = {
        "_id": ObjectId(DATASET_ID),
        "name": "sample_sales.csv",
        "file_path": "sample_sales.csv",
        "file_type": ".csv",
        "file_size_bytes": 100,
        "row_count": len(sample_frame),
        "column_count": len(sample_frame.columns),
        "columns": [str(column) for column in sample_frame.columns],
        "created_at": None,
    }
    frame = sample_frame.copy()

    def get_dataset(dataset_id):
        return document if dataset_id == DATASET_ID else None

    def get_dataset_dataframe(document):
        return frame.copy()

    for module in (analytics_api, charts_api, ml_api):
        monkeypatch.setattr(module, "get_dataset", get_dataset)
        monkeypatch.setattr(
            module, "get_dataset_dataframe", get_dataset_dataframe
        )

    charts_api.chart_cache.clear()

    return document


def test_root_and_openapi(client):
    assert client.get("/").status_code == 200

    schema = client.get("/openapi.json").json()
    paths = schema["paths"]

    for path in (
        "/api/v1/datasets/upload",
        "/api/v1/datasets/",
        "/api/v1/datasets/{dataset_id}",
        "/api/v1/datasets/{dataset_id}/preview",
        "/api/v1/datasets/{dataset_id}/profile",
        "/api/v1/analytics/{dataset_id}/overview",
        "/api/v1/charts/{dataset_id}",
        "/api/v1/charts/{dataset_id}/{chart_key}",
        "/api/v1/ml/{dataset_id}/forecast",
    ):
        assert path in paths, path


def test_analytics_overview(client, dataset_document):
    response = client.get(f"/api/v1/analytics/{DATASET_ID}/overview")
    body = response.json()

    assert response.status_code == 200
    assert body["success"] is True
    assert body["dataset"]["id"] == DATASET_ID
    assert body["kpis"]["total_revenue"] > 0
    assert body["kpis"]["total_orders"] > 0
    assert body["kpis"]["data_quality"]["rows"] > 0
    assert body["monthly_revenue"]
    assert body["region_sales"]
    assert body["top_products"]
    assert body["detected_columns"]["revenue"] == "Sales"
    assert "Sales" in body["available_columns"]


def test_analytics_overview_unknown_dataset(client, dataset_document):
    response = client.get(f"/api/v1/analytics/{ObjectId()}/overview")

    assert response.status_code == 404


def test_analytics_overview_invalid_dataset_id(client, dataset_document):
    response = client.get("/api/v1/analytics/not-an-id/overview")

    assert response.status_code == 404


def test_analytics_overview_unknown_column(client, dataset_document):
    response = client.get(
        f"/api/v1/analytics/{DATASET_ID}/overview",
        params={"revenue_column": "Nope"},
    )

    assert response.status_code == 400
    assert "Nope" in response.json()["detail"]


def test_analytics_overview_filters(client, dataset_document):
    response = client.get(
        f"/api/v1/analytics/{DATASET_ID}/overview",
        params={"date_from": "2026-01-01", "date_to": "2026-12-31"},
    )
    body = response.json()

    assert response.status_code == 200
    assert body["filters"]["date_from"] == "2026-01-01"
    assert 0 < body["rows_analyzed"] < dataset_document["row_count"]
    assert body["kpis"]["total_rows"] == body["rows_analyzed"]


def test_analytics_overview_bad_date(client, dataset_document):
    response = client.get(
        f"/api/v1/analytics/{DATASET_ID}/overview",
        params={"date_from": "31/01/2026-typo"},
    )

    assert response.status_code == 400


def test_charts_endpoint_returns_plotly_figures(client, dataset_document):
    response = client.get(f"/api/v1/charts/{DATASET_ID}")
    body = response.json()

    assert response.status_code == 200
    assert body["success"] is True
    assert body["cached"] is False

    ready = {
        chart["key"]: chart for chart in body["charts"]
        if chart["status"] == "ready"
    }

    assert {"monthly_revenue", "sales_by_region", "top_products"} <= set(ready)

    for chart in ready.values():
        assert chart["figure"]["data"]
        assert "layout" in chart["figure"]

    detect = body["detected_columns"]
    assert detect["sales_column"] == "Sales"
    assert detect["date_column"] == "OrderDate"


def test_charts_endpoint_is_cached(client, dataset_document):
    first = client.get(f"/api/v1/charts/{DATASET_ID}").json()
    second = client.get(f"/api/v1/charts/{DATASET_ID}").json()

    assert first["cached"] is False
    assert second["cached"] is True
    assert second["charts"] == first["charts"]


def test_charts_endpoint_unknown_dataset(client, dataset_document):
    assert client.get(f"/api/v1/charts/{ObjectId()}").status_code == 404


def test_single_chart_endpoint(client, dataset_document):
    response = client.get(f"/api/v1/charts/{DATASET_ID}/monthly_revenue")
    body = response.json()

    assert response.status_code == 200
    assert body["chart"]["status"] == "ready"
    assert body["chart"]["figure"]["data"]


def test_single_chart_unknown_key(client, dataset_document):
    response = client.get(f"/api/v1/charts/{DATASET_ID}/not_a_chart")

    assert response.status_code == 404
    assert "Available charts" in response.json()["detail"]


def test_forecast_endpoint(client, dataset_document):
    response = client.post(
        f"/api/v1/ml/{DATASET_ID}/forecast",
        params={"periods": 3},
    )
    body = response.json()

    assert response.status_code == 200
    assert body["success"] is True
    assert body["columns"]["date_column"] == "OrderDate"
    assert body["columns"]["sales_column"] == "Sales"
    assert len(body["data"]["forecasts"]) == 3
    assert body["data"]["evaluation"]["status"] == "evaluated"
    assert body["figure"]["data"]


def test_forecast_endpoint_unknown_dataset(client, dataset_document):
    response = client.post(f"/api/v1/ml/{ObjectId()}/forecast")

    assert response.status_code == 404


def test_forecast_endpoint_validates_periods(client, dataset_document):
    response = client.post(
        f"/api/v1/ml/{DATASET_ID}/forecast",
        params={"periods": 99},
    )

    assert response.status_code == 422


def test_forecast_endpoint_unknown_column(client, dataset_document):
    response = client.post(
        f"/api/v1/ml/{DATASET_ID}/forecast",
        params={"sales_column": "Nope"},
    )

    assert response.status_code == 400
    assert "Nope" in response.json()["detail"]


def test_dataset_upload_validates_file(client):
    response = client.post(
        "/api/v1/datasets/upload",
        files={"file": ("notes.txt", b"hello", "text/plain")},
    )

    assert response.status_code == 400
    assert "CSV and XLSX" in response.json()["detail"]


def test_dataset_list_returns_schema(client, monkeypatch):
    monkeypatch.setattr(
        datasets_api,
        "list_datasets",
        lambda: [{
            "id": DATASET_ID,
            "name": "sample_sales.csv",
            "file_type": ".csv",
            "file_size_bytes": 100,
            "row_count": 10,
            "column_count": 2,
            "columns": ["a", "b"],
            "created_at": "2026-01-01T00:00:00+00:00",
        }],
    )

    response = client.get("/api/v1/datasets/")
    body = response.json()

    assert response.status_code == 200
    assert body["datasets"][0]["id"] == DATASET_ID
    assert body["datasets"][0]["columns"] == ["a", "b"]
