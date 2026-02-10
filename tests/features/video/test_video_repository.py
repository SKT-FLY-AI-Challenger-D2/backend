import pytest
from app.features.video.video_repository import VideoRepository
from app.features.video.video_model import Video, WatchHistory
from app.features.user.user_repository import UserRepository
from app.features.user.user_model import User

def test_video_crud(db_session):
    repo = VideoRepository(db_session)

    # 1. Create
    video = Video(
        video_id="v1", 
        video_title="테스트영상", 
        status="PENDING", 
        video_runtime=100
    )
    repo.create_video(video)

    # 2. Read
    fetched = repo.get_video("v1")
    assert fetched.video_title == "테스트영상"

    # 3. Read by Status (AI 분석 대기열 확인용)
    pending_videos = repo.get_videos_by_status("PENDING")
    assert len(pending_videos) >= 1
    assert pending_videos[0].video_id == "v1"

    # 4. Update
    fetched.status = "SAFE"
    repo.update_video(fetched)
    assert repo.get_video("v1").status == "SAFE"

    # 5. Delete
    repo.delete_video("v1")
    assert repo.get_video("v1") is None

def test_watch_history(db_session):
    video_repo = VideoRepository(db_session)
    user_repo = UserRepository(db_session)

    # 사전 데이터 준비 (FK 제약조건 때문)
    user = User(user_id="u_watch", password="pw", name="시청자", user_email="w@w.com", sex="F")
    video = Video(video_id="v_watch", video_title="잼난거", status="SAFE")
    
    user_repo.create_user(user)
    video_repo.create_video(video)

    # 시청 기록 저장
    history = WatchHistory(history_id="h1", user_id="u_watch", video_id="v_watch")
    video_repo.add_watch_history(history)

    # 조회
    logs = video_repo.get_user_watch_history("u_watch")
    assert len(logs) == 1
    assert logs[0].video_id == "v_watch"