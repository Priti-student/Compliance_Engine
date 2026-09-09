"""Inspect a single image: quality, preprocessing, zones, full OCR text."""
import os
import sys

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from compliance_engine.cv import assess_quality, detect_zones, load_image, preprocess


def main():
    img = sys.argv[1] if len(sys.argv) > 1 else "Product005.jpeg"
    print("image path exists:", os.path.exists(os.path.join(_REPO_ROOT, img)))
    image = load_image(img)
    if image is None:
        print("FAILED to decode image")
        return
    q = assess_quality(image)
    print(f"size {q.width}x{q.height} usable={q.is_usable} blur={q.blur_variance:.0f}")
    pre = preprocess(image)
    zr = detect_zones(pre.image)
    print(f"zones detected: {len(zr.zones)}")
    for z in zr.zones:
        print(f"  {z.zone_type}: {z.text[:80]!r}")
    from compliance_engine.cv.ocr_engine import ocr_full_image
    ocr = ocr_full_image(pre.image)
    print(f"full OCR words={len(ocr.words)} conf={ocr.mean_confidence:.0f}")
    print("--- full OCR text (first 1200 chars) ---")
    print(ocr.text[:1200])


if __name__ == "__main__":
    main()