# james-demo — CRM Monorepo Foundation

Technical scaffolding for a future **CRM customer-registration product**. This repository provides a reproducible local development environment with **FastAPI**, **Angular**, and **PostgreSQL** orchestrated via Docker Compose.

> **Delivery scope (JAMESD-1):** infrastructure and project structure only. There are **no** customer registration screens, CRUD endpoints, or external integrations in this delivery. Future stories will build on this base.

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

**Required:** `POSTGRES_PASSWORD` must be set (see `.env.example`). If missing, the API fails at startup with a message referencing `.env.example`.

## CRM domain (reserved)

The `apps/api/crm_api/customers/` package is reserved for future customer-registration features. It contains documentation only — **no routes, models, or forms** are exposed.

## What is NOT in this delivery

For product owners and stakeholders:

- No customer registration, listing, editing, or deletion
- No Salesforce, email, or payment integrations
- No user authentication flows
- No database migrations (Alembic) or CI pipeline

These will be addressed in follow-up stories.

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

## Q2 Helix connection (authentication gate)

Server-side Helix connectivity lives under `james/ext/q2/` (owned by the Q2 authentication workflow). Credentials are **never** sent to the Angular app.

### Environment

Copy `.env.example` → `.env` and set:

| Variable | Purpose |
|----------|---------|
| `Q2_HELIX_API_URL` | Base URL (`https://sandbox-api.helix.q2.com` or `https://api.helix.q2.com`) |
| `Q2_HELIX_API_KEY` | HTTP Basic Auth username |
| `Q2_HELIX_API_SECRET` | HTTP Basic Auth password |
| `Q2_HELIX_PROGRAM_ID` | Program identifier (optional for connectivity; required for some provision flows) |
| `Q2_ENVIRONMENT` | `sandbox` or `production` |

Production requires IP whitelisting; sandbox and production whitelists may differ. See [Authentication](https://docs.helix.q2.com/reference/authentication), [Environment Differences](https://docs.helix.q2.com/reference/environment-differences), and [Test Connectivity](https://docs.helix.q2.com/reference/test-connectivity).

### Gate check

From the repository root (with dependencies from root `requirements.txt` installed):

```bash
pip install -r requirements.txt
python3 scripts/q2_gate_check.py
```

The script reports `PASS`, `CONFIG_ERROR` (missing env), or `API_BUSINESS_ERROR` (401/403/network — report-only; fix credentials or whitelist). It never prints secret values.

### Hub API

```bash
PYTHONPATH=. uvicorn james.hub.app:app --reload --host 0.0.0.0 --port 8001
```

| Endpoint | Purpose |
|----------|---------|
| `GET /api/v1/q2/connection/status` | Environment + configured flags (no secrets) |
| `POST /api/v1/q2/connection/test` | Live Helix connectivity + program product discovery |
| `POST /api/v1/q2/customers/onboard` | Onboard customer (Helix `/customer/onboard`) |
| `GET /api/v1/q2/customers/{id}` | Get customer (KYC/status masked PII) |
| `GET /api/v1/q2/customers/by-tag/{tag}` | Get customer by external tag |
| `PUT /api/v1/q2/customers/{id}` | Update customer profile |
| `POST /api/v1/q2/customers/{id}/archive` | Archive customer |
| `POST /api/v1/q2/customers/{id}/lock` | Lock customer |
| `POST /api/v1/q2/customers/{id}/unlock` | Unlock customer |
| `GET/POST /api/v1/q2/customers/{id}/beneficiaries` | List / add beneficiaries |
| `POST /api/v1/q2/accounts` | Create account |
| `GET /api/v1/q2/accounts/by-customer/{customerId}` | List accounts |
| `GET /api/v1/q2/accounts/{customerId}/{accountId}` | Account detail (balance/status/type) |
| `POST /api/v1/q2/accounts/close` | Close account |
| `POST /api/v1/q2/accounts/lock` | Lock account |
| `POST /api/v1/q2/accounts/{customerId}/{accountId}/unlock` | Unlock account |
| `POST /api/v1/q2/accounts/stop-pays` | Create check/ACH stop pay |
| `GET /api/v1/q2/accounts/{customerId}/{accountId}/stop-pays` | List stop pays |
| `POST /api/v1/q2/accounts/stop-pays/cancel` | Expire/cancel stop pay |

Customer and account services live under `james/ext/q2/services/`; Helix credentials stay server-side.

```bash
PYTHONPATH=. pytest tests/q2 -q
```

## Related documentation

- [FastAPI](https://fastapi.tiangolo.com/)
- [Angular](https://angular.dev/)
- [Docker Compose](https://docs.docker.com/compose/)
- [Q2 Helix Authentication](https://docs.helix.q2.com/reference/authentication)
