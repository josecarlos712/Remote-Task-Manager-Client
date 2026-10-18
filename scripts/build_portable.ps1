# Build a portable RTM Client folder under build/RTM-Client (does not stop running agents).
$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $Root

Write-Output "Installing PyInstaller if needed..."
python -m pip install --quiet "pyinstaller>=6.0"

$WorkDist = Join-Path $Root "build\_pyi_dist"
$WorkBuild = Join-Path $Root "build\_pyi_work"
$OutRoot = Join-Path $Root "build\RTM-Client"

if (Test-Path $WorkDist) { Remove-Item -Recurse -Force $WorkDist }
if (Test-Path $WorkBuild) { Remove-Item -Recurse -Force $WorkBuild }
if (Test-Path $OutRoot) { Remove-Item -Recurse -Force $OutRoot }

$hidden = @(
  "command_modules",
  "command_modules.download_file",
  "command_modules.execute_program",
  "command_modules.kill_program",
  "command_modules.list_processes",
  "command_modules.lock_workstation",
  "command_modules.open_url",
  "command_modules.screenshot",
  "command_modules.show_popup",
  "command_modules.shutdown",
  "command_modules.test_command",
  "endpoints",
  "endpoints.download_status",
  "endpoints.get_time",
  "endpoints.program_list",
  "endpoints.program_status",
  "endpoints.show_message_window",
  "endpoints.test",
  "endpoints.test_folder.endpoint",
  "PIL",
  "PIL.ImageGrab",
  "psutil",
  "waitress",
  "flask",
  "flask_cors",
  "requests"
)

$hiArgs = @()
foreach ($h in $hidden) { $hiArgs += @("--hidden-import", $h) }

$IconPath = Join-Path $Root "assets\app.ico"
$FixIco = Join-Path $Root "scripts\_fix_ico.py"
if (Test-Path $FixIco) {
  Write-Output "Preparing multi-size app.ico..."
  python $FixIco
}
if (-not (Test-Path $IconPath)) {
  throw "App icon not found: $IconPath"
}

Write-Output "Running PyInstaller..."
python -m PyInstaller `
  --noconfirm `
  --clean `
  --onedir `
  --console `
  --name "RemoteTaskManagerClient" `
  --icon $IconPath `
  --distpath $WorkDist `
  --workpath $WorkBuild `
  --specpath (Join-Path $Root "build") `
  --paths $Root `
  --collect-submodules command_modules `
  --collect-submodules endpoints `
  @hiArgs `
  (Join-Path $Root "main.py")

$built = Join-Path $WorkDist "RemoteTaskManagerClient"
if (-not (Test-Path $built)) {
  throw "PyInstaller output not found: $built"
}

New-Item -ItemType Directory -Force -Path $OutRoot | Out-Null
Copy-Item -Recurse -Force (Join-Path $built "*") $OutRoot

# Sidecar folders (editable without rebuild)
Copy-Item -Recurse -Force (Join-Path $Root "command_modules") (Join-Path $OutRoot "command_modules")
Copy-Item -Recurse -Force (Join-Path $Root "endpoints") (Join-Path $OutRoot "endpoints")

New-Item -ItemType Directory -Force -Path (Join-Path $OutRoot "config") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $OutRoot "downloads") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $OutRoot "logs") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $OutRoot "sensible") | Out-Null

Copy-Item -Force (Join-Path $Root "packaging\configuration.portable.ini") (Join-Path $OutRoot "configuration.ini")
$RoutesExample = Join-Path $Root "config\download_routes.example.json"
$ProgramsExample = Join-Path $Root "config\programs.example.json"
Copy-Item -Force $RoutesExample (Join-Path $OutRoot "config\download_routes.json")
Copy-Item -Force $RoutesExample (Join-Path $OutRoot "config\download_routes.example.json")
Copy-Item -Force $ProgramsExample (Join-Path $OutRoot "config\programs.example.json")
# Fresh install: empty program list (edit locally; not the example placeholders)
Set-Content -Path (Join-Path $OutRoot "config\programs.json") -Value "[]" -Encoding UTF8
Copy-Item -Force (Join-Path $Root "packaging\secrets.example.json") (Join-Path $OutRoot "sensible\secrets.example.json")
Copy-Item -Force (Join-Path $Root "packaging\LEEME.txt") (Join-Path $OutRoot "LEEME.txt")

New-Item -ItemType Directory -Force -Path (Join-Path $OutRoot "assets") | Out-Null
Copy-Item -Force $IconPath (Join-Path $OutRoot "assets\app.ico")

# Launcher bat
@"
@echo off
cd /d "%~dp0"
title RTM-CLIENT
RemoteTaskManagerClient.exe
"@ | Set-Content -Path (Join-Path $OutRoot "start_client.bat") -Encoding ASCII

# Strip local caches from copied python packages
Get-ChildItem -Path $OutRoot -Recurse -Directory -Filter "__pycache__" -ErrorAction SilentlyContinue |
  Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

Write-Output ""
Write-Output "OK: portable package ready at:"
Write-Output $OutRoot
Write-Output "Copy the entire RTM-Client folder to another PC."
