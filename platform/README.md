# LMPC Compliance Platform (Sitara)

Web platform for checking compliance of **packaged commodities** against the
**Legal Metrology (Packaged Commodities) Rules, 2011** by scanning product
images/labels. This repository is the **platform layer**: report rendering
(PDF / XLSX / JSON), dashboard UI, PostgreSQL + S3 object persistence,
JWT authentication with role-based access control (Officer / Reviewer / Admin),
and a searchable product-repository.

The CV/OCR engine (`Compliance_Engine_CV_NLP/`, sibling of this folder) is owned
by a teammate and is consumed **read-only over HTTP** on port 8000 — this
platform never modifies or imports it. Commands below run from the workspace
root `Compliance_Engine/` unless `cd` says otherwise.

---

## 1. Components

```
Compliance_Engine/
├── Compliance_Engine_CV_NLP/          # teammate CV/OCR module (read-only)
│   └── venv/                          # engine Python environment (git-ignored)
├── platform/                          # THIS platform (backend + frontend)
│   ├── backend/                       # FastAPI service (:8001)
│   ├── frontend/                      # React + Tailwind + Recharts (:5173)
│   ├── scripts/                       # seed, e2e, scans, launchers
│   ├── docs/                          # ARCHITECTURE.md, DEPLOYMENT.md
│   └── venv/                          # platform Python environment (git-ignored)
├── tessdata/                          # eng.traineddata for Tesseract (OCR)
├── start_engine.bat                   # engine launcher (:8000)
└── engine_requirements.txt            # deps for the engine venv
```

## 2. Prerequisites

| Tool | Version used |
|---|---|
| PostgreSQL | 18.x running on localhost:5432 |
| Python | 3.13 (Store) — both venvs created from it |
| Node / npm | 22 / 10 |
| CV/OCR engine | optional for full scans; demo import works without it |

> Note on packages: PyPI's file host (`files.pythonhosted.org`) is blocked on
> some networks. If `pip install` fails with DNS errors, use a reachable
> mirror, e.g. `pip -i https://pypi.tuna.tsinghua.edu.cn/simple install ...`

## 3. Setup

```bash
# 1) Database
psql -U postgres -h localhost -f Compliance_Engine\platform\scripts\create_databases.sql   # idempotent
# (uses postgres user; override credentials in .env)

# 2) Python environment (from Python 3.13)
py -3.13 -m venv Compliance_Engine\platform\venv
Compliance_Engine\platform\venv\Scripts\python.exe -m pip install -r Compliance_Engine\platform\requirements.txt

# 3) Configure
copy Compliance_Engine\platform\.env.example Compliance_Engine\platform\.env      # edit DATABASE_URL / JWT_SECRET / S3 keys

# 4) Seed (creates tables + admin/reviewer/officer + 5 demo inspections with reports)
cd Compliance_Engine\platform\backend
..\venv\Scripts\python.exe -m app.services.seed
```

## 4. Run

```bash
# Backend API (:8001) — terminal 1
cd Compliance_Engine\platform\backend
..\venv\Scripts\python.exe run.py

# Frontend dev server (:5173, proxies /api → :8001) — terminal 2
cd Compliance_Engine\platform\frontend
npm install
npm run dev

# (Optional) CV/OCR engine (:8000) — see section 9
```

Open **http://localhost:5173**.

### Demo users

| Username | Password | Role |
|---|---|---|
| `admin` | `Admin@123` | Admin — user management, everything |
| `reviewer` | `Reviewer@123` | Reviewer — approve/reject inspections |
| `officer` | `Officer@123` | Officer — scan products, browse reports |

## 5. Quick API tour (Swagger: http://127.0.0.1:8001/docs)

