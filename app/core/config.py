import os
from dotenv import load_dotenv
import itertools

# .env 파일 로드
load_dotenv()

class Settings:
    PROJECT_NAME: str = "SKT FLY AI Final Project"
    VERSION: str = "1.0.0"
    
    # .env에 있는 DB_URL을 가져옵니다.
    # 실제 자격증명을 기본값으로 두지 않는다. 없으면 None이며, DB 접근 시점에
    # database.py가 명확한 오류로 알려준다 (TASK-04, FR-10).
    DB_URL: str | None = os.getenv("DB_URL")

    # AI 서버 주소. 로컬 실행/Compose 등 실행 환경에 따라 값만 바꾸면 된다 (TASK-04, FR-06).
    AI_BASE_URL: str = os.getenv("AI_BASE_URL", "http://127.0.0.1:8001")

    YOUTUBE_API_KEYS = []#= [os.getenv(f"YOUTUBE_API_KEY{i}") for i in range(10)]
    for i in range(10):
        key = os.getenv(f"YOUTUBE_API_KEY{i}", "")
        if key != "":
            YOUTUBE_API_KEYS.append(key)

    youtube_api_key_cycle = itertools.cycle(YOUTUBE_API_KEYS)

    def get_next_youtube_api_key(self) -> str:
        """다음 순서의 API 키를 반환합니다."""
        key = self.youtube_api_key_cycle
        print(f"[Config] Youtube Key 바꿈: {key}")
        return next(key)



settings = Settings()
