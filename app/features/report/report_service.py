#from app.ai.supervisor import build_graph
from app.features.report.report_schema import AnalysisRequest, AnalysisResult
import httpx
# [TODO]: DB 저장
# from app.features.report.report_repository import ReportRepository

class ReportService:
    """
    AI 에이전트를 활용하여 분석 및 리포트 생성
    """

    def __init__(self):
        # 그래프 초기화. 더이상 안쓴다 
        #self.ai_graph = build_graph()
        # self.report_repo = ReportRepository()
        pass


    def analysis_ai_result(self, ai_result: dict) -> AnalysisResult:
        def check_risk(category, score_key, evidence_key):
            data = ai_result.get(category, {})
            score = data.get(score_key, 0.0)
            evidence = data.get(evidence_key, [])
            # 증거가 있고 점수가 0.4 이상이면 1(위험), 아니면 0
            status = 1 if evidence and (score >= 0.4) else 0
            return score, status, evidence

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

        final_score = ai_result.get("final_score", 0.0) # default = 0.0

        if final_score >= 0.7: # 0.7 이상 : 위험도 2  ( 높음 )
            final_status = 2
            short_report_result = short_report + " 확률이 매우 높아 위험합니다."  

        elif final_score >= 0.3: # 0.3 이상 : 위험도 1 ( 중간 )
            final_status = 1
            short_report_result = short_report + " 확률이 있어 주의가 필요합니다."
        else:
            final_status = 0 # 0.3 미만 : 위험도 0 ( 낮음 )
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
                raise Exception(f"AI 서버 호출 실패: {response.status_code}")
                
            ai_result = response.json()
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