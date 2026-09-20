"""
Phase 5 - Font size & readability analysis (CV).

Provides:
  * detect_barcode(image_rgb) -- in-image EAN-13/UPC-A barcode detection via
    OpenCV's BarcodeDetector; used as an in-scene reference to derive px->mm.
  * calibration_from_barcode() / get_calibration() -- mm-per-pixel conversion.
  * measure_zone_font(crop_rgb, zone_text, mm_per_px) -- character-height
    measurement (px, and mm when calibrated) + readability proxies
    (text/background contrast ratio, uppercase ratio).

The numerals in MRP / net-quantity / date blocks are small and critical for
LMPC font-size checks (Rule 7), so character height is measured from
Tesseract char-level boxes (image_to_boxes), not just word boxes.

Calibration reference: EAN-13 and UPC-A barcodes have a standardized overall
width of 37.29 mm at 100% magnification (module width 0.33 mm x 95 modules
plus quiet zones). Therefore mm_per_px = 37.29 / barcode_width_px. When no
barcode is present the system reports px measurements only and downstream
mm-based rules are marked needs_review (they need a manual calibration value).
"""
import re
from typing import List, Optional

import cv2
import numpy as np
try:
    import pytesseract  # pyright: ignore[reportMissingImports]
except ImportError:
    # Barcode detection and manually calibrated measurements do not require
    # the optional Tesseract Python package.
    pytesseract = None

from compliance_engine import config
from compliance_engine.schema import CalibrationInfo, FontMetricInfo

# Standard nominal width for EAN-13 / UPC-A (GS1, 100% magnification).
BARCODE_NOMINAL_WIDTH_MM = 37.29

# Character heights outside this px band are treated as OCR/geometry noise.
_CHAR_HEIGHT_MIN_PX = 2.0
_CHAR_HEIGHT_MAX_PX = 200.0


# ---------------------------------------------------------------------------
# Barcode-based calibration
# ---------------------------------------------------------------------------
def detect_barcode(image_rgb: np.ndarray) -> Optional[dict]:
    """Return info on the first usable EAN/UPC barcode in the image.

    Returns dict with keys: barcode_type, barcode_value, bbox [x,y,w,h],
    width_px, height_px -- or None when no decodable barcode is found.
    """
    try:
        detector = cv2.barcode.BarcodeDetector()
        ok, decoded, types, quads = detector.detectAndDecodeWithType(image_rgb)
    except Exception:
        return None
    if not ok or types is None or quads is None or len(quads) == 0:
        return None

    for i, btype in enumerate(types):
        btype_upper = (btype or "").upper()
        if "EAN" in btype_upper or "UPC" in btype_upper:
            quad = np.asarray(quads[i]).reshape(-1, 4, 2)
            if quad.shape[0] == 0:
                continue
            pts = quad[0]
            # Module axis = the longest quad edge. Using the correct edge matters:
            # EAN/UPC codes are 37.29 mm along the bars, so a photo that shows the
            # code rotated 90 degrees must still be calibrated on the LONG side.
            edges = sorted(
                float(np.linalg.norm(pts[k] - pts[(k + 1) % 4]))
                for k in range(4)
            )
            width_px, height_px = edges[-1], edges[0]
            if width_px < 5:
                continue
            x, y = float(np.min(pts[:, 0])), float(np.min(pts[:, 1]))
            return {
                "barcode_type": btype_upper,
                "barcode_value": decoded[i] if i < len(decoded) else "",
                "bbox": [int(round(x)), int(round(y)),
                         int(round(width_px)), int(round(height_px))],
                "width_px": width_px,
                "height_px": height_px,
            }
    return None


# ---------------------------------------------------------------------------
# OCR-based calibration fallback
# ---------------------------------------------------------------------------
# cv2.barcode frequently fails on small, glossy or slightly-curved codes (very
# common on real package photos). Those symbols still OCR their printed
# EAN-13/UPC-A digits cleanly, and the digits span the full 37.29 mm symbol
# width (between the quiet zones). We verify a candidate digit run by checking
# that the strip of pixels directly adjacent to it looks like a barcode
# (uniformly dense vertical edges) - text runs such as 14-digit FSSAI licence
# numbers do not - and derive the reference width from that digit run.

_STRIP_MIN_MEAN = 70.0     # mean |dI/dx| inside the adjacent strip
_STRIP_MAX_CV = 0.95       # uniformity (bars are periodic; text is spiky)
_STRIP_HEIGHT_PX = 26      # how many rows to search above/below the digits
_DIGIT_RUN_MIN_W_PX = 60   # a real symbol is wider than any short number


