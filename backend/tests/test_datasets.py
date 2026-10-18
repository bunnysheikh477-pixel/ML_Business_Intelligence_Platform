
import io
from pathlib import Path

import openpyxl
import pytest

from app.ingestion.csv_reader import read_csv_file
from app.ingestion.excel_reader import read_excel_file
from app.ingestion.validator import validate_file
from app.services import dataset_service


class FakeInsertResult:
    def __init__(self, inserted_id):
        self.inserted_id = inserted_id


class FakeCollection:
    def __init__(self, documents=None):
        self.documents = list(documents or [])
        self.inserted = []

    def insert_one(self, document):
        self.documents.append(document)
        self.inserted.append(document)
        return FakeInsertResult(len(self.documents))

    def find_one(self, query):
        for document in self.documents:
            if all(document.get(key) == value for key, value in query.items()
                   if key != "_id"):
                return document

        return None

    def find(self):
        return list(self.documents)


@pytest.fixture
def upload_environment(tmp_path, monkeypatch):
    collection = FakeCollection()

    monkeypatch.setattr(
        dataset_service, "get_dataset_collection", lambda: collection
    )
    monkeypatch.setattr(dataset_service.settings, "UPLOAD_DIR", str(tmp_path))

    return collection, tmp_path


def test_validate_file_rejects_unknown_extension():
    with pytest.raises(ValueError):
        validate_file("data.txt", b"a,b\n1,2\n", 20)


def test_validate_file_rejects_empty_content():
    with pytest.raises(ValueError):
        validate_file("data.csv", b"", 20)


def test_validate_file_rejects_too_large_content():
    with pytest.raises(ValueError):
        validate_file("data.csv", b"a" * (2 * 1024 * 1024), 1)


def test_validate_file_accepts_csv_and_xlsx():
    assert validate_file("DATA.CSV", b"a\n1\n", 5) == ".csv"
    assert validate_file("data.XLSX", b"a\n1\n", 5) == ".xlsx"


def test_read_csv_supports_bom_and_cp1252():
    utf8 = read_csv_file("amount\n10\n".encode("utf-8-sig"))
    cp1252 = read_csv_file("city\nZürich\n".encode("cp1252"))

    assert list(utf8.columns) == ["amount"]
    assert cp1252.iloc[0, 0] == "Zürich"


def test_read_csv_rejects_unreadable_payload():
    # 0x81/0x8d are undefined in cp1252 and invalid UTF-8.
    with pytest.raises(ValueError):
        read_csv_file(b"\x81\x8d\n")


def test_read_excel_round_trip():
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.append(["OrderDate", "Sales"])
    sheet.append(["2026-01-01", 100])

    buffer = io.BytesIO()
    workbook.save(buffer)

    frame = read_excel_file(buffer.getvalue())

    assert list(frame.columns) == ["OrderDate", "Sales"]
    assert frame.iloc[0]["Sales"] == 100


def test_upload_dataset_stores_file_and_metadata(upload_environment):
    collection, upload_dir = upload_environment
    content = b"OrderDate,Sales\n2026-01-01,100\n2026-02-01,200\n"

    result = dataset_service.upload_dataset("orders.csv", content)

    assert result["name"] == "orders.csv"
    assert result["file_type"] == ".csv"
    assert result["row_count"] == 2
    assert result["column_count"] == 2
    assert result["columns"] == ["OrderDate", "Sales"]
    assert result["id"] == "1"

    stored = Path(collection.inserted[0]["file_path"])
    assert stored.is_file()
    assert stored.parent == upload_dir
    assert stored.read_bytes() == content
    assert collection.inserted[0]["preview"]["rows"][0]["Sales"] == 100


def test_upload_dataset_rejects_bad_filenames(upload_environment):
    content = b"a\n1\n"

    with pytest.raises(ValueError):
        dataset_service.upload_dataset("bad/name.csv", content)

    with pytest.raises(ValueError):
        dataset_service.upload_dataset("bad\\name.csv", content)


