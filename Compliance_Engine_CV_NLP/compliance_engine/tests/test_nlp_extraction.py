"""Phase 6 - NLP declaration-extraction tests."""
from compliance_engine.nlp import regex_patterns as rx
from compliance_engine.nlp.declaration_extractor import extract_declarations
from compliance_engine.pipeline import run_scan


def _find(decls, field):
    return next((d for d in decls if d.field_name == field), None)


def test_unit_finder():
    assert rx._find_unit("52g") == "g"
    assert rx._find_unit("52 g") == "g"
    assert rx._find_unit("1.5 kg") == "kg"
    assert rx._find_unit("750 ml") == "ml"
    assert rx._find_unit("dozen") == ""        # non-standard, rejected by rule layer


def test_mrp_extractor():
    assert rx._extract_mrp("MRP Rs. 20.00 (incl. of all taxes)")[0]["value"] == "20.00"
    # Token-per-line OCR variant.
    hits = rx._extract_mrp("MRP / & / 20.00 / (incl. / of / all / taxes)")
    assert hits and hits[0]["value"] == "20.00"


def test_net_qty_extractor_handles_glued_unit():
    hits = rx._extract_net_quantity("Net Quantity: 52g")
    assert hits and hits[0]["unit"] == "g"
    assert hits[0]["amount"] == "52"


def test_declaration_extraction_package_001(sample_images):
    scan = run_scan(sample_images[0])
    decls = extract_declarations(scan)
    assert _find(decls, "mrp") and _find(decls, "mrp").value == "20.00"
    assert _find(decls, "net_quantity") is not None
    assert _find(decls, "use_by_date") is not None
    assert _find(decls, "month_year_of_manufacture") is not None


def test_manufacturer_zone_heuristic_absent_value(sample_images):
    """A manufacturer block with no parsed address yields an empty-value row."""
    scan = run_scan(sample_images[0])
    decls = extract_declarations(scan)
    m = _find(decls, "manufacturer_packer_importer")
    assert m is not None
    assert m.value == ""
    assert m.method == "heuristic"


# --- regression tests for fixed extraction bugs ------------------------------
def test_phone_extracts_tollfree_4_2_4_chunks():
    """'1800 22 4020' (standard toll-free format) must yield 1800224020."""
    hits = rx._extract_phone("Toll Free: 1800 22 4020 (Customer Care)")
    assert hits and hits[0]["value"] == "1800224020"


def test_mrp_extracts_mre_ocr_variant():
    """OCR often reads 'MRP' as 'mre' (package_002). Must still extract."""
    hits = rx._extract_mrp("= 68.00 mre")
    assert hits and hits[0]["value"] == "68.00"


def test_mrp_reversed_label_value():
    """'20.00 = MRP:' (value before label) must still extract."""
    hits = rx._extract_mrp("ye 20.00 = MRP:")
    assert hits and hits[0]["value"] == "20.00"


def test_net_qty_with_equals_separator():
    """OCR '=' between label and value (Wheet) must not block extraction."""
    hits = rx._extract_net_quantity("Net Quantity: = 11kg")
    assert hits and hits[0]["value"] == "11 kg"


def test_net_qty_reversed_label():
    """'id 120g Weight: Net' (number before label, package_003)."""
    hits = rx._extract_net_quantity("id 120g Weight: Net")
    assert hits and hits[0]["value"] == "120 g"


def test_net_qty_qualifier_not_from_far_away_text():
    """'Approx.' in a nutrition table must NOT qualify a clean net-qty line."""
    hits = rx._extract_net_quantity(
        "Net Quantity: 52g  Protein 2g (Approx. values per 100g)"
    )
    assert hits
    assert hits[0]["qualifiers"] == []  # tight window around the value


def test_product_name_picks_commodity_run():
    assert rx._extract_product_name("WHEAT FLOUR 100% atta")[0]["value"] == "Wheat Flour"
    assert rx._extract_product_name("Salted Potato Chips 20g")[0]["value"] == "Potato Chips"
    # ingredients line must not produce a 4-word run.
    assert len(rx._extract_product_name("Wheat Flour Maida Sugar Salt")[0]["value"].split()) <= 2


def test_unit_sale_price_extracts_garbled():
    hits = rx._extract_unit_sale_price("Unit Sle Pre: €60.00 perkg")
    assert hits and hits[0]["value"] == "60.00"