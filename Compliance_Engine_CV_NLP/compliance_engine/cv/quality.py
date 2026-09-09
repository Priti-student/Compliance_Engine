"""
Phase 1 - Image ingestion & quality gate.

Accepts an image path or raw bytes, decodes it with OpenCV, and returns a
structured quality report that the pipeline uses to decide whether the scan is
usable enough for OCR, or whether it should be flagged for re-capture before
expensive downstream steps run.
"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import cv2
import numpy as np

from compliance_engine import config


@dataclass
class QualityReport:
    is_usable: bool
    width: int
    height: int
    channels: int
    blur_variance: float
    brightness_mean: float
    darkness_ratio: float
    glare_ratio: float
    orientation_angle: float = 0.0
    warnings: list = field(default_factory=list)


def load_image(image_path_or_bytes) -> Optional[np.ndarray]:
    """Decode an image from a path or raw bytes into a BGR numpy array.

    Returns None when the data is not a decodable image.
    """
    if isinstance(image_path_or_bytes, (str, Path)):
        image_path_or_bytes = str(image_path_or_bytes)
        buf = np.fromfile(image_path_or_bytes, dtype=np.uint8)
    else:
        buf = np.frombuffer(image_path_or_bytes, dtype=np.uint8)

    image = cv2.imdecode(buf, cv2.IMREAD_COLOR)
    if image is None:
        return None
    return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)


def _blur_variance(gray: np.ndarray) -> float:
    """Variance of the Laplacian -- standard focus/sharpness metric."""
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def _brightness_stats(gray: np.ndarray) -> tuple:
    mean = float(gray.mean())
    dark_ratio = float((gray < 50).mean())
    glare_ratio = float((gray > 245).mean())
    return mean, dark_ratio, glare_ratio


def assess_quality(image: np.ndarray) -> QualityReport:
    """Run the quality gate: blur, brightness, strong glare, plus size checks."""
    if image is None:
        return QualityReport(
            is_usable=False, width=0, height=0, channels=0,
            blur_variance=0.0, brightness_mean=0.0,
            darkness_ratio=0.0, glare_ratio=0.0,
            warnings=["Unreadable image data"],
        )

    h, w = image.shape[:2]
    channels = image.shape[2] if image.ndim == 3 else 1
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)

    blur = _blur_variance(gray)
    brightness, dark_ratio, glare_ratio = _brightness_stats(gray)

    warnings = []
    if w < config.MIN_WIDTH or h < config.MIN_HEIGHT:
        warnings.append(
            f"Low resolution: {w}x{h}; minimum expected is "
            f"{config.MIN_WIDTH}x{config.MIN_HEIGHT}"
        )
    if blur < config.BLUR_VARIANCE_THRESHOLD:
        warnings.append(f"Image appears blurred (Laplacian variance {blur:.1f})")
    if brightness < config.BRIGHTNESS_MIN:
        warnings.append(f"Image too dark (mean brightness {brightness:.1f})")
    if brightness > config.BRIGHTNESS_MAX:
        warnings.append(f"Image overexposed (mean brightness {brightness:.1f})")
    if glare_ratio > 0.30:
        warnings.append(f"Strong glare present ({glare_ratio * 100:.0f}% pixels saturated)")

    is_usable = (w >= config.MIN_WIDTH
                 and h >= config.MIN_HEIGHT
                 and blur >= config.BLUR_VARIANCE_THRESHOLD
                 and config.BRIGHTNESS_MIN <= brightness <= config.BRIGHTNESS_MAX)

    return QualityReport(
        is_usable=is_usable, width=w, height=h, channels=channels,
        blur_variance=blur, brightness_mean=brightness,
        darkness_ratio=dark_ratio, glare_ratio=glare_ratio,
        warnings=warnings,
    )