def test_upload_dataset_rejects_duplicate_columns(
    upload_environment, monkeypatch
):
    import pandas as pd

    monkeypatch.setattr(
        dataset_service,
        "read_csv_file",
        lambda content: pd.DataFrame([[1, 2]], columns=["Sales", "Sales"]),
    )

    with pytest.raises(ValueError):
        dataset_service.upload_dataset("dup.csv", b"Sales,Sales\n1,2\n")


def test_upload_dataset_rejects_empty_column_names(
    upload_environment, monkeypatch
):
    import pandas as pd

    monkeypatch.setattr(
        dataset_service,
        "read_csv_file",
        lambda content: pd.DataFrame([[1]], columns=["  "]),
    )

    with pytest.raises(ValueError):
        dataset_service.upload_dataset("blank.csv", b" , \n1\n")


def test_upload_dataset_removes_file_when_metadata_fails(
    upload_environment, monkeypatch
):
    _, upload_dir = upload_environment

    def boom(document):
        raise RuntimeError("database down")

    monkeypatch.setattr(
        dataset_service, "get_dataset_collection", lambda: type(
            "C", (), {"insert_one": staticmethod(boom)}
        )()
    )

    with pytest.raises(RuntimeError):
        dataset_service.upload_dataset("orders.csv", b"a\n1\n")

    assert list(upload_dir.iterdir()) == []


def test_get_dataset_rejects_invalid_object_id(upload_environment):
    assert dataset_service.get_dataset("not-an-object-id") is None


def test_get_dataset_dataframe_reports_missing_file(upload_environment):
    with pytest.raises(FileNotFoundError):
        dataset_service.get_dataset_dataframe({
            "file_path": "does/not/exist.csv",
            "file_type": ".csv",
        })


def test_get_dataset_details_includes_detected_columns(
    upload_environment, monkeypatch
):
    collection, _ = upload_environment
    content = (
        b"OrderID,OrderDate,Product,Category,Region,Quantity,Sales,Profit\n"
        b"O1,2026-01-01,Widget,Hardware,North,2,100,25\n"
    )
    dataset_service.upload_dataset("orders.csv", content)
    document = collection.inserted[0]

    import bson

    document["_id"] = bson.ObjectId()

    monkeypatch.setattr(
        dataset_service, "get_dataset",
        lambda dataset_id: document,
    )

    details = dataset_service.get_dataset_details(str(document["_id"]))

    assert details["detected_columns"]["revenue"] == "Sales"
    assert details["detected_columns"]["date"] == "OrderDate"
    assert details["filters"] == {
        "date": True, "category": True, "region": True,
    }
    assert details["profile"]["row_count"] == 1


def test_load_sample_dataset_uses_bundled_file(
    upload_environment, monkeypatch, backend_root
):
    monkeypatch.setattr(
        dataset_service.settings,
        "SAMPLE_DATASET_PATH",
        str(backend_root / "sample_sales.csv"),
    )

    result = dataset_service.load_sample_dataset()

    assert result["name"] == "sample_sales.csv"
    assert result["row_count"] > 100
    assert "Sales" in result["columns"]


def test_load_sample_dataset_missing_file(upload_environment, monkeypatch, tmp_path):
    monkeypatch.setattr(
        dataset_service.settings,
        "SAMPLE_DATASET_PATH",
        str(tmp_path / "missing.csv"),
    )

    with pytest.raises(FileNotFoundError):
        dataset_service.load_sample_dataset()


def test_serialize_dataset_shape():
    from datetime import datetime, timezone

    document = {
        "_id": "abc",
        "name": "orders.csv",
        "file_type": ".csv",
        "file_size_bytes": 10,
        "row_count": 1,
        "column_count": 2,
        "columns": ["a", "b"],
        "created_at": datetime(2026, 1, 1, tzinfo=timezone.utc),
    }

    serialized = dataset_service.serialize_dataset(document)

    assert serialized["id"] == "abc"
    assert serialized["created_at"].startswith("2026-01-01")
