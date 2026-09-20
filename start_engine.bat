@echo off
REM ===========================================================================
REM  Start the CV/OCR compliance engine on 127.0.0.1:8000 (headless-safe).
REM
REM  Uses the engine's own Python environment inside the repository:
REM      Compliance_Engine_CV_NLP\venv\Scripts\python.exe
REM  (git-ignored; create on a fresh clone - see "Setup (Windows)" in README.md)
REM  TESSDATA_PREFIX points at <repo>\tessdata for Tesseract language data.
REM ===========================================================================

set TESSDATA_PREFIX=%~dp0tessdata
cd /d "%~dp0Compliance_Engine_CV_NLP"
"%~dp0Compliance_Engine_CV_NLP\venv\Scripts\python.exe" -m uvicorn compliance_engine.api:app --host 127.0.0.1 --port 8000