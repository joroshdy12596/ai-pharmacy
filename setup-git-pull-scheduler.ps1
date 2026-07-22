# Setup Windows Task Scheduler for Hourly Git Data Pull (deployment side)
# Run this script as Administrator to create the scheduled task

$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "ERROR: This script must be run as Administrator!" -ForegroundColor Red
    Write-Host "Right-click PowerShell and select 'Run as administrator'" -ForegroundColor Yellow
    exit 1
}

$TaskName = "AI-Pharmacy Hourly Git Pull"
$ScriptPath = "C:\Users\Mahmoud\ai-pharmacy\hourly-git-pull.ps1"

Write-Host "Setting up Windows Task Scheduler..." -ForegroundColor Cyan

$taskExists = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue

if ($taskExists) {
    Write-Host "Task already exists. Removing old task..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

# Start at the next top of hour, repeat every 1 hour, indefinitely.
# Offset by 10 minutes from the push schedule so the pull always runs
# after that hour's push has had time to land on GitHub.
$startTime = (Get-Date).Date.AddHours((Get-Date).Hour + 1).AddMinutes(10)
$trigger = New-ScheduledTaskTrigger -Once -At $startTime `
    -RepetitionInterval (New-TimeSpan -Hours 1) `
    -RepetitionDuration ([TimeSpan]::MaxValue)

$arg = "-NoProfile -ExecutionPolicy Bypass -File `"$ScriptPath`""
$action = New-ScheduledTaskAction `
    -Execute "PowerShell.exe" `
    -Argument $arg

$settings = New-ScheduledTaskSettingsSet `
    -RunOnlyIfNetworkAvailable `
    -StartWhenAvailable `
    -MultipleInstances IgnoreNew

Register-ScheduledTask `
    -TaskName $TaskName `
    -Trigger $trigger `
    -Action $action `
    -Settings $settings `
    -Description "Fetches db.sqlite3 from GitHub every hour, if changed, without touching app code" `
    -Force

Write-Host "Task created successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "Task Details:" -ForegroundColor Cyan
Write-Host "  Name: $TaskName" -ForegroundColor White
Write-Host "  Frequency: Every 1 hour, starting $startTime" -ForegroundColor White
Write-Host "  Script: $ScriptPath" -ForegroundColor White
Write-Host ""
Write-Host "To run the task manually for testing:" -ForegroundColor Yellow
$msg = "  powershell -NoProfile -ExecutionPolicy Bypass -File $ScriptPath"
Write-Host $msg -ForegroundColor Gray

exit 0
