from fastapi import APIRouter, HTTPException
from app.features.video.video_schema import SearchRequest, SearchResponse
from app.features.video.video_service import VideoService

router = APIRouter(prefix="/search", tags=["Video"])
video_service = VideoService()

@router.post("", response_model=SearchResponse)
def search_video_endpoint(request: SearchRequest):
    """
    [POST] /search
    제목과 채널명을 받아 유튜브 URL을 검색,
    해당 영상의 자막을 추출하여 사기 여부를 분석
    """
    try:
        return video_service.search_and_analyze_video(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))