"""
Creative Admin Router - управление креативами и доступ к видео.

Endpoints:
- POST /force-analyze - принудительный анализ креатива
- GET /video-access/{creative_id} - получить presigned URL для видео (с JWT)
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import uuid

from database.base import get_db
from database.models import Creative
from utils.analysis_orchestrator import force_analyze
from utils.storage import get_storage
from utils.logger import setup_logger

# JWT authentication (будет реализован позже)
from api.dependencies import get_current_user

logger = setup_logger(__name__)
router = APIRouter(prefix="/api/v1/creatives", tags=["Creative Admin"])


# ========== SCHEMAS ==========

class ForceAnalyzeRequest(BaseModel):
    """Request for force analyze."""
    creative_id: str


class VideoAccessResponse(BaseModel):
    """Response with video access URL."""
    creative_id: str
    creative_name: str
    video_url: str
    is_public: bool
    expires_in: Optional[int] = None  # Seconds (only for private videos)


class GetUploadUrlRequest(BaseModel):
    """Request for presigned upload URL."""
    filename: str  # Original filename (e.g., "my-video.mp4")


class UploadUrlResponse(BaseModel):
    """Response with presigned upload URL."""
    upload_url: str  # PUT request here with video file
    file_key: str  # Internal file key
    internal_key: str  # Save this in DB (e.g., r2://client-assets/videos/...)
    expires_in: int  # Seconds
    bucket: str  # client-assets


class GetDownloadUrlRequest(BaseModel):
    """Request for presigned download URL."""
    internal_key: str  # e.g., r2://client-assets/videos/client_uuid/file.mp4


class DownloadUrlResponse(BaseModel):
    """Response with presigned download URL."""
    download_url: str  # Use in <video> tag
    expires_in: int  # Seconds


# ========== ENDPOINTS ==========

@router.post("/force-analyze")
async def api_force_analyze(
    request: ForceAnalyzeRequest,
    db: Session = Depends(get_db),
    # current_user = Depends(get_current_user)  # Uncomment for JWT auth
):
    """
    🚀 FORCE Claude Vision analysis (admin only).

    Bypasses all triggers (5 conversions, is_benchmark).
    Useful for:
    - Re-analyzing creatives after manual tagging
    - Immediate benchmark analysis
    - Testing/debugging

    Example:
    ```json
    {
      "creative_id": "uuid-123"
    }
    ```

    Returns:
    ```json
    {
      "success": true,
      "creative_id": "uuid-123",
      "message": "Force analysis triggered...",
      "analysis_status": "processing"
    }
    ```
    """
    try:
        creative_id = uuid.UUID(request.creative_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid creative_id format")

    result = force_analyze(creative_id, db)

    if not result.get("success"):
        raise HTTPException(
            status_code=400,
            detail=result.get("error", "Analysis failed")
        )

    return result


@router.get("/video-access/{creative_id}", response_model=VideoAccessResponse)
async def get_video_access(
    creative_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[dict] = Depends(get_current_user)
):
    """
    🔐 Get video access URL with JWT authentication.

    Security logic:
    - Public benchmarks (is_public=True): accessible to all authenticated users
    - Client videos (is_public=False): accessible ONLY to owner (user_id match)

    Returns:
    - For public benchmarks: direct public URL
    - For client videos: presigned URL (expires in 1 hour)

    Example:
    ```
    GET /api/v1/creatives/video-access/uuid-123
    Authorization: Bearer <jwt_token>
    ```

    Returns:
    ```json
    {
      "creative_id": "uuid-123",
      "creative_name": "My Creative",
      "video_url": "https://...",
      "is_public": false,
      "expires_in": 3600
    }
    ```
    """
    try:
        creative_id_uuid = uuid.UUID(creative_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid creative_id format")

    # Get creative
    creative = db.query(Creative).filter(Creative.id == creative_id_uuid).first()

    if not creative:
        raise HTTPException(status_code=404, detail="Creative not found")

    # Security check
    if not creative.is_public:
        # Client video - check ownership
        if not current_user:
            raise HTTPException(status_code=401, detail="Authentication required")

        # Check if user owns this creative
        user_id = current_user.get("id")
        if str(creative.user_id) != str(user_id):
            raise HTTPException(
                status_code=403,
                detail="Access denied. This video belongs to another user."
            )

    # Get video URL
    storage = get_storage()
    video_url = creative.video_url

    # If it's a private R2 video (starts with r2://), generate presigned URL
    if video_url.startswith("r2://"):
        presigned_url = storage.generate_client_video_access_url(
            video_url,
            expiration=3600  # 1 hour
        )

        logger.info(f"🔐 Generated presigned URL for {current_user.get('email') if current_user else 'anonymous'}")

        return VideoAccessResponse(
            creative_id=str(creative.id),
            creative_name=creative.name,
            video_url=presigned_url,
            is_public=creative.is_public,
            expires_in=3600
        )
    else:
        # Public URL or local file
        return VideoAccessResponse(
            creative_id=str(creative.id),
            creative_name=creative.name,
            video_url=video_url,
            is_public=creative.is_public,
            expires_in=None
        )


@router.get("/benchmarks")
async def list_public_benchmarks(
    product_category: Optional[str] = None,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """
    📚 List public benchmark videos (accessible to all users).

    These are market winners from FB Ad Library, TikTok, etc.

    Query params:
    - product_category: Filter by category (optional)
    - limit: Max results (default 20)

    Returns:
    ```json
    {
      "benchmarks": [
        {
          "id": "uuid",
          "name": "FB Winner: Too Busy to Learn?",
          "product_category": "language_learning",
          "video_url": "https://...",
          "hook_type": "problem_agitation",
          "emotion": "frustration",
          "market_cvr": 0.05,
          "market_longevity_days": 30
        }
      ]
    }
    ```
    """
    query = db.query(Creative).filter(
        Creative.is_public == True,
        Creative.is_benchmark == True
    )

    if product_category:
        query = query.filter(Creative.product_category == product_category)

    benchmarks = query.order_by(Creative.predicted_cvr.desc()).limit(limit).all()

    return {
        "benchmarks": [
            {
                "id": str(b.id),
                "name": b.name,
                "product_category": b.product_category,
                "video_url": b.video_url,  # Public URL
                "hook_type": b.hook_type,
                "emotion": b.emotion,
                "pacing": b.pacing,
                "target_audience_pain": b.target_audience_pain,
                "market_cvr": (b.predicted_cvr or 0) / 10000,
                "market_longevity_days": b.features.get("market_longevity_days") if b.features else None,
                "analysis_status": b.analysis_status,
                "deeply_analyzed": b.deeply_analyzed
            }
            for b in benchmarks
        ],
        "count": len(benchmarks)
    }


@router.post("/get-upload-url", response_model=UploadUrlResponse)
async def get_upload_url(
    request: GetUploadUrlRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    🚀 Get presigned PUT URL for direct video upload to R2.

    **Architecture: Direct Upload**
    - Frontend uploads video DIRECTLY to Cloudflare R2
    - Bypasses backend server (saves bandwidth & processing time)
    - Supports files up to 500MB

    **Frontend Flow:**
    ```javascript
    // 1. Get upload URL
    const { upload_url, internal_key } = await fetch('/api/v1/creatives/get-upload-url', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: JSON.stringify({ filename: 'my-video.mp4' })
    }).then(r => r.json());

    // 2. Upload video directly to R2
    await fetch(upload_url, {
        method: 'PUT',
        body: videoFile,
        headers: { 'Content-Type': 'video/mp4' }
    });

    // 3. Save internal_key to backend
    await fetch('/api/v1/creatives', {
        method: 'POST',
        body: JSON.stringify({
            name: 'My Creative',
            video_url: internal_key  // r2://client-assets/videos/...
        })
    });
    ```

    Request:
    ```json
    {
      "filename": "my-awesome-video.mp4"
    }
    ```

    Response:
    ```json
    {
      "upload_url": "https://r2.cloudflarestorage.com/...",
      "file_key": "videos/client_uuid/abc123.mp4",
      "internal_key": "r2://client-assets/videos/client_uuid/abc123.mp4",
      "expires_in": 3600,
      "bucket": "client-assets"
    }
    ```

    Notes:
    - URL expires in 1 hour
    - Video namespace: client_{user_id}/
    - Save `internal_key` in Creative.video_url field
    """
    user_id = current_user.get("id")
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID not found in token")

    storage = get_storage()

    try:
        upload_data = storage.get_upload_url(
            user_id=str(user_id),
            filename=request.filename,
            expiration=3600  # 1 hour
        )

        logger.info(f"✅ Generated upload URL for user {current_user.get('email')}: {request.filename}")

        return UploadUrlResponse(**upload_data)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Upload URL generation failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate upload URL")


