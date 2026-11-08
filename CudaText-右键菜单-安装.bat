@echo off
rem CudaText right-click menu + "Send To" integration
rem Mirrors the local EmEditor setup: per-user HKCU registration + SendTo shortcut, no admin needed
rem Usage: double-click = install;  run this file with argument "uninstall" = remove
setlocal
if /i "%~1"=="uninstall" goto uninstall
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0set-cudatext-contextmenu.ps1"
goto end
:uninstall
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0set-cudatext-contextmenu.ps1" -Uninstall
:end
pause
