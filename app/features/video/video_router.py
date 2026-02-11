from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db

from app.features.video.video_schema import SearchRequest, SearchResponse
from app.features.video.video_service import VideoService

router = APIRouter()
video_service = VideoService()

@router.get("/test")
def test_video():
    return {"message": "Video Router is working!"}

@router.post("/analysis", response_model=SearchResponse)
def search_video_endpoint(request: SearchRequest):
    """
    [POST] /search
    제목과 채널명을 받아 유튜브 URL을 검색 후 사기 여부를 분석
    """
    try:
        return video_service.search_and_analyze_video(request)
    except ValueError as e: # API 키 누락 등 문제
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"설정 에러: {str(e)}"
        )
    except Exception as e: # 기타 에러
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"서버 에러: {str(e)}")