"""Smoke: run /compliance/scan via TestClient over all 5 sample images."""
import os
import sys

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from fastapi.testclient import TestClient

from compliance_engine.api import app


def main():
    client = TestClient(app)
    images = ["package_001.jpg", "package_002.jpg", "package_003.jpg",
              "ProductLays.jpeg", "Wheet.jpeg"]
    for img in images:
        with open(os.path.join(_REPO_ROOT, img), "rb") as fh:
            resp = client.post("/compliance/scan",
                               files={"file": (img, fh, "image/jpeg")})
        j = resp.json()
        s = j["stats"]
        decls = [(d["field_name"], d["value"]) for d in j["declarations"]
                 if d["value"]]
        print(f"{img:<22} {resp.status_code} | {j['compliance_status']:<13} "
              f"missing={s['missing']} non={s['non_compliant']} "
              f"review={s['needs_review']} na={s['not_applicable']}")
        print(f"    extracted: {decls[:8]}")


if __name__ == "__main__":
    main()