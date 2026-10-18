
import re
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pandas as pd
from bson import ObjectId

from app.analytics.columns import detect_columns
from app.core.config import settings
from app.db.connection import get_database
from app.ingestion.csv_reader import read_csv_file
from app.ingestion.excel_reader import read_excel_file
from app.ingestion.validator import validate_file


def json_safe(value):
    if value is None:
        return None

    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass

    if hasattr(value, "isoformat"):
        return value.isoformat()

    if hasattr(value, "item"):
        value = value.item()

    if isinstance(value, (str, int, float, bool)):
        return value

    return str(value)


def dataframe_preview(df: pd.DataFrame, limit: int = 10):
    columns = [str(column) for column in df.columns]

    rows = []
    for record in df.head(limit).to_dict(orient="records"):
        rows.append({
            str(key): json_safe(value)
            for key, value in record.items()
        })

    return {"columns": columns, "rows": rows}


def profile_dataframe(df: pd.DataFrame):
    return {
        "row_count": int(len(df)),
        "column_count": int(len(df.columns)),
        "columns": [
            {
                "name": str(column),
                "dtype": str(df[column].dtype),
                "missing_values": int(df[column].isna().sum()),
                "missing_percentage": round(
                    float(df[column].isna().mean() * 100), 2
                ),
                "unique_values": int(df[column].nunique()),
            }
            for column in df.columns
        ],
        "duplicate_rows": int(df.duplicated().sum()),
    }


def get_dataset_collection():
    return get_database()["datasets"]


def get_dataset_dataframe(document):
    file_path = Path(document["file_path"])

    if not file_path.is_file():
        raise FileNotFoundError("Dataset file is no longer available.")

    content = file_path.read_bytes()

    if document["file_type"] == ".csv":
        return read_csv_file(content)

    return read_excel_file(content)


def upload_dataset(filename: str, content: bytes):
    extension = validate_file(
        filename,
        content,
        settings.MAX_UPLOAD_SIZE_MB,
    )

    if "\x00" in filename or "/" in filename or "\\" in filename:
        raise ValueError("Invalid filename.")

    if extension == ".csv":
        df = read_csv_file(content)
    else:
        df = read_excel_file(content)

    if len(df.columns) > 500:
        raise ValueError("The file contains too many columns.")

    if len(df) > 1_000_000:
        raise ValueError("The file contains too many rows.")

    columns = [str(column) for column in df.columns]

    if any(not name.strip() for name in columns):
        raise ValueError("Column names must not be empty.")

    if len(set(columns)) != len(columns):
        raise ValueError(
            "Duplicate column names detected. Please rename them."
        )

    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)

    stored_name = f"{uuid4().hex}{extension}"
    file_path = upload_dir / stored_name

    try:
        file_path.write_bytes(content)

        document = {
            "name": Path(filename).name,
            "stored_name": stored_name,
            "file_path": str(file_path.resolve()),
            "file_type": extension,
            "file_size_bytes": len(content),
            "row_count": int(len(df)),
            "column_count": int(len(df.columns)),
            "columns": columns,
            "preview": dataframe_preview(df),
            "profile": profile_dataframe(df),
            "created_at": datetime.now(timezone.utc),
        }

        result = get_dataset_collection().insert_one(document)
        document["_id"] = result.inserted_id

        return serialize_dataset(document)

    except Exception:
        file_path.unlink(missing_ok=True)
        raise


def serialize_dataset(document):
    return {
        "id": str(document["_id"]),
        "name": document["name"],
        "file_type": document["file_type"],
        "file_size_bytes": document["file_size_bytes"],
        "row_count": document["row_count"],
        "column_count": document["column_count"],
        "columns": document["columns"],
        "created_at": document["created_at"].isoformat(),
    }


def list_datasets():
    collection = get_dataset_collection()

    return [
        serialize_dataset(document)
        for document in collection.find().sort("created_at", -1).limit(100)
    ]


def get_dataset(dataset_id: str):
    if not ObjectId.is_valid(dataset_id):
        return None

    document = get_dataset_collection().find_one(
        {"_id": ObjectId(dataset_id)}
    )

    return document


def dataset_file_signature(document) -> tuple:
    """Cheap signature used to invalidate cached results when a file changes."""
    try:
        stat = Path(document["file_path"]).stat()
        return (
            int(document.get("row_count", 0)),
            int(stat.st_size),
            int(stat.st_mtime_ns),
        )
    except (KeyError, OSError):
        return (int(document.get("row_count", 0)), 0, 0)


def get_dataset_details(dataset_id: str):
    """Dataset metadata plus detected column roles and stored profile."""
    document = get_dataset(dataset_id)

    if document is None:
        return None

    df = get_dataset_dataframe(document)
    detected = detect_columns(df)

    return {
        **serialize_dataset(document),
        "detected_columns": detected,
        "filters": {
            "date": detected.get("date") is not None,
            "category": detected.get("category") is not None,
            "region": detected.get("region") is not None,
        },
        "profile": document.get("profile") or profile_dataframe(df),
    }


def load_sample_dataset():
    """Ingest the bundled sample CSV, reusing an identical existing copy."""
    sample_path = Path(settings.SAMPLE_DATASET_PATH)

    if not sample_path.is_file():
        raise FileNotFoundError(
            "The bundled sample dataset could not be found on the server."
        )

    content = sample_path.read_bytes()
    df = read_csv_file(content)

    try:
        existing = get_dataset_collection().find_one(
            {"name": sample_path.name}
        )
    except Exception:
        existing = None

    if (
        existing is not None
        and existing.get("row_count") == len(df)
        and Path(existing.get("file_path", "")).is_file()
    ):
        return serialize_dataset(existing)

    return upload_dataset(sample_path.name, content)


def get_dataset_preview(dataset_id: str, limit: int = 10):
    document = get_dataset(dataset_id)

    if document is None:
        return None

    df = get_dataset_dataframe(document)

    return {
        "dataset_id": dataset_id,
        "name": document["name"],
        **dataframe_preview(df, limit),
    }


def get_dataset_profile(dataset_id: str):
    document = get_dataset(dataset_id)

    if document is None:
        return None

    df = get_dataset_dataframe(document)

    return {
        "dataset_id": dataset_id,
        "name": document["name"],
        **profile_dataframe(df),
    }
