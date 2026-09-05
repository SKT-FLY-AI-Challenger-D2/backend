from sqlalchemy.orm import Session
import re
import html # html 문법 정규화
import difflib

from app.core.database import SessionLocal

from app.features.video.video_search import VideoSearch
from app.features.video.video_schema import SearchRequest, SearchResponse

from app.features.video.video_model import Video
from app.features.video.video_repository import VideoRepository

from app.features.report.report_service import ReportService
from app.features.report.report_schema import AnalysisRequest, AnalysisResult

class VideoService:
    """
    검색(video) -> DB 확인 -> 분석 요청(report) -> 결과 파싱 -> 알림(notification) 및 신고(complaint)
    """

    def __init__(self):
        self.db: Session = SessionLocal()

        self.video_search = VideoSearch()
        self.report_service = ReportService(self.db)
        self.video_repo = VideoRepository(self.db)

    def close(self):
        self.db.close()

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
        print("[Video Service] 영상 검색 시작")

        query = f"{request.title} {request.channel}".strip() # 제목 + 채널명으로 검색 쿼리 만들기
        query = re.sub(r'[|&"\-\(\)]', ' ', query) # 검색 명령어로 쓰이는 특수문자 지우기
        search_result = self.video_search.search_youtube(query) # 검색 수행
        # # 더미 데이터
        # search_result = {
        #     'video_id': 'rA5Mt_XdoSQ', 
        #     'title': '[무한도전] 왔다 내 도파민🤑 돈으로도 못 사는 무한도전 표 명품 티키타카 모음.zip | 무한도전⏱오분순삭 MBC070915방송', 
        #     'channel_title': '오분순삭', 
        #     'url': 'https://www.youtube.com/watch?v=rA5Mt_XdoSQ'
        # }


        # 1-2. 검색 실패 처리
        if not search_result:
            print("[Video Service] 영상 검색에 실패했습니다.")
            raise RuntimeError("영상 검색에 실패했습니다.")
        
        # 1-3. 검색한 url의 제목, 채널명과 입력받은 제목, 채널 명이 다른 경우 분석하지 않고 반환
        print("[Video Service] 검색 완료, 비교 중")
        search_result['title'] = html.unescape(search_result['title'])
        if not self._is_video_match(request, search_result):
            print(
                f"[Video Service] 검색 결과와 요청 내용이 다릅니다. (검색된 제목: {search_result['title']}, 채널명: {search_result['channel_title']})"
            )
            raise RuntimeError(
                f"검색 결과와 요청 내용이 다릅니다. (검색된 제목: {search_result['title']}, 채널명: {search_result['channel_title']})"
            )

        print("[Video Service] 기존 비디오 DB 확인 시작")
        # 1-4. DB에 기존 데이터가 있는지 확인 후 있으면 바로 반환
        # 광고가 아닌 경우는 바로 반환
        
        video = self.video_repo.get_video(video_id=search_result['video_id'])
        
        if video:
            if video.status == 'SAFE':
                return SearchResponse(
                    video_id=search_result['video_id'],
                    youtube_url=search_result['url'],
                    title=search_result['title'],
                    channel_title=search_result['channel_title'],
                    found=True,
                    error=None,
                    message="DB에서 기존 분석 광고 아님 반환",
                    
                    final_score=0.0,
                    final_risk_level=9,
                    danger_evidence=[],
                    analysis_report="",
                    short_report=""
                )
            elif video.status == 'HARMFUL':
                previous_report: AnalysisResult = self.report_service.get_existing_analysis(video_id=search_result['video_id'])
                
                if previous_report:
                    if previous_report.error: # DB에 저장된 기존 분석에 오류 내용이 있을 시
                        print(f"기존 DB 데이터 가공 실패: {previous_report.error}")
                        raise RuntimeError(f"기존 DB 데이터 가공 실패: {previous_report.error}")
                    
                    print("[VideoService] DB에서 기존 분석 반환")
                    return self._build_success_response(
                        search_result=search_result,
                        analysis_data=previous_report,
                        message="DB에서 기존 분석 반환"
                    )
                # HARMFUL인데 previous_report가 없으면 PENDING으로 되돌려 재분석 허용
                print(f"[VideoService] HARMFUL 상태이나 리포트 없음, PENDING으로 재설정")
                video.status = 'PENDING'
                self.video_repo.update_video(video)

        # vide가 없거나 video.status == 'PENDING'이거나, previous_report가 없거나 => AI 서버 호출
        print(f"[VideoService] 검색 성공 -> ReportService로 분석 이동")

        # 1-5. AI 분석 전에 DB에 미리 값만 넣기
        # 이미 Video 테이블에 존재하는지 확인
        current_video = self.video_repo.get_video(search_result['video_id'])
        
        if not current_video:
            # 검색된 정보로 Video 객체 생성
            new_video = Video(
                video_id=search_result['video_id'],
                video_title=search_result['title'],
                channel=search_result['channel_title'],
                youtube_url=search_result['url'],
                thumbnail=search_result.get('thumbnail', None), # 아직 썸네일 저장은 미구현
                status='PENDING'  # 분석 대기 상태
            )
            # DB 저장
            if not self.video_repo.create_video(new_video):
                print(f"[VideoService] Video DB 저장 실패")
                raise RuntimeError("Video DB 저장 실패")
            print(f"[VideoService] 신규 영상 정보 저장 완료: {search_result['title']} (PENDING)")
            current_video = new_video
        elif current_video.status == 'PENDING': # 기존 AI 분석 시 오류로 중단되었을 경우
            pass # TODO 원래는 분석을 기다려야 함
        else: 
            print(f"[VideoService] DB 이상, current_video.status:", current_video.status)
            raise RuntimeError("[VideoService] DB 이상")

        # 2. report_service.py 호출
        # Video 도메인의 데이터를 Report 도메인의 스키마로 변환하여 전달
        try:
            analysis_request = AnalysisRequest(
                youtube_url=search_result['url'],
                video_id=search_result["video_id"]
            )
            
            analysis_result: AnalysisResult = self.report_service.analyze_video(analysis_request)
        except Exception as e: # report_service.py 과정에서 오류 발생 시
            print(f"[Video Service] 분석 서비스 요청 오류: {str(e)}")
            self.db.rollback() # 세션 롤백
            raise RuntimeError(f"분석 서비스 요청 오류: {str(e)}") from e

        if analysis_result.error:
            # TODO: AI 분석 중 오류 발생 시 current_video.status 수정해야 함
            print(f"[Video Service] 분석 과정 중 오류: {analysis_result.error}")
            raise RuntimeError(f"분석 과정 중 오류: {analysis_result.error}")

        # 3. 결과 통합 및 반환
        # 아까 저장한 Video 테이블의 객체의 state를 광고이면 HARMFUL, 광고가 아니면 SAFE로 분류하여 수정
        if current_video:
            # report_service.py의 로직에 따라 광고가 아니면 final_risk_level이 9임
            if analysis_result.final_risk_level == 9:
                current_video.status = 'SAFE'
            else:
                current_video.status = 'HARMFUL'
                
            self.video_repo.update_video(current_video)
            print(f"[VideoService] 영상 상태 업데이트 완료: {current_video.video_title} ({current_video.status})")

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
        
        # HTML 엔티티를 실제 문자로 변환
        text = html.unescape(text)
        
        return re.sub(r'[^\w]', ' ' if add_blank else '', text).lower()

    def _is_video_match(self, request: SearchRequest, result: dict) -> bool:
        """
        요청한 제목/채널명과 검색 결과가 동일한지 판단(exact match)
        
        Args:
            request (SearchRequest):    프론트엔드가 요청한 내용(영상 제목, 채널명)
            result (dict):              Youtube API로 찾은 내용(url, video_id, 영상 제목, 채널명)
        """
        req_channel = self._normalize_text(request.channel)
        res_channel = self._normalize_text(result['channel_title'])
        
        req_title = self._normalize_text(request.title)
        res_title = self._normalize_text(result['title'])

        # 1. 채널명 유사도 검사
        channel_similarity = difflib.SequenceMatcher(None, req_channel, res_channel).ratio()

        channel_match = (req_channel in res_channel) or (res_channel in req_channel) or (channel_similarity >= 0.9)
        
        if not channel_match:
            return False 

        # 2. 제목 유사도 검사
        title_similarity = difflib.SequenceMatcher(None, req_title, res_title).ratio()
        
        title_match = (req_title in res_title) or (res_title in req_title) or (title_similarity >= 0.8)

        if not title_match:
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