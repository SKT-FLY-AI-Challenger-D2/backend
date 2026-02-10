# tests/features/video/test_video_model.py
from app.features.video.video_model import Video, WatchHistory
from app.features.user.user_model import User
from datetime import datetime

def test_video_flow(db_session):
    # [Step 1] INSERT
    video = Video(
        video_id="vid_123",
        video_title="재밌는 영상",
        channel="김유튜브",
        video_runtime=600,
        status="SAFE" # CHECK 제약조건 테스트
    )
    db_session.add(video)
    
    # [Step 2] COMMIT
    db_session.commit()

    # [Step 3] SELECT
    saved_video = db_session.query(Video).filter(Video.video_id == "vid_123").first()
    assert saved_video.video_title == "재밌는 영상"
    assert saved_video.status == "SAFE"

    # [Step 4] DELETE
    db_session.delete(saved_video)
    db_session.commit()
    assert db_session.query(Video).filter_by(video_id="vid_123").first() is None


def test_watch_history(db_session):
    # FK를 위해 유저와 비디오가 먼저 있어야 함
    user = User(user_id="u1", password="p", name="n", user_email="e@e.com")
    video = Video(video_id="v1", video_title="t", status="PENDING")
    db_session.add_all([user, video])
    db_session.commit()

    # 시청 기록 생성
    history = WatchHistory(
        history_id="h1",
        user_id="u1",
        video_id="v1"
    )
    db_session.add(history)
    db_session.commit()

    # 조회
    saved_history = db_session.query(WatchHistory).first()
    assert saved_history.user_id == "u1"
    assert saved_history.video_id == "v1"