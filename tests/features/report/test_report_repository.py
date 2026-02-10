import pytest
from app.features.report.report_repository import ReportRepository
from app.features.video.video_repository import VideoRepository
from app.features.report.report_model import AIReport
from app.features.video.video_model import Video

def test_report_lifecycle(db_session):
    report_repo = ReportRepository(db_session)
    video_repo = VideoRepository(db_session)

    # 비디오가 먼저 있어야 리포트 생성 가능 (FK)
    video = Video(video_id="v_rep", video_title="분석대상", status="PENDING")
    video_repo.create_video(video)

    # 1. Create Report
    report = AIReport(
        report_id="r1",
        video_id="v_rep",
        summary="요약입니다",
        fact_report="사실입니다",
        is_generated_by="GPT-4"
    )
    report_repo.create_report(report)

    # 2. Get by Video ID (핵심 기능)
    fetched_report = report_repo.get_report_by_video_id("v_rep")
    assert fetched_report is not None
    assert fetched_report.summary == "요약입니다"

    # 3. Delete
    report_repo.delete_report("r1")
    assert report_repo.get_report_by_id("r1") is None