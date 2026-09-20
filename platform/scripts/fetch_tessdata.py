"""Download eng.traineddata for Tesseract into Compliance_Engine/tessdata (no admin needed).

Tries several mirrors; verifies the result looks like a real tessdata file
(size > 200 KB). Sets up the TESSDATA_PREFIX layout for the engine launchers
(prefix = the folder that CONTAINS the "tessdata" directory).
"""
from __future__ import annotations

import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEST_DIR = ROOT / "tessdata"
DEST = DEST_DIR / "eng.traineddata"

URLS = [
    "https://digi.bib.uni-mannheim.de/tesseract/tessdata_fast/eng.traineddata",
    "https://digi.bib.uni-mannheim.de/tesseract/tessdata/eng.traineddata",
    "https://tessdata.projectnaptha.com/4.0.0_best/eng.traineddata",
    "https://tessdata.projectnaptha.com/4.0.0_fast/eng.traineddata",
]


def main() -> int:
    DEST_DIR.mkdir(parents=True, exist_ok=True)
    for url in URLS:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=60) as resp, open(DEST, "wb") as fh:
                data = resp.read()
                fh.write(data)
            size = DEST.stat().st_size
            if size > 200_000:
                print(f"OK {size} bytes <- {resp.geturl()}")
                return 0
            print(f"TOO-SMALL {size} <- {resp.geturl()}; trying next")
        except Exception as exc:  # network / 404 / redirect dead-end
            print(f"FAIL {url}: {exc}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())