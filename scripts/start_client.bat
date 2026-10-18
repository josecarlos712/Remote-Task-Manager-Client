@echo off
setlocal
cd /d "%~dp0\.."
title RTM-CLIENT

echo Starting Remote Task Manager Client...
python main.py

endlocal