| Endpoint | Purpose |
|---|---|
| `POST /api/auth/login` · `GET /api/auth/me` | JWT login / session (OAuth2 password flow) |
| `GET/POST/PATCH/DELETE /api/users*` | admin-only user & role management |
| `POST /api/inspections` (multipart image) | run engine scan → persist everything |
| `POST /api/inspections/from-demo` | import a stored demo report (offline mode) |
| `GET /api/inspections/{token}` | full detail (declarations/violations/font/evidence) |
| `PATCH /api/inspections/{token}` | reviewer approval / remarks |
| `GET/POST /api/reports/{token}/...` | download / regenerate PDF, XLSX, JSON |
| `GET /api/search` · `/api/search/suggest` | product-repository search + autocomplete |
| `GET /api/dashboard/*` | enforcement dashboard aggregates |
| `GET /api/rules` | read-only digitized LMPC rule database |
| `GET /api/health` | DB + engine connectivity |

## 6. Tests & validation

```bash
# Backend suite (uses in-memory sqlite; engine mocked)
cd Compliance_Engine\platform\backend && ..\venv\Scripts\python.exe -m pytest tests -q

# Frontend production build (tsc + vite)
cd Compliance_Engine\platform\frontend && npm run build

# End-to-end against real Postgres + storage (spawns uvicorn itself)
Compliance_Engine\platform\venv\Scripts\python.exe Compliance_Engine\platform\scripts\run_e2e.py
```

## 7. Storage

`STORAGE_BACKEND=local` writes images/reports under
`Compliance_Engine\platform\storage_data` (works offline). Set
`STORAGE_BACKEND=s3` with `S3_BUCKET`/`AWS_*` env vars to store in AWS S3 (or
MinIO via `S3_ENDPOINT_URL`). If S3 is unreachable the service logs a warning
and falls back to local storage automatically.

Layout: `inspections/{token}/`, `inspections/{token}/evidence/`,
`inspections/{token}/reports/`.

## 8. Scope boundary

- **Included**: platform backend + frontend, PostgreSQL persistence, S3/local
  storage, JWT + RBAC, PDF/XLSX/JSON report generation, dashboards, search.
- **Not touched**: `Compliance_Engine_CV_NLP/**` (teammate engine module —
  no reads other than demo report import + rules display).

## 9. Running the real CV/OCR engine (:8000) for live scans

The engine repository is consumed **read-only over HTTP**. To enable real
(OCR based) scans you also need to start the engine service:

```bat
:: 1) One-off setup (already done on this machine)
py -3.13 -m venv Compliance_Engine\Compliance_Engine_CV_NLP\venv
Compliance_Engine\Compliance_Engine_CV_NLP\venv\Scripts\python.exe -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r Compliance_Engine\engine_requirements.txt
:: install Tesseract 5.x (winget: UB-Mannheim.TesseractOCR)
:: download eng.traineddata into Compliance_Engine\tessdata\ :
Compliance_Engine\platform\venv\Scripts\python.exe Compliance_Engine\platform\scripts\fetch_tessdata.py

:: 2) Start the engine (TESSDATA_PREFIX is set inside)
Compliance_Engine\start_engine.bat
:: or:
Compliance_Engine\platform\venv\Scripts\python.exe Compliance_Engine\platform\scripts\start_engine.py

:: 3) Verify
curl http://127.0.0.1:8000/cv/health        :: opencv + tesseract versions
curl http://127.0.0.1:8001/api/health       :: engine_online: true
```

> The engine venv lives inside the repo at `Compliance_Engine_CV_NLP\venv`
> (git-ignored). `start_engine.bat` and `platform\scripts\start_engine.py`
> resolve it and set `TESSDATA_PREFIX` to `<repo>\tessdata` automatically.

Any scan created from the platform UI now genuinely runs the engine pipeline:
quality gate → OpenCV preprocessing → zone detection → Tesseract OCR →
declaration extraction → rule-engine evaluation (a real example extracted
`MRP 20.00, Net Quantity 52 g, MFD 10/07/2024, Batch LT240710A` from
`package_001.jpg`).

If Tesseract cannot find `eng.traineddata` it fails with a
`TESSDATA_PREFIX` error — the launchers above set it to `<workspace>\tessdata`.