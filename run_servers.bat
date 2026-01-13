@echo off
chcp 65001 >nul
echo ========================================
echo   Auto-Bid-Gen 서버 시작
echo ========================================
echo.

REM 백엔드 서버 시작 (포트 8000)
echo [1/3] 백엔드 서버 시작 중... (포트 8000)
start "Backend Server" cmd /k "cd /d %~dp0 && python server.py"

REM 잠시 대기 (백엔드 서버 초기화 시간)
timeout /t 3 /nobreak >nul

REM 프론트엔드 서버 시작 (포트 3000)
echo [2/3] 프론트엔드 서버 시작 중... (포트 3000)
start "Frontend Server" cmd /k "cd /d %~dp0frontend && npm run dev"

REM 잠시 대기 (프론트엔드 서버 초기화 시간)
echo [3/3] 서버 초기화 대기 중...
timeout /t 5 /nobreak >nul

REM 브라우저에서 localhost:3000 열기
echo.
echo ========================================
echo   브라우저 열기: http://localhost:3000
echo ========================================
start http://localhost:3000

echo.
echo 완료! 서버가 실행 중입니다.
echo.
echo - 백엔드: http://localhost:8000
echo - 프론트엔드: http://localhost:3000
echo.
echo 서버를 종료하려면 각 터미널 창을 닫으세요.
echo.
pause