def _ocr_digit_runs(gray: np.ndarray) -> List[tuple]:
    """Pixel boxes of consecutive numeric OCR words (x, y, w, h, digits)."""
    if pytesseract is None:
        return []
    try:
        data = pytesseract.image_to_data(gray, output_type=pytesseract.Output.DICT)
    except Exception:
        return []
    n = len(data["text"])
    runs: List[tuple] = []
    i = 0
    while i < n:
        while i < n and not (data["text"][i] or "").strip():
            i += 1
        if i >= n:
            break
        digits = re.sub(r"\D", "", data["text"][i])
        if len(digits) < 6:
            i += 1
            continue
        xs = int(data["left"][i]); ys = int(data["top"][i])
        x1 = xs + int(data["width"][i]); y1 = ys + int(data["height"][i])
        acc = digits
        j = i + 1
        while j < n:
            nxt = re.sub(r"\D", "", data["text"][j] or "")
            if not nxt:
                break
            tj = int(data["top"][j]); hj = int(data["height"][j] or 10)
            if abs(tj - ys) > 0.5 * hj:        # different text line
                break
            if int(data["left"][j]) - x1 > max(8, 0.5 * hj):   # large gap
                break
            acc += nxt
            x1 = int(data["left"][j] + data["width"][j])
            y1 = max(y1, int(data["top"][j] + hj))
            ys = min(ys, int(data["top"][j]))
            j += 1
        if 8 <= len(acc) <= 16:
            runs.append((xs, ys, x1 - xs, y1 - ys, acc))
        i = j
    return runs


def _estimate_barcode_from_ocr(image_rgb: np.ndarray) -> Optional[dict]:
    """Estimate the EAN/UPC reference width from OCR digits + edge uniformity.

    Returns None when no credible barcode-like digit run is found, otherwise
    a dict mirroring detect_barcode()'s shape (barcode_type/value/bbox/
    width_px/height_px) with the type flagged as an estimate.
    """
    gray = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2GRAY)
    runs = _ocr_digit_runs(gray)
    if not runs:
        return None
    h, w = gray.shape
    gx = np.abs(cv2.Sobel(gray, cv2.CV_64F, 1, 0)).astype(np.uint8)
    best: Optional[tuple] = None  # (score, info_dict)

    for (x, y, rw, rh, digits) in runs:
        if rw < _DIGIT_RUN_MIN_W_PX:
            continue
        x0 = max(0, x - 12); x1 = min(w, x + rw + 12)
        for y0, y1 in (
            (max(0, y - _STRIP_HEIGHT_PX), max(0, y)),            # digits under bars
            (min(h, y + rh), min(h, y + rh + _STRIP_HEIGHT_PX)),   # digits above bars
        ):
            if y1 - y0 < 6 or x1 - x0 < 24:
                continue
            band = gx[y0:y1, x0:x1]
            if band.size == 0:
                continue
            col = band.mean(axis=0)
            mean_e = float(col.mean())
            cvv = float(col.std() / (col.mean() + 1e-6))
            if mean_e < _STRIP_MIN_MEAN or cvv > _STRIP_MAX_CV:
                continue
            score = mean_e * (rw / 100.0)   # wide, dense, uniform -> best
            info = {
                "barcode_type": "EAN/UPC (OCR estimate)",
                "barcode_value": digits,
                "bbox": [x0, y0, x1 - x0, y1 - y0],
                "width_px": float(rw),
                "height_px": float(rh),
            }
            if best is None or score > best[0]:
                best = (score, info)
    return best[1] if best else None


def get_calibration(image_rgb: np.ndarray) -> CalibrationInfo:
    """Build the px->mm CalibrationInfo from an in-image barcode."""
    info = CalibrationInfo(
        method="none",
        notes="No barcode found; mm-based checks will require manual calibration.",
    )
    barcode = detect_barcode(image_rgb)
    if barcode is None:
        # cv2's decoder often misses small/curved/glossy codes; fall back to an
        # OCR-digit-based estimate of the same 37.29 mm reference width.
        barcode = _estimate_barcode_from_ocr(image_rgb)
        if barcode is None:
            return info
        mm_per_px = BARCODE_NOMINAL_WIDTH_MM / barcode["width_px"]
        return CalibrationInfo(
            method="ean_upc_barcode_ocr",
            mm_per_px=round(mm_per_px, 6),
            barcode_type=barcode["barcode_type"],
            barcode_value=barcode["barcode_value"],
            barcode_bbox=barcode["bbox"],
            reference_width_mm=BARCODE_NOMINAL_WIDTH_MM,
            reference_width_px=round(barcode["width_px"], 2),
            notes=("Calibrated from the OCR-detected EAN/UPC digit run (cv2 "
                   "could not decode the code; px->mm is an estimate from the "
                   "37.29 mm symbol width - verify on the physical label if a "
                   "hard verdict is needed)."),
        )
    mm_per_px = BARCODE_NOMINAL_WIDTH_MM / barcode["width_px"]
    return CalibrationInfo(
        method="ean_upc_barcode",
        mm_per_px=round(mm_per_px, 6),
        barcode_type=barcode["barcode_type"],
        barcode_value=barcode["barcode_value"],
        barcode_bbox=barcode["bbox"],
        reference_width_mm=BARCODE_NOMINAL_WIDTH_MM,
        reference_width_px=round(barcode["width_px"], 2),
        notes=f"Calibrated from {barcode['barcode_type']} barcode "
              f"(ref width {BARCODE_NOMINAL_WIDTH_MM} mm).",
    )


