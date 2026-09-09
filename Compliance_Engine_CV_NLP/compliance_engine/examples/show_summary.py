"""Show per-image compliance summary + key violation drivers after fixes."""
import os
import sys

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from compliance_engine.pipeline import run_full_pipeline


def show(img):
    r = run_full_pipeline(img)
    print("=" * 90)
    print(f"IMAGE {img}  ->  {r.compliance_status.upper()}")
    print(f"  stats: {r.stats}")
    for d in r.declarations:
        if d.value or d.field_name in ("manufacturer_packer_importer",
                                        "consumer_care_details"):
            print(f"  DECL {d.field_name:<28} {d.value!r:<22} [{d.source_zone}]")
    for v in r.violations:
        if v.status in ("non_compliant", "missing", "needs_review") and v.rule_id in (
                "MD-01", "MD-02", "MD-03", "MD-04", "MD-05", "MD-07", "MD-10"):
            print(f"  {v.status:<12} {v.rule_id:<6} | {v.reason[:100]}")
    print(f"  *non/missing drivers: {r.stats.non_compliant+r.stats.missing}")


if __name__ == "__main__":
    for img in sys.argv[1:] or [
        "package_001.jpg", "package_002.jpg", "package_003.jpg",
        "ProductLays.jpeg", "Wheet.jpeg",
    ]:
        show(img)