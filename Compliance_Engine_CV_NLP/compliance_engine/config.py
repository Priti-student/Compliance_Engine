"""
Central configuration for the CV/OCR compliance pipeline (Phases 0-4).

Nothing in here is hardcoded logic -- these are tunable knobs so accuracy can be
improved later (Phase 9 testing/tuning) without touching the pipeline code.
"""
import shutil

# --- Tesseract binary location -----------------------------------------------
# Falls back to the default Windows install path if not found on PATH.
TESSERACT_CMD = shutil.which("tesseract") or r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# --- Phase 1: Image quality gate ---------------------------------------------
MIN_WIDTH = 150
MIN_HEIGHT = 150
BLUR_VARIANCE_THRESHOLD = 60.0   # variance of Laplacian below this => likely blurred
BRIGHTNESS_MIN = 40.0            # mean pixel intensity (0-255) below this => too dark
BRIGHTNESS_MAX = 235.0           # above this => overexposed / glare
# High glare (specular highlight ratio) strongly suggests a re-capture is needed
# even when the mean brightness still passes the gate.
HIGH_GLARE_RATIO = 0.35
LOW_OCR_CONFIDENCE = 45.0        # mean Tesseract word confidence below this
                                 # => text was not read reliably; advisory only

# -----------------------------------------------------------------------------
# Phase 7 - verdict tuning
# -----------------------------------------------------------------------------
# When OCR cannot *prove* a declaration aspect (it was not readable in the
# photo, not that it is absent), the check is reported as a review note
# ("referral") that does not block a clean 'compliant' verdict:
#   * "referral" -> non-blocking review note (default)
#   * ""         -> keep blocking (strict enforcement mode)
MRP_QUALIFIER_OCR_MISS_KIND = "referral"

# --- Phase 2: Preprocessing ----------------------------------------------------
CLAHE_CLIP_LIMIT = 2.0
CLAHE_TILE_GRID_SIZE = (8, 8)
DENOISE_H = 7                     # fastNlMeansDenoising strength
DESKEW_MAX_ANGLE = 15.0           # ignore skew corrections beyond this (unreliable estimate)
DESKEW_MIN_ANGLE = 0.3            # ignore corrections smaller than this (noise, not real skew)
PERSPECTIVE_MIN_AREA_RATIO = 0.35  # candidate quad must cover >= this fraction of frame area

# --- Phase 3: Declaration zone keyword patterns -------------------------------
# Order matters: first matching pattern wins when a text block matches more than one.
# Field names align with rules/lmpc_rules_database.json `field_name` values where applicable.
ZONE_KEYWORD_PATTERNS = [
    ("fssai_block", r"\bfssai\b|\blic\.?\s*no\.?\s*[:\-]?\s*\d{10,}"),
    ("mrp_block", r"\bm\.?\s?r\.?\s?[pe]\b|maximum\s+retail\s+price"),
    ("unit_sale_price_block", r"unit\s+sale\s+price"),
    ("net_qty_block", r"\bnet\b.{0,12}\b(quantity|qty|weight|wt)\b|\b(quantity|qty|weight|wt)\b.{0,12}\bnet\b"),
    ("mfg_date_block", r"\b(mfd|mfg\.?\s*date|manufactur(ed|ing)\s+date|month\s*&?\s*year\s+of\s+manufacture)\b"),
    ("expiry_date_block", r"\b(use\s*by|best\s*before|useby|expiry|exp\.?\s*date)\b"),
    ("batch_block", r"\bbatch\s*(no\.?|number)?\s*[:.]?"),
    ("consumer_care_block", r"consumer\s+care|customer\s+care|toll[\s-]*free|customer\s+complaints?|consumer\s+complaints?"),
    ("manufacturer_address_block", r"manufactur(ed|er)\b|packed\s+by|marketed\s+by|imported\s+by"),
]

# --- Phase 4: Per-zone OCR settings --------------------------------------------
# Short, single-line declaration fields work better with Tesseract's "single text
# line" layout mode (psm 7); multi-line free text (address/consumer-care) works
# better with "uniform block of text" mode (psm 6).
SHORT_LINE_ZONE_TYPES = {
    "mrp_block", "unit_sale_price_block", "net_qty_block", "mfg_date_block",
    "expiry_date_block", "batch_block", "fssai_block",
}
DEFAULT_OCR_PSM = 6
SHORT_LINE_OCR_PSM = 7
TESSERACT_OEM = 3

# Padding (in px) added around a zone bbox before re-cropping for focused OCR.
ZONE_CROP_PADDING = 8

# If a cropped zone is shorter than this (px), upscale before OCR to help small
# MRP/date/batch text recognise more reliably.
ZONE_MIN_HEIGHT_FOR_UPSCALE = 40
ZONE_UPSCALE_FACTOR = 2

# Minimum Tesseract word confidence (0-100) to keep a word; -1 rows are always dropped.
MIN_WORD_CONFIDENCE = 0
