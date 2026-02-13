from typing import Optional, List
from pydantic import BaseModel, ConfigDict

class SearchRequest(BaseModel):
    """
    프론트엔드가 백엔드로 전달하는 영상 검색 요청 스키마
    """
    title: str                              # 영상 제목
    channel: str                            # 채널명
    duration: int                           # 동영상의 총재생시간(초), 일단 테스트용으로 주석처리 

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
    error: Optional[str] = None             # 처리 중 에러 메시지

    # 보고서 출력용
    final_score: Optional[float] = None     # 위험도 점수(0.00(안전)~1.00(위험))
    final_risk_level: Optional[int] = None  # 위험도: 0(낮음), 1(중간), 2(높음)
    danger_evidence: Optional[List[str]]    # 위험하다고 판단한 근거들
    analysis_report: str                    # 긴 글 형식의 최종 분석 내용

    short_report: str                       # 짧은 형식의 분석 요약(알림용)