import os

from compliance_engine.reports import export_report
from compliance_engine.repository.store import ComplianceRepository
from compliance_engine.schema import ComplianceReport, ScanResult

# Repository / report storage (created lazily).
_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")
_REPO_DIR = os.path.join(_DATA_DIR, "repository")
_REPORTS_DIR = os.path.join(_DATA_DIR, "reports")

repository = ComplianceRepository(_REPO_DIR)