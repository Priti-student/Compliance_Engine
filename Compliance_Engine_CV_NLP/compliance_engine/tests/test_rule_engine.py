"""Phase 7 - rule engine & validator tests."""
from compliance_engine.rules.rule_engine import RuleEngine, RuleContext, overall_status
from compliance_engine.rules.rule_loader import Rule, load_all
from compliance_engine.schema import DeclarationInfo, FontMetricInfo


def _rule(rule_id="R-1", field_name="x", logic=None, ref="Rule X"):
    return Rule(rule_id=rule_id, rule_reference=ref, field_name=field_name,
                validation_logic=logic or {"type": "presence_check"})


def test_presence_check_missing():
    from compliance_engine.rules.validators import presence_check
    v = presence_check(None, _rule(), RuleContext())
    assert v is not None and v.status == "missing"


def test_presence_check_passes_with_value():
    from compliance_engine.rules.validators import presence_check
    d = DeclarationInfo(field_name="x", value="10 g")
    assert presence_check(d, _rule(), RuleContext()) is None


def test_unit_check_rejects_dozen():
    from compliance_engine.rules.validators import presence_and_unit_check
    d = DeclarationInfo(field_name="net_quantity", value="10 dozen")
    v = presence_and_unit_check(d, _rule(), RuleContext())
    assert v is not None and v.status == "non_compliant"
    assert "dozen" in v.reason


def test_unit_check_allows_grams():
    from compliance_engine.rules.validators import presence_and_unit_check
    d = DeclarationInfo(field_name="net_quantity", value="52 g")
    assert presence_and_unit_check(d, _rule(), RuleContext()) is None


def test_date_format_accepts_ddmmyyyy():
    from compliance_engine.rules.validators import presence_and_date_format_check
    d = DeclarationInfo(field_name="month_year_of_manufacture", value="10/07/2024")
    assert presence_and_date_format_check(d, _rule(), RuleContext()) is None


def test_date_format_rejects_garbage():
    from compliance_engine.rules.validators import presence_and_date_format_check
    d = DeclarationInfo(field_name="month_year_of_manufacture", value="sometime 2024")
    v = presence_and_date_format_check(d, _rule(), RuleContext())
    assert v is not None and v.status == "non_compliant"


def test_mrp_rounding_accepts_00_paise():
    from compliance_engine.rules.validators import format_regex_and_value_check
    d = DeclarationInfo(field_name="mrp", value="20.00",
                        raw_text="MRP Rs. 20.00 (incl. of all taxes)")
    assert format_regex_and_value_check(d, _rule(), RuleContext()) is None


def test_mrp_rounding_rejects_10_paise():
    from compliance_engine.rules.validators import format_regex_and_value_check
    d = DeclarationInfo(field_name="mrp", value="20.10",
                        raw_text="MRP Rs. 20.10 (incl. of all taxes)")
    v = format_regex_and_value_check(d, _rule(), RuleContext())
    assert v is not None and "round" in v.reason


def test_mrp_missing_incl_qualifier_is_needs_review():
    """An OCR window that doesn't show 'incl of all taxes' is not proof the
    qualifier is missing on the physical label -> needs_review, not a hard
    non_compliant."""
    from compliance_engine.rules.validators import format_regex_and_value_check
    d = DeclarationInfo(field_name="mrp", value="20.00",
                        raw_text="MRP Rs. 20.00")
    v = format_regex_and_value_check(d, _rule(), RuleContext())
    assert v is not None
    assert v.status == "needs_review"
    assert v.severity == "low"
    assert "incl" in v.reason


def test_contact_check_requires_phone_or_email():
    from compliance_engine.rules.validators import presence_and_contact_format_check
    d = DeclarationInfo(field_name="consumer_care_details",
                        raw_text="customer care available")
    v = presence_and_contact_format_check(d, _rule(), RuleContext())
    assert v is not None and v.status == "non_compliant"


