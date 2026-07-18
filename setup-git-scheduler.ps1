# Setup Windows Task Scheduler for Git Auto-Push every 30 minutes
# This uses the same Git credential flow as your VS Code terminal.

$TaskName = 'AI-Pharmacy Git Auto-Push'
$ScriptPath = 'C:\Users\Dr.ESRAA\Desktop\ai-pharmacy\daily-git-commit.ps1'

Write-Host 'Setting up Windows Task Scheduler...' -ForegroundColor Cyan

$taskExists = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($taskExists) {
    Write-Host 'Task already exists. Removing old task...' -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

$startAt = [DateTime]::Now.AddMinutes(5)
$trigger = New-ScheduledTaskTrigger -Once -At $startAt -RepetitionInterval (New-TimeSpan -Minutes 30) -RepetitionDuration (New-TimeSpan -Days 3650)
$scriptArgs = '-NoProfile -ExecutionPolicy Bypass -File "' + $ScriptPath + '"'
$action = New-ScheduledTaskAction -Execute 'PowerShell.exe' -Argument $scriptArgs
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -RunOnlyIfNetworkAvailable -StartWhenAvailable -MultipleInstances IgnoreNew

Register-ScheduledTask -TaskName $TaskName -Trigger $trigger -Action $action -Settings $settings -Description 'Automatically commits changes and pushes them to GitHub every 30 minutes' -Force

Write-Host '✓ Task created successfully!' -ForegroundColor Green
Write-Host ''
Write-Host 'Task Details:' -ForegroundColor Cyan
Write-Host ('  Name: ' + $TaskName) -ForegroundColor White
Write-Host ('  Script: ' + $ScriptPath) -ForegroundColor White
Write-Host '  Frequency: Every 30 minutes' -ForegroundColor White
Write-Host ''
Write-Host 'To manage this task:' -ForegroundColor Yellow
Write-Host '  1. Open Task Scheduler' -ForegroundColor Gray
Write-Host '  2. Navigate to Task Scheduler Library' -ForegroundColor Gray
Write-Host '  3. Search for: AI-Pharmacy Git Auto-Push' -ForegroundColor Gray

exit 0
