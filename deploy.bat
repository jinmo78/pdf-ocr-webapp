@echo off
chcp 65001 >nul
echo === GitHub + Render 배포 ===
echo.
echo 1단계: GitHub 로그인 (브라우저가 열립니다)
powershell -NoProfile -ExecutionPolicy Bypass -Command "$env:Path = [System.Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [System.Environment]::GetEnvironmentVariable('Path','User'); gh auth login -h github.com -p https -w"
if errorlevel 1 (
    echo GitHub 로그인 실패. 수동 배포 안내를 deploy.ps1 실행 후 확인하세요.
    pause
    exit /b 1
)
echo.
echo 2단계: deploy.ps1 실행
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0deploy.ps1"
pause
