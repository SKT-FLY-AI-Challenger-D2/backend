# tests/features/report/test_report_model.py
from app.features.report.report_model import AIReport
from app.features.video.video_model import Video

def test_report_flow(db_session):
    # 비디오 먼저 생성
    video = Video(video_id="v_rep", video_title="분석할 영상", status="PENDING")
    db_session.add(video)
    db_session.commit()

    # [Step 1] 리포트 생성 (INSERT)
    report = AIReport(
        report_id="r_1",
        video_id="v_rep", # FK & Unique
        summary="이 영상은 안전합니다.",
        fact_report="사실 관계 확인됨"
    )
    db_session.add(report)
    
    # [Step 2] COMMIT
    db_session.commit()

    # [Step 3] SELECT
    saved_report = db_session.query(AIReport).filter_by(report_id="r_1").first()
    assert saved_report.video_id == "v_rep"
    assert saved_report.summary == "이 영상은 안전합니다."

    # [Step 4] DELETE
    db_session.delete(saved_report)
    db_session.commit()