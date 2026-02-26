#from app.ai.supervisor import build_graph
from app.features.report.report_schema import AnalysisRequest, AnalysisResult

import httpx
import uuid
from sqlalchemy.orm import Session

# DB 저장용 
from app.features.report.report_repository import ReportRepository
from app.features.report.report_model import AIReport, ReportEvidence

class ReportService:
    """
    AI 에이전트를 활용하여 분석 및 리포트 생성
    """

    def __init__(self, db: Session):
        # 그래프 초기화. 더이상 안쓴다 
        #self.ai_graph = build_graph()
        self.report_repo = ReportRepository(db)
        pass

    def get_existing_analysis(self, video_id: str) -> AnalysisResult | None:
        """
        DB에 기존 분석 결과가 있는지 확인하고, 
        있다면 AI 서버가 응답하는 dict와 동일한 형태로 가공하여 반환
        """
        previous_report = self.report_repo.get_report_by_video_id(video_id=video_id)
        
        if not previous_report:
            return None

        # 연관된 Evidence 목록 가져오기
        evidences = self.report_repo.get_evidence_by_report(report_id=previous_report.report_id)
        
        # 카테고리 별로 근거 내용 리스트 가져오기
        legal_evidence = [e.content for e in evidences if e.category == "LEGAL"]
        deepfake_evidence = [e.content for e in evidences if e.category == "DEEPFAKE"]
        fact_evidence = [e.content for e in evidences if e.category == "FACT"]

        # AI 서버 응답과 동일한 형태의 dict로 만들기
        report_dict = {
            "is_ad": True, # 광고가 아닌 경우는 안 들어온다고 가정
            "legal": {
                "legal_issue_score": float(previous_report.legal_issue_score),
                "legal_issue_evidence": legal_evidence
            },
            "deepfake": {
                "deepfake_ai_score": float(previous_report.deepfake_score),
                "deepfake_ai_evidence": deepfake_evidence
            },
            "fact": {
                "fake_score": float(previous_report.fact_score),
                "fake_evidence": fact_evidence
            },
            "final_score": float(previous_report.final_score),
            "report": previous_report.analysis_result
        }
        
        print("[Report Service] 기존 분석 데이터 가공 완료")
        
        return self.analysis_ai_result(report_dict)


    def analysis_ai_result(self, ai_result: dict) -> AnalysisResult:
        def check_risk(category, score_key, evidence_key):
            data = ai_result.get(category, {})
            if data is None:
                return 0.0, 0, []
            score = data.get(score_key, 0.0)
            evidence = data.get(evidence_key, [])
            # 증거가 있고 점수가 0.4 이상이면 1(위험), 아니면 0
            status = 1 if evidence and (score >= 0.4) else 0
            return score, status, evidence
        
        
        if ai_result is None:
            print("[Report Service] ai_result가 None입니다.")
            raise RuntimeError("[Report Service] ai_result가 None입니다.")
        # 광고가 아니면 바로 반환
        if not ai_result.get("is_ad", "True"):
            return AnalysisResult(
            final_risk_level = 9, # 광고가 아닌 경우는 9로 표시
        )

        legal_score, legal_status, legal_evidence = check_risk("legal", "legal_issue_score", "legal_issue_evidence")
        deepfake_score, deepfake_status, deepfake_evidence = check_risk("deepfake", "deepfake_ai_score", "deepfake_ai_evidence")
        fact_score, fact_status, fact_evidence = check_risk("fact", "fake_score", "fake_evidence")

        # danger_evidence : 일단 특정 점수 ( 0.6으로 우선 세팅 ) 넘기면 danger_evidence에 추가하도록 함
        danger_threshold = 0.6
        danger_evidence = []
        if legal_score >= danger_threshold:
            danger_evidence.extend(legal_evidence)
        if deepfake_score >= danger_threshold:
            danger_evidence.extend(deepfake_evidence)
        if fact_score >= danger_threshold:
            danger_evidence.extend(fact_evidence)

        # 짧은 리포트 생성 (순서: Deepfake -> Fact -> Legal)
        descriptions = []
        if deepfake_status: descriptions.append("AI로 생성된")
        if fact_status: descriptions.append("허위 정보를 포함한")
        if legal_status: descriptions.append("위법의 소지가 있는")

        if descriptions:
            short_report = f"해당 영상은 {' '.join(descriptions)} 영상일"
        else:
            short_report = "해당 영상은 분석 결과 위험한 영상일"

        final_score = ai_result.get("final_score", None) # default = None
        # 세 부분 점수 중 최솟값만 제외하고 평균내어 최종 점수 계산
        if not final_score:
            scores = [legal_score, deepfake_score, fact_score]
            min_score = min(scores)
            final_score = (sum(scores) - min_score) / 2

        if final_score >= 0.6: # 0.65 이상 : 위험도 2  ( 높음 )
            final_status = 2
            short_report_result = short_report + " 확률이 매우 높아 위험합니다."  

        elif final_score >= 0.3: # 0.4 이상 : 위험도 1 ( 중간 )
            final_status = 1
            short_report_result = short_report + " 확률이 있어 주의가 필요합니다."
        else:
            final_status = 0 # 0.4 미만 : 위험도 0 ( 낮음 )
            short_report_result = "해당 영상은 안전한 영상일 확률이 높습니다."

        analysis_report = ai_result.get("report", "") # 보고서용 긴 글.

        return AnalysisResult(
            final_score = final_score,
            final_risk_level = final_status,
            danger_evidence = danger_evidence,
            analysis_report = analysis_report,
            short_report = short_report_result,
        )




    def create_error_result(self, error_msg: str) -> AnalysisResult:
        return AnalysisResult(
            final_score=None,
            final_risk_level=None,
            danger_evidence=None,
            analysis_report=None,
            short_report=None,
            error=error_msg
        )
    
    
    def save_report_to_db(self, video_id: str, ai_result: dict) -> None:
        try:
            existing = self.report_repo.get_report_by_video_id(video_id)
            if existing:
                print(f"[ReportService] video_id={video_id} 이미 리포트 존재, 저장 스킵")
                return
            report_id = str(uuid.uuid4())
            while self.report_repo.get_report_by_id(report_id):
                report_id = str(uuid.uuid4())
            
            # 카테고리 데이터가 None으로 올 경우 빈 딕셔너리로 강제 변환하여 AttributeError 방지
            fact_data = ai_result.get("fact") or {}
            deepfake_data = ai_result.get("deepfake") or {}
            legal_data = ai_result.get("legal") or {}
            
            # AIReport 엔티티 생성 및 저장
            new_report = AIReport(
                report_id=report_id,
                video_id=video_id,
                final_score=ai_result.get("final_score", 0.0),
                fact_score=fact_data.get("fake_score", 0.0),
                deepfake_score=deepfake_data.get("deepfake_ai_score", 0.0),
                legal_issue_score=legal_data.get("legal_issue_score", 0.0),
                analysis_result=ai_result.get("report", "")
            )
            if not self.report_repo.create_report(new_report):
                print(f"[ReportService] 데이터 저장 실패")
                raise RuntimeError("AIReport DB 저장 실패")

            # ReportEvidence 엔티티 생성 및 저장
            def _save_evidence(category: str, evidence_list: list):
                # evidence_list가 None이거나 비어있을 경우 스킵
                if not evidence_list:
                    return
                    
                for content in evidence_list:
                    evidence_id = str(uuid.uuid4())
                    while self.report_repo.get_report_by_id(evidence_id):
                        evidence_id = str(uuid.uuid4())

                    new_evidence = ReportEvidence(
                        evidence_id=evidence_id,
                        report_id=report_id,
                        category=category,
                        content=content
                    )
                    if not self.report_repo.add_evidence(new_evidence):
                        print(f"[ReportService] ReportEvidence DB 저장 실패")
                        raise RuntimeError("ReportEvidence DB 저장 실패")

            _save_evidence("FACT", fact_data.get("fake_evidence", []))
            _save_evidence("DEEPFAKE", deepfake_data.get("deepfake_ai_evidence", []))
            _save_evidence("LEGAL", legal_data.get("legal_issue_evidence", []))
            
            print(f"[ReportService] DB 저장 성공: report_id={report_id}")
            
        except AttributeError as e:
            # 딕셔너리 파싱이나 데이터 타입이 예상과 달라 발생하는 오류
            print(f"[ReportService] 데이터 구조 파싱 오류: {e}")
            raise RuntimeError(f"AI 응답 데이터 형식이 올바르지 않아 DB 저장에 실패했습니다: {e}")
            
        except Exception as e:
            # SQLAlchemy DB 에러(IntegrityError 등) 및 기타 예기치 않은 오류
            print(f"[ReportService] DB 저장 중 예외 발생: {e}")
            raise RuntimeError(f"[ReportService] DB 처리 중 시스템 오류가 발생했습니다: {e}")


    def analyze_video(self, request: AnalysisRequest) -> AnalysisResult:
        """
        AI Agent를 호출하여 영상 분석
        
        Args:
            request (AnalysisRequest): 분석할 영상 정보

        Returns:
            AnalysisResult: 분석 결과
        """
        print(f"[ReportService] 분석 시작: {request.youtube_url}")

        try:
            response = httpx.post( #httpx가 비동기가 가능해서 httpx 사용
                url = "http://127.0.0.1:8001/analyze", # AI 서버와 통신
                json={
                    "youtube_url" : request.youtube_url
                },
                timeout = 600 # timeout 넉넉하게 걸었음.
            )
            

            if response.status_code != 200:
                print(f"AI 서버 호출 실패: {response.status_code}")
                raise Exception(f"AI 서버 호출 실패: {response.status_code}")
                
            ai_result = response.json()

            # DB에 저장하기
            if hasattr(request, "video_id"):
                self.save_report_to_db(request.video_id, ai_result)
            else:
                print("[ReportService] 경고: AnalysisRequest에 video_id가 없어 DB에 저장할 수 없습니다.")
            return self.analysis_ai_result(ai_result)

        except Exception as e:
            print(f"[ReportService] 분석 중 오류 발생: {e}")
            return self.create_error_result(str(e))





















