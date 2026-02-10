from app.ai.supervisor import build_graph
from app.features.report.report_schema import AnalysisRequest, AnalysisResult
import httpx
# [TODO]: DB 저장
# from app.features.report.report_repository import ReportRepository

class ReportService:
    """
    AI 에이전트를 활용하여 분석 및 리포트 생성
    """

    def __init__(self):
        # 그래프 초기화
        self.ai_graph = build_graph()
        # self.report_repo = ReportRepository()

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
                url = "http://127.0.0.1:8000/analyze",
                json={
                    "youtube_url" : request.youtube_url
                },
                timeout = 600 # timeout 넉넉하게 걸었음.
            )
            result = response.json() 
            result_legal = result.get("legal_issue", False) # 일단 기본값 False로 설정
            result_deepfake = result.get("deepfake_issue", False)
            result_ai_voice = result.get("ai_voice_issue", False)

            # 결과 텍스트 생성
            result_text= []
            if result_legal is True:
                result_text.append("법적으로 문제가 있는 영상입니다.\n")
            if result_deepfake is True:
                result_text.append("딥페이크 영상일 확률이 있습니다.\n")
            if result_ai_voice is True:
                result_text.append("AI 목소리 영상일 확률이 있습니다.\n")
            if len(result_text) == 0:
                result_text = "해당 영상은 문제가 없습니다."
            result_text = "\n".join(result_text)

            if response.status_code != 200:
                raise Exception(f"AI 서버 호출 실패: {response.status_code}")

            return AnalysisResult(
                report = result_text,
                error = None
            )
            # [TODO]: DB에 리포트 저장 로직
        except Exception as e:
            print(f"[ReportService] 분석 중 오류 발생: {e}")
            return AnalysisResult(
                report = None,
                error = str(e)
            )
