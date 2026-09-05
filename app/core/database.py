from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

Base = declarative_base()

_MISSING_DB_URL_MESSAGE = (
    "DB_URL 환경변수가 설정되지 않아 DB 기능을 사용할 수 없습니다. "
    ".env 또는 배포 환경 변수에 DB_URL을 지정하세요."
)


class _MissingDBUrlEngine:
    """DB_URL이 없을 때 engine 자리를 대신하는 placeholder (TASK-04).

    import 시점에는 DB_URL 유무와 관계없이 항상 성공해야 하므로(FR-10),
    실제 create_engine 호출을 미루고 이 객체를 대신 둔다. 이후 누군가
    (예: main.py의 Base.metadata.create_all) 이 객체를 실제 엔진처럼
    사용하려는 순간(속성 접근)에만 명확한 오류를 낸다.
    """

    def __getattr__(self, name):
        raise RuntimeError(_MISSING_DB_URL_MESSAGE)


def _build_engine():
    if not settings.DB_URL:
        return _MissingDBUrlEngine()
    # pymysql을 사용하여 MySQL 연결
    return create_engine(
        settings.DB_URL,
        pool_recycle=1800,   # 30분마다 연결 재생성 (MySQL wait_timeout보다 짧게)
        pool_pre_ping=True,  # 쿼리 전 연결 유효성 자동 확인
    )


engine = _build_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Dependency Injection용 함수
def get_db():
    if not settings.DB_URL:
        raise RuntimeError(_MISSING_DB_URL_MESSAGE)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
