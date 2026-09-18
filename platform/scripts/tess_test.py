"""Verify Tesseract OCR works with the downloaded tessdata (no engine needed)."""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SAMPLE = ROOT / "Compliance_Engine_CV_NLP" / "package_001.jpg"

os.environ["TESSDATA_PREFIX"] = str(ROOT / "tessdata")  # tesseract's tessdata directory

import cv2  # noqa: E402
import pytesseract  # noqa: E402

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

img = cv2.imread(str(SAMPLE))
assert img is not None, "could not read sample image"
text = pytesseract.image_to_string(img)
print("OCR-OK chars:", len(text))
print(text[:400])