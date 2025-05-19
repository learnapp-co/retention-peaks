from fastapi import APIRouter, HTTPException, Query
from ..models.heatmap import HeatmapResponse
from ..services.heatmap_extraction import HeatmapExtractionService
from datetime import datetime
from logging import getLogger

logger = getLogger(__name__)


router = APIRouter(prefix="/api", tags=["heatmap"])


def init_routes() -> APIRouter:
    global heatmap_service
    heatmap_service = HeatmapExtractionService()
    return router


@router.post(
    "/extract-peaks",
    response_model=HeatmapResponse,  # Changed from Dict[str, Any]
    summary="Extract Retention Peaks from a YouTube Video",
    description="Extracts heatmap retention peaks from a YouTube video and analyzes interesting sections.",
    responses={
        200: {"description": "Successful extraction with peaks"},
        400: {"description": "Failed to extract heatmap or no peaks found"},
        503: {"description": "Service not initialized"},
        500: {"description": "Internal server error"},
    },
)
async def extract_peaks(
    video_id: str = Query(..., description="YouTube video URL"),
) -> HeatmapResponse:
    if not heatmap_service:
        raise HTTPException(status_code=503, detail="Service not initialized")

    try:
        # Extract peaks and Base64-encoded cropped image
        peaks, base64_image = await heatmap_service.extract_peaks(video_id)

        if not peaks:
            raise HTTPException(status_code=400, detail="No peaks detected")

        # Return HeatmapResponse directly
        return HeatmapResponse(
            video_id=video_id,
            peaks=peaks,
            processed_at=datetime.utcnow(),
            cropped_image=base64_image,
        )

    except HTTPException as http_exc:
        logger.info("❌ Error in extract_peaks:%s", str(http_exc))
        raise
