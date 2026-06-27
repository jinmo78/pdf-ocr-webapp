# GitHub + Render 배포 스크립트
# PowerShell에서 이 폴더로 이동한 뒤 실행: .\deploy.ps1

$ErrorActionPreference = "Stop"
$RepoName = "pdf-ocr-webapp"

# PATH에 gh 추가
$env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")

Write-Host "=== 1. GitHub 로그인 확인 ===" -ForegroundColor Cyan
$authStatus = gh auth status 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "GitHub에 로그인되어 있지 않습니다. 브라우저에서 로그인을 완료하세요." -ForegroundColor Yellow
    gh auth login -h github.com -p https -w
}

Write-Host "`n=== 2. GitHub 저장소 생성 및 Push ===" -ForegroundColor Cyan
$existingRemote = git remote get-url origin 2>$null
if (-not $existingRemote) {
    gh repo create $RepoName --public --source=. --remote=origin --push
} else {
    git push -u origin main
}

$repoUrl = gh repo view --json url -q .url
Write-Host "`nGitHub 저장소: $repoUrl" -ForegroundColor Green

Write-Host "`n=== 3. Render 배포 ===" -ForegroundColor Cyan
Write-Host @"

Render 대시보드에서 Blueprint를 연결하세요:

1. https://dashboard.render.com/blueprints 접속
2. 'New Blueprint Instance' 클릭
3. 방금 만든 GitHub 저장소($RepoName) 선택
4. render.yaml 자동 인식 확인 후 'Apply'

배포 완료 후:
- FastAPI: https://pdf-ocr-api.onrender.com
- Streamlit: https://pdf-ocr-app.onrender.com

참고: FastAPI는 EasyOCR 때문에 Starter 플랜(유료)으로 설정되어 있습니다.
무료로 테스트하려면 render.yaml에서 pdf-ocr-api의 plan을 free로 변경하세요.

"@ -ForegroundColor Yellow

Start-Process "https://dashboard.render.com/blueprints"
