"""Verify the CV/OCR engine imports and Tesseract resolves in the engine venv."""
import sys
from pathlib import Path

ENGINE = Path(__file__).resolve().parents[2] / "Compliance_Engine_CV_NLP"
sys.path.insert(0, str(ENGINE))

import cv2  # noqa: E402
import numpy as np  # noqa: E402
import pytesseract  # noqa: E402

from compliance_engine.api import app  # noqa: E402

print("ENGINE-APP-OK routes=", len(app.routes))
print("opencv", cv2.__version__)
print("numpy", np.__version__)
print("tesseract_version", pytesseract.get_tesseract_version())