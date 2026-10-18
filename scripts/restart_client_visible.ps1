# Kill client on port 5000, start visible console, arrange RTM windows 50/50 on primary monitor.
param(
    [int]$Port = 5000,
    [string]$ClientRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
)

$ErrorActionPreference = 'SilentlyContinue'
$conns = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
if ($conns) {
    $conns | ForEach-Object {
        $procId = $_.OwningProcess
        Write-Output "Stopping PID $procId on port $Port"
        Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
    }
    Start-Sleep -Seconds 1
}

$bat = Join-Path $ClientRoot 'scripts\start_client.bat'
Start-Process -FilePath 'cmd.exe' -ArgumentList '/k', "`"$bat`"" -WorkingDirectory $ClientRoot
Write-Output "Started visible client console"

$arrange = Join-Path $PSScriptRoot 'arrange_rtm_consoles.ps1'
& $arrange -WaitSeconds 2
