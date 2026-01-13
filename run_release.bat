@echo off
chcp 65001 >nul
echo ========================================
echo   AutoBidGen 실행
echo ========================================
echo.

cd /d %~dp0

if exist "dist\AutoBidGen\AutoBidGen.exe" (
    echo AutoBidGen을 시작합니다...
    echo.
    echo 브라우저가 자동으로 열립니다.
    echo 종료하려면 이 창을 닫으세요.
    echo.
    start "" "dist\AutoBidGen\AutoBidGen.exe"
) else (
    echo [오류] AutoBidGen.exe를 찾을 수 없습니다.
    echo.
    echo 먼저 build_release.bat을 실행하여 빌드하세요.
    echo.
    pause
)
