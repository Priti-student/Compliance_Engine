"""
Phase 4 - OCR extraction (Tesseract).

Provides:
  - ocr_block_text(crop): quick whole-block OCR used by the zone detector for
    keyword tagging (Phase 3).
  - ocr_zone(zone_crop, zone_type): focused OCR of a single declaration zone,
    tuned per zone type (single-line psm 7 for MRP/net-qty/date/batch/FSSAI,
    paragraph psm 6 for address/consumer-care), with small-text upscaling.
  - ocr_full_image(image): whole-image fallback pass used to cross-check
    anything the zone detector missed.

All functions return word-level data (text, confidence, bbox) so downstream
phases can reason about readability and font metrics (Phase 5) rather than
just the raw concatenated text.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import cv2
import numpy as np
import pytesseract

from compliance_engine import config

# Point pytesseract at the actual binary (config falls back to the standard
# Windows install path when Tesseract is not on PATH).
pytesseract.pytesseract.tesseract_cmd = config.TESSERACT_CMD


@dataclass
class WordResult:
    text: str
    confidence: float
    bbox: tuple               # (left, top, width, height) in the crop coords
    block_id: int = -1        # Tesseract block number (layout analysis)
    par_id: int = -1          # paragraph number within block
    line_id: int = -1         # line number within paragraph


@dataclass
class OCRResult:
    text: str = ""                      # line-joined text
    words: List[WordResult] = field(default_factory=list)
    mean_confidence: float = 0.0
    psm_used: int = config.DEFAULT_OCR_PSM
    upscaled: bool = False
    warnings: List[str] = field(default_factory=list)


def _tess(
    image: np.ndarray,
    psm: int,
    image_to_data: bool = False,
    config_str: str = "",
) -> str:
    """Run Tesseract with the configured binary/OEM."""
    if image_to_data:
        return pytesseract.image_to_data(
            image,
            config=f"--oem {config.TESSERACT_OEM} --psm {psm} {config_str}".strip(),
            output_type=pytesseract.Output.DICT,
        )
    return pytesseract.image_to_string(
        image,
        config=f"--oem {config.TESSERACT_OEM} --psm {psm} {config_str}".strip(),
    )


def _maybe_upscale(gray: np.ndarray) -> Tuple[np.ndarray, bool]:
    """Upscale small crops before OCR so tiny MRP/date/batch text works better."""
    h = gray.shape[0]
    if h < config.ZONE_MIN_HEIGHT_FOR_UPSCALE:
        scaled = cv2.resize(
            gray, None, fx=config.ZONE_UPSCALE_FACTOR, fy=config.ZONE_UPSCALE_FACTOR,
            interpolation=cv2.INTER_CUBIC,
        )
        return scaled, True
    return gray, False


def _image_to_ocr_result(image: np.ndarray, psm: int) -> OCRResult:
    """Word-aware OCR of the given image (useful for zones and full-image pass)."""
    result = OCRResult(psm_used=psm)
    data = _tess(image, psm=psm, image_to_data=True)

    words: List[WordResult] = []
    texts = data.get("text", [])
    confs = data.get("conf", [])
    lefts, tops, widths, heights = data.get("left", []), data.get("top", []), \
        data.get("width", []), data.get("height", [])
    blocks = data.get("block_num", [])
    pars = data.get("par_num", [])
    lines = data.get("line_num", [])

    for i in range(len(texts)):
        text = texts[i].strip()
        try:
            conf = float(confs[i])
        except (TypeError, ValueError):
            conf = -1.0
        if conf < config.MIN_WORD_CONFIDENCE:
            continue
        if not text:
            continue
        words.append(WordResult(
            text=text,
            confidence=conf,
            bbox=(int(lefts[i]), int(tops[i]), int(widths[i]), int(heights[i])),
            block_id=int(blocks[i]) if i < len(blocks) else -1,
            par_id=int(pars[i]) if i < len(pars) else -1,
            line_id=int(lines[i]) if i < len(lines) else -1,
        ))

    result.words = words
    result.text = "\n".join(w.text for w in words)
    result.mean_confidence = (
        float(np.mean([w.confidence for w in words])) if words else 0.0
    )
    return result


def ocr_block_text(crop: np.ndarray, psm: int = config.DEFAULT_OCR_PSM) -> Tuple[str, float]:
    """Cheap whole-block OCR (used by zone detection to get taggable text)."""
    if crop is None or crop.size == 0:
        return "", 0.0
    gray = cv2.cvtColor(crop, cv2.COLOR_RGB2GRAY)
    gray, _ = _maybe_upscale(gray)
    text = _tess(gray, psm=psm)
    conf = _mean_conf_from_string(text, gray, psm)
    return text.strip(), conf


def _mean_conf_from_string(text: str, gray: np.ndarray, psm: int = config.DEFAULT_OCR_PSM) -> float:
    """Best-effort confidence: re-run word OCR if the block had any text."""
    if not text.strip():
        return 0.0
    data = _tess(gray, psm=psm, image_to_data=True)
    confs = [float(c) for c in data.get("conf", []) if str(c).strip() and float(c) >= 0]
    return float(np.mean(confs)) if confs else 0.0


def ocr_zone(zone_crop: np.ndarray, zone_type: str) -> OCRResult:
    """Focused OCR of a single declaration-zone crop, tuned per zone type."""
    if zone_crop is None or zone_crop.size == 0:
        result = OCRResult(text="")
        result.warnings.append("Empty zone crop - nothing to OCR")
        return result

    psm = config.SHORT_LINE_OCR_PSM if zone_type in config.SHORT_LINE_ZONE_TYPES \
        else config.DEFAULT_OCR_PSM

    gray = cv2.cvtColor(zone_crop, cv2.COLOR_RGB2GRAY)
    gray, upscaled = _maybe_upscale(gray)

    result = _image_to_ocr_result(gray, psm)
    result.psm_used = psm
    result.upscaled = upscaled
    if upscaled:
        # bboxes referenced a 2x image; rescale back to the crop's coordinate space.
        for word in result.words:
            x, y, w, h = word.bbox
            word.bbox = (x // 2, y // 2, w // 2, h // 2)
    if not result.words:
        result.warnings.append("No words recognised in this zone crop")

    return result


def ocr_full_image(image: np.ndarray) -> OCRResult:
    """Whole-image fallback OCR pass (cross-check for anything zones missed)."""
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    return _image_to_ocr_result(gray, psm=config.DEFAULT_OCR_PSM)


def lines_from_words(words: List[WordResult]) -> List[dict]:
    """Group OCR words into visual lines using Tesseract's layout ids.

    Returns a list of dicts:
      {"bbox": (x, y, w, h), "text": str, "confidence": float}
    ordered top-to-bottom.
    """
    groups = {}
    for word in words:
        key = (word.block_id, word.par_id, word.line_id)
        if key not in groups:
            groups[key] = []
        groups[key].append(word)

    lines = []
    for words_in_line in groups.values():
        if not words_in_line:
            continue
        x0 = min(w.bbox[0] for w in words_in_line)
        y0 = min(w.bbox[1] for w in words_in_line)
        x1 = max(w.bbox[0] + w.bbox[2] for w in words_in_line)
        y1 = max(w.bbox[1] + w.bbox[3] for w in words_in_line)
        text = " ".join(w.text for w in sorted(
            words_in_line, key=lambda w: (w.bbox[1], w.bbox[0])
        ))
        conf = float(np.mean([w.confidence for w in words_in_line]))
        lines.append({"bbox": (x0, y0, x1 - x0, y1 - y0), "text": text,
                      "confidence": conf})

    # Sort top-to-bottom (then left-to-right within the same band).
    lines.sort(key=lambda ln: (round(ln["bbox"][1] / max(1, ln["bbox"][3] // 3)),
                               ln["bbox"][0]))
    return lines