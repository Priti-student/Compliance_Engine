# LMPC Compliance Platform — Deployment

## 1. Target topology

```
                        ┌───────────────────────────────────────────┐
  Enforcement Officer / │  Nginx (TLS, static React dist, /api proxy)|
  Reviewer / Admin      └──────────────┬────────────────────────────┘
        browser                        │
                                       ▼
                          ┌─────────────────────────────┐
                          │  App service (uvicorn/gunicorn)│
                          │  Compliance_Engine/platform/backend/app.main:app │
                          └───────┬─────────────┬─────────┘
                                  │             │
                          ┌───────▼─────┐  ┌────▼──────────────┐
                          │ PostgreSQL   │  │ Object storage     │
                          │ lmpc_platform│  │ AWS S3 / MinIO     │
                          └─────────────┘  └────────────────────┘
                                                    ▲
                          CV/OCR engine service     │   HTTP :8000 (read-only
                          (Compliance_Engine,       │   integration; teammate)
                          uvicorn on :8000) ────────┘
```

## 2. Environment variables (`.env`)

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | SQLAlchemy URL, e.g. `postgresql+psycopg://postgres:pass@localhost:5432/lmpc_platform` |
| `JWT_SECRET` | long random secret — `python -c "import secrets;print(secrets.token_hex(32))"` |
| `ACCESS_TOKEN_MINUTES` | JWT lifetime (default 60) |
| `ENGINE_BASE_URL` | CV/OCR engine service URL (default `http://127.0.0.1:8000`) |
| `STORAGE_BACKEND` | `local` (dev) or `s3` (prod) |
| `S3_BUCKET`, `S3_REGION`, `S3_ENDPOINT_URL`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` | object store (MinIO uses the endpoint URL + keys) |
| `STORAGE_LOCAL_ROOT` | local fallback root (default `./storage_data`) |
| `SEED_DEMO` | `true` | `false` | `force` — import demo inspections on boot |
| `CORS_ORIGINS` | comma-separated allowed origins |
| `MAX_UPLOAD_MB` | image upload cap |

## 3. Backend service

Local (Windows):

```bat
cd Compliance_Engine\platform\backend
..\venv\Scripts\python.exe run.py        :: uvicorn app.main:app on 127.0.0.1:8001
```

Linux / production:

```bash
cd Compliance_Engine/platform/backend
# gunicorn with uvicorn workers
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8001
```

The seed runs automatically on startup (idempotent). For a clean re-import:

```bash
Compliance_Engine/platform/venv/bin/python -m app.services.seed   # or SEED_DEMO=force ...
```

## 4. Database

```bash
psql -U postgres -h localhost -f Compliance_Engine/platform/scripts/create_databases.sql
```
Tables are created by SQLAlchemy at startup (`Base.metadata.create_all`);
backups = standard `pg_dump lmpc_platform`.

## 5. Frontend service

```bash
cd Compliance_Engine/platform/frontend
npm ci && npm run build          # static output in Compliance_Engine/platform/frontend/dist
```
Serve `dist/` from Nginx and proxy `/api` to the backend:

```nginx
server {
  listen 443 ssl;                       # TLS certificates not shown
  root /srv/lmpc/frontend/dist;
  location / { try_files $uri /index.html; }
  location /api/ { proxy_pass http://127.0.0.1:8001; }
}
```

Development: `npm run dev` (Vite on :5173 proxies `/api` → :8001).

## 6. Object storage hardening

- AWS S3: configure an IAM user with least privilege on `S3_BUCKET`
  (PutObject, GetObject, DeleteObject, ListBucket).
- MinIO: set `S3_ENDPOINT_URL=http://minio:9000` + access/secret keys; bucket
  created on demand by the service.
- If neither is reachable the service falls back to `STORAGE_LOCAL_ROOT`
  (with a startup warning) so the platform never hard-fails.

## 7. Security notes

- Change `JWT_SECRET` in any shared/preview environment.
- Demo passwords (`Admin@123`, `Reviewer@123`, `Officer@123`) are for local
  development only — reset or disable demo users before public exposure.
- Media/report URLs support `?access_token=` for `<img>`/downloads; keep TLS
  enabled in production so tokens are not sent in cleartext.
- Media streaming is backend-controlled (path traversal guarded in
  `LocalStorage`); S3 keys are never exposed to the browser.

## 8. Health & monitoring

- `GET /api/health` → DB + engine connectivity.
- `GET /api/rules/health` → rules DB presence + engine reachability.
- Uvicorn/gunicorn access logs → `Compliance_Engine/platform/server.log` (launcher)
  or stdout.
- PostgreSQL: rely on `pg_stat_activity` / standard tooling; every scan,
  artifact and review action is persisted for audit.

## 9. Scaling

- Stateless API → scale horizontally behind Nginx.
- OCR scans call the engine synchronously; for high volume, move
  `/api/inspections` to a background job (Celery/RQ) and poll a status field.
- Aggregate dashboards over the relational rows; if volume grows, replace the
  Python-side sums with materialized views (`inspections.stats_json` already
  mirrors all counters).