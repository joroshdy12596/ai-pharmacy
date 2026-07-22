# Setup Windows Task Scheduler for the pending-prescription Telegram nag
# Run this script as Administrator to create the scheduled task

$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "ERROR: This script must be run as Administrator!" -ForegroundColor Red
    Write-Host "Right-click PowerShell and select 'Run as administrator'" -ForegroundColor Yellow
    exit 1
}

$TaskName = "AI-Pharmacy Prescription Reminder"
$ScriptPath = "C:\Users\Mahmoud\ai-pharmacy\remind-pending-prescriptions.ps1"

Write-Host "Setting up Windows Task Scheduler..." -ForegroundColor Cyan

$taskExists = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($taskExists) {
    Write-Host "Task already exists. Removing old task..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) `
    -RepetitionInterval (New-TimeSpan -Minutes 5) `
    -RepetitionDuration ([TimeSpan]::MaxValue)

$arg = "-NoProfile -ExecutionPolicy Bypass -File `"$ScriptPath`""
$action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument $arg

$settings = New-ScheduledTaskSettingsSet `
    -RunOnlyIfNetworkAvailable `
    -StartWhenAvailable `
    -MultipleInstances IgnoreNew

Register-ScheduledTask `
    -TaskName $TaskName `
    -Trigger $trigger `
    -Action $action `
    -Settings $settings `
    -Description "Resends a Telegram nag every 5 minutes for pending guest prescription requests" `
    -Force

Write-Host "Task created successfully! Runs every 5 minutes." -ForegroundColor Green
exit 0
