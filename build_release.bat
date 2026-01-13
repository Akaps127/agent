@echo off
chcp 65001 >nul
echo ========================================
echo   AutoBidGen Release 빌드
echo ========================================
echo.

REM 가상환경 활성화
echo [1/5] 가상환경 확인 중...
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    echo       가상환경 활성화됨
) else (
    echo       가상환경이 없습니다. 시스템 Python 사용
)

REM PyInstaller 설치 확인
echo.
echo [2/5] PyInstaller 확인 중...
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo       PyInstaller 설치 중...
    pip install pyinstaller
) else (
    echo       PyInstaller 이미 설치됨
)

REM 프론트엔드 빌드
echo.
echo [3/5] 프론트엔드 빌드 중...
cd frontend
if not exist "node_modules" (
    echo       npm install 실행 중...
    call npm install
)
echo       npm run build 실행 중...
call npm run build
cd ..

REM 기존 dist 폴더 정리
echo.
echo [4/5] 이전 빌드 정리 중...
if exist "dist\AutoBidGen" rmdir /s /q "dist\AutoBidGen"

REM PyInstaller 빌드
echo.
echo [5/5] PyInstaller 빌드 실행 중...
echo       (이 작업은 몇 분 걸릴 수 있습니다)
pyinstaller AutoBidGen.spec --clean

echo.
echo ========================================
echo   빌드 완료!
echo ========================================
echo.
echo 결과물 위치: dist\AutoBidGen\
echo 실행 파일: dist\AutoBidGen\AutoBidGen.exe
echo.
echo [중요] 배포 시 함께 복사할 파일:
echo   1. dist\AutoBidGen\ 폴더 전체
echo   2. .env 파일 (API 키 포함)
echo.
echo .env 파일을 AutoBidGen.exe와 같은 폴더에 넣어주세요.
echo.
pause
