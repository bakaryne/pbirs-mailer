@echo off
setlocal

pushd "%~dp0" >nul 2>&1
if errorlevel 1 exit /b 1

if not exist "config.json" copy /Y "config.example.json" "config.json" >nul
start "" notepad.exe "config.json"

popd
exit /b 0

