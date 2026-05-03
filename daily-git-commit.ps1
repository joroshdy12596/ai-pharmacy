# Daily Git Auto-Commit Script
# Runs every day at 11 PM Egypt Time
# Sets up automatic: git add . && git commit -m "date" && git push

# Get current date in Egypt timezone
$egyptTz = [System.TimeZoneInfo]::FindSystemTimeZoneById("Egypt Standard Time")
$now = [System.TimeZoneInfo]::ConvertTime([datetime]::Now, $egyptTz)
$commitDate = $now.ToString("dddd, MMMM dd, yyyy HH:mm:ss")

# Change to the repository directory
Set-Location "C:\Users\Dr.ESRAA\Desktop\ai-pharmacy"

# Run git commands
Write-Host "[$(Get-Date)] Starting daily git commit at $commitDate (Egypt Time)" -ForegroundColor Green

try {
    # Stage all changes
    Write-Host "Running: git add ." -ForegroundColor Yellow
    git add .
    
    # Commit with date message
    Write-Host "Running: git commit -m '$commitDate'" -ForegroundColor Yellow
    git commit -m "$commitDate"
    
    # Push to remote
    Write-Host "Running: git push" -ForegroundColor Yellow
    git push
    
    Write-Host "[$(Get-Date)] Daily git commit completed successfully!" -ForegroundColor Green
} catch {
    Write-Host "[$(Get-Date)] Error occurred: $_" -ForegroundColor Red
    exit 1
}

exit 0
