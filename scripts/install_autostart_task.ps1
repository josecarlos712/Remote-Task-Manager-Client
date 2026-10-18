# Creates a Windows Scheduled Task to start the client at user logon.
# Run in PowerShell: powershell -ExecutionPolicy Bypass -File scripts\install_autostart_task.ps1

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$python = (Get-Command python).Source
$main = Join-Path $root "main.py"
$taskName = "RemoteTaskManagerClient"

$action = New-ScheduledTaskAction -Execute $python -Argument "`"$main`"" -WorkingDirectory $root
$trigger = New-ScheduledTaskTrigger -AtLogOn
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Force | Out-Null
Write-Host "Scheduled task '$taskName' registered. It will start the client at logon."
