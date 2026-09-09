# Run the Phase 1-4 CV/OCR test suite from the project root:
#   venv/Scripts/python.exe -m pytest compliance_engine/tests -q
import os
import sys

import pytest

# Ensure the project root is importable when running pytest from the repo root.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from compliance_engine.pipeline import run_scan

# Sample images currently live at the repo root,
# e.g. C:\\Users\\PRITI RAM\\Desktop\\Test\\package_001.jpg
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


@pytest.fixture(scope="session")
def sample_images():
    """All packaged-commodity sample images used for the regression suite."""
    names = [
        "package_001.jpg",
        "package_002.jpg",
        "package_003.jpg",
        "ProductLays.jpeg",
        "Wheet.jpeg",
    ]
    return [os.path.join(_REPO_ROOT, name) for name in names]


@pytest.fixture()
def scan_package_001(sample_images):
    return run_scan(sample_images[0])