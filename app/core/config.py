import os
from dotenv import load_dotenv

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

settings = Settings()