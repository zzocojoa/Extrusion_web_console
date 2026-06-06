@echo off
setlocal
set SCRIPT_DIR=%~dp0
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%start_web_console.ps1"
if errorlevel 1 (
  echo.
  echo Extrusion Web Console launcher failed. Review the message above.
  pause
)
endlocal
