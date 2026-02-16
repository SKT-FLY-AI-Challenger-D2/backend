import pytest
from app.features.video.video_repository import VideoRepository
from app.features.video.video_model import Video, WatchHistory
from app.features.user.user_repository import UserRepository
from app.features.user.user_model import User

# [테스트 목적] VideoRepository의 Video CRUD + status 필터 조회 검증
# [테스트 방식] 인메모리 SQLite DB + Repository 메서드 호출
# [테스트 동작]
#   1. create_video → 생성 확인
#   2. get_video → video_title 일치 assert
#   3. get_videos_by_status("PENDING") → 1건 이상, video_id 일치 assert
#   4. update_video (status → "SAFE") → 변경 확인
#   5. delete_video → get_video → None assert
# [Input] Video(video_id="v1", status="PENDING", video_runtime=100)
# [Output] CRUD 각 단계 정상, status 필터 조회 1건 이상, 삭제 후 None
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

# [테스트 목적] VideoRepository의 WatchHistory 저장 및 조회 검증
# [테스트 방식] 인메모리 SQLite DB + Repository 메서드 호출
# [테스트 동작]
#   1. UserRepository.create_user + VideoRepository.create_video (선행조건)
#   2. add_watch_history로 시청 기록 생성
#   3. get_user_watch_history → 1건, video_id 일치 assert
# [Input] User("u_watch") + Video("v_watch") → WatchHistory(history_id="h1")
# [Output] 시청 기록 1건 조회, video_id="v_watch" 일치
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