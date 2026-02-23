from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.core.database import Base

class Complaint(Base):
    __tablename__ = "complaints"

    complaint_id = Column(String(255), primary_key=True)
    video_id = Column(String(255), ForeignKey("videos.video_id", ondelete="SET NULL"), nullable=True)
    report_id = Column(String(255), ForeignKey("ai_reports.report_id", ondelete="SET NULL"), nullable=True)
    
    complaint_date = Column(DateTime, default=func.now())
    complaint_content = Column(Text)
    complaint_target = Column(String(255))