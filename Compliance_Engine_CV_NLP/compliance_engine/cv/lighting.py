"""
Phase 2 - Image preprocessing helpers (lighting normalization, denoise, deskew).

See preprocessing.py for the orchestrated pipeline.
"""
from typing import Optional, Tuple

import cv2
import numpy as np

from compliance_engine import config


def normalize_lighting(image_rgb: np.ndarray) -> np.ndarray:
    """CLAHE equalization on the L channel (Lab space) to even out lighting."""
    lab = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(
        clipLimit=config.CLAHE_CLIP_LIMIT, tileGridSize=config.CLAHE_TILE_GRID_SIZE
    )
    l_eq = clahe.apply(l)
    return cv2.cvtColor(cv2.merge((l_eq, a, b)), cv2.COLOR_LAB2RGB)


def denoise(image_rgb: np.ndarray) -> np.ndarray:
    """Fast non-local means denoising on the grayscale channel."""
    gray = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2GRAY)
    denoised = cv2.fastNlMeansDenoising(gray, None, h=config.DENOISE_H)
    return cv2.cvtColor(denoised, cv2.COLOR_GRAY2RGB)


def _deskew_angle_from_min_area_rect(gray: np.ndarray) -> Optional[float]:
    """Estimate package tilt from the dominant text-line orientation.

    Uses the angle of the minimum-area rectangle around all detected
    text-like contours. Returns the rotation angle in degrees to apply
    (positive = rotate counter-clockwise to right it), or None if there is
    no usable text structure to measure.
    """
    thresh = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY,
        blockSize=35, C=10
    )
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None

    all_pts = np.vstack(contours)
    (_, _, angle) = cv2.minAreaRect(all_pts)
    if angle > 45:      # opencv reports -45..0 for near-vertical rects
        angle -= 90     # remap to the horizontal text-line case
    if abs(angle) < config.DESKEW_MIN_ANGLE or abs(angle) > config.DESKEW_MAX_ANGLE:
        return None
    return float(angle)


def deskew(image_rgb: np.ndarray) -> Tuple[np.ndarray, float]:
    """Rotate the image by the estimated skew angle; falls back to no-op."""
    gray = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2GRAY)
    angle = _deskew_angle_from_min_area_rect(gray)
    if angle is None or abs(angle) < config.DESKEW_MIN_ANGLE:
        return image_rgb, 0.0
    h, w = image_rgb.shape[:2]
    matrix = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)
    rotated = cv2.warpAffine(image_rgb, matrix, (w, h),
                             flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    return rotated, angle