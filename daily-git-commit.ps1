param(
    [switch]$SkipPush
)

$repoPath = "C:\Users\Dr.ESRAA\Desktop\ai-pharmacy"
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

Set-Location $repoPath
Write-Host "[$timestamp] Starting Git auto-push..." -ForegroundColor Green

try {
    git rev-parse --is-inside-work-tree | Out-Null
} catch {
    Write-Host "Repository not found at $repoPath" -ForegroundColor Red
    exit 1
}

# Configure identity so commits can be created automatically.
git config user.name "joroshdy12596" | Out-Null
git config user.email "joroshdy12596@gmail.com" | Out-Null

$branch = git branch --show-current 2>$null
if ($LASTEXITCODE -eq 0 -and $branch) {
    Write-Host "Running: git pull --rebase origin $branch" -ForegroundColor Yellow
    git pull --rebase origin $branch
} else {
    Write-Host "Running: git pull --rebase origin HEAD" -ForegroundColor Yellow
    git pull --rebase origin HEAD
}

Write-Host "Running: git add -A" -ForegroundColor Yellow
git add -A

$stagedFiles = git diff --cached --name-only
if (-not $stagedFiles) {
    Write-Host "No changes detected. Nothing to commit." -ForegroundColor Yellow
    exit 0
}

$commitMessage = "Auto commit $timestamp"
Write-Host "Running: git commit -m '$commitMessage'" -ForegroundColor Yellow
git commit -m $commitMessage

if ($SkipPush) {
    Write-Host "Skipping push because -SkipPush was supplied." -ForegroundColor Yellow
    exit 0
}

$remoteUrl = git remote get-url origin 2>$null
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($remoteUrl)) {
    Write-Host "No GitHub remote was found for origin." -ForegroundColor Red
    exit 1
}

Write-Host "Running: git push origin HEAD" -ForegroundColor Yellow
git push origin HEAD

Write-Host "[$(Get-Date)] Git auto-push completed successfully." -ForegroundColor Green
exit 0
