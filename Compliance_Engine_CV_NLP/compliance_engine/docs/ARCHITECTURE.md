# LMPC Compliance Engine — Technical Documentation

## 1. Overview

A software system that scans packaged-commodity labels/images and automatically
assesses compliance with the **Legal Metrology (Packaged Commodities) Rules,
2011**. Input: one product image. Output: a compliance report (declarations
found/missing, violations, verdict) in PDF / XLSX / JSON + a persistent
repository and dashboard aggregates.

```
  product image
      │  Phase 1-4: CV/OCR
      ▼
  quality gate → preprocess → zone detection → OCR (Tesseract)
      │  Phase 5
      ▼
  font metrics + barcode calibration (px→mm) + contrast
      │  Phase 6
      ▼
  declaration extraction (regex extractors)
      │  Phase 7
      ▼
  rule engine (rules/lmpc_rules_database.json → validators → violations)
      │  Phase 8-10
      ▼
  PDF+XLSX+JSON exports │ file-backed repository │ dashboard metrics
```

## 2. Architecture

| Component | Module | Responsibility |
|---|---|---|
| API layer | `api.py` | FastAPI endpoints for scan / report / repository / dashboard |
| Pipeline | `pipeline.py` | `run_scan()` (Phases 1-4) + `run_full_pipeline()` (Phases 1-7) |
| CV/OCR | `cv/quality.py`, `cv/preprocessing.py`, `cv/zone_detection.py`, `cv/ocr_engine.py`, `cv/font_metrics.py` | image gate → preprocess → zone detection → Tesseract OCR → font metrics + barcode calibration |
| NLP | `nlp/regex_patterns.py`, `nlp/declaration_extractor.py` | deterministic declaration extraction (regex layer) |
| Rule engine | `rules/rule_loader.py`, `rules/validators.py`, `rules/rule_engine.py` | data-driven evaluation of `rules/lmpc_rules_database.json` |
| Reports | `reports/` | PDF (ReportLab), XLSX (openpyxl), JSON export |
| Repository | `repository/store.py` | file-backed scan history + search |
| Dashboard | `dashboard.py` | aggregate metrics for the UI |
| Schema | `schema.py` | dataclasses = the JSON contract between phases |

## 3. JSON contract

- **ScanResult** (Phases 1-4): quality report, preprocessing transforms,
  detected declaration zones (type, bbox, OCR words), full-image OCR text.
- **ComplianceReport** (Phases 1-7): `ScanResult` + calibration + font metrics +
  extracted `DeclarationInfo` rows + `Violation` rows + `ComplianceStats` +
  `compliance_status` + operator `advice` (re-capture advisory).

The API returns these as JSON; the report endpoints serialize them to
PDF / XLSX.

## 4. Deployment model

### 4.1 Local development (this repo)

```bash
venv/Scripts/python.exe -m pip install -r requirements.txt   # see repo README
venv/Scripts/python.exe -m uvicorn compliance_engine.api:app --reload --port 8000
```

Requires system **Tesseract 5.x** (`C:\Program Files\Tesseract-OCR\tesseract.exe`
or on PATH). Rules live in `rules/lmpc_rules_database.json`; reports/repository
write to `data/` by default.

### 4.2 Production (target)

| Concern | Suggested |
|---|---|
| API | FastAPI behind uvicorn/gunicorn workers |
| Storage | PostgreSQL for `ComplianceReport` rows; object store (AWS S3/MinIO) for images + generated PDF/XLSX |
| Auth/RBAC | JWT + OAuth2 (Enforcement Officer / Reviewer / Admin); out of scope here |
| Model services | OCR as a queue job (Celery/RQ) for high volume |
| Deployment | Docker image: python:3.13-slim + libtesseract + this package; Kubernetes/ECS for scale |

The `repository.store` is intentionally a thin file-backed implementation so it
can be swapped for SQL/S3 without changing the API surface.

## 5. Rule engine design (data-driven)

- All thresholds/rule references are in `rules/lmpc_rules_database.json`;
  editing a rule is a **data change**, not a code change.
- `validators.py` implements one function per `validation_logic.type`
  (`presence_check`, `presence_and_unit_check`, `format_regex_and_value_check`,
  `presence_and_contact_format_check`, `presence_and_ner_check`,
  `conditional_presence_check`, ...) keyed by `REGISTRY`.
- Unknown/unrecognized rule types fall back to `presence_check`.
- Rules can be gated by `metadata` (e.g. `product_category`,
  `package_flagged_as_imported`, `enforce_unit_sale_price`).

## 6. Report formats

- **PDF**: verdict banner + metadata + declarations + violations + font metrics
  (ReportLab, A4).
- **XLSX**: 4 sheets — Summary / Declarations / Violations / FontMetrics
  (editable evidence for officers).
- **JSON**: same data machine-readable (matches the API body).

## 7. Testing

`pytest compliance_engine/tests -q` (75 tests):
- unit: quality, preprocessing, zone detection, OCR, font/barcode
- unit: regex extractors (MRP variants, net-qty, phone, dates)
- unit: every validator (format, units, dates, MRP, contact, NER)
- integration: full pipeline on 5 sample images, API endpoints, report export,
  repository, dashboard.

## 8. Known limitations & roadmap

- OCR accuracy depends on photo quality; high-glare/low-contrast images are
  flagged with a **re-capture advisory** (`ComplianceReport.advice`).
- Single-face scans miss back-panel declarations (second photo recommended).
- English-only labels currently.
- spaCy/BERT classification + YOLOv8 zone detection are the planned Phase 6/3
  upgrades; the schema already supports them.
- The rules DB is a first draft — verify thresholds against the consolidated
  gazette text before production enforcement.

## 9. Roles & responsibilities (team split)

| Area | Owner |
|---|---|
| CV/OCR, declaration extraction, rule engine, reports, repository, dashboard | this module (Phases 1-10) |
| Backend storage (PostgreSQL/S3), auth/RBAC (JWT/OAuth2) | backend teammate |
| Frontend (React + Tailwind + Recharts), PDF queue, dashboards UI | frontend teammate |

## 10. Quick reference

```bash
# API
venv/Scripts/python.exe -m uvicorn compliance_engine.api:app --port 8000

# Full test suite
venv/Scripts/python.exe -m pytest compliance_engine/tests -q

# Manual scan of one image
venv/Scripts/python.exe compliance_engine/examples/smoke_full_pipeline.py package_001.jpg

# All 5 samples via API test client
venv/Scripts/python.exe compliance_engine/examples/smoke_api.py

# Phase 8-10 (report + repository + dashboard) smoke
venv/Scripts/python.exe compliance_engine/examples/smoke_phase8_10.py
```