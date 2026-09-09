"""
Phase 2 - Perspective correction for packages photographed at an angle.

Finds the dominant roughly-quadrilateral contour in the frame (the visible face
of the package) and warps it to frontal with a projective transform.
"""
from typing import Optional, Tuple

import cv2
import numpy as np

from compliance_engine import config


def _order_corners(quad: np.ndarray) -> np.ndarray:
    rect = np.zeros((4, 2), dtype="float32")
    s = quad.sum(axis=1)
    rect[0] = quad[np.argmin(s)]          # top-left (smallest x+y)
    rect[2] = quad[np.argmax(s)]          # bottom-right (largest x+y)
    diff = np.diff(quad, axis=1)
    rect[1] = quad[np.argmin(diff)]       # top-right (smallest x-y)
    rect[3] = quad[np.argmax(diff)]       # bottom-left (largest x-y)
    return rect


def _largest_quadrilateral(image_rgb: np.ndarray) -> Optional[np.ndarray]:
    """Return ordered corners (tl, tr, br, bl) of the biggest quad, or None."""
    gray = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    thresh = cv2.adaptiveThreshold(
        blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, blockSize=35, C=10
    )

    best_box = None
    # Package may be brighter or darker than the background - try both.
    for candidate in (
        cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                              cv2.THRESH_BINARY, blockSize=35, C=10),
        cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                              cv2.THRESH_BINARY_INV, blockSize=35, C=10),
    ):
        contours, _ = cv2.findContours(candidate, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < (image_rgb.shape[0] * image_rgb.shape[1]
                       * config.PERSPECTIVE_MIN_AREA_RATIO):
                continue
            epsilon = 0.02 * cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, epsilon, True)
            if len(approx) != 4:
                continue
            if best_box is None or area > best_box[1]:
                best_box = (approx.reshape(4, 2).astype("float32"), area)

    if best_box is None:
        return None
    return _order_corners(best_box[0])


def rectify_perspective(image_rgb: np.ndarray) -> Tuple[np.ndarray, bool]:
    """Projectively transform the dominant package face to frontal.

    Returns (image, applied) where applied is False when no usable
    quadrilateral was found (caller should keep the original image).
    """
    quad = _largest_quadrilateral(image_rgb)
    if quad is None:
        return image_rgb, False

    (tl, tr, br, bl) = quad
    width_a = np.linalg.norm(br - bl)
    width_b = np.linalg.norm(tr - tl)
    height_a = np.linalg.norm(tr - br)
    height_b = np.linalg.norm(tl - bl)
    max_width = max(int(width_a), int(width_b))
    max_height = max(int(height_a), int(height_b))
    if max_width < 10 or max_height < 10:
        return image_rgb, False

    dst = np.array([
        [0, 0],
        [max_width - 1, 0],
        [max_width - 1, max_height - 1],
        [0, max_height - 1],
    ], dtype="float32")
    matrix = cv2.getPerspectiveTransform(quad, dst)
    warped = cv2.warpPerspective(image_rgb, matrix, (max_width, max_height))
    return warped, True