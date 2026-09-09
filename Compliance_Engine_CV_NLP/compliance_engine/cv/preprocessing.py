"""
Phase 2 - Orchestrated image preprocessing pipeline.

    normalize lighting (CLAHE) -> denoise -> deskew -> perspective rectify

Tracks what was applied so later phases can interpret measurements correctly.
"""
from dataclasses import dataclass, field
from typing import List

import numpy as np

from compliance_engine import config
from compliance_engine.cv.lighting import denoise, deskew, normalize_lighting
from compliance_engine.cv.perspective import rectify_perspective


@dataclass
class PreprocessResult:
    image: np.ndarray                          # preprocessed RGB image
    deskew_angle: float = 0.0                  # degrees applied
    perspective_rectified: bool = False
    transforms_applied: List[str] = field(default_factory=list)


def preprocess(image_rgb: np.ndarray) -> PreprocessResult:
    """Run the full Phase 2 chain on an RGB image."""
    result = PreprocessResult(image=image_rgb)

    result.image = normalize_lighting(result.image)
    result.transforms_applied.append("CLAHE")

    result.image = denoise(result.image)
    result.transforms_applied.append("denoise")

    result.image, result.deskew_angle = deskew(result.image)
    if abs(result.deskew_angle) >= config.DESKEW_MIN_ANGLE:
        result.transforms_applied.append(f"deskew {result.deskew_angle:.1f}deg")

    result.image, result.perspective_rectified = rectify_perspective(result.image)
    if result.perspective_rectified:
        result.transforms_applied.append("perspective_rectify")

    return result