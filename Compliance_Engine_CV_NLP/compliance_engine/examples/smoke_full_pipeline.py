"""Manual smoke test: run the full Phases 1-7 pipeline on a sample image."""
import os
import sys

# Allow running this script directly: `python examples/smoke_full_pipeline.py`
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from compliance_engine.pipeline import run_full_pipeline


def main():
    image = sys.argv[1] if len(sys.argv) > 1 else "package_001.jpg"
    report = run_full_pipeline(image)

    print("IMAGE           ", image)
    print("COMPLIANCE      ", report.compliance_status)
    if report.calibration:
        print("CALIBRATION     ", report.calibration.method,
              report.calibration.mm_per_px)
    print("DECLARATIONS    ", len(report.declarations))
    for d in report.declarations:
        print(f"  {d.field_name:<32} = {d.value!r:<24} "
              f"[{d.source_zone}, conf {d.confidence:.2f}]")
    print("FONT METRICS    ", len(report.font_metrics))
    for m in report.font_metrics:
        print(f"  {m.zone_type:<32} h_px {m.char_height_px_median:<6} "
              f"h_mm {m.char_height_mm_median:<6} contrast {m.contrast_ratio}")
    print("STATS           ", report.stats)
    for v in report.violations:
        sev = ""
        print(f"  [{v.status:<12}] {v.rule_id:<6} {v.reason[:78]}")


if __name__ == "__main__":
    main()