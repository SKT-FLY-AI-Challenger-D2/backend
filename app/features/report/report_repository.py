from sqlalchemy.orm import Session
from app.features.report.report_model import AIReport
from typing import Optional

class ReportRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_report(self, report: AIReport) -> AIReport:
        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)
        return report

    def get_report_by_id(self, report_id: str) -> Optional[AIReport]:
        return self.db.query(AIReport).filter(AIReport.report_id == report_id).first()

    def get_report_by_video_id(self, video_id: str) -> Optional[AIReport]:
        """비디오 ID로 분석 결과 조회 (1:1 관계)"""
        return self.db.query(AIReport).filter(AIReport.video_id == video_id).first()

    def update_report(self, report: AIReport) -> AIReport:
        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)
        return report

    def delete_report(self, report_id: str) -> None:
        report = self.get_report_by_id(report_id)
        if report:
            self.db.delete(report)
            self.db.commit()