'''
            [Legacy Code] 기존 로직 보존 (주석 처리)
             legal_score = ai_result.get("legal", {}).get("legal_issue_score", 0.0)
             legal_evidence = ai_result.get("legal", {}).get("legal_issue_evidence", [])
             if legal_evidence and (legal_score >=0.4):
                 legal_status = 1
             else:
               legal_status = 0
            
             deepfake_score = ai_result.get("deepfake", {}).get("deepfake_score", 0.0)
             deepfake_evidence = ai_result.get("deepfake", {}).get("deepfake_evidence", [])
             if deepfake_evidence and (deepfake_score >=0.4) :
                deepfake_status = 1
             else:
                 deepfake_status = 0
            
             fact_score = ai_result.get("fact", {}).get("fake_score", 0.0)
             fact_evidence = ai_result.get("fact", {}).get("fake_evidence", [])
             if fact_evidence and ( fact_score >=0.4 ):
                 fact_status = 1
             else:
                 fact_status = 0
            
             danger_evidence = legal_evidence + deepfake_evidence + fact_evidence
            
             short_report = "해당 영상은 분석 결과 위험한 영상일"
             if legal_status == 1 and deepfake_status == 1 and fact_status == 1:
                 short_report = "해당 영상은 AI로 생성된 허위 정보를 포함한 위법의 소지가 있는 영상일"
             elif legal_status == 1 and deepfake_status == 1 and fact_status == 0:
                 short_report = "해당 영상은 AI로 생성된 위법의 소지가 있는 영상일"
             elif legal_status == 1 and deepfake_status == 0 and fact_status == 1:
                 short_report = "해당 영상은 허위 정보를 포함한 위법의 소지가 있는 영상일"
             elif legal_status == 1 and deepfake_status == 0 and fact_status == 0:
                 short_report = "해당 영상은 위법의 소지가 있는 영상일"
             elif legal_status == 0 and deepfake_status == 1 and fact_status == 1:
                 short_report = "해당 영상은 AI로 생성된 허위 정보를 포함한 영상일"
             elif legal_status == 0 and deepfake_status == 1 and fact_status == 0:
                 short_report = "해당 영상은 AI로 생성된 영상일"
             elif legal_status == 0 and deepfake_status == 0 and fact_status == 1:
                 short_report = "해당 영상은 허위 정보를 포함한 영상일"
'''
