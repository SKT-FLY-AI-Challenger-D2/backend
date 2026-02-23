import pytest
from unittest.mock import patch, MagicMock
from googleapiclient.errors import HttpError
from httplib2 import Response

from app.features.video.video_search import VideoSearch

# [테스트 목적] 유튜브 영상 검색 성공 로직 검증
# [테스트 방식] googleapiclient.discovery.build Mocking하여 성공 응답 반환
# [테스트 동작]
#   1. youtube.search().list().execute()의 반환값을 Mocking
#   2. search_youtube 호출
#   3. 결과값이 딕셔너리로 알맞게 파싱(video_id, title, channel_title, url)되었는지 assert
# [Input] 검색 쿼리 "무한도전 오분순삭"
# [Output] 파싱된 딕셔너리 정보 일치 여부 검증
@patch("app.features.video.video_search.build")
def test_search_youtube_success(mock_build):
    # Mocking Setup
    mock_youtube = MagicMock()
    mock_build.return_value = mock_youtube
    mock_youtube.search().list().execute.return_value = {
        "items": [{
            "id": {"videoId": "rA5Mt_XdoSQ"},
            "snippet": {
                "title": "[무한도전] 왔다 내 도파민🤑",
                "channelTitle": "오분순삭"
            }
        }]
    }

    # 실행
    searcher = VideoSearch()
    searcher.api_key = "valid_dummy_key" # API 키 설정 보장
    result = searcher.search_youtube("무한도전 오분순삭")

    # 검증
    assert result is not None
    assert result["video_id"] == "rA5Mt_XdoSQ"
    assert result["title"] == "[무한도전] 왔다 내 도파민🤑"
    assert result["channel_title"] == "오분순삭"
    assert result["url"] == "https://www.youtube.com/watch?v=rA5Mt_XdoSQ"


# [테스트 목적] 검색 결과가 없을 경우 예외 처리 검증
# [테스트 방식] API 검색 결과가 빈 배열(items: [])로 오도록 Mocking
# [테스트 동작]
#   1. 반환값 "items": [] Mocking
#   2. search_youtube 호출
#   3. 반환값이 None인지 assert
# [Input] 검색 쿼리 "세상에 존재하지 않는 영상 검색어 12345"
# [Output] None 반환
@patch("app.features.video.video_search.build")
def test_search_youtube_no_result(mock_build):
    mock_youtube = MagicMock()
    mock_build.return_value = mock_youtube
    mock_youtube.search().list().execute.return_value = {"items": []}

    searcher = VideoSearch()
    searcher.api_key = "valid_dummy_key"
    result = searcher.search_youtube("세상에 존재하지 않는 영상 검색어 12345")

    assert result is None


# [테스트 목적] API 키 누락 시 사전 차단 로직 검증
# [테스트 방식] VideoSearch 객체의 api_key를 None으로 설정 후 호출
# [테스트 동작]
#   1. api_key를 강제로 None으로 초기화
#   2. search_youtube 호출 시 ValueError가 발생하는지 pytest.raises로 확인
# [Input] 검색 쿼리 "아무 검색어"
# [Output] ValueError ("서버 설정 오류...") 발생
def test_search_youtube_missing_api_key():
    searcher = VideoSearch()
    searcher.api_key = None  # API 키가 없다고 가정

    with pytest.raises(ValueError, match="서버 설정 오류: 영상 검색 과정에서 YOUTUBE_API_KEY가 없습니다."):
        searcher.search_youtube("아무 검색어")


# [테스트 목적] YouTube API 통신 중 HTTP 에러 발생 시 예외 처리 검증
# [테스트 방식] execute() 호출 시 HttpError가 발생하도록 side_effect 설정
# [테스트 동작]
#   1. HttpError(403 Forbidden 등) 발생 Mocking
#   2. search_youtube 호출 시 RuntimeError로 래핑되어 발생하는지 확인
# [Input] 검색 쿼리 "에러나는 검색어"
# [Output] RuntimeError ("...HTTP 오류...") 발생
@patch("app.features.video.video_search.build")
def test_search_youtube_http_error(mock_build):
    mock_youtube = MagicMock()
    mock_build.return_value = mock_youtube
    
    # HttpError Mocking (httplib2.Response 필요)
    resp = Response({"status": 403})
    error = HttpError(resp=resp, content=b"Forbidden")
    mock_youtube.search().list().execute.side_effect = error

    searcher = VideoSearch()
    searcher.api_key = "valid_dummy_key"

    with pytest.raises(RuntimeError, match="영상 검색 Youtube API 호출 중 HTTP 오류"):
        searcher.search_youtube("에러나는 검색어")


# [테스트 목적] 알 수 없는 예외(Exception) 발생 시 예외 처리 검증
# [테스트 방식] execute() 호출 시 일반 Exception이 발생하도록 side_effect 설정
# [테스트 동작]
#   1. Exception("Unknown network error") 발생 Mocking
#   2. search_youtube 호출 시 RuntimeError로 래핑되어 발생하는지 확인
# [Input] 검색 쿼리 "알 수 없는 에러 검색어"
# [Output] RuntimeError ("...알 수 없는 오류...") 발생
@patch("app.features.video.video_search.build")
def test_search_youtube_general_exception(mock_build):
    mock_youtube = MagicMock()
    mock_build.return_value = mock_youtube
    
    # 일반 Exception 발생
    mock_youtube.search().list().execute.side_effect = Exception("Unknown network error")

    searcher = VideoSearch()
    searcher.api_key = "valid_dummy_key"

    with pytest.raises(RuntimeError, match="영상 검색 중 알 수 없는 오류: Unknown network error"):
        searcher.search_youtube("알 수 없는 에러 검색어")