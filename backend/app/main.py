from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.analytics import router as analytics_router
from app.api.v1.charts import router as charts_router
from app.api.v1.datasets import router as datasets_router
from app.api.v1.ml import router as ml_router
from app.core.config import settings
from app.db.connection import check_database_connection

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="ML-powered Business Intelligence API"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

for router in (
    datasets_router,
    analytics_router,
    charts_router,
    ml_router,
):
    app.include_router(router, prefix=settings.API_V1_PREFIX)


@app.get("/")
def root():
    return {
        "message": "ML BI Platform Backend",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health/database")
def database_health():
    try:
        check_database_connection()
        return {"database": "connected", "type": "MongoDB"}

    except Exception:
        raise HTTPException(
            status_code=503,
            detail="MongoDB connection failed. Check MONGODB_URL, credentials, network access and Atlas IP allowlist."
        )
