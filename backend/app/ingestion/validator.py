
from pathlib import Path

ALLOWED_EXTENSIONS = {".csv", ".xlsx"}


def validate_file(filename: str, content: bytes, max_size_mb: int):
    extension = Path(filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise ValueError("Only CSV and XLSX files are supported.")

    if not content:
        raise ValueError("The uploaded file is empty.")

    max_size_bytes = max_size_mb * 1024 * 1024

    if len(content) > max_size_bytes:
        raise ValueError(
            f"File size exceeds the {max_size_mb} MB limit."
        )

    return extension
