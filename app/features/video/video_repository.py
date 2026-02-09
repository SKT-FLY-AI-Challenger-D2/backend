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
            dict | None: 검색된 영상 정보 또는 검색 결과(영상 ID, 제목, 채널명, URL) 또는 에러
        """
        if not self.api_key:
            return {"error": "서버 설정 오류: 영상 검색 과정에서 YOUTUBE_API_KEY가 없습니다."}

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
            if not items:
                return None

            item = items[0]
            return {
                "video_id": item["id"]["videoId"],
                "title": item["snippet"]["title"],
                "channel_title": item["snippet"]["channelTitle"],
                "url": f"https://www.youtube.com/watch?v={item['id']['videoId']}"
            }

        except HttpError as e:
            return {"error": f"http 오류: {e}"}
        except Exception as e:
            return {"error": f"검색 중 오류 발생: {e}"}