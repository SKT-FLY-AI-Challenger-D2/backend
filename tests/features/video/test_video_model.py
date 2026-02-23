# tests/features/video/test_video_model.py
from app.features.video.video_model import Video, WatchHistory
from app.features.user.user_model import User
from datetime import datetime

# [테스트 목적] Video 모델의 기본 CRUD + CHECK 제약조건(status) 검증
# [테스트 방식] 인메모리 SQLite DB에서 직접 ORM 조작
# [테스트 동작]
#   1. Video INSERT (status="SAFE"로 CHECK 제약조건 테스트)
#   2. COMMIT
#   3. SELECT → video_title, status 일치 assert
#   4. UPDATE (status → "HARMFUL") → COMMIT → SELECT → 변경 확인 assert
#   5. DELETE → COMMIT → SELECT → None assert
# [Input] Video(video_id="vid_123", video_title="재밌는 영상", status="SAFE")
# [Output] 저장 후 값 일치, Update 후 status="HARMFUL" 확인, 삭제 후 None
def test_video_flow(db_session):
    # 1. Create (INSERT)
    video = Video(
        video_id="vid_123",
        video_title="재밌는 영상",
        channel="김유튜브",
        video_runtime=600,
        status="SAFE" # CHECK 제약조건 테스트
    )
    db_session.add(video)
    db_session.commit()

    # 2. Read (SELECT)
    saved_video = db_session.query(Video).filter(Video.video_id == "vid_123").first()
    assert saved_video.video_title == "재밌는 영상"
    assert saved_video.status == "SAFE"

    # 3. Update
    saved_video.status = "HARMFUL"
    db_session.commit()
    updated_video = db_session.query(Video).filter(Video.video_id == "vid_123").first()
    assert updated_video.status == "HARMFUL"

    # 4. Delete
    db_session.delete(updated_video)
    db_session.commit()
    assert db_session.query(Video).filter_by(video_id="vid_123").first() is None


# [테스트 목적] WatchHistory 모델의 FK 관계(User, Video) 및 저장 검증
# [테스트 방식] 인메모리 SQLite DB에서 직접 ORM 조작
# [테스트 동작]
#   1. User + Video INSERT (FK 선행조건)
#   2. COMMIT
#   3. WatchHistory INSERT (user_id FK, video_id FK)
#   4. COMMIT
#   5. SELECT → user_id, video_id 일치 assert
# [Input] User("u1") + Video("v1") → WatchHistory(history_id="h1")
# [Output] WatchHistory의 user_id="u1", video_id="v1" 일치
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