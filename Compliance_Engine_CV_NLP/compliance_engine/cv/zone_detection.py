"""
Phase 3 - Declaration zone detection (heuristic).

Locates the label regions that legally-required declarations live in
(MRP block, net-quantity block, manufacturing-date block, FSSAI block,
batch block, consumer-care block, manufacturer/address block) so OCR can
be applied per region instead of over the whole image.

Approach (works without any training data):
  1. Run one word-aware Tesseract pass over the whole image.
  2. Group words into visual lines using Tesseract's layout analysis
     (block/paragraph/line ids).
  3. Tag each line as a declaration zone via keyword patterns (config.py).
  4. Merge consecutive lines carrying the same tag into one zone bbox.

A YOLOv8 region detector is the planned Phase 3 upgrade; when trained, its
output will replace/augment this heuristic so OCR runs per detected label
region (source="yolo").

The output zone_type values align with rules/lmpc_rules_database.json field
names where applicable and with the OCR settings in config.py.
"""
import re
from dataclasses import dataclass, field
from typing import List

import numpy as np

from compliance_engine import config
from compliance_engine.cv.ocr_engine import lines_from_words, ocr_full_image

# Compile the keyword patterns once at import time.
_ZONE_PATTERNS = [
    (zone_type, re.compile(pattern, re.IGNORECASE))
    for zone_type, pattern in config.ZONE_KEYWORD_PATTERNS
]


@dataclass
class Zone:
    zone_type: str
    bbox: tuple                    # (x, y, w, h) in image pixel coords
    text: str = ""
    confidence: float = 0.0        # mean OCR word confidence of the block
    source: str = "heuristic"      # "heuristic" | "yolo" (Phase 3 upgrade)
    method: str = "keyword_tag"    # how the zone was detected/tagged


@dataclass
class ZoneDetectionResult:
    zones: List[Zone] = field(default_factory=list)
    text_lines: List[dict] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


def _tag_zone(text: str):
    """Tag OCR'd text with a declaration-zone type (first match wins)."""
    for zone_type, pattern in _ZONE_PATTERNS:
        if pattern.search(text):
            return zone_type
    return None


def _absorbs_naturally(zone_type: str) -> bool:
    """Zone types whose text spans several lines under a leading keyword."""
    return zone_type in {
        "manufacturer_address_block",
        "consumer_care_block",
        "fssai_block",
    }


def detect_zones(image_rgb: np.ndarray) -> ZoneDetectionResult:
    """Run the heuristic zone-detection pipeline (Phase 3)."""
    ocr = ocr_full_image(image_rgb)
    lines = lines_from_words(ocr.words)

    result = ZoneDetectionResult()
    result.text_lines = [
        {"bbox": {"x": int(line["bbox"][0]), "y": int(line["bbox"][1]),
                  "w": int(line["bbox"][2]), "h": int(line["bbox"][3])},
         "text": line["text"], "confidence": line["confidence"]}
        for line in lines
    ]

    # Tag each line.
    tagged_lines: List[tuple] = []     # (tag, x, y, w, h, text, conf)
    for line in lines:
        x, y, w, h = [int(v) for v in line["bbox"]]
        zone_type = _tag_zone(line["text"])
        if zone_type is None:
            continue
        tagged_lines.append((zone_type, x, y, w, h, line["text"], line["confidence"]))

    all_lines_sorted = sorted(
        lines, key=lambda ln: (ln["bbox"][1], ln["bbox"][0])
    )

    def _merge_into(zone: Zone, x: int, y: int, w: int, h: int,
                    text: str, conf: float) -> None:
        px, py, pw, ph = zone.bbox
        nx, ny = min(x, px), min(y, py)
        nw = max(x + w, px + pw) - nx
        nh = max(y + h, py + ph) - ny
        zone.bbox = (nx, ny, nw, nh)
        zone.text = f"{zone.text} {text}".strip()
        zone.confidence = (zone.confidence + conf) / 2.0

    # Merge consecutive same-tag lines into one zone.
    zones: List[Zone] = []
    for tag, x, y, w, h, text, conf in tagged_lines:
        if zones and zones[-1].zone_type == tag:
            _merge_into(zones[-1], x, y, w, h, text, conf)
        else:
            zones.append(Zone(
                zone_type=tag, bbox=(x, y, w, h), text=text.strip(),
                confidence=conf, source="heuristic", method="keyword_tag",
            ))

    # Absorb lookup-untagged continuation lines into natural multi-line zones
    # (e.g. the second line of a manufacturer address with no keyword).
    if zones:
        zone_idx = 0
        for ln in all_lines_sorted:
            lx, ly, lw, lh = [int(v) for v in ln["bbox"]]
            # advance to the zone that ends above this line
            while (zone_idx < len(zones)
                   and zones[zone_idx].bbox[1] + zones[zone_idx].bbox[3] <= ly):
                zone_idx += 1
            if zone_idx >= len(zones):
                break
            zone = zones[zone_idx]
            if not _absorbs_naturally(zone.zone_type):
                continue
            if ln["text"] in zone.text:          # already part of this zone
                continue
            zx, zy, zw, zh = zone.bbox
            gap = ly - (zy + zh)
            if 0 <= gap <= max(0.8 * zh, 8) and _x_overlap(lx, lw, zx, zw):
                tagged = _tag_zone(ln["text"])
                if tagged is None or tagged == zone.zone_type:
                    _merge_into(zone, lx, ly, lw, lh, ln["text"], ln["confidence"])

    result.zones = zones

    if not result.zones:
        result.warnings.append(
            "No declaration zones detected (no keyword-matched text lines found); "
            "the whole-image OCR fallback will still run."
        )
    return result


def _x_overlap(x1: int, w1: int, x2: int, w2: int) -> bool:
    return not (x1 + w1 < x2 or x2 + w2 < x1)