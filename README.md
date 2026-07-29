# james-demo — CRM Monorepo Foundation

Technical scaffolding for a future **CRM customer-registration product**. This repository provides a reproducible local development environment with **FastAPI**, **Angular**, and **PostgreSQL** orchestrated via Docker Compose.

> **Delivery scope:** CRM monorepo foundation (JAMESD-1), landing dashboard (JAMESD-3), and Q2 Helix customer/account provisioning under `/api/v1/q2/` (JAMESD-4).

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
| `WEB_PORT` | Host port for Angular dev server |
| `CORS_ORIGINS` | Allowed origins for API CORS |
| `Q2_HELIX_API_URL` | Helix base URL (sandbox or production) |
| `Q2_HELIX_API_KEY` / `Q2_HELIX_API_SECRET` | HTTP Basic Auth credentials (server-side only) |
| `Q2_HELIX_PROGRAM_ID` | Helix program identifier |
| `Q2_HELIX_PRODUCT_ID` | Default product id used when creating accounts |
| `Q2_ENVIRONMENT` | `sandbox` or `production` |
| `Q2_MOCK_MODE` | `true` to stub Helix calls for local/CI |
| `Q2_ALLOW_PLACEHOLDER_PII` | Allow sandbox placeholder KYC fields when CRM rows lack taxId/DOB/address |

**Required:** `POSTGRES_PASSWORD` must be set (see `.env.example`). If missing, the API fails at startup with a message referencing `.env.example`.

## Q2 Helix provisioning (JAMESD-4)

Server-side integration that provisions every CRM base customer into Q2 Helix (customer + account) with durable local↔Helix mapping.

Layout (reconciled under the API package):

- `apps/api/ext/q2/` — config, Helix client, models, repositories, adapters, orchestration, routes
- `apps/api/scripts/q2_gate_check.py` (also `scripts/q2_gate_check.py`) — Gate A/C connectivity check
- `apps/api/migrations/` — Alembic revision for `q2_customers`, `q2_accounts`, `q2_provision_runs`

### Operator API

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/api/v1/q2/health` | Config presence + Helix connectivity (no secrets) |
| `POST` | `/api/v1/q2/provision` | Idempotent provision of local CRM customers |
| `GET` | `/api/v1/q2/provision/{run_id}` | Provision run status |
| `POST` | `/api/v1/q2/customers/onboard` | Helix customer onboard helper |
| `GET` | `/api/v1/q2/customers/by-tag/{tag}` | Customer getByTag helper |
| `POST` | `/api/v1/q2/accounts/create` | Helix account create helper |
| `GET` | `/api/v1/q2/accounts/by-tag/{tag}` | Account getByTag helper |

### Gate check

```bash
cd apps/api
python3 scripts/q2_gate_check.py
# or from repo root:
python3 scripts/q2_gate_check.py
```

Results: `PASS` (exit 0), `CONFIG_ERROR` (exit 2), `API_BUSINESS_ERROR` (exit 3).

### Security API gate (PING)

```bash
cd apps/api
python3 scripts/q2_security_ping.py
```

Confirms `GET /api/v1/q2/health` succeeds and the payload never echoes Helix secrets.

### Migrations

```bash
cd apps/api
alembic upgrade head
```

The API also calls `create_all` on startup so local/dev tables exist even before Alembic is applied.

### API tests

```bash
cd apps/api
pip install -r requirements.txt
pytest -q
```

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
