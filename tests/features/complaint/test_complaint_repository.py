import pytest
from app.features.complaint.complaint_repository import ComplaintRepository
from app.features.video.video_repository import VideoRepository
from app.features.complaint.complaint_model import Complaint
from app.features.video.video_model import Video

def test_complaint_crud(db_session):
    comp_repo = ComplaintRepository(db_session)
    video_repo = VideoRepository(db_session)

    # 비디오 준비
    video = Video(video_id="v_bad", video_title="나쁜영상", status="HARMFUL")
    video_repo.create_video(video)

    # 1. Create Complaint
    complaint = Complaint(
        complaint_id="c1",
        video_id="v_bad",
        complaint_content="사기 영상입니다.",
        complaint_target="Platform"
    )
    comp_repo.create_complaint(complaint)

    # 2. Get by Video
    complaints = comp_repo.get_complaints_by_video("v_bad")
    assert len(complaints) == 1
    assert complaints[0].complaint_content == "사기 영상입니다."

    # 3. Delete
    comp_repo.delete_complaint("c1")
    assert comp_repo.get_complaint("c1") is None