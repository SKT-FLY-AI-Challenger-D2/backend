from sqlalchemy.orm import Session
from app.features.video.video_model import Video, WatchHistory
from typing import Optional, List

class VideoRepository:
    def __init__(self, db: Session):
        self.db = db

    # ==========================
    # 1. Video (영상)
    # ==========================
    def create_video(self, video: Video) -> Video:
        self.db.add(video)
        self.db.commit()
        self.db.refresh(video)
        return video

    def get_video(self, video_id: str) -> Optional[Video]:
        return self.db.query(Video).filter(Video.video_id == video_id).first()
    
    def get_videos_by_status(self, status: str, limit: int = 10) -> List[Video]:
        """AI 분석 대기중(PENDING)인 영상 등을 가져올 때 사용"""
        return self.db.query(Video).filter(Video.status == status).limit(limit).all()

    def update_video(self, video: Video) -> Video:
        self.db.add(video)
        self.db.commit()
        self.db.refresh(video)
        return video
    
    def delete_video(self, video_id: str) -> None:
        video = self.get_video(video_id)
        if video:
            self.db.delete(video)
            self.db.commit()

    # ==========================
    # 2. WatchHistory (시청 기록)
    # ==========================
    def add_watch_history(self, history: WatchHistory) -> WatchHistory:
        self.db.add(history)
        self.db.commit()
        self.db.refresh(history)
        return history

    def get_user_watch_history(self, user_id: str, limit: int = 50) -> List[WatchHistory]:
        """특정 유저의 시청 기록 조회 (최신순)"""
        return self.db.query(WatchHistory)\
            .filter(WatchHistory.user_id == user_id)\
            .order_by(WatchHistory.watched_at.desc())\
            .limit(limit).all()