from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.core.database import Base

class AIReport(Base):
    __tablename__ = "ai_reports"

    report_id = Column(String(255), primary_key=True)
    # Unique Constraint for 1:1 relationship
    video_id = Column(String(255), ForeignKey("videos.video_id", ondelete="CASCADE"), unique=True, nullable=False)
    
    legal_report = Column(Text)
    fact_report = Column(Text)
    is_generated_by = Column(Text)
    summary = Column(Text)
    created_at = Column(DateTime, default=func.now())