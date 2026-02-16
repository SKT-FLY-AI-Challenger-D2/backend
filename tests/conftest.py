# tests/conftest.py
# 모든 테스트 파일이 공유하는 설정 파일
# pytest를 실행하면 자동으로 이 파일을 읽어서 테스트 환경을 구성함

# 현재 역할
# 1. 테스트용 인메모리 DB를 생성하고 관리
# 2. 테스트 전에 테이블 생성, 테스트 후에 테이블 삭제
# 3. 테스트 함수가 실행될 때마다 새로운 DB 세션을 생성하고 반환

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from app.core.database import Base

# 모든 모델 import (어떤 테스트를 실행하든 전체 테이블이 올바른 순서로 생성되도록 보장)
import app.features.user.user_model
import app.features.video.video_model
import app.features.report.report_model
import app.features.complaint.complaint_model

# 1. 테스트용 인메모리 DB
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False},
    echo = True # 로그 출력용. 출력 안 할 거면 False로 변경
)

# SQLite에서 FK CASCADE 삭제를 동작시키기 위해 매 연결마다 PRAGMA foreign_keys=ON 활성화
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    # 2. 테이블 생성 (Create)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()

    # 테스트용 데이터 추가
    

    try:
        yield db
    finally:
        db.close()
        # 3. 테스트 끝나면 테이블 삭제 (Cleanup)
        Base.metadata.drop_all(bind=engine)