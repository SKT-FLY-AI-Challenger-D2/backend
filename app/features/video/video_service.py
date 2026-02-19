from sqlalchemy.orm import Session
import re

from app.features.video.video_search import VideoSearch
from app.features.video.video_schema import SearchRequest, SearchResponse

from app.features.report.report_service import ReportService
from app.features.report.report_schema import AnalysisRequest, AnalysisResult
from app.features.report.report_repository import ReportRepository

class VideoService:
    """
    검색(video) -> DB 확인 -> 분석 요청(report) -> 결과 파싱 -> 알림(notification) 및 신고(complaint)
    """

    def __init__(self, db: Session):
        self.video_search = VideoSearch()
        self.report_service = ReportService(db)
        self.report_repo = ReportRepository(db)

    def search_and_analyze_video(self, request: SearchRequest) -> SearchResponse:
        """
        영상 검색 및 사기 여부 분석

        Args:
            request (SearchRequest): 검색 요청 데이터(제목, 채널명)

        Returns:
            SearchResponse: 최종 응답 데이터(영상 ID, 유튜브 URL, 제목, 채널명, 분석 결과, 에러)

        Raises:
            RuntimeError: 검색 실패, AI 분석 요청 등에서 발생한 오류
            ValueError: API KEY 에러
        """
        # 1. 입력받은 제목, 채널명으로 YouTube URL 검색 수행
        req_channel = self._normalize_text(request.channel, add_blank=True)
        req_title = self._normalize_text(request.title, add_blank=True)
        query = f"{req_title} {req_channel}".strip() # 제목 + 채널명으로 검색 쿼리 만들기
        search_result = self.video_search.search_youtube(query) # 검색 수행

        # 1-2. 검색 실패 처리
        if not search_result:
            raise RuntimeError("영상 검색에 실패했습니다.")
        
        # 1-3. 검색한 url의 제목, 채널명과 입력받은 제목, 채널 명이 다른 경우 분석하지 않고 반환
        if not self._is_video_match(request, search_result):
            raise RuntimeError(
                f"검색 결과와 요청 내용이 다릅니다. (검색된 제목: {search_result['title']}, 채널명: {search_result['channel_title']})"
            )

        # 1-4. DB에 기존 데이터가 있는지 확인 후 있으면 바로 반환
        previous_report = self.report_repo.get_report_by_video_id(video_id=search_result['video_id'])
        if previous_report:
            # report_service에서 데이터 가공
            processed_report: AnalysisResult = self.report_service.analysis_ai_result(previous_report)
            if processed_report.error: # DB에 저장된 기존 분석에 오류 내용이 있을 시
                raise RuntimeError(f"기존 DB 데이터 가공 실패: {processed_report.error}")
            
            return self._build_success_response(
                search_result=search_result, 
                analysis_data=processed_report, 
                message="DB에서 기존 분석 반환"
            )

        print(f"[VideoService] 검색 성공 -> ReportService로 분석 이동")

        # [TODO]: AI 분석 전에 DB에 미리 값만 넣기

        # 2. report_service.py 호출
        # Video 도메인의 데이터를 Report 도메인의 스키마로 변환하여 전달
        try:
            analysis_request = AnalysisRequest(
                youtube_url=search_result['url'],
                video_id=search_result["video_id"]
            )
            
            analysis_result: AnalysisResult = self.report_service.analyze_video(analysis_request)
        except Exception as e: # report_service.py 과정에서 오류 발생 시
            raise RuntimeError(f"분석 서비스 요청 오류: {str(e)}") from e

        if analysis_result.error:
            raise RuntimeError(f"분석 과정 중 오류: {analysis_result.error}")

        # 3. 결과 통합 및 반환
        return self._build_success_response(
            search_result=search_result, 
            analysis_data=analysis_result, 
            message="분석 완료"
        )
    
    def _normalize_text(self, text: str, add_blank:bool = False) -> str:
        """
        문자열 비교를 위해 정규화 수행
        1. 모든 공백 제거
        2. 특수문자 제거
        3. 소문자 변환
        """
        if not text:
            return ""
        
        return re.sub(r'[^\w]', ' ' if add_blank else '', text).lower()

    def _is_video_match(self, request: SearchRequest, result: dict) -> bool:
        """
        요청한 제목/채널명과 검색 결과가 동일한지 판단(exact match)
        
        Args:
            request (SearchRequest):    프론트엔드가 요청한 내용(영상 제목, 채널명)
            result (dict):              Youtube API로 찾은 내용(url, video_id, 영상 제목, 채널명)
        """
        # 1. 채널명 검사
        req_channel = self._normalize_text(request.channel)
        res_channel = self._normalize_text(result['channel_title'])
        
        if req_channel not in res_channel and res_channel not in req_channel:
            return False 
        
        # 2. 제목 검사
        req_title = self._normalize_text(request.title)
        res_title = self._normalize_text(result['title'])
        # 유사도가 임계값보다 낮으면 다른 영상으로 간주
        if req_title not in res_title and res_title not in req_title:
            return False
            
        return True
    
    def _build_success_response(self, search_result: dict, analysis_data: AnalysisResult, message: str) -> SearchResponse:
        """
        성공 응답 객체(SearchResponse)를 조립하여 반환합니다.
        """
        return SearchResponse(
            video_id=search_result['video_id'],
            youtube_url=search_result['url'],
            title=search_result['title'],
            channel_title=search_result['channel_title'],
            found=True,
            error=None,
            message=message,
            
            final_score=analysis_data.final_score,
            final_risk_level=analysis_data.final_risk_level,
            danger_evidence=analysis_data.danger_evidence,
            analysis_report=analysis_data.analysis_report,
            short_report=analysis_data.short_report
        )