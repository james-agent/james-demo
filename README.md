# james-demo — CRM Monorepo

Technical scaffolding for a **CRM customer-registration product** with **FastAPI**, **Angular**, and **PostgreSQL**, plus a **Q2 Helix** integration that provisions Helix customers and accounts from the local customer base.

## Monorepo layout

```
james-demo/
├── apps/
│   ├── api/                 # CRM FastAPI backend (isolated from legacy James AI)
│   │   ├── crm_api/
│   │   │   ├── main.py      # Application entrypoint
│   │   │   ├── config.py    # Environment-based settings
│   │   │   ├── routes/      # HTTP routers (health)
│   │   │   └── customers/   # Reserved domain — no CRUD yet
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   └── web/                 # CRM Angular frontend (Angular 19)
│       ├── src/app/
│       │   ├── layout/      # CRM shell + sidebar
│       │   ├── features/    # Dashboard welcome view
│       │   └── shared/      # Coming soon tooltip directive
│       ├── proxy.conf.json  # Dev proxy: /api → CRM API
│       └── Dockerfile
├── infra/
│   └── docker/              # Local infrastructure notes
├── docker-compose.yml       # API + web + PostgreSQL
├── .env.example             # Documented environment variables
└── README.md
```

### Legacy coexistence

This repository may also contain legacy **James AI** platform code under `james/` (if present on other branches). The CRM product lives under `apps/` and is **fully separate** from the legacy `james/hub` FastAPI application.

## Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| [Docker](https://docs.docker.com/get-docker/) | 24+ | Run full stack locally |
| [Docker Compose](https://docs.docker.com/compose/) | v2+ | Orchestrate services |
| [Node.js](https://nodejs.org/) | 20+ | Optional — run Angular without Docker |
| [Python](https://www.python.org/) | 3.12+ | Optional — run API without Docker |

## Quick start (Docker Compose)

**One command** to start API, web frontend, and PostgreSQL:

```bash
# 1. Clone the repository
git clone https://github.com/james-agent/james-demo.git
cd james-demo

# 2. Configure environment
cp .env.example .env
# Edit .env if you need different ports or credentials

# 3. Start all services
docker compose up --build
```

### Verify the stack

| Check | Command / URL | Expected result |
|-------|---------------|-----------------|
| API health | `curl http://localhost:8000/health` | `{"status":"ok","service":"crm-api"}` |
| Frontend | Open [http://localhost:4200](http://localhost:4200) | CRM landing shell with Gemini-style sidebar and welcome dashboard |
| PostgreSQL | Service `db` healthy in `docker compose ps` | `healthy` status |

> Port numbers follow `.env` (`API_PORT`, `WEB_PORT`, `POSTGRES_PORT`). Defaults: API **8000**, web **4200**, Postgres **5432**.

## Local development (without full Compose)

### API only

```bash
cd apps/api
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp ../../.env.example ../../.env   # if not already done
export $(grep -v '^#' ../../.env | xargs)
uvicorn crm_api.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend only

```bash
cd apps/web
npm install
npm start
# Opens http://localhost:4200 — proxies /api/* to http://localhost:8000 when API is running
```

For local (non-Docker) API development, update `apps/web/proxy.conf.json` target to `http://localhost:8000`.

### PostgreSQL only (container)

```bash
docker compose up db
```

## Environment variables

All variables are documented in [`.env.example`](.env.example). Copy it to `.env` before starting services.

| Variable | Description |
|----------|-------------|
| `API_HOST` | API bind address inside container |
| `API_PORT` | Host port for CRM API |
| `POSTGRES_*` | Database connection settings |
| `DATABASE_URL` | Optional SQLAlchemy URL override (e.g. SQLite for local tests) |
| `WEB_PORT` | Host port for Angular dev server |
| `CORS_ORIGINS` | Allowed origins for API CORS |
| `Q2_HELIX_API_URL` | Helix base URL (sandbox or production) |
| `Q2_HELIX_API_KEY` / `Q2_HELIX_API_SECRET` | Helix HTTP Basic Auth credentials |
| `Q2_HELIX_PROGRAM_ID` | Helix program id |
| `Q2_ENVIRONMENT` | `sandbox` or `production` |
| `Q2_DEFAULT_PRODUCT_ID` | Helix `productId` used when sync creates accounts |

**Required:** `POSTGRES_PASSWORD` must be set (see `.env.example`). If missing, the API fails at startup with a message referencing `.env.example`.

## Q2 Helix customer + account provisioning

Local `customers` rows are the identity source of truth. Helix `tag` stores the local customer UUID for idempotent correlation (`/customer/getByTag`, `/account/getByTag`). Account tags use `{customer_id}:primary`.

### Connectivity gate

```bash
# From repo root (with Q2_HELIX_* set)
python3 scripts/q2_gate_check.py
```

Reports `PASS`, `CONFIG_ERROR` (missing/invalid credentials), or `API_BUSINESS_ERROR` (reachable Helix business/program issue). Missing config is never treated as success.

### Database migration

```bash
cd apps/api
alembic upgrade head
```

On API startup, `init_db()` also ensures tables exist for local/demo databases.

### Key APIs

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/api/v1/customers` | Persist a local customer (KYC fields for Helix onboard) |
| `GET` | `/api/v1/customers` | List local customers + Q2 linkage status |
| `POST` | `/api/v1/q2/customers/onboard` | Helix customer onboard proxy |
| `GET` | `/api/v1/q2/customers/by-tag/{tag}` | Helix getByTag |
| `POST` | `/api/v1/q2/accounts/create` | Helix account create |
| `POST` | `/api/v1/q2/sync/customers` | Bulk ensure Helix customer + account for all local customers |
| `POST` | `/api/v1/q2/sync/customers/{id}` | Sync a single local customer |

Sync outcomes per row: `created`, `linked_existing`, `already_linked`, `skipped_incomplete`, or `failed`. Incomplete KYC skips that row without aborting the batch. Tax IDs and full account numbers are never written to application logs or API responses.

## CRM mock listing (inception)

The `apps/api/crm_api/customers/` package still serves the mock CRM list/detail UI under `/api/v1/crm/customers`. Durable Q2 linkage uses the SQL `customers` table via `/api/v1/customers` and `/api/v1/q2/sync/*`.

## CRM landing dashboard (JAMESD-3)

The post-login index route at `/` renders a CRM shell in `apps/web/`:

- **Sidebar:** eight English menu labels (Dashboard active; Leads–Settings are disabled placeholders with “Coming soon” tooltip).
- **Main area:** “Welcome back” headline and “Your CRM dashboard is ready” subtext.
- **Responsive:** hamburger menu collapses the sidebar on viewports ≤768px.
- **No auth guard** on the index route in this phase.

Run locally:

```bash
cd apps/web
npm install
npm start
```

Run unit tests:

```bash
cd apps/web
npm test -- --no-watch --browsers=ChromeHeadless
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Port already in use | Change `API_PORT`, `WEB_PORT`, or `POSTGRES_PORT` in `.env` and restart |
| Docker not running | Start Docker Desktop / Docker daemon, then retry `docker compose up` |
| Missing env variable | Ensure `.env` exists (copy from `.env.example`) and required keys are set |
| Postgres not ready | Wait for `db` healthcheck; run `docker compose logs db` |
| Frontend cannot reach API | Confirm API is up; in Compose, proxy targets `http://api:8000` automatically |

## Technology stack

| Layer | Technology | Version (at scaffolding) |
|-------|------------|--------------------------|
| API | FastAPI + Uvicorn | See `apps/api/requirements.txt` |
| Web | Angular | 19.x (see `apps/web/package.json`) |
| Database | PostgreSQL | 16 (Alpine image in Compose) |
| Orchestration | Docker Compose | v2 |

## Related documentation

- [FastAPI](https://fastapi.tiangolo.com/)
- [Angular](https://angular.dev/)
- [Docker Compose](https://docs.docker.com/compose/)
