@echo off
setlocal

pushd "%~dp0" >nul 2>&1
if errorlevel 1 (
    echo ERREUR : impossible d'ouvrir le dossier PBIRS Mailer.
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    echo ERREUR : PBIRS Mailer n'est pas installe.
    echo Lancez d'abord .\setup.cmd.
    popd
    exit /b 2
)

".venv\Scripts\python.exe" main.py %*
set "PBIRS_EXIT_CODE=%ERRORLEVEL%"

popd
exit /b %PBIRS_EXIT_CODE%
