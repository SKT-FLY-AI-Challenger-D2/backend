import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.features.video.video_router import router as video_router

def create_app() -> FastAPI: # FastAPI 앱 생성
    
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description="유튜브 영상의 자막을 분석하여 사기/스팸 여부를 판별합니다.",
        version=settings.VERSION
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
    app.include_router(video_router) 

    # 헬스 체크
    @app.get("/")
    def health_check():
        return {"status": "ok", "message": "Server is running"}

    return app

app = create_app()

if __name__ == "__main__":
    # 로컬 개발용 실행 설정
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)