"""Regenerate demo artifacts: 5-sample reports + repository + dashboard dump."""
import json
import os
import sys

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from compliance_engine.dashboard import dashboard_summary
from compliance_engine.pipeline import run_full_pipeline
from compliance_engine.reports import export_report
from compliance_engine.repository.store import ComplianceRepository

OUT = os.path.join(_REPO_ROOT, "data", "demo")
repo = ComplianceRepository(os.path.join(OUT, "repository"))

IMAGES = {
    "package_001": "package_001.jpg",
    "package_002": "package_002.jpg",
    "package_003": "package_003.jpg",
    "ProductLays": "ProductLays.jpeg",
    "Wheet": "Wheet.jpeg",
}


def main():
    for stem, img in IMAGES.items():
        report = run_full_pipeline(img)
        paths = export_report(report, os.path.join(OUT, "reports"), stem=stem)
        row = repo.save_scan(report, metadata={"scan_id": stem,
                                               "officer": f"demo_{stem}"})
        print(f"{stem:<14} {report.compliance_status:<14} "
              f"files={len(paths)} advice={report.advice}")

    dash = dashboard_summary(repo)
    with open(os.path.join(OUT, "dashboard_summary.json"), "w") as fh:
        json.dump(dash, fh, indent=2, default=str)
    print("\nDashboard total_scans:", dash["total_scans"])
    print("Status distribution:", dash["status_distribution"])
    print("Top violation rules:", dash["top_violation_rules"][:5])


if __name__ == "__main__":
    main()