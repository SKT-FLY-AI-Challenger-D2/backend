from sqlalchemy.orm import Session
from app.features.report.report_model import AIReport, ReportEvidence
from typing import Optional, List

class ReportRepository:
    def __init__(self, db: Session):
        self.db = db

    # ==========================
    # AIReport (리포트)
    # ==========================

    # [목적] AI 분석 리포트를 DB에 저장
    # [동작] AIReport 객체 → DB INSERT → COMMIT → REFRESH → 반환
    # [Input] AIReport 객체 (report_id, video_id, 점수 컬럼들, analysis_result)
    # [Output] 저장된 AIReport 객체
    def create_report(self, report: AIReport) -> AIReport:
        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)
        return report

    # [목적] 리포트 1건을 report_id로 조회
    # [동작] report_id로 필터링하여 단건 조회
    # [Input] report_id (str)
    # [Output] Optional[AIReport]
    def get_report_by_id(self, report_id: str) -> Optional[AIReport]:
        return self.db.query(AIReport).filter(AIReport.report_id == report_id).first()

    # [목적] 특정 비디오에 대한 리포트 조회
    # [동작] video_id로 필터링하여 단건 조회
    # [Input] video_id (str)
    # [Output] Optional[AIReport]
    def get_report_by_video_id(self, video_id: str) -> Optional[AIReport]:
        return self.db.query(AIReport).filter(AIReport.video_id == video_id).first()

    # [목적] 기존 리포트의 내용을 수정
    # [동작] AIReport 객체 → DB UPDATE → COMMIT → REFRESH → 반환
    # [Input] 수정된 AIReport 객체
    # [Output] 업데이트된 AIReport 객체
    def update_report(self, report: AIReport) -> AIReport:
        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)
        return report

    # [목적] 리포트를 DB에서 삭제
    # [동작] report_id로 조회 → 존재하면 DELETE → COMMIT
    # [Input] report_id (str)
    # [Output] None
    def delete_report(self, report_id: str) -> None:
        report = self.get_report_by_id(report_id)
        if report:
            self.db.delete(report)
            self.db.commit()

    # ==========================
    # ReportEvidence (근거)
    # ==========================

    # [목적] 분석 근거를 DB에 저장
    # [동작] ReportEvidence 객체 → DB INSERT → COMMIT → REFRESH → 반환
    # [Input] ReportEvidence 객체 (evidence_id, report_id, category, content)
    # [Output] 저장된 ReportEvidence 객체
    def add_evidence(self, evidence: ReportEvidence) -> ReportEvidence:
        self.db.add(evidence)
        self.db.commit()
        self.db.refresh(evidence)
        return evidence

    # [목적] 특정 근거 1건을 ID로 조회
    # [동작] evidence_id로 필터링하여 단건 조회
    # [Input] evidence_id (str)
    # [Output] Optional[ReportEvidence] (존재하면 객체, 없으면 None)
    def get_evidence_by_id(self, evidence_id: str) -> Optional[ReportEvidence]:
        return self.db.query(ReportEvidence).filter(ReportEvidence.evidence_id == evidence_id).first()

    # [목적] 특정 리포트에 연결된 모든 근거 조회
    # [동작] report_id로 필터링하여 ReportEvidence 전체 조회
    # [Input] report_id (str)
    # [Output] List[ReportEvidence] (해당 리포트의 근거 목록)
    def get_evidence_by_report(self, report_id: str) -> List[ReportEvidence]:
        return self.db.query(ReportEvidence).filter(ReportEvidence.report_id == report_id).all()

    # [목적] 기존 근거의 내용을 수정
    # [동작] ReportEvidence 객체 → DB UPDATE → COMMIT → REFRESH → 반환
    # [Input] 수정된 ReportEvidence 객체
    # [Output] 업데이트된 ReportEvidence 객체
    def update_evidence(self, evidence: ReportEvidence) -> ReportEvidence:
        self.db.add(evidence)
        self.db.commit()
        self.db.refresh(evidence)
        return evidence

    # [목적] 특정 근거를 DB에서 삭제
    # [동작] evidence_id로 조회 → 존재하면 DELETE → COMMIT
    # [Input] evidence_id (str)
    # [Output] None (삭제 완료)
    def delete_evidence(self, evidence_id: str) -> None:
        evidence = self.get_evidence_by_id(evidence_id)
        if evidence:
            self.db.delete(evidence)
            self.db.commit()
