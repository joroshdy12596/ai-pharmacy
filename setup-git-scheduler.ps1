# Setup Windows Task Scheduler for Daily Git Commits
# Run this script as Administrator to create the scheduled task

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "ERROR: This script must be run as Administrator!" -ForegroundColor Red
    Write-Host "Right-click PowerShell and select 'Run as administrator'" -ForegroundColor Yellow
    exit 1
}

$TaskName = "AI-Pharmacy Daily Git Commit"
$ScriptPath = "C:\Users\Dr.ESRAA\Desktop\ai-pharmacy\daily-git-commit.ps1"
$TaskTime = "23:00:00"  # 11 PM in 24-hour format
$TimeZone = "Egypt Standard Time"

Write-Host "Setting up Windows Task Scheduler..." -ForegroundColor Cyan

# Check if task already exists
$taskExists = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue

if ($taskExists) {
    Write-Host "Task already exists. Removing old task..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

# Create trigger (daily at 11 PM Egypt Time)
$trigger = New-ScheduledTaskTrigger `
    -Daily `
    -At $TaskTime `
    -TimeZone $TimeZone

# Create action (run PowerShell script)
$arg = "-NoProfile -ExecutionPolicy Bypass -File `"$ScriptPath`""
$action = New-ScheduledTaskAction `
    -Execute "PowerShell.exe" `
    -Argument $arg

# Create task settings
$settings = New-ScheduledTaskSettingsSet `
    -RunOnlyIfNetworkAvailable `
    -StartWhenAvailable `
    -MultipleInstances IgnoreNew

# Create the scheduled task
Register-ScheduledTask `
    -TaskName $TaskName `
    -Trigger $trigger `
    -Action $action `
    -Settings $settings `
    -Description "Automatically commits all changes and pushes to Git at 11 PM Egypt Time daily" `
    -Force

Write-Host "✓ Task created successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "Task Details:" -ForegroundColor Cyan
Write-Host "  Name: $TaskName" -ForegroundColor White
Write-Host "  Time: $TaskTime (Egypt Standard Time)" -ForegroundColor White
Write-Host "  Script: $ScriptPath" -ForegroundColor White
Write-Host "  Frequency: Daily" -ForegroundColor White
Write-Host ""
Write-Host "To manage this task:" -ForegroundColor Yellow
Write-Host "  1. Open 'Task Scheduler'" -ForegroundColor Gray
Write-Host "  2. Navigate to Task Scheduler Library" -ForegroundColor Gray
Write-Host "  3. Search for: AI-Pharmacy Daily Git Commit" -ForegroundColor Gray
Write-Host ""
Write-Host "To run the task manually for testing:" -ForegroundColor Yellow
$msg = "  powershell -NoProfile -ExecutionPolicy Bypass -File $ScriptPath"
Write-Host $msg -ForegroundColor Gray

exit 0
