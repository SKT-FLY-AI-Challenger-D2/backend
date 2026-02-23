from typing import Optional, List
from pydantic import BaseModel

class AnalysisRequest(BaseModel):
    """
    AI 분석 요청 스키마
    """
    youtube_url: str
    video_id: str

class AnalysisResult(BaseModel):
    """
    AI 분석 결과 스키마
    """

    final_score: Optional[float] = None
    final_risk_level: Optional[int] = None
    danger_evidence: Optional[List[str]] = []
    analysis_report: Optional[str] = None
    short_report: Optional[str] = None
    error: Optional[str] = None