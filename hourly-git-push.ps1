# Hourly Git Data Push Script
# Runs every hour via Windows Task Scheduler
# Pushes ONLY the database file (db.sqlite3) to GitHub - never app code,
# so a deployed copy pulling this data can never accidentally pick up
# unreviewed code changes from this machine.

$egyptTz = [System.TimeZoneInfo]::FindSystemTimeZoneById("Egypt Standard Time")
$now = [System.TimeZoneInfo]::ConvertTime([datetime]::Now, $egyptTz)
$commitDate = $now.ToString("dddd, MMMM dd, yyyy HH:mm:ss")

Set-Location "C:\Users\Dr.ESRAA\Desktop\ai-pharmacy"

Write-Host "[$(Get-Date)] Starting hourly data push at $commitDate (Egypt Time)" -ForegroundColor Green

try {
    # Stage ONLY the database file - app code changes are never included
    Write-Host "Running: git add db.sqlite3" -ForegroundColor Yellow
    git add db.sqlite3

    # Commit with date message (no-op if the data hasn't changed)
    Write-Host "Running: git commit -m 'data: $commitDate'" -ForegroundColor Yellow
    git commit -m "data: $commitDate"

    # Push to remote
    Write-Host "Running: git push" -ForegroundColor Yellow
    git push

    Write-Host "[$(Get-Date)] Hourly data push completed successfully!" -ForegroundColor Green
} catch {
    Write-Host "[$(Get-Date)] Error occurred: $_" -ForegroundColor Red
    exit 1
}

exit 0
