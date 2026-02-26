from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv("DB_URL")

# pymysql을 사용하여 MySQL 연결
engine = create_engine(
    DB_URL,
    pool_recycle=1800,        # 30분마다 연결 재생성 (MySQL wait_timeout보다 짧게)
    pool_pre_ping=True,       # 쿼리 전 연결 유효성 자동 확인
    )
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency Injection용 함수
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()