import logging
import io
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from dependencies.auth import get_current_user
from models import User
from core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["upload"])

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_SIZE = 5 * 1024 * 1024  # 5MB


@router.post("/upload/image")
async def upload_image(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
):
    """Upload an image to Cloudinary and return its URL. Auth required."""
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {file.content_type}. Allowed: JPEG, PNG, WebP, GIF",
        )

    contents = await file.read()
    if len(contents) > MAX_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large ({len(contents)} bytes). Max: 5MB",
        )

    cfg = settings.cloudinary_config
    if not cfg:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Cloudinary not configured",
        )

    import cloudinary
    import cloudinary.uploader

    cloudinary.config(
        cloud_name=cfg["cloud_name"],
        api_key=cfg["api_key"],
        api_secret=cfg["api_secret"],
    )

    try:
        result = cloudinary.uploader.upload(
            io.BytesIO(contents),
            folder="ikobiz_products",
            public_id=None,
            overwrite=True,
        )
        url = result.get("secure_url") or result.get("url")
        logger.info(f"Uploaded image for user {user.id}: {url}")
        return {"url": url, "public_id": result.get("public_id")}
    except Exception as e:
        logger.error(f"Cloudinary upload failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Image upload failed",
        )
