from typing import Optional
from pydantic import BaseModel, ConfigDict

class SearchRequest(BaseModel):
    """
    프론트엔드가 백엔드로 전달하는 영상 검색 요청 스키마
    """
    title: str                              # 영상 제목
    channel: str                            # 채널명
    # runtime: Optional[str] = None         # [TODO] runtime 추가 예정

    model_config = ConfigDict(
        extra='forbid' # 추가로 들어오는 필드 금지(추가 시 422 error)
    )

class SearchResponse(BaseModel):
    """
    영상 검색 및 분석 결과 응답 스키마
    """
    video_id: Optional[str] = None          # 추출한 영상 ID
    youtube_url: Optional[str] = None       # 유튜브 URL
    title: Optional[str] = None             # 영상 제목
    channel_title: Optional[str] = None     # 채널명
    found: bool                             # 영상 검색 결과 성공 여부
    message: Optional[str] = None           # 메시지
    analysis_result: Optional[str] = None   # AI 분석 결과
    error: Optional[str] = None             # 처리 중 에러 메시지