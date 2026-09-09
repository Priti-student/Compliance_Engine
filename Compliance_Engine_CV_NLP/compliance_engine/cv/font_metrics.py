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
from typing import List, Optional

import cv2
import numpy as np
import pytesseract

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
            width_px = float(max(
                np.linalg.norm(pts[0] - pts[1]),
                np.linalg.norm(pts[2] - pts[3]),
            ))
            height_px = float(max(
                np.linalg.norm(pts[1] - pts[2]),
                np.linalg.norm(pts[3] - pts[0]),
            ))
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


def get_calibration(image_rgb: np.ndarray) -> CalibrationInfo:
    """Build the px->mm CalibrationInfo from an in-image barcode."""
    info = CalibrationInfo(
        method="none",
        notes="No barcode found; mm-based checks will require manual calibration.",
    )
    barcode = detect_barcode(image_rgb)
    if barcode is None:
        return info
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
    try:
        data = pytesseract.image_to_boxes(
            gray_crop,
            config=f"--oem {config.TESSERACT_OEM} --psm {psm}",
            output_type=pytesseract.Output.DICT,
        )
    except pytesseract.TesseractError:
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