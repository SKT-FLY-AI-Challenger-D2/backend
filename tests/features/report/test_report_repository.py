import pytest
from app.features.report.report_repository import ReportRepository
from app.features.video.video_repository import VideoRepository
from app.features.report.report_model import AIReport, ReportEvidence
from app.features.video.video_model import Video

# [테스트 목적] ReportRepository의 AIReport CRUD 동작 검증 (새 스키마)
# [테스트 방식] 인메모리 SQLite DB + Repository 메서드 호출
# [테스트 동작]
#   1. VideoRepository.create_video로 Video 생성 (FK 선행조건)
#   2. ReportRepository.create_report로 AIReport 생성 (점수 컬럼 포함)
#   3. get_report_by_video_id로 조회 → 필드 값 일치 assert
#   4. update_report (analysis_result 변경) → 조회 → 변경 확인 assert
#   5. delete_report → get_report_by_id → None assert
# [Input] Video(video_id="v_rep") → AIReport(report_id="r1", final_score=0.9, analysis_result="분석 완료")
# [Output] 조회 시 값 일치, Update 후 변경 확인, 삭제 후 None
def test_report_lifecycle(db_session):
    report_repo = ReportRepository(db_session)
    video_repo = VideoRepository(db_session)

    video = Video(video_id="v_rep", video_title="분석대상", status="PENDING")
    video_repo.create_video(video)

    # 1. Create
    report = AIReport(
        report_id="r1",
        video_id="v_rep",
        final_score=0.9,
        fact_score=0.5,
        deepfake_score=0.2,
        legal_issue_score=0.7,
        analysis_result="분석 완료"
    )
    report_repo.create_report(report)

    # 2. Read
    fetched = report_repo.get_report_by_video_id("v_rep")
    assert fetched is not None
    assert float(fetched.final_score) == 0.9
    assert fetched.analysis_result == "분석 완료"

    # 3. Update
    fetched.analysis_result = "수정된 분석"
    report_repo.update_report(fetched)
    updated = report_repo.get_report_by_id("r1")
    assert updated.analysis_result == "수정된 분석"

    # 4. Delete
    report_repo.delete_report("r1")
    assert report_repo.get_report_by_id("r1") is None


# [테스트 목적] ReportRepository의 Evidence CRUD 동작 검증
# [테스트 방식] 인메모리 SQLite DB + Repository 메서드 호출
# [테스트 동작]
#   1. VideoRepository.create_video → ReportRepository.create_report (선행조건)
#   2. add_evidence로 Evidence 1건 추가
#   3. get_evidence_by_id로 단건 조회 → evidence_id 일치 assert
#   4. get_evidence_by_report로 리포트별 조회 → 1건, category 일치 assert
#   5. update_evidence (content 변경) → get_evidence_by_id → 변경 확인 assert
#   6. delete_evidence → get_evidence_by_report → 0건 assert
# [Input] Video → AIReport(report_id="r_ev") → ReportEvidence(evidence_id="ev1", category="LEGAL")
# [Output] 단건 조회 성공, 리포트별 1건, Update 후 content 변경 확인, 삭제 후 0건
def test_evidence_lifecycle(db_session):
    report_repo = ReportRepository(db_session)
    video_repo = VideoRepository(db_session)

    video = Video(video_id="v_ev", video_title="근거테스트", status="PENDING")
    video_repo.create_video(video)

    report = AIReport(report_id="r_ev", video_id="v_ev", final_score=0.6)
    report_repo.create_report(report)

    # 1. Create
    evidence = ReportEvidence(evidence_id="ev1", report_id="r_ev", category="LEGAL", content="법적 문제 발견")
    report_repo.add_evidence(evidence)

    # 2. Read (단건)
    fetched = report_repo.get_evidence_by_id("ev1")
    assert fetched is not None
    assert fetched.evidence_id == "ev1"

    # 3. Read (리포트별)
    results = report_repo.get_evidence_by_report("r_ev")
    assert len(results) == 1
    assert results[0].category == "LEGAL"

    # 4. Update
    fetched.content = "수정된 법적 문제"
    report_repo.update_evidence(fetched)
    updated = report_repo.get_evidence_by_id("ev1")
    assert updated.content == "수정된 법적 문제"

    # 5. Delete
    report_repo.delete_evidence("ev1")
    assert len(report_repo.get_evidence_by_report("r_ev")) == 0
