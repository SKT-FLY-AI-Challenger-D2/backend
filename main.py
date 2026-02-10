import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
#from app.features.video.video_router import router as video_router
from app.core.database import engine, Base

# 각 기능별 모델 임포트
import app.features.user.user_model
import app.features.video.video_model
import app.features.report.report_model
import app.features.complaint.complaint_model

# 각 기능별 라우터 임포트
from app.features.user.user_router import router as user_router
from app.features.video.video_router import router as video_router
from app.features.report.report_router import router as report_router
from app.features.complaint.complaint_router import router as complaint_router

# 수명주기(Lifespan) 관리: 앱 시작/종료 시 실행될 로직
@asynccontextmanager
async def lifespan(app: FastAPI):
    # [Startup] 앱이 켜질 때 DB 테이블 생성
    print("[Startup] Checking & Creating DB Tables...")

    Base.metadata.create_all(bind=engine)
    
    # 서버 시작
    yield

    # 서버 종료
    # [Shutdown] 앱이 꺼질 때 (필요시 리소스 정리)
    print("[Shutdown] Server is shutting down...")

def create_app() -> FastAPI:
    
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description="유튜브 영상의 자막을 분석하여 사기/스팸 여부를 판별합니다.",
        version=settings.VERSION,
        lifespan=lifespan
    )

    # 미들웨어 설정
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 라우터 등록
    # app.include_router(video_router)
    app.include_router(user_router, prefix="/api/v1/users", tags=["User"])
    app.include_router(video_router, prefix="/api/v1/videos", tags=["Video"])
    app.include_router(report_router, prefix="/api/v1/reports", tags=["Report"])
    app.include_router(complaint_router, prefix="/api/v1/complaints", tags=["Complaint"])

    # 헬스 체크
    @app.get("/")
    def health_check():
        return {"status": "ok", "message": "Server is running"}

    return app

app = create_app()

if __name__ == "__main__":
    # 로컬 개발용 실행 설정
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)