# tests/features/report/test_report_model.py
from app.features.report.report_model import AIReport, ReportEvidence
from app.features.video.video_model import Video

# [테스트 목적] AIReport 모델의 기본 CRUD 동작 검증 (새 스키마)
# [테스트 방식] 인메모리 SQLite DB에서 직접 ORM 조작
# [테스트 동작]
#   1. Video INSERT (FK 선행조건)
#   2. AIReport INSERT (점수 컬럼 + analysis_result 포함)
#   3. COMMIT
#   4. SELECT → 각 필드 값 일치 assert
#   5. UPDATE (analysis_result 변경) → COMMIT → SELECT → 변경 확인 assert
#   6. DELETE → COMMIT
# [Input] Video(video_id="v_rep"), AIReport(report_id="r_1", final_score=0.85, fact_score=0.3, deepfake_score=0.1, legal_issue_score=0.6)
# [Output] SELECT 시 값 일치, UPDATE 후 변경된 값 확인, DELETE 후 완료
def test_report_flow(db_session):
    # FK 선행조건
    video = Video(video_id="v_rep", video_title="분석할 영상", status="PENDING")
    db_session.add(video)
    db_session.commit()

    # 1. Create
    report = AIReport(
        report_id="r_1",
        video_id="v_rep",
        final_score=0.85,
        fact_score=0.3,
        deepfake_score=0.1,
        legal_issue_score=0.6,
        analysis_result="종합 분석 결과입니다."
    )
    db_session.add(report)
    db_session.commit()

    # 2. Read
    saved = db_session.query(AIReport).filter_by(report_id="r_1").first()
    assert saved.video_id == "v_rep"
    assert float(saved.final_score) == 0.85
    assert saved.analysis_result == "종합 분석 결과입니다."

    # 3. Update
    saved.analysis_result = "수정된 분석 결과"
    db_session.commit()
    updated = db_session.query(AIReport).filter_by(report_id="r_1").first()
    assert updated.analysis_result == "수정된 분석 결과"

    # 4. Delete
    db_session.delete(updated)
    db_session.commit()


# [테스트 목적] ReportEvidence 모델의 CRUD + AIReport와의 1:N 관계 + CASCADE 삭제 검증
# [테스트 방식] 인메모리 SQLite DB에서 직접 ORM 조작
# [테스트 동작]
#   1. Video INSERT (FK 선행조건)
#   2. AIReport INSERT
#   3. ReportEvidence 2건 INSERT (FACT, DEEPFAKE)
#   4. COMMIT
#   5. SELECT → 2건 assert
#   6. UPDATE (ev_1의 content 변경) → COMMIT → SELECT → 변경 확인 assert
#   7. AIReport DELETE → COMMIT
#   8. Evidence SELECT → CASCADE로 0건 assert
# [Input] Video → AIReport(report_id="r_ev") → ReportEvidence 2건 (FACT, DEEPFAKE)
# [Output] 2건 저장 확인, Update 후 content 변경 확인, CASCADE 삭제 후 0건 확인
def test_report_evidence_flow(db_session):
    # FK 선행조건
    video = Video(video_id="v_ev", video_title="근거 테스트", status="PENDING")
    db_session.add(video)
    db_session.commit()

    report = AIReport(report_id="r_ev", video_id="v_ev", final_score=0.7)
    db_session.add(report)
    db_session.commit()

    # 1. Create
    ev1 = ReportEvidence(evidence_id="ev_1", report_id="r_ev", category="FACT", content="허위 주장 발견")
    ev2 = ReportEvidence(evidence_id="ev_2", report_id="r_ev", category="DEEPFAKE", content="음성 변조 의심")
    db_session.add_all([ev1, ev2])
    db_session.commit()

    # 2. Read
    evidences = db_session.query(ReportEvidence).filter_by(report_id="r_ev").all()
    assert len(evidences) == 2

    # 3. Update
    ev1.content = "수정된 허위 주장"
    db_session.commit()
    updated_ev = db_session.query(ReportEvidence).filter_by(evidence_id="ev_1").first()
    assert updated_ev.content == "수정된 허위 주장"

    # 4. CASCADE 삭제: 리포트 삭제 → 근거도 삭제
    db_session.delete(report)
    db_session.commit()
    remaining = db_session.query(ReportEvidence).filter_by(report_id="r_ev").all()
    assert len(remaining) == 0