@router.post("/get-download-url", response_model=DownloadUrlResponse)
async def get_download_url(
    request: GetDownloadUrlRequest,
    current_user: Optional[dict] = Depends(get_current_user)
):
    """
    📥 Get presigned GET URL for video playback.

    **Used by frontend video player:**
    ```javascript
    const { download_url } = await fetch('/api/v1/creatives/get-download-url', {
        method: 'POST',
        body: JSON.stringify({
            internal_key: creative.video_url  // r2://client-assets/...
        })
    }).then(r => r.json());

    // Use in video player
    <video src={download_url} controls />
    ```

    Request:
    ```json
    {
      "internal_key": "r2://client-assets/videos/client_uuid/abc123.mp4"
    }
    ```

    Response:
    ```json
    {
      "download_url": "https://r2.cloudflarestorage.com/...",
      "expires_in": 3600
    }
    ```

    Notes:
    - URL expires in 1 hour
    - Public benchmarks return direct URL (no expiration)
    - Private client videos require authentication
    """
    storage = get_storage()

    try:
        # Get download URL
        download_url = storage.get_download_url(
            internal_key=request.internal_key,
            expiration=3600  # 1 hour
        )

        logger.info(f"✅ Generated download URL for user {current_user.get('email') if current_user else 'anonymous'}")

        return DownloadUrlResponse(
            download_url=download_url,
            expires_in=3600
        )

    except Exception as e:
        logger.error(f"Download URL generation failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate download URL")
