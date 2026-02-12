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
            ai_result = response.json()

            legal_score = ai_result.get("legal", {}).get("legal_issue_score", 0.0)
            legal_evidence = ai_result.get("legal", {}).get("legal_issue_evidence", [])
            if legal_evidence : # 먼가 내용이 담겨 왔다면
                legal_status = "위법의 소지가 있고"
            else:
                legal_status = ""

            deepfake_score = ai_result.get("deepfake", {}).get("deepfake_score", 0.0)
            deepfake_evidence = ai_result.get("deepfake", {}).get("deepfake_evidence", [])
            if deepfake_evidence :
                deepfake_status = "딥페이크로 조작된 영상일 가능성이 있고"
            else:
                deepfake_status = ""

            fact_score = ai_result.get("fact", {}).get("fake_score", 0.0)
            fact_evidence = ai_result.get("fact", {}).get("fake_evidence", [])
            if fact_evidence :
                fact_status = "허위 사실의 가능성이 있고"
            else:
                fact_status = ""

            final_score = ai_result.get("final_score", 0.0) # default = 0.0
            if final_score >= 0.7: # 0.7 이상 : 위험도 2  ( 높음 )
                final_status = 2
                short_report = f"해당 영상은 {legal_status}, {deepfake_evidence}, {fact_evidence} 피해 위험이 높은 영상입니다."
            elif final_score >= 0.3: # 0.3 이상 : 위험도 1 ( 중간 )
                final_status = 1
                short_report = f"해당 영상은 {legal_status}, {deepfake_evidence}, {fact_evidence} 피해 위험이 있기에 주의가 필요합니다."
            else:
                final_status = 0 # 0.3 미만 : 위험도 0 ( 낮음 )
                short_report = "해당 영상은 안전한 영상일 확률이 높습니다."
            
            analysis_report = ai_result.get("report", "") # 보고서용 긴 글.



            

            if response.status_code != 200:
                raise Exception(f"AI 서버 호출 실패: {response.status_code}")

            return AnalysisResult(
                report =    result_text,
                error = None
            )
            # [TODO]: DB에 리포트 저장 로직
        except Exception as e:
            print(f"[ReportService] 분석 중 오류 발생: {e}")
            return AnalysisResult(
                report = None,
                error = str(e)
            )
