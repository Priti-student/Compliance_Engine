# LMPC Compliance Engine — CV/OCR + NLP + Rule Engine (Phases 0–7)

Full image-to-compliance pipeline for the Legal Metrology (Packaged
Commodities) Rules, 2011 scanning system. One product/label image in →
structured compliance report out (declarations found/missing + violations).

## Status

| Phase | What                             | State                                                          |
|-------|----------------------------------|----------------------------------------------------------------|
| 0     | Environment & scaffold           | Done — `compliance_engine/` package                            |
| 1     | Quality gate                     | Done — `cv/quality.py`                                         |
| 2     | Preprocessing                    | Done — `cv/preprocessing.py`                                   |
| 3     | Zone detection (heuristic)       | Done — `cv/zone_detection.py`                                  |
| 4     | OCR extraction (Tesseract)       | Done — `cv/ocr_engine.py`                                      |
| 5     | Font metrics & calibration       | Done — `cv/font_metrics.py` (barcode px→mm)                    |
| 6     | Declaration extraction (regex)   | Done — `nlp/` (spaCy/BERT residue later)                       |
| 7     | Rule-engine compliance           | Done — `rules/` (data-driven off the JSON rule DB)             |
| 8     | Report generation (PDF/XLSX/JSON)| Done — `reports/` (ReportLab + openpyxl)                       |
| 9     | Repository & scan history        | Done — `repository/` (file-backed store + search)              |
| 10    | Dashboard aggregation            | Done — `dashboard.py` + `/dashboard/summary`                  |
| 3*    | YOLOv8 region detector           | Future upgrade (needs labeled data)                            |
| 6*    | spaCy / BERT classification      | Future upgrade                                                 |
| 8+    | PDF/editable report generation   | Teammate scope (consumes ComplianceReport json)               |

## Setup (Windows)

1. Install Tesseract 5.x (`C:\Program Files\Tesseract-OCR\tesseract.exe`).
2. venv packages:
   ```
   opencv-python numpy scikit-image imutils fastapi uvicorn pydantic pytest
   python-multipart httpx2 spacy
   ```

## Run

```bash
# Tests (from repo root)
venv/Scripts/python.exe -m pytest compliance_engine/tests -q

# API server
venv/Scripts/python.exe -m uvicorn compliance_engine.api:app --port 8000

# CV-only scan (Phases 1-4)
curl -F "file=@package_001.jpg" http://127.0.0.1:8000/cv/scan

# Full compliance scan (Phases 1-7)
curl -F "file=@package_001.jpg" http://127.0.0.1:8000/compliance/scan

# With manual calibration + metadata
curl -F "file=@package_001.jpg" \
     -F "calibration_mm_per_px=0.05" \
     -F "metadata={\"product_category\":\"food\"}" \
     http://127.0.0.1:8000/compliance/scan

# Generate + download report (PDF/XLSX/JSON into ./data/reports)
curl -F "file=@package_001.jpg" -F "metadata={\"scan_id\":\"pkg001\"}" \
     http://127.0.0.1:8000/compliance/scan/report

# Repository + dashboard
curl http://127.0.0.1:8000/repository/scans?limit=10
curl "http://127.0.0.1:8000/repository/search?q=pepsico"
curl http://127.0.0.1:8000/repository/stats
curl http://127.0.0.1:8000/dashboard/summary
```

All report/repository/dashboard data is written under `./data/` by default.
OpenAPI docs: http://127.0.0.1:8000/docs

## Module map

