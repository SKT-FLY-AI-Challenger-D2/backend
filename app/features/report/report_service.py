from app.ai.supervisor import build_graph
from app.features.report.report_schema import AnalysisRequest, AnalysisResult

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
            # 1. AI Supervisor 호출
            initial_state = {"youtube_url": request.youtube_url}
            ai_output = self.ai_graph.invoke(initial_state)

            # 2. 결과 파싱
            result_text = ai_output.get("analysis_result")
            error_msg = ai_output.get("error")

            if error_msg:
                return AnalysisResult(error=error_msg)

            # [TODO]: DB에 리포트 저장 로직

            return AnalysisResult(
                report=result_text,
                error=None
            )

        except Exception as e:
            print(f"[ReportService] 에러 발생: {e}")
            return AnalysisResult(error=str(e))