def manual_calibration(mm_per_px: float) -> CalibrationInfo:
    """Build a CalibrationInfo from a user-supplied mm-per-pixel value."""
    return CalibrationInfo(
        method="manual",
        mm_per_px=round(float(mm_per_px), 6),
        notes="Pixel-to-mm conversion supplied manually by the operator.",
    )


# ---------------------------------------------------------------------------
# Character height
# ---------------------------------------------------------------------------
def _char_heights_px(gray_crop: np.ndarray, psm: int) -> List[float]:
    """Character heights (px) from Tesseract char-level boxes."""
    if pytesseract is None:
        return []
    try:
        data = pytesseract.image_to_boxes(
            gray_crop,
            config=f"--oem {config.TESSERACT_OEM} --psm {psm}",
            output_type=pytesseract.Output.DICT,
        )
    except Exception:
        return []

    tops = data.get("top", [])
    bottoms = data.get("bottom", [])
    heights = []
    for top, bottom in zip(tops, bottoms):
        try:
            h = abs(int(top) - int(bottom))
        except (TypeError, ValueError):
            continue
        if _CHAR_HEIGHT_MIN_PX <= h <= _CHAR_HEIGHT_MAX_PX:
            heights.append(float(h))
    return heights


def _contrast_ratio(gray_crop: np.ndarray) -> float:
    """WCAG-style luminance contrast ratio between text and background."""
    if gray_crop.size == 0 or float(np.std(gray_crop)) < 8.0:
        return 0.0
    _, thresh = cv2.threshold(gray_crop, 0, 255,
                              cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    dark = gray_crop[thresh == 0]
    light = gray_crop[thresh == 255]
    if dark.size == 0 or light.size == 0:
        return 0.0

    def luminance(vals):
        channel = vals.astype(np.float32) / 255.0
        channel = np.where(channel <= 0.04045,
                           channel / 12.92,
                           ((channel + 0.055) / 1.055) ** 2.4)
        return float(np.mean(channel))

    l_dark, l_light = luminance(dark), luminance(light)
    l1, l2 = max(l_dark, l_light), min(l_dark, l_light)
    return round((l1 + 0.05) / (l2 + 0.05), 2)


def _uppercase_ratio(text: str) -> float:
    letters = [ch for ch in text if ch.isalpha()]
    if not letters:
        return 0.0
    return round(sum(1 for ch in letters if ch.isupper()) / len(letters), 3)


def measure_zone_font(
    crop_rgb: np.ndarray,
    zone_text: str,
    mm_per_px: Optional[float] = None,
    psm: Optional[int] = None,
) -> FontMetricInfo:
    """Measure font/readability metrics for one zone crop.

    crop_rgb: RGB patch of the declaration zone.
    zone_text: OCR text of that zone (for uppercase ratio).
    mm_per_px: optional calibrated conversion (None -> px-only reporting).
    """
    if crop_rgb is None or crop_rgb.size == 0:
        return FontMetricInfo(zone_type="", warnings=["Empty zone crop"])

    gray = cv2.cvtColor(crop_rgb, cv2.COLOR_RGB2GRAY)
    psm = psm or config.SHORT_LINE_OCR_PSM
    heights = _char_heights_px(gray, psm)

    metric = FontMetricInfo(zone_type="")
    if heights:
        metric.char_height_px_median = round(float(np.median(heights)), 2)
        metric.char_height_px_min = round(float(np.min(heights)), 2)
        metric.char_height_px_max = round(float(np.max(heights)), 2)
        if mm_per_px:
            metric.calibrated = True
            metric.char_height_mm_median = round(
                metric.char_height_px_median * mm_per_px, 3)
    else:
        metric.warnings.append("No character boxes found in this zone crop")

    metric.contrast_ratio = _contrast_ratio(gray)
    metric.uppercase_ratio = _uppercase_ratio(zone_text)
    if metric.contrast_ratio <= 0.0:
        metric.warnings.append(
            "Contrast ratio not measurable (uniform/low-variance crop)")
    return metric