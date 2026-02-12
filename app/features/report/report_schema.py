from typing import Optional
from pydantic import BaseModel

class AnalysisRequest(BaseModel):
    """
    AI 분석 요청 스키마
    """
    youtube_url: str

class AnalysisResult(BaseModel):
    """
    AI 분석 결과 스키마
    """
    report: Optional[str] = None
    error: Optional[str] = None