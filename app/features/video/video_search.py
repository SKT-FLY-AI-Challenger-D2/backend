from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from app.core.config import settings

class VideoSearch:

    def __init__(self):
        self.api_key = settings.get_next_youtube_api_key()
        self.retry = False

    def search_youtube(self, query: str) -> dict | None:
        """
        주어진 검색어를 바탕으로 YouTube API를 사용하여 영상을 검색 (1건만).

        하위 호환용 래퍼 — search_youtube_candidates(query, max_results=1)의
        결과 중 첫 번째만 반환한다.

        Args:
            query (str): 검색어 (제목 + 채널명)

        Returns:
            dict: 검색된 영상 정보(영상 ID, 제목, 채널명, URL)
            None: 검색 실패, 또는 검색 결과가 없을 경우

        Raises:
            ValueError: YOUTUBE_API_KEY가 없는 경우
            RuntimeError: API 통신 중 오류 또는 기타 알 수 없는 오류
        """
        candidates = self.search_youtube_candidates(query, max_results=1)
        return candidates[0] if candidates else None

    def search_youtube_candidates(self, query: str, max_results: int = 5) -> list[dict]:
        """
        주어진 검색어로 YouTube API를 검색해 관련성 순 후보 여러 건을 반환한다.

        (개발 로그 참고) 기존엔 maxResults=1로 1건만 가져와서, 구독자 많은
        채널의 경우 검색 관련성 랭킹 1위가 사용자가 실제로 본 그 영상이
        아니라 채널의 다른 인기 영상으로 나오는 경우가 있었다(실사용자
        재현 사례: "지무비" 채널에서 "메이드 인 코리아 시즌2.." 로 검색했는데
        1위로 "취사병 전설이 되다.." 가 나옴). 여러 후보를 받아 호출부에서
        실제 매칭되는 것을 고르도록 바꿈.

        Args:
            query (str): 검색어 (제목 + 채널명)
            max_results (int): 가져올 후보 개수 (YouTube API 상한 50)

        Returns:
            list[dict]: 검색된 영상 정보 리스트(영상 ID, 제목, 채널명, URL), 없으면 빈 리스트

        Raises:
            ValueError: YOUTUBE_API_KEY가 없는 경우
            RuntimeError: API 통신 중 오류 또는 기타 알 수 없는 오류
        """
        if not self.api_key:
            raise ValueError("서버 설정 오류: 영상 검색 과정에서 YOUTUBE_API_KEY가 없습니다.")

        try:
            youtube = build("youtube", "v3", developerKey=self.api_key)

            # 검색 요청
            search_response = youtube.search().list(
                q=query,
                part="snippet",
                type="video",
                maxResults=max_results
            ).execute()

            self.retry = False

            items = search_response.get("items", [])

            return [
                {
                    "video_id": item["id"]["videoId"],
                    "title": item["snippet"]["title"],
                    "channel_title": item["snippet"]["channelTitle"],
                    "url": f"https://www.youtube.com/watch?v={item['id']['videoId']}"
                }
                for item in items
            ]

        except HttpError as e:
            print(f"[Video Search] 영상 검색 Youtube API 호출 중 HTTP 오류 재시도: {e}")
            self.api_key = settings.get_next_youtube_api_key()
            if not self.retry:
                self.retry = True
                return self.search_youtube_candidates(query, max_results=max_results)

            print(f"[Video Search] 영상 검색 Youtube API 호출 중 HTTP 오류: {e}")
            raise RuntimeError(f"영상 검색 Youtube API 호출 중 HTTP 오류: {e}")

        except Exception as e:
            print(f"[Video Search] 영상 검색 중 알 수 없는 오류: {e}")
            raise RuntimeError(f"영상 검색 중 알 수 없는 오류: {e}")
