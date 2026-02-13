@echo off
chcp 65001
echo ==============================================
echo  🕸️ 동료평가 제도 진단 대시보드 v2.0
echo ==============================================

echo.
echo [1/2] 기존 서버 종료 중...
taskkill /F /IM uvicorn.exe >nul 2>&1

echo [2/2] 새 서버 시작...
start "Network Analyzer Server" /D "backend" uvicorn main:app --reload --port 8000

echo.
echo ⏳ 서버 초기화 대기 중 (5초)...
timeout /t 5 >nul

echo.
echo 🌐 브라우저 실행!
start http://localhost:8000

echo.
echo ==============================================
echo  ✅ 실행 완료!
echo  이제 브라우저에서 분석을 시작하세요.
echo ==============================================
pause
