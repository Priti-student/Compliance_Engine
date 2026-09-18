@echo off
REM Start the CV/OCR compliance engine on 127.0.0.1:8000 (headless-safe).
REM engine_venv lives OUTSIDE this folder, at the workspace root.
set TESSDATA_PREFIX=%~dp0tessdata
cd /d "%~dp0Compliance_Engine_CV_NLP"
..\..\engine_venv\Scripts\python.exe -m uvicorn compliance_engine.api:app --host 127.0.0.1 --port 8000 --log-config "%~dp0..\engine_venv\uvicorn_log_config.json"