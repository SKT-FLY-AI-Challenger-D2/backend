# tests/features/complaint/test_complaint_model.py
from app.features.complaint.complaint_model import Complaint
from app.features.video.video_model import Video

# [테스트 목적] Complaint 모델의 CRUD + report_id NULL 허용 검증
# [테스트 방식] 인메모리 SQLite DB에서 직접 ORM 조작
# [테스트 동작]
#   1. Video INSERT (FK 선행조건)
#   2. COMMIT
#   3. Complaint INSERT (report_id 없이 = NULL)
#   4. COMMIT
#   5. SELECT → video_id 일치 + report_id is None assert
#   6. UPDATE (complaint_content 변경) → COMMIT → SELECT → 변경 확인 assert
#   7. DELETE → COMMIT
# [Input] Video("v_comp") → Complaint(complaint_id="c_1", report_id=None)
# [Output] report_id=None 저장 확인, Update 후 content 변경, 삭제 완료
def test_complaint_flow(db_session):
    # 비디오 생성
    video = Video(video_id="v_comp", video_title="나쁜 영상", status="HARMFUL")
    db_session.add(video)
    db_session.commit()

    # 1. Create (INSERT) — report_id는 NULL 허용이므로 없이 생성
    complaint = Complaint(
        complaint_id="c_1",
        video_id="v_comp",
        complaint_content="이 영상 사기 같아요!",
        complaint_target="경찰청"
    )
    db_session.add(complaint)
    db_session.commit()

    # 2. Read (SELECT)
    saved_complaint = db_session.query(Complaint).first()
    assert saved_complaint.video_id == "v_comp"
    assert saved_complaint.report_id is None  # 리포트 없이도 신고 가능 확인

    # 3. Update
    saved_complaint.complaint_content = "수정된 신고 내용"
    db_session.commit()
    updated = db_session.query(Complaint).first()
    assert updated.complaint_content == "수정된 신고 내용"

    # 4. Delete
    db_session.delete(updated)
    db_session.commit()