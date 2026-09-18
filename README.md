# LMPC Compliance System — Packaged Commodities Scanning & Compliance Platform

**Legal Metrology (Packaged Commodities) Rules, 2011 — automated image/label
inspection, declaration extraction, rule-based compliance checking, reporting
and enforcement dashboards.**

This repository (`Compliance_Engine/`) contains the entire **Sitara** project:
the CV/OCR compliance engine, the web platform (backend + frontend), OCR
language data, launchers and configuration. The only component that lives
outside this folder is `engine_venv/` (the engine's Python environment), which
the launchers reference via relative paths.

---

## 1. Project overview

Packaged commodities sold through retail stores, supermarkets and e-commerce
platforms in India must bear mandatory declarations under the **Legal
Metrology Act, 2009** and the **Legal Metrology (Packaged Commodities) Rules,
2011** — for example:

- Name and address of manufacturer / packer / importer
- Common or generic name of the commodity
- Net quantity in standard units
- Month and year of manufacture / packing / import
- MRP with the mandatory *"incl. of all taxes"* qualifier
- Consumer care details (phone / e-mail)
- Batch / use-by / best-before information where applicable
- Font size & numeral-height minima (Rule 7), placement & manner rules
  (Rules 8–9)

Manual inspection of these declarations is slow and inconsistent, so this
system automates it: a **product photograph** goes in, a **structured
compliance report** (verdict, extracted declarations, violations, font
metrics) and digital artifacts (PDF / XLSX / JSON) come out, and everything is
stored in a searchable repository with an enforcement dashboard.

---

## 2. Architecture at a glance

```
 product image / label photograph
        │
        ▼  POST /compliance/scan  (image + metadata)
┌───────────────────────────────┐         ┌─────────────────────────────────────┐
│ CV/OCR ENGINE  (:8000)        │   HTTP  │ LMPC COMPLIANCE PLATFORM  (:8001)   │
│ · quality gate                │ ──────► │ · FastAPI REST API                  │
│ · OpenCV preprocessing        │  (read- │ · Auth (JWT) + RBAC                 │
│ · zone detection              │  only)  │ · PostgreSQL persistence            │
│ · Tesseract OCR               │         │ · S3 / local object storage         │
│ · font metrics & calibration  │         │· PDF / XLSX / JSON reports          │
│ · declaration extraction      │         │ · Dashboards & product search       │
│ · rule-engine compliance      │         │ · React + Tailwind + Recharts UI    │
└───────────────────────────────┘         │   (web app on :5173)                │
                                          └─────────────────────────────────────┘
```

The two services communicate over HTTP only. The `Compliance_Engine_CV_NLP/`
engine is owned by a teammate and is consumed **read-only** — the platform
never imports or modifies its code.

---

## 3. Folder structure (inside `Compliance_Engine/`)

```
Compliance_Engine/
├── Compliance_Engine_CV_NLP/         # CV/OCR engine (teammate module)
│   ├── compliance_engine/            #   FastAPI package (Phases 0–10)
│   │   ├── api.py                    #   /cv/health, /cv/scan, /compliance/scan …
│   │   ├── pipeline.py               #   run_scan() + run_full_pipeline()
│   │   ├── schema.py                 #   JSON contract (ScanResult, ComplianceReport)
│   │   ├── config.py                 #   tunable knobs (thresholds, psm, patterns)
│   │   ├── cv/                       #   quality, preprocessing, zone detection,
│   │   │                             #   ocr_engine, font_metrics, lighting, perspective
│   │   ├── nlp/                      #   declaration extraction (regex layer)
│   │   ├── rules/                    #   data-driven rule evaluator on the JSON rule DB
│   │   ├── reports/                  #   engine's PDF/XLSX/JSON exporters
│   │   ├── repository/               #   file-backed scan repository (demo)
│   │   ├── dashboard.py              #   aggregate metrics (Phase 10)
│   │   ├── examples/  tests/  docs/  #   demo scripts, 75 tests, docs
│   ├── rules/lmpc_rules_database.json#   digitized LMPC rule database
│   ├── data/demo/                    #   sample reports + repository (engine demo)
│   └── *.jpg / *.jpeg                #   sample product images (package_001 …, Lays, Wheet)
│
├── platform/                         # LMPC web platform (this team's deliverable)
│   ├── backend/                      #   FastAPI service (:8001)
│   │   ├── app/
│   │   │   ├── main.py               #     app factory, CORS, lifespan seed
│   │   │   ├── config.py             #     env-driven settings (.env)
│   │   │   ├── database.py           #     SQLAlchemy engine/session
│   │   │   ├── models/               #     users, products, inspections, violations,
│   │   │   │                         #     declarations, font_metrics, artifacts, evidence
│   │   │   ├── schemas/              #     Pydantic DTOs
│   │   │   ├── core/                 #     security (JWT+RBAC), storage (S3/local),
│   │   │   │                         #     engine HTTP client, exceptions
│   │   │   ├── api/                  #     auth, users, products, inspections, reports,
│   │   │   │                         #     search, dashboard, rules, health
│   │   │   └── services/             #     inspection/report/dashboard/search/seed + PDF,
│   │   │                             #     XLSX builders, annotation, demo import
│   │   ├── tests/                    #     pytest suite (32 tests, sqlite in-memory)
│   │   └── run.py                    #     headless-safe uvicorn launcher
│   ├── frontend/                     #   React 18 + TS + Tailwind + Recharts (:5173)
│   │   └── src/                      #     login, dashboard, scan, report, repository,
│   │                                 #     products, users, rules pages
│   ├── scripts/                      #   seed, run_e2e, real_scan, start_engine,
│   │                                 #   start_platform, fetch_tessdata, smokes/probes
│   ├── docs/                         #   ARCHITECTURE.md, DEPLOYMENT.md
│   ├── storage_data/                 #   local object-storage fallback (images/artifacts)
│   ├── venv/                         #   platform Python environment (Python 3.11)
│   ├── requirements.txt
│   ├── .env.example → .env           #   configuration (PostgreSQL, JWT, S3, engine URL)
│   └── README.md                     #   platform-scoped readme (see also this file)
│
├── tessdata/                         # eng.traineddata for Tesseract (OCR language data)
├── data/                             # engine runtime data (reports/repository)
├── start_engine.bat                  # engine launcher (:8000, sets TESSDATA_PREFIX)
├── engine_requirements.txt           # dependencies for the engine environment
└── engine_server.log / .err.log      # engine runtime logs
```

<small>Outside this folder: `Sitara/engine_venv/` — the engine's Python runtime
(kept outside intentionally; `start_engine.bat` and
`platform/scripts/start_engine.py` resolve it as `..\engine_venv`).</small>

---

## 4. Technology stack

| Layer | CV/OCR engine (`:8000`) | Platform (`:8001`) + UI (`:5173`) |
|---|---|---|
| Language | Python 3.11 (engine_venv) | Python 3.11 (platform/venv) |
| Web API | FastAPI + Uvicorn | FastAPI + Uvicorn |
| Image / OCR | OpenCV 5.x, NumPy, scikit-image, imutils, Tesseract 5.x + pytesseract | Pillow (annotation, PDF images) |
| NLP / extraction | regex declaration extractors (spaCy/BERT planned) | — (consumes engine output) |
| Rules | data-driven `rules/lmpc_rules_database.json` + custom evaluator | read-only rules viewer (`GET /api/rules`) |
| Persistence | JSON-file repository (demo) | PostgreSQL 18 (SQLAlchemy 2.x) |
| Object storage | — | AWS S3 via boto3 / MinIO, local fallback |
| Reports | engine PDF (ReportLab) / XLSX (openpyxl) | branded PDF + editable XLSX + JSON |
| Auth / RBAC | none (internal service) | JWT (OAuth2 password flow) · Officer/Reviewer/Admin |
| Frontend | — | React 18 · TypeScript · Tailwind · Recharts · Vite |

---

## 5. How a scan works (end-to-end pipeline)

1. **Image capture** — officer uploads a package/label photo through the UI
   (or API `POST /api/inspections`).
2. **Storage** — the original image is persisted first
   (`inspections/{token}/…` in S3/local).
3. **Engine scan** — the platform forwards the image to the engine
   `POST /compliance/scan` (read-only HTTP):
   - Phase 1 · quality gate (blur/brightness/glare/resolution)
   - Phase 2 · OpenCV preprocessing (CLAHE, denoise, deskew, perspective)
   - Phase 3 · declaration-zone detection (MRP, net qty, dates, batch, FSSAI, …)
   - Phase 4 · Tesseract OCR (per-zone + full image, word-level boxes)
   - Phase 5 · font metrics + barcode px→mm calibration + contrast
   - Phase 6 · declaration extraction (regex layer)
   - Phase 7 · rule-engine evaluation off `lmpc_rules_database.json`
     (MD-01…MD-11, FS/font rules, PL placement rules) → violations + verdict
4. **Persistence** — the platform stores the full `ComplianceReport` JSON and
   normalised rows (declarations, violations, font metrics) in PostgreSQL and
   creates/updates a `Product` master row.
5. **Reports** — PDF (verdict banner, annotated package image, declaration &
   violation tables, font metrics, evidence, signatures), editable **XLSX**
   (6 sheets), and **JSON** are generated and stored as artifacts.
6. **Review & dashboard** — reviewers approve/reject; dashboards aggregate
   status, trends, top violated rules, officer activity; the product repository
   is searchable.

If the engine is offline (or for training), `POST /api/inspections/from-demo`
imports one of the stored engine demo reports through the same persistence
path.

---

## 6. Environment prerequisites

| Tool | Notes |
|---|---|
| PostgreSQL 18 | running on `localhost:5432`, databases `lmpc_platform` (+ `lmpc_platform_test`) |
| Python 3.11 | create venvs from the Store 3.11 interpreter (`py -3.11`) |
| Node / npm | 22 / 10 (frontend build & dev server) |
| Tesseract OCR 5.x | `C:\Program Files\Tesseract-OCR\tesseract.exe`; language data in `tessdata/` |
| Internet mirror | `files.pythonhosted.org` is blocked on some networks — pip uses the Tsinghua mirror (see READMEs) |

---

## 7. Setup (Windows)

```bat
:: 1) Database (superuser; creates lmpc_platform + lmpc_platform_test)
psql -U postgres -h localhost -f Compliance_Engine\platform\scripts\create_databases.sql

:: 2) Platform Python environment (from Python 3.11)
py -3.11 -m venv Compliance_Engine\platform\venv
Compliance_Engine\platform\venv\Scripts\python.exe -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r Compliance_Engine\platform\requirements.txt

:: 3) Configure
copy Compliance_Engine\platform\.env.example Compliance_Engine\platform\.env
::    edit DATABASE_URL / JWT_SECRET / S3 keys as needed (kept out of git)

:: 4) Engine Python environment (kept outside Compliance_Engine by design)
py -3.11 -m venv engine_venv
engine_venv\Scripts\python.exe -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r Compliance_Engine\engine_requirements.txt

:: 5) Tesseract OCR + English language data
::    install Tesseract 5.x (winget: UB-Mannheim.TesseractOCR)
::    download eng.traineddata into Compliance_Engine\tessdata\ :
Compliance_Engine\platform\venv\Scripts\python.exe Compliance_Engine\platform\scripts\fetch_tessdata.py

:: 6) Seed (users + 5 demo inspections with PDF/XLSX/JSON reports)
cd Compliance_Engine\platform\backend
..\venv\Scripts\python.exe -m app.services.seed
```

## 8. Running the system (three terminals)

```bat
:: Terminal 1 — CV/OCR engine (:8000)   (used by real scans)
Compliance_Engine\start_engine.bat
::    or: Compliance_Engine\platform\venv\Scripts\python.exe Compliance_Engine\platform\scripts\start_engine.py

:: Terminal 2 — platform backend (:8001)
cd Compliance_Engine\platform\backend
..\venv\Scripts\python.exe run.py

:: Terminal 3 — frontend (:5173, proxies /api → :8001)
cd Compliance_Engine\platform\frontend
npm install
npm run dev
```

Open **http://localhost:5173**. API docs (Swagger) at
**http://127.0.0.1:8001/docs**.

### Demo users

| Username | Password | Role |
|---|---|---|
| `admin` | `Admin@123` | Admin — user management, everything |
| `reviewer` | `Reviewer@123` | Reviewer — review/approve inspections |
| `officer` | `Officer@123` | Officer — scan products, browse reports |

> Reset these credentials before any shared/public deployment.

## 9. Platform API overview (all under `/api`, JWT-protected except login)

| Endpoint | Purpose |
|---|---|
| `POST /auth/login` · `GET /auth/me` · `POST /auth/refresh` | OAuth2/JWT session |
| `GET/POST/PATCH/DELETE /users*` | admin-only user & role management |
| `GET/POST/PATCH/DELETE /products*` | product master |
| `POST /inspections` (multipart image) | real engine scan → full persistence |
| `POST /inspections/from-demo` | offline/training mode (demo report import) |
| `GET /inspections` · `GET /inspections/{token}` | list/filter/detail with filters |
| `PATCH /inspections/{token}` | reviewer workflow (remarks/review/approve) |
| `POST /inspections/{token}/evidence` | attach supporting photos |
| `GET /inspections/{token}/image` | original or zone-annotated image |
| `POST /reports/{token}` · `GET /reports/{token}/{pdf,xlsx,json}` | generate/download artifacts |
| `GET /search` · `GET /search/suggest` | product-repository search + autocomplete |
| `GET /dashboard/*` | enforcement KPIs, trends, top violations, officers |
| `GET /rules` | read-only digitized LMPC rule database |
| `GET /health` | DB + engine connectivity |

Engine API (`:8000`): `GET /cv/health`, `POST /cv/scan`, `POST /compliance/scan`,
`POST /compliance/scan/report`, `GET /repository/*`, `GET /dashboard/summary`.

---

## 10. Report artifacts

- **PDF** (ReportLab, A4): GOV header, report number `LMPC-YYYYMMDD-XXXXXX`,
  color-coded verdict banner, inspection/product metadata, zone-annotated
  package image, declarations table, violations table, font-metric table,
  evidence exhibits, signature blocks, page-numbered footer.
- **XLSX** (openpyxl): editable workbook — `Summary / Product / Declarations /
  Violations / FontMetrics / Evidence` sheets with frozen headers + filters.
- **JSON**: `{meta, compliance_report}` envelope matching the engine output.
- Artifacts are re-generatable (`POST /api/reports/{token}`) and stored in
  S3/local under `inspections/{token}/reports/`.

## 11. Testing & validation

```bat
:: Platform backend unit/integration tests (sqlite in-memory, engine mocked)
cd Compliance_Engine\platform\backend && ..\venv\Scripts\python.exe -m pytest tests -q

:: Live end-to-end against real Postgres + storage (spawns uvicorn itself)
Compliance_Engine\platform\venv\Scripts\python.exe Compliance_Engine\platform\scripts\run_e2e.py

:: Real OCR scan through platform → engine → Postgres
Compliance_Engine\platform\venv\Scripts\python.exe Compliance_Engine\platform\scripts\real_scan.py [image]

:: Frontend production build
cd Compliance_Engine\platform\frontend && npm run build

:: Engine's own tests (per its README)
cd Compliance_Engine\Compliance_Engine_CV_NLP && ..\..\engine_venv\Scripts\python.exe -m pytest compliance_engine\tests -q
```

Current status: platform suite **32/32 tests**, live E2E **24/24 checks**,
engine suite **75 tests**, frontend **tsc + Vite build clean**, and real OCR
scans verified on sample images (e.g., `package_001.jpg` → `MRP 20.00`,
`Net 52 g`, `MFD 10/07/2024`, `Batch LT240710A`).

## 12. Deployment framework

- Stateless FastAPI app behind **uvicorn/gunicorn + Nginx** (static React `dist`
  + `/api` reverse proxy), PostgreSQL for data, **AWS S3 / MinIO** for images,
  evidence and report artifacts.
- `STORAGE_BACKEND=local|s3`; S3 falls back to local storage automatically.
- Full details: `platform/docs/ARCHITECTURE.md`, `platform/docs/DEPLOYMENT.md`.

## 13. Known limitations

- OCR accuracy depends on photo quality; poor lighting/blur/glare produces a
  **re-capture advisory**; high-glare/busy labels under-extract.
- Font-size rules (FS-01) need px→mm calibration (in-shot barcode or manual
  `calibration_mm_per_px`); uncalibrated checks report `needs_review`, not
  false violations.
- Single-face scans miss back-panel declarations (e.g. consumer-care details) —
  a second photo is recommended.
- English-language labels currently; spaCy/BERT + YOLOv8 are planned upgrades
  (the JSON contract already supports them).
- The rule database is a working draft — verify thresholds against the
  consolidated gazette before production enforcement (see the rules file's
  disclaimer).
- `.env` contains local PostgreSQL credentials — keep it out of version control
  (already git-ignored).

## 14. Security notes

- JWT secret (`JWT_SECRET`) and demo passwords must be changed before any
  shared deployment; passwords are stored as salted PBKDF2 hashes.
- Media/report URLs accept `?access_token=` for `<img>`/downloads — use TLS in
  production. S3 keys are never exposed to the browser; local-storage paths are
  traversal-guarded.
- RBAC is enforced on the server (`require_roles`) — the UI only hides routes.