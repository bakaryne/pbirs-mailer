@echo off
setlocal

pushd "%~dp0" >nul 2>&1
if errorlevel 1 exit /b 1

if not exist ".venv\Scripts\python.exe" (
    echo ERREUR : PBIRS Mailer n'est pas installe.
    echo Lancez d'abord .\setup.cmd.
    popd
    exit /b 2
)

if not exist "config.json" copy /Y "config.example.json" "config.json" >nul
set "PYTHONPATH=%CD%\src;%PYTHONPATH%"
".venv\Scripts\python.exe" -m pbirs_mailer.gui --config "config.json"
set "PBIRS_EXIT_CODE=%ERRORLEVEL%"

popd
exit /b %PBIRS_EXIT_CODE%
