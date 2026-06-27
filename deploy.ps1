# GitHub + Render 배포 스크립트
# 실행: powershell -ExecutionPolicy Bypass -File .\deploy.ps1

$RepoName = "pdf-ocr-webapp"

# PATH에 gh 추가
$env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")

Write-Host "=== 1. GitHub 로그인 확인 ===" -ForegroundColor Cyan
$null = gh auth status 2>&1
$loggedIn = ($LASTEXITCODE -eq 0)

if (-not $loggedIn) {
    Write-Host "GitHub에 로그인되어 있지 않습니다. 브라우저에서 로그인을 완료하세요." -ForegroundColor Yellow
    gh auth login -h github.com -p https -w
    if ($LASTEXITCODE -ne 0) {
        Write-Host "`nGitHub 로그인에 실패했습니다. 아래 수동 방법을 사용하세요:" -ForegroundColor Red
        Write-Host @"

1. https://github.com/new 에서 저장소 이름 '$RepoName' 생성 (Public)
2. 아래 명령 실행 (YOUR_USERNAME을 본인 GitHub 아이디로 변경):

   git remote add origin https://github.com/YOUR_USERNAME/$RepoName.git
   git push -u origin main

3. https://dashboard.render.com/blueprints 에서 Blueprint 연결

"@ -ForegroundColor Yellow
        exit 1
    }
}

Write-Host "`n=== 2. GitHub 저장소 생성 및 Push ===" -ForegroundColor Cyan
$existingRemote = git remote get-url origin 2>$null
if (-not $existingRemote) {
    gh repo create $RepoName --public --source=. --remote=origin --push
    if ($LASTEXITCODE -ne 0) {
        Write-Host "저장소 생성 실패. GitHub에 같은 이름 저장소가 이미 있는지 확인하세요." -ForegroundColor Red
        exit 1
    }
} else {
    git push -u origin main
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Push 실패. git remote -v 와 GitHub 로그인 상태를 확인하세요." -ForegroundColor Red
        exit 1
    }
}

$repoUrl = gh repo view --json url -q .url 2>$null
if ($repoUrl) {
    Write-Host "`nGitHub 저장소: $repoUrl" -ForegroundColor Green
}

Write-Host "`n=== 3. Render 배포 ===" -ForegroundColor Cyan
Write-Host @"

Render 대시보드에서 Blueprint를 연결하세요:

1. https://dashboard.render.com/blueprints 접속
2. 'New Blueprint Instance' 클릭
3. GitHub 저장소 '$RepoName' 선택
4. render.yaml 확인 후 'Apply'

배포 완료 후:
- FastAPI: https://pdf-ocr-api.onrender.com
- Streamlit: https://pdf-ocr-app.onrender.com

OCR 메모리 부족 시 pdf-ocr-api Instance Type을 Starter(2GB)로 올리세요.

"@ -ForegroundColor Yellow

Start-Process "https://dashboard.render.com/blueprints"
