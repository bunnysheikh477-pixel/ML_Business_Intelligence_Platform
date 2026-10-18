
import os
from dotenv import load_dotenv

load_dotenv()


def _float_env(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default


class Settings:
    APP_NAME = "ML Business Intelligence Platform"
    API_V1_PREFIX = "/api/v1"

    MONGODB_URL = os.getenv("MONGODB_URL", "")
    MONGODB_DATABASE = os.getenv(
        "MONGODB_DATABASE",
        "ml_bi_platform"
    )

    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

    UPLOAD_DIR = os.getenv(
        "UPLOAD_DIR",
        "storage/uploads"
    )

    MAX_UPLOAD_SIZE_MB = int(
        os.getenv("MAX_UPLOAD_SIZE_MB", "20")
    )

    # Comma-separated list of allowed browser origins.
    CORS_ORIGINS = [
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS",
            "http://localhost:3000,http://127.0.0.1:3000",
        ).split(",")
        if origin.strip()
    ]

    # Seconds a generated chart payload is reused for an unchanged dataset.
    CHART_CACHE_TTL_SECONDS = _float_env("CHART_CACHE_TTL_SECONDS", 60.0)

    # Path of the bundled sample dataset used by POST /datasets/sample.
    SAMPLE_DATASET_PATH = os.getenv(
        "SAMPLE_DATASET_PATH",
        "sample_sales.csv",
    )


settings = Settings()
