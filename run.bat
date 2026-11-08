@echo off
chcp 65001 > nul
title YouTube Video Downloader

echo ========================================================
echo       YouTube Video Downloader (유튜브 영상 다운로더)
echo ========================================================
echo.

:: Python 경로 탐색
set "PYTHON_EXE="

if exist "C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe" (
    set "PYTHON_EXE=C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe"
) else (
    where python >nul 2>nul
    if %ERRORLEVEL% equ 0 (
        set "PYTHON_EXE=python"
    )
)

if "%PYTHON_EXE%"=="" (
    echo [오류] Python 실행 파일을 찾을 수 없습니다.
    echo Python 3.10 이상이 설치되어 있는지 확인해주세요.
    pause
    exit /b 1
)

echo [1/2] 서비스 실행 중... (http://127.0.0.1:5000)
echo.

:: 기본 브라우저 열기 (1초 대기 후)
start "" cmd /c "timeout /t 2 >nul & start http://127.0.0.1:5000"

:: FastAPI 서버 실행
"%PYTHON_EXE%" -m uvicorn app:app --host 127.0.0.1 --port 5000
pause