```
compliance_engine/
  config.py            # all tunables (thresholds, patterns, psm modes)
  schema.py            # dataclasses = JSON contract (ScanResult, ComplianceReport)
  pipeline.py          # run_scan() (Phases 1-4), run_full_pipeline() (Phases 1-7)
  api.py               # FastAPI: /cv/scan, /cv/health, /compliance/scan
  cv/
    quality.py         # Phase 1 - blur/brightness/resolution gate
    preprocessing.py   # Phase 2 - CLAHE -> denoise -> deskew -> perspective rectify
    lighting.py        #            helpers
    perspective.py     #            helpers
    zone_detection.py  # Phase 3 - keyword-tagged declaration zones
    ocr_engine.py      # Phase 4 - per-zone + full-image Tesseract OCR
    font_metrics.py    # Phase 5 - char-height (px+mm), contrast, barcode calibration
  nlp/
    regex_patterns.py          # Phase 6 - MRP/net-qty/date/FSSAI/batch/phone/email patterns
    declaration_extractor.py   # Phase 6 - turns ScanResult into DeclarationInfo rows
  rules/
    rule_loader.py     # Phase 7 - loads rules/lmpc_rules_database.json
    validators.py      # Phase 7 - one function per validation_logic.type
    rule_engine.py     # Phase 7 - dispatches rules, produces Violations + stats
  reports/
    pdf_report.py      # Phase 8 - ReportLab PDF certificate
    xlsx_report.py     # Phase 8 - openpyxl editable workbook
    base.py            # Phase 8 - shared serializer / version helpers
  repository/
    store.py           # Phase 9 - file-backed scan store + search
  dashboard.py         # Phase 10 - dashboard aggregates (status/trend/officer)
  docs/
    ARCHITECTURE.md    # technical documentation (architecture + deployment)
  tests/               # pytest suite (75 tests pass)
  examples/
    scan_package_001.json        # Phase 1-4 example output
    smoke_full_pipeline.py       # run Phases 1-7 on any image from CLI
    smoke_api.py                 # Phase 1-7 over the API
    smoke_phase8_10.py           # report + repository + dashboard smoke
    generate_demo.py             # build the full demo dataset
    debug_image.py               # inspect a single image / OCR detail
```

## How the phases connect

1. **Phases 1-4**: image → quality gate → preprocess → declaration-zone
   detection → per-zone + full-image OCR (word-level boxes).
2. **Phase 5**: Tesseract char-box heights per zone (px); when an EAN-13/UPC-A
   barcode is in the shot, its standardized 37.29 mm width gives mm/px and
   char heights become mm. WCAG-style text/background contrast ratio is also
   computed as a legibility proxy.
3. **Phase 6**: regex layer extracts declarations (mrp, net_quantity,
   month_year_of_manufacture, use_by_date, batch_number, fssai_license,
   consumer_phone/email) from zone + full-image text.
4. **Phase 7**: rule engine reads `rules/lmpc_rules_database.json`, matches
   each mandatory rule (MD-01..MD-10), Rule 7(3) font-height, and placement
   references (PL-*) → violations + stats + overall compliance status.

## Declarations mapped to zones (config.py)

`mrp_block`, `unit_sale_price_block`, `net_qty_block`, `mfg_date_block`,
`expiry_date_block`, `batch_block`, `fssai_block`, `consumer_care_block`,
`manufacturer_address_block` — same naming scheme used by
`rules/lmpc_rules_database.json`.

## Rule-engine design (data-driven)

- All thresholds/logic references live in `rules/lmpc_rules_database.json`;
  updating a rule is a JSON edit, no code redeploy.
- Each `validation_logic.type` maps to one function in `rules/validators.py`
  (`REGISTRY`). Unknown types fall back to `presence_check`.
- Conditions (e.g. `product_category in ['textiles']`) are evaluated safely
  against the `metadata` map passed by callers; rules whose condition is not
  met emit `not_applicable`, and `ecommerce_declarations` is auto-N/A for
  physical package scans.

## Known limitations (Phase 9 tuning targets)

- OCR accuracy is best on sharp, front-facing labels; busy small labels
  (e.g. `package_002.jpg`) still produce noise and can under-extract.
- Font-size checks need calibration: use an in-image barcode (auto) or pass
  `calibration_mm_per_px` (manual). Uncalibrated font rules are reported as
  `needs_review`, not false "non_compliant".
- These are single-face scans:  some "missing" declarations (consumer-care,
  mfg date, manufacturer address) live on the back panel of the same package
  and are genuinely absent from the imaged side -- a second photo would
  resolve them.
- `unit_sale_price` (MD-10) is effective-date sensitive (2021-2023 LMPC
  amendments, repeatedly deferred); when not detected it is reported as
  `needs_review` unless the caller passes `enforce_unit_sale_price`.
- OCR artifacts that are now absorbed: reversed `MRP 20.00: = MRP`,
  `mre` for `MRP`, `Net Quantity: = 11kg` `=`-separators, nutrition-table
  "Approx." no longer mis-flags net-qty, toll-free `1800 22 4020` form,
  and generic commodity name (MD-02) extraction from full-image text.
- Zone detection is heuristic; a fine-tuned YOLOv8 model is the planned
  upgrade for low-confidence cases.
- English-language labels only for now; spaCy/BERT layers are the planned
  Phase 6 upgrade for ambiguous multi-line blocks.
- The rules DB is a first working draft — verify thresholds against the
  consolidated gazette text before production use.