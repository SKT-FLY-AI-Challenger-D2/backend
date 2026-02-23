from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Numeric
from sqlalchemy.sql import func
from app.core.database import Base

class AIReport(Base):
    __tablename__ = "ai_reports"

    report_id = Column(String(255), primary_key=True)
    video_id = Column(String(255), ForeignKey("videos.video_id", ondelete="CASCADE"), unique=True, nullable=False)

    final_score = Column(Numeric(5, 4))
    fact_score = Column(Numeric(5, 4))
    deepfake_score = Column(Numeric(5, 4))
    legal_issue_score = Column(Numeric(5, 4))
    analysis_result = Column(Text)
    created_at = Column(DateTime, default=func.now())

# [목적] AI 분석 리포트의 점수를 뒷받침하는 근거 문장을 저장하는 모델
# [동작] ai_reports 테이블과 1:N 관계, CASCADE 삭제
# [Input] evidence_id(PK), report_id(FK), category(FACT/DEEPFAKE/LEGAL), content(근거 문장)
# [Output] report_evidence 테이블 레코드
class ReportEvidence(Base):
    __tablename__ = "report_evidence"

    evidence_id = Column(String(255), primary_key=True)
    report_id = Column(String(255), ForeignKey("ai_reports.report_id", ondelete="CASCADE"), nullable=False)
    category = Column(String(20))
    content = Column(Text)
