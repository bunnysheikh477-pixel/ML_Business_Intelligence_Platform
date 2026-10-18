
from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from pymongo.errors import PyMongoError

from app.services.dataset_service import (
    get_dataset_details,
    get_dataset_preview,
    get_dataset_profile,
    list_datasets,
    load_sample_dataset,
    upload_dataset,
)

router = APIRouter(prefix="/datasets", tags=["Datasets"])


@router.post("/upload")
async def upload_dataset_endpoint(
    file: UploadFile = File(...)
):
    try:
        content = await file.read()

        return {
            "success": True,
            "dataset": upload_dataset(
                file.filename or "",
                content,
            ),
        }

    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    except PyMongoError:
        raise HTTPException(
            status_code=503,
            detail="Unable to save dataset metadata to MongoDB.",
        )

    finally:
        await file.close()


@router.post("/sample")
def load_sample_dataset_endpoint():
    """Load the bundled sample dataset so the app is usable immediately."""
    try:
        return {
            "success": True,
            "dataset": load_sample_dataset(),
        }

    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    except PyMongoError:
        raise HTTPException(
            status_code=503,
            detail="Unable to save dataset metadata to MongoDB.",
        )


@router.get("/")
def list_datasets_endpoint():
    try:
        return {
            "success": True,
            "datasets": list_datasets(),
        }
    except PyMongoError:
        raise HTTPException(
            status_code=503,
            detail="Unable to retrieve datasets.",
        )


@router.get("/{dataset_id}")
def dataset_details_endpoint(dataset_id: str):
    try:
        result = get_dataset_details(dataset_id)

        if result is None:
            raise HTTPException(
                status_code=404,
                detail="Dataset not found. Check the dataset ID.",
            )

        return {"success": True, "dataset": result}

    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    except PyMongoError:
        raise HTTPException(
            status_code=503,
            detail="Database is unavailable.",
        )


@router.get("/{dataset_id}/preview")
def preview_dataset_endpoint(
    dataset_id: str,
    limit: int = Query(default=10, ge=1, le=100),
):
    try:
        result = get_dataset_preview(dataset_id, limit)

        if result is None:
            raise HTTPException(
                status_code=404,
                detail="Dataset not found.",
            )

        return {"success": True, "data": result}

    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    except PyMongoError:
        raise HTTPException(
            status_code=503,
            detail="Database is unavailable.",
        )


@router.get("/{dataset_id}/profile")
def profile_dataset_endpoint(dataset_id: str):
    try:
        result = get_dataset_profile(dataset_id)

        if result is None:
            raise HTTPException(
                status_code=404,
                detail="Dataset not found.",
            )

        return {"success": True, "profile": result}

    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    except PyMongoError:
        raise HTTPException(
            status_code=503,
            detail="Database is unavailable.",
        )
