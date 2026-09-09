"""End-to-end Phases 5-7 pipeline tests (ComplianceReport)."""
from compliance_engine.pipeline import run_full_pipeline
from compliance_engine.schema import ComplianceReport


def test_full_pipeline_returns_report(sample_images):
    report = run_full_pipeline(sample_images[0])
    assert isinstance(report, ComplianceReport)
    assert report.status == "ok"
    assert report.compliance_status in ("compliant", "non_compliant",
                                        "needs_review", "not_applicable")
    assert report.calibration is not None
    assert report.declarations
    assert report.font_metrics
    assert report.violations
    assert report.stats is not None
    assert report.stats.total_checks == len(report.violations)


def test_full_pipeline_mrp_netqty_not_flag_as_missing(sample_images):
    """package_001 has a valid MRP + net qty; MD-03/MD-05 must not be missing."""
    report = run_full_pipeline(sample_images[0])
    by_id = {v.rule_id: v.status for v in report.violations}
    assert by_id.get("MD-05") != "missing"
    assert by_id.get("MD-03") != "missing"
    # MRP was found: expect either compliant (no row) or non_compliant
    # (e.g. paise), never missing.
    assert "MD-05" not in by_id or by_id["MD-05"] in ("non_compliant",)


def test_full_pipeline_manual_calibration_enables_font_check(sample_images):
    """A manual mm/px calibration should mark font metrics as calibrated."""
    report = run_full_pipeline(sample_images[0], calibration_mm_per_px=0.05)
    assert report.calibration.method == "manual"
    assert any(m.calibrated for m in report.font_metrics)


def test_full_pipeline_rejects_invalid_image(tmp_path):
    junk = tmp_path / "bad.png"
    junk.write_bytes(b"not really an image")
    report = run_full_pipeline(str(junk))
    assert report.status == "rejected"


# --- regression: previously-false violations are now correctly cleared -------

def test_full_pipeline_package_001_netqty_and_mrp_pass(sample_images):
    """package_001: MRP 20.00 + net qty 52 g must NOT be flagged missing."""
    report = run_full_pipeline(sample_images[0])
    by_id = {v.rule_id: v for v in report.violations}
    assert by_id.get("MD-03", "").status != "missing" if "MD-03" in by_id else True
    assert by_id.get("MD-05", "").status != "missing" if "MD-05" in by_id else True
    # consumer care is genuinely absent from this label face.
    assert by_id.get("MD-07", "").status == "missing" if "MD-07" in by_id else True


def test_full_pipeline_wheet_unit_sale_price_found(sample_images):
    """Wheet prints 'Unit Sale Price' -> MD-10 must not be missing/review
    purely from extraction failure (it should be found)."""
    report = run_full_pipeline(sample_images[4])
    assert any(d.field_name == "unit_sale_price" and d.value for d in report.declarations)
    by_id = {v.rule_id: v for v in report.violations}
    assert "MD-10" not in by_id


def test_full_pipeline_product_name_found(sample_images):
    """MD-02 (generic commodity name) is extracted for every sample now
    (previously always 'missing' -- no extractor existed)."""
    for idx in (0, 1, 2, 3, 4):
        report = run_full_pipeline(sample_images[idx])
        names = [d.value for d in report.declarations
                 if d.field_name == "generic_name_of_commodity" and d.value]
        assert names, f"sample {idx}: no generic name extracted"
        by_id = {v.rule_id: v for v in report.violations}
        assert by_id.get("MD-02", "").status != "missing" if "MD-02" in by_id else True