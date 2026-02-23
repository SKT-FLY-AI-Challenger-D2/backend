import pytest
from app.features.complaint.complaint_repository import ComplaintRepository
from app.features.video.video_repository import VideoRepository
from app.features.complaint.complaint_model import Complaint
from app.features.video.video_model import Video

# [테스트 목적] ComplaintRepository의 Complaint CRUD + video별 조회 검증
# [테스트 방식] 인메모리 SQLite DB + Repository 메서드 호출
# [테스트 동작]
#   1. VideoRepository.create_video (선행조건)
#   2. create_complaint로 신고 생성
#   3. get_complaints_by_video → 1건, complaint_content 일치 assert
#   4. update_complaint (complaint_content 변경) → get_complaint → 변경 확인 assert
#   5. delete_complaint → get_complaint → None assert
# [Input] Video("v_bad") → Complaint(complaint_id="c1", complaint_content="사기 영상입니다.")
# [Output] video별 조회 1건, Update 후 content 변경, 삭제 후 None
def test_complaint_crud(db_session):
    comp_repo = ComplaintRepository(db_session)
    video_repo = VideoRepository(db_session)

    # 비디오 준비
    video = Video(video_id="v_bad", video_title="나쁜영상", status="HARMFUL")
    video_repo.create_video(video)

    # 1. Create
    complaint = Complaint(
        complaint_id="c1",
        video_id="v_bad",
        complaint_content="사기 영상입니다.",
        complaint_target="Platform"
    )
    comp_repo.create_complaint(complaint)

    # 2. Read (Get by Video)
    complaints = comp_repo.get_complaints_by_video("v_bad")
    assert len(complaints) == 1
    assert complaints[0].complaint_content == "사기 영상입니다."

    # 3. Update
    complaint.complaint_content = "수정된 신고 내용"
    comp_repo.update_complaint(complaint)
    updated = comp_repo.get_complaint("c1")
    assert updated.complaint_content == "수정된 신고 내용"

    # 4. Delete
    comp_repo.delete_complaint("c1")
    assert comp_repo.get_complaint("c1") is None