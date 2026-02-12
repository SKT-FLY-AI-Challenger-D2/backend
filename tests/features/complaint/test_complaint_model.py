# tests/features/complaint/test_complaint_model.py
from app.features.complaint.complaint_model import Complaint
from app.features.video.video_model import Video

def test_complaint_flow(db_session):
    # 비디오 생성
    video = Video(video_id="v_comp", video_title="나쁜 영상", status="HARMFUL")
    db_session.add(video)
    db_session.commit()

    # [Step 1] 신고 생성 (INSERT)
    # report_id는 NULL 허용이므로 없이 생성해봄
    complaint = Complaint(
        complaint_id="c_1",
        video_id="v_comp",
        complaint_content="이 영상 사기 같아요!",
        complaint_target="경찰청"
    )
    db_session.add(complaint)
    
    # [Step 2] COMMIT
    db_session.commit()

    # [Step 3] SELECT
    saved_complaint = db_session.query(Complaint).first()
    assert saved_complaint.video_id == "v_comp"
    assert saved_complaint.report_id is None  # 리포트 없이도 신고 가능 확인

    # [Step 4] DELETE
    db_session.delete(saved_complaint)
    db_session.commit()