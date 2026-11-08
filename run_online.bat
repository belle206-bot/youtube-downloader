@echo off
chcp 65001 > nul
title YouTube Video Downloader - 온라인 서비스

echo ========================================================
echo       YouTube Video Downloader (온라인 외부 접속)
echo ========================================================
echo.

:: Python 실행 파일 감지
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
    pause
    exit /b 1
)

:: 온라인 실행 파이썬 스크립트 구동
"%PYTHON_EXE%" run_online.py
pause
