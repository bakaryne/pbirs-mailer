@echo off
setlocal

pushd "%~dp0" >nul 2>&1
if errorlevel 1 (
    echo ERREUR : impossible d'ouvrir le dossier PBIRS Mailer.
    exit /b 1
)

powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\setup.ps1"
set "PBIRS_EXIT_CODE=%ERRORLEVEL%"

popd
exit /b %PBIRS_EXIT_CODE%

