@echo off
chcp 65001
echo ==============================================
echo  🕸️ 동료평가 네트워크 분석기 실행
echo ==============================================

echo [1/2] 백엔드 서버를 시작합니다...
echo (새 창에서 서버가 실행됩니다. 종료하려면 해당 창을 닫으세요.)
start "Network Analyzer Server" /D "backend" uvicorn main:app --reload --port 8000

echo.
echo [2/2] 서버 초기화를 기다립니다 (5초)...
timeout /t 5 >nul

echo.
echo 🌐 브라우저를 엽니다...
start http://localhost:8000

echo.
echo ==============================================
echo  ✅ 실행 완료!
echo  - 대시보드: http://localhost:8000
echo  - API 문서: http://localhost:8000/docs
echo ==============================================
pause
