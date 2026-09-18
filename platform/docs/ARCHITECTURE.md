# LMPC Compliance Platform — Technical Architecture

## 1. System overview

```
  package image (smartphone camera)
        ▼                 CV/OCR ENGINE (teammate, :8000, READ-ONLY)
  POST /compliance/scan   (image bytes + metadata JSON)
        ▼  ComplianceReport JSON (status/declarations/violations/font/stats)
  ─────────────────────────────────────────────────────────────────
  LMPC COMPLIANCE PLATFORM   (this repo)
    │
    ├─ API layer   FastAPI (:8001)  REST /api/*
    ├─ Services    inspection_service · report_service · dashboard_service · search_service
    ├─ Storage     Storage protocol → LocalStorage | S3Storage (boto3/MinIO)
    ├─ Data        PostgreSQL (SQLAlchemy 2.x, JSON-with-JSONB-variant DDL)
    └─ UI          React 18 + Tailwind + Recharts (:5173 dev, proxied /api)
```

## 2. Technology stack

| Layer | Technology |
|---|---|
| Web API | Python 3.11 · FastAPI 0.141 · Uvicorn |
| ORM / DB | SQLAlchemy 2.0 · PostgreSQL 18 (JSONB via variant; SQLite for tests) |
| Auth | OAuth2 password flow · JWT (PyJWT) · PBKDF2-HMAC-SHA256 (600k iters) |
| RBAC | Enforcement Officer / Reviewer / Admin via `require_roles(...)` dependency |
| Storage | AWS S3 via boto3 (or MinIO) with automatic local fallback |
| Reports | ReportLab (PDF) · openpyxl (XLSX) · JSON envelope |
| Images | Pillow (zone-box annotation + PDF embeds) |
| Frontend | React 18 · TypeScript · Tailwind CSS · Recharts 2 · Vite 5 |
| Tests | pytest + FastAPI TestClient (sqlite in-memory) · `scripts/run_e2e.py` |

## 3. Database model (PostgreSQL: `lmpc_platform`)

```
users       id, username*, email*, full_name, password_hash, role, is_active, last_login_at
products    id, generic_name*, brand, category, manufacturer, packer, importer,
            net_quantity_text, mrp, batch_no, created_by→users
inspections id, token*, product_id→products, image_key, image_name, image_mime,
            image_size, engine_scan_id, compliance_status, workflow_status
            (open|reviewed|approved), compliance_json(JSONB), stats_json(JSONB),
            advice_json(JSON), remarks, officer_id→users, reviewed_by→users, reviewed_at
declarations id, inspection_id→inspections*, field_name*, value, raw_text, confidence,
             method, source_zone, qualifiers(JSON), rule_id
violations   id, inspection_id*, rule_id*, rule_reference, field_name, status,
             severity, reason, evidence(JSON)
font_metrics id, inspection_id*, zone_type, char_height_px_median, char_height_mm_median,
             contrast_ratio, calibrated
report_artifacts id, inspection_id*, report_type(pdf|xlsx|json), storage_key*, filename,
             size_bytes, created_by, created_at
evidence     id, inspection_id*, storage_key, filename, mime_type, size_bytes,
             uploaded_by, created_at
```
Indexes: `inspections(compliance_status)`, `inspections(officer_id)`,
`inspections(created_at)`, `declarations(field_name)`, `violations(rule_id)`,
`products(generic_name)`.

## 4. Request flow (new scan)

1. Officer uploads image (+ optional metadata JSON) → `POST /api/inspections`.
2. Image is stored first (`inspections/{token}/{file}`) through the `Storage`
   backend.
3. The **engine client** (httpx) calls the CV/OCR engine's
   `/compliance/scan` and receives the ComplianceReport JSON (engine owned;
   schema in `Compliance_Engine/.../compliance_engine/schema.py`).
4. `inspection_service` persists the inspection row + normalised
   declarations/violations/font metrics; a `Product` row is created/updated
   from extracted declarations (generic name, net qty, MRP, manufacturer).
5. `report_service.generate_all` renders **PDF + XLSX + JSON** artifacts,
   uploads them to storage and records `report_artifacts` rows.
6. The UI redirects to `/inspections/{token}` where officers/reviewers see
   verdict, declarations, violations, font metrics, annotated image, evidence
   and download buttons.

If the engine is offline, `POST /api/inspections/from-demo` imports one of the
stored engine demo reports (training / demo mode) — same persistence path.

## 5. Reports

- **PDF** (ReportLab platypus, A4): GOV header + report number `LMPC-YYYYMMDD-XXXXXX`,
  verdict banner (color-coded), inspection & product metadata, annotated package
  image with detected zones, declarations table, violations table, font-metrics
  table, evidence exhibits, signature blocks, footer with page numbers.
- **XLSX** (openpyxl): sheets `Summary / Product / Declarations / Violations /
  FontMetrics / Evidence`, frozen header row + auto-filters (editable evidence).
- **JSON**: `{meta, compliance_report}` envelope identical to the engine output.
- Artifacts are re-generatable (`POST /api/reports/{token}`) and served via
  authenticated endpoints that accept header or `?access_token=` bearer.

## 6. Auth / RBAC

- Passwords: salted PBKDF2 (stdlib), never stored in plain text.
- JWT: HS256, role + sub claims, 60 min expiry, `OAuth2PasswordBearer`.
- Roles:
  - **Officer** — scan products, browse repository, download reports.
  - **Reviewer** — everything Officer + mark reviewed/approved, add remarks.
  - **Admin** — everything + user management & role assignment.
- Enforcement: `require_roles(...)` FastAPI dependency; frontend hides routes by
  role. `401` clears the token; `403` blocks role violations server-side.

## 7. Dashboard

`dashboard_service` aggregates over PostgreSQL (status distribution, 30-day
violation trend, top violated rules, officer activity, category stats, recent
inspections). The React UI renders them with Recharts (donut, line, bar) and a
KPI card row. All aggregations are portable across SQLite/PostgreSQL (no
JSONB-specific SQL in queries).

## 8. Search

`search_service` performs a free-text ILIKE match over product
name/brand/manufacturer, image name, remarks and inspection token, combined
with optional filters (compliance status, category, officer, date range),
ordered newest-first with pagination, plus a product-name autocomplete
(`/api/search/suggest`).

## 9. Failure handling

- Engine unreachable → `503 EngineUnavailable` on upload (image upload is
  rolled back); demo import remains available.
- Storage S3 failure → automatic local fallback at boot (`get_storage()`).
- Report generation failure after a successful scan is non-fatal: the scan is
  persisted and artifacts can be regenerated on demand.
- Seed is idempotent (upsert users; demo import skipped when rows exist unless
  `SEED_DEMO=force`).