from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from app.core.config import settings

class VideoRepository:

    def __init__(self):
        self.api_key = settings.YOUTUBE_API_KEY

    def search_youtube(self, query: str) -> dict | None:
        """
        주어진 검색어를 바탕으로 YouTube API를 사용하여 영상을 검색
        
        Args:
            query (str): 검색어 (제목 + 채널명)
            
        Returns:
            dict: 검색된 영상 정보(영상 ID, 제목, 채널명, URL)
            None: 검색 실패, 또는 검색 결과가 없을 경우

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
                maxResults=1
            ).execute()

            items = search_response.get("items", [])
            if not items: # 검색된 내용이 없는 경우
                return None

            item = items[0]
            return {
                "video_id": item["id"]["videoId"],
                "title": item["snippet"]["title"],
                "channel_title": item["snippet"]["channelTitle"],
                "url": f"https://www.youtube.com/watch?v={item['id']['videoId']}"
            }

        except HttpError as e:
            raise RuntimeError(f"영상 검색 Youtube API 호출 중 HTTP 오류: {e}")
        except Exception as e:
            raise RuntimeError(f"영상 검색 중 알 수 없는 오류: {e}")