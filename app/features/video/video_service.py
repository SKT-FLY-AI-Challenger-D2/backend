from app.features.video.video_repository import VideoRepository
from app.features.video.video_schema import SearchRequest, SearchResponse


from app.features.report.report_service import ReportService
from app.features.report.report_schema import AnalysisRequest

class VideoService:
    """
    검색(video) -> DB 확인 -> 분석 요청(report) -> 결과 파싱 -> 알림(notification) 및 신고(complaint)
    """

    def __init__(self):
        self.video_repo = VideoRepository()
        self.report_service = ReportService()

    def search_and_analyze_video(self, request: SearchRequest) -> SearchResponse:
        """
        영상 검색 및 사기 여부 분석

        Args:
            request (SearchRequest): 검색 요청 데이터(제목, 채널명)

        Returns:
            SearchResponse: 최종 응답 데이터(영상 ID, 유튜브 URL, 제목, 채널명, 분석 결과, 에러)
        """
        # 1. 입력받은 제목, 채널명으로 YouTube URL 검색 수행
        query = f"{request.title} {request.channel}".strip() # 제목 + 채널명으로 검색 쿼리 만들기
        search_result = self.video_repo.search_youtube(query) # 검색 수행

        # 1-1. 검색 실패 처리
        if not search_result:
            return SearchResponse(found=False, message="영상을 찾을 수 없습니다.")
        
        if "error" in search_result:
             return SearchResponse(found=False, message=search_result["error"])

         # [TODO]: DB에 기존 데이터가 있는지 확인하는 로직 추가

        print(f"[VideoService] 검색 성공 -> ReportService로 분석 이동")

        # 2. report_service.py 호출
        # Video 도메인의 데이터를 Report 도메인의 스키마로 변환하여 전달
        analysis_request = AnalysisRequest(
            youtube_url=search_result['url'],
        )
        
        analysis_result = self.report_service.analyze_video(analysis_request)

        # 3. 결과 통합 및 반환
        response = SearchResponse(
            video_id=search_result['video_id'],
            youtube_url=search_result['url'],
            title=search_result['title'],
            channel_title=search_result['channel_title'],
            found=True,
            # Report 서비스의 결과를 Video 응답 스키마에 매핑
            analysis_result=analysis_result.report, 
            error=analysis_result.error,
            message="분석 완료" if not analysis_result.error else "분석 실패"
        )

        return response