# Hourly Git Data Pull Script (deployment side)
# Runs every hour via Windows Task Scheduler on the machine hosting the
# deployed app (NOT the pharmacy PC).
#
# Fetches from GitHub and, if db.sqlite3 changed on origin/main, checks out
# ONLY that one file into the working tree. This deliberately does NOT run
# `git pull` / `git merge` - app code here is never touched or overwritten
# by whatever is on GitHub, only the data file is refreshed.
#
# Because docker-compose.yml bind-mounts this directory into the `web`
# container (".:/app"), overwriting db.sqlite3 here is immediately visible
# to the running app - no container restart needed (Django opens a fresh
# SQLite connection per request by default).

Set-Location "C:\Users\Mahmoud\ai-pharmacy"

Write-Host "[$(Get-Date)] Checking for new data on GitHub..." -ForegroundColor Green

try {
    git fetch origin main

    $remoteHash = git rev-parse origin/main:db.sqlite3
    $localHash = git hash-object db.sqlite3

    if ($remoteHash -ne $localHash) {
        Write-Host "[$(Get-Date)] New data found (local $localHash -> remote $remoteHash). Updating db.sqlite3 only..." -ForegroundColor Yellow
        git checkout origin/main -- db.sqlite3
        Write-Host "[$(Get-Date)] db.sqlite3 updated from GitHub." -ForegroundColor Green
    } else {
        Write-Host "[$(Get-Date)] No new data (hash unchanged). Nothing to do." -ForegroundColor Cyan
    }
} catch {
    Write-Host "[$(Get-Date)] Error occurred: $_" -ForegroundColor Red
    exit 1
}

exit 0
