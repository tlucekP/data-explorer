@echo off
setlocal

cd /d "%~dp0"

set "PY_CMD="
where py >nul 2>nul
if not errorlevel 1 (
    py -3.12 -c "import streamlit" >nul 2>nul
    if not errorlevel 1 (
        set "PY_CMD=py -3.12"
    )

    if not defined PY_CMD (
        py -3 -c "import streamlit" >nul 2>nul
        if not errorlevel 1 (
            set "PY_CMD=py -3"
        )
    )
)

if not defined PY_CMD (
    where python >nul 2>nul
    if not errorlevel 1 (
        python -c "import streamlit" >nul 2>nul
        if not errorlevel 1 (
            set "PY_CMD=python"
        )
    )
)

if not defined PY_CMD (
    echo [ERROR] Streamlit neni dostupny pro zadny nalezeny Python.
    echo [ERROR] Streamlit is not available for any detected Python.
    echo.
    echo Spustte / Run: py -3.12 -m pip install -r requirements.txt
    echo nebo / or:   python -m pip install -r requirements.txt
    echo.
    pause
    endlocal
    exit /b 1
)

set "APP_URL=http://localhost:8501"
set "APP_CMD=%PY_CMD% -m streamlit run app.py --server.port 8501 --server.headless true --browser.gatherUsageStats false"

powershell -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -Command ^
  "Start-Process -WindowStyle Hidden -FilePath 'cmd.exe' -ArgumentList '/c cd /d ""%~dp0"" && %APP_CMD%'"

timeout /t 2 /nobreak >nul

start "" "%APP_URL%"

endlocal
exit /b
