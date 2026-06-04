@echo off
setlocal

set "BASE=%~dp0"
set "PYTHON=%BASE%python\python.exe"
set "SCRIPT=%BASE%Analizza_RU.py"

if not exist "%PYTHON%" (
    echo Python portatile non trovato:
    echo %PYTHON%
    pause
    exit /b 1
)

if "%~1"=="" (
    "%PYTHON%" "%SCRIPT%"
) else (
    "%PYTHON%" "%SCRIPT%" "%~1"
)

endlocal
