import os
from dotenv import load_dotenv
import itertools

# .env 파일 로드
load_dotenv()

class Settings:
    PROJECT_NAME: str = "SKT FLY AI Final Project"
    VERSION: str = "1.0.0"
    
    # .env에 있는 DB_URL을 가져옵니다. 
    # 만약 못 가져오면 뒤에 있는 기본값을 사용합니다.
    DB_URL: str = os.getenv(
        "DB_URL", 
        "mysql+pymysql://root:1234@localhost:3306/skt_fly_ai_final_project"
    )

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
