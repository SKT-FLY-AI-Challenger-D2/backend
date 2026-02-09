import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    """
    프로젝트 설정, 키 설정
    """
    PROJECT_NAME: str = "YouTube Scam Detector API"
    VERSION: str = "1.0.0"
    YOUTUBE_API_KEY: str = os.getenv("YOUTUBE_API_KEY", "")
    
    # [TODO]: llm API 키 추가
    # [TODO]: DB 설정 추가

settings = Settings()