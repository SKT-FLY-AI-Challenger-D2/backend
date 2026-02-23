from sqlalchemy.orm import Session
from app.features.complaint.complaint_model import Complaint
from typing import Optional, List

class ComplaintRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_complaint(self, complaint: Complaint) -> Complaint:
        self.db.add(complaint)
        self.db.commit()
        self.db.refresh(complaint)
        return complaint

    def get_complaint(self, complaint_id: str) -> Optional[Complaint]:
        return self.db.query(Complaint).filter(Complaint.complaint_id == complaint_id).first()

    def get_complaints_by_video(self, video_id: str) -> List[Complaint]:
        """특정 비디오에 대한 신고 목록"""
        return self.db.query(Complaint).filter(Complaint.video_id == video_id).all()

    # [목적] 기존 신고의 내용을 수정
    # [동작] Complaint 객체 → DB UPDATE → COMMIT → REFRESH → 반환
    # [Input] 수정된 Complaint 객체
    # [Output] 업데이트된 Complaint 객체
    def update_complaint(self, complaint: Complaint) -> Complaint:
        self.db.add(complaint)
        self.db.commit()
        self.db.refresh(complaint)
        return complaint

    def delete_complaint(self, complaint_id: str) -> None:
        complaint = self.get_complaint(complaint_id)
        if complaint:
            self.db.delete(complaint)
            self.db.commit()