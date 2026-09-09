"""Debug helper: print zone-detector text lines for the 5 sample images."""
import os
import sys

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from compliance_engine.cv import detect_zones, load_image, preprocess


def show(img):
    print("=" * 70)
    print(img)
    zr = detect_zones(preprocess(load_image(img)).image)
    for ln in zr.text_lines[:22]:
        b = ln["bbox"]
        print(f'  ({b["x"]},{b["y"]},{b["w"]},{b["h"]}) | {ln["text"][:70]!r}')


if __name__ == "__main__":
    for img in sys.argv[1:] or [
        "package_001.jpg", "package_002.jpg", "package_003.jpg",
        "ProductLays.jpeg", "Wheet.jpeg",
    ]:
        show(img)