@echo off
echo ============================================================
echo   Menjalankan Aplikasi Streamlit - Kelompok KKA-05
echo ============================================================
echo.

set PYTHON_CMD=python
if exist "C:\Users\LEGION\AppData\Local\Programs\Python\Python313\python.exe" (
    set PYTHON_CMD="C:\Users\LEGION\AppData\Local\Programs\Python\Python313\python.exe"
)

echo [INFO] Menggunakan: %PYTHON_CMD%
%PYTHON_CMD% -m streamlit run app.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [INFO] Menjalankan dengan python default...
    python -m streamlit run app.py
)

pause