def test_ner_check_requires_address_evidence():
    from compliance_engine.rules.validators import presence_and_ner_check
    d = DeclarationInfo(field_name="manufacturer_packer_importer",
                        raw_text="ACME Corp")
    v = presence_and_ner_check(d, _rule(), RuleContext())
    assert v is not None and v.status == "non_compliant"
    assert "address" in v.reason


def test_ner_check_passes_with_pin():
    from compliance_engine.rules.validators import presence_and_ner_check
    d = DeclarationInfo(field_name="manufacturer_packer_importer",
                        raw_text="PepsiCo India Holdings Pvt. Ltd., Channo, "
                                 "Patiala 147105, Punjab, India")
    assert presence_and_ner_check(d, _rule(), RuleContext()) is None


def test_conditional_presence_not_applicable():
    from compliance_engine.rules.validators import conditional_presence_check
    rule = _rule(field_name="dimensions",
                 logic={"type": "conditional_presence_check",
                        "condition": "product_category in ['textiles']"})
    ctx = RuleContext(metadata={"product_category": "food"})
    v = conditional_presence_check(None, rule, ctx)
    assert v is not None and v.status == "not_applicable"


def test_font_height_requires_calibration():
    from compliance_engine.rules.validators import font_height_general_check
    metric = FontMetricInfo(zone_type="mrp_block", char_height_px_median=11.0,
                            calibrated=False)
    v = font_height_general_check(metric, _rule(ref="Rule 7(3)"), 1.0)
    assert v is not None and v.status == "needs_review"
    assert "calibrat" in v.reason


def test_font_height_flags_small_text():
    from compliance_engine.rules.validators import font_height_general_check
    metric = FontMetricInfo(zone_type="net_qty_block", char_height_px_median=10.0,
                            char_height_mm_median=0.5, calibrated=True)
    v = font_height_general_check(metric, _rule(ref="Rule 7(3)"), 1.0)
    assert v is not None and v.status == "non_compliant"


def test_rule_engine_full_evaluation_missing_and_na():
    bundle = load_all()
    engine = RuleEngine(bundle)
    violations, stats = engine.evaluate(
        [DeclarationInfo(field_name="mrp", value="20.00",
                         raw_text="MRP Rs.20.00 incl of all taxes")],
        [],
        metadata={},
    )
    by_id = {v.rule_id: v for v in violations}
    # MD-05 (mrp) is compliant (no violation row).
    assert "MD-05" not in by_id
    # MD-09 (ecommerce) is N/A for a physical package scan.
    assert by_id["MD-09"].status == "not_applicable"
    assert stats.missing >= 2          # several mandatory declarations absent
    assert stats.not_applicable >= 2   # dimensions + country of origin + ecommerce
    assert overall_status(stats) == "non_compliant"


def test_consumer_care_passes_when_phone_extracted_elsewhere():
    """MD-07 must pass when consumer_phone/email was extracted from any source."""
    bundle = load_all()
    engine = RuleEngine(bundle)
    violations, _ = engine.evaluate(
        [
            DeclarationInfo(field_name="consumer_care_details", value="",
                            raw_text="call us for complaints", method="heuristic"),
            DeclarationInfo(field_name="consumer_phone", value="18001234567",
                            source_zone="full_image"),
        ],
        [],
        metadata={},
    )
    by_id = {v.rule_id: v for v in violations}
    assert "MD-07" not in by_id or by_id["MD-07"].status != "non_compliant"


def test_mrp_validator_sees_label_in_raw_text():
    """A full-image-sourced MRP row carries label context in raw_text."""
    from compliance_engine.rules.validators import format_regex_and_value_check
    d = DeclarationInfo(field_name="mrp", value="100",
                        raw_text="NET WT 500 g MRP Rs.100 (incl. of all taxes)")
    assert format_regex_and_value_check(d, _rule(), RuleContext()) is None