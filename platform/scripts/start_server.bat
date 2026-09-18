@echo off
REM Launch the LMPC platform backend on port 8001 (programmatic uvicorn).
cd /d "%~dp0\..\backend"
..\venv\Scripts\python.exe run.py >> ..\server.log 2>&1