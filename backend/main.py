"""
main.py — FastAPI 서버 진입점

실행 방법:
    uvicorn main:app --reload --port 8000

핵심 설계 결정:
  - startup 이벤트에서 데이터를 미리 로드하여 첫 요청 지연을 방지합니다.
  - CORS를 허용하여 프론트엔드(localhost:3000)에서 API를 호출할 수 있게 합니다.
  - /frontend 경로에서 정적 파일(HTML/JS/CSS)을 서빙하여 별도 서버 없이도 동작합니다.
"""
import sys
import os

# backend 디렉토리를 모듈 검색 경로에 추가
sys.path.insert(0, os.path.dirname(__file__))

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from routers.network import router as network_router
from services.data_loader import preload_all_data
from config import FRONTEND_DIR


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    서버 시작/종료 시 실행되는 생명주기 관리자.
    
    Why: 서버 시작 시 엑셀 데이터를 미리 로드하여 캐싱합니다.
         이렇게 하면 첫 번째 API 요청도 빠르게 응답할 수 있습니다.
    """
    # Startup: 데이터 사전 로딩
    preload_all_data()
    yield
    # Shutdown: 정리 작업 (필요 시)
    print("[INFO] 서버 종료")


app = FastAPI(
    title="동료평가 네트워크 분석 API",
    description="조직 내 평가 관계를 네트워크로 시각화하고 분석합니다.",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS 설정 — 프론트엔드에서 API를 호출할 수 있도록 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 개발 환경에서는 전체 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 라우터 등록
app.include_router(network_router)

# 프론트엔드 정적 파일 서빙
# Why: index.html에서 'css/style.css', 'js/app.js'로 접근하므로 
#      해당 경로들을 명시적으로 마운트해줍니다.
if os.path.exists(FRONTEND_DIR):
    # 1. CSS/JS 폴더 직접 마운트 (루트 상대 경로 지원)
    app.mount("/css", StaticFiles(directory=os.path.join(FRONTEND_DIR, "css")), name="css")
    app.mount("/js", StaticFiles(directory=os.path.join(FRONTEND_DIR, "js")), name="js")
    
    # 2. /static 경로도 유지 (혹시 모를 명시적 접근용)
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="frontend")

    @app.get("/")
    async def serve_frontend():
        """프론트엔드 메인 페이지를 서빙합니다."""
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))
