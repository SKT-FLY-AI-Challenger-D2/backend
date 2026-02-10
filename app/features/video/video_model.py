from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, CheckConstraint, Index
from sqlalchemy.sql import func
from app.core.database import Base

class Video(Base):
    __tablename__ = "videos"

    video_id = Column(String(255), primary_key=True)
    video_title = Column(String(255))
    channel = Column(String(255))
    upload_date = Column(DateTime)
    video_script = Column(Text)
    video_runtime = Column(Integer)
    thumbnail = Column(String(500))
    youtube_url = Column(String(500))
    saved_url = Column(String(500))
    status = Column(String(20), default='PENDING')

    # Constraint: CHECK status
    __table_args__ = (
        CheckConstraint("status IN ('SAFE', 'HARMFUL', 'PENDING')", name="chk_video_status"),
    )

class WatchHistory(Base):
    __tablename__ = "watch_history"

    history_id = Column(String(255), primary_key=True)
    user_id = Column(String(255), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    video_id = Column(String(255), ForeignKey("videos.video_id", ondelete="CASCADE"), nullable=False)
    watched_at = Column(DateTime, default=func.now())

    # Manual Indexes
    __table_args__ = (
        Index("idx_watch_user", "user_id"),
        Index("idx_watch_video", "video_id"),
        Index("idx_watch_time", "watched_at"),
    )