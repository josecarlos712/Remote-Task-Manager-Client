# Arrange RTM server (left) and client (right) on the secondary monitor, 50/50.
# (User has cables swapped: the desired display is the non-primary screen.)
# Matches console titles set by start_*.bat (RTM-SERVER / RTM-CLIENT) or legacy titles.
param(
    [int]$WaitSeconds = 2
)

Add-Type @"
using System;
using System.Runtime.InteropServices;
public class RtmWin {
  [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
  [DllImport("user32.dll")] public static extern bool MoveWindow(IntPtr hWnd, int X, int Y, int nWidth, int nHeight, bool bRepaint);
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd);
  public const int SW_RESTORE = 9;
}
"@

function Get-TargetWorkArea {
    Add-Type -AssemblyName System.Windows.Forms
    $screens = [System.Windows.Forms.Screen]::AllScreens
    $secondary = $screens | Where-Object { -not $_.Primary } | Select-Object -First 1
    if ($null -eq $secondary) {
        $secondary = [System.Windows.Forms.Screen]::PrimaryScreen
    }
    return $secondary.WorkingArea
}

function Find-ConsoleHwnd([string[]]$TitlePatterns) {
    $procs = Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowHandle -ne [IntPtr]::Zero }
    foreach ($p in $procs) {
        $title = $p.MainWindowTitle
        if ([string]::IsNullOrWhiteSpace($title)) { continue }
        foreach ($pat in $TitlePatterns) {
            if ($title -like $pat) {
                return $p.MainWindowHandle
            }
        }
    }
    return [IntPtr]::Zero
}

function Place-Window([IntPtr]$Hwnd, [int]$X, [int]$Y, [int]$W, [int]$H) {
    if ($Hwnd -eq [IntPtr]::Zero) { return $false }
    [void][RtmWin]::ShowWindow($Hwnd, [RtmWin]::SW_RESTORE)
    [void][RtmWin]::MoveWindow($Hwnd, $X, $Y, $W, $H, $true)
    return $true
}

Start-Sleep -Seconds $WaitSeconds
$wa = Get-TargetWorkArea
$half = [int]([math]::Floor($wa.Width / 2))
$leftW = $half
$rightW = $wa.Width - $half
$xLeft = $wa.X
$xRight = $wa.X + $leftW
$y = $wa.Y
$h = $wa.Height
Write-Output ("Target monitor work area: X={0} Y={1} W={2} H={3}" -f $wa.X, $wa.Y, $wa.Width, $wa.Height)

$serverHwnd = Find-ConsoleHwnd @(
    '*RTM-SERVER*',
    '*start_server_https*',
    '*start_server.bat*',
    '*runsslserver*',
    '*manage.py*'
)
$clientHwnd = Find-ConsoleHwnd @(
    '*RTM-CLIENT*',
    '*start_client.bat*',
    '*Remote Task Manager Client*'
)

$okS = Place-Window $serverHwnd $xLeft $y $leftW $h
$okC = Place-Window $clientHwnd $xRight $y $rightW $h

if ($okS) { Write-Output "Server window -> left half" } else { Write-Output "Server window not found" }
if ($okC) { Write-Output "Client window -> right half" } else { Write-Output "Client window not found" }
