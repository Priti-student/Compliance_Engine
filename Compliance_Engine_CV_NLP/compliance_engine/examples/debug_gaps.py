"""Debug remaining extraction gaps after fixes."""
import os
import sys

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from compliance_engine.nlp.declaration_extractor import extract_declarations
from compliance_engine.nlp.regex_patterns import _extract_phone, _extract_mfg
from compliance_engine.pipeline import run_scan


def main():
    for img, checks in [
        ("ProductLays.jpeg", None),
        ("Wheet.jpeg", None),
        ("package_002.jpg", None),
    ]:
        scan = run_scan(img)
        ft = (scan.full_image_ocr.text or "") if scan.full_image_ocr else ""
        print("=" * 90)
        print(img, "| full-OCR lines around phone / month / mre / MRP:")
        toks = [x for x in ["phone", "1800", "month", "manufacture", "mre",
                            "MFD", "MED", "mfd", "med"]]
        for tok in toks:
            low = ft.lower()
            i = 0
            while True:
                j = low.find(tok.lower(), i)
                if j < 0:
                    break
                print(f"   [{tok}] ...{ft[max(0, j-30):j+60]!r}")
                i = j + 1
        decls = extract_declarations(scan)
        print("  consumer_phone:", [d.value for d in decls if d.field_name == "consumer_phone"])
        print("  consumer_email:", [d.value for d in decls if d.field_name == "consumer_email"])
        print("  mfg:", [d.value for d in decls if d.field_name == "month_year_of_manufacture"])
        print("  mrp:", [d.value for d in decls if d.field_name == "mrp"])


if __name__ == "__main__":
    main()