@echo off
echo ========================================================
echo   Starting RCM System (Reliability Centered Maint.)
echo ========================================================
call "%~dp0venv\Scripts\activate.bat"
streamlit run "%~dp0app.py"
pause
