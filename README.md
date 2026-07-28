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
├── ext/
│   └── q2/                  # Q2 Helix connection (config + HTTP client)
├── scripts/
│   └── q2_gate_check.py     # Helix connectivity gate check
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
| `Q2_HELIX_API_KEY` | Helix Basic Auth username (API key) |
| `Q2_HELIX_API_SECRET` | Helix Basic Auth password (API secret) |
| `Q2_HELIX_PROGRAM_ID` | Helix program identifier |
| `Q2_ENVIRONMENT` | `sandbox` or `production` |

**Required:** `POSTGRES_PASSWORD` must be set (see `.env.example`). If missing, the API fails at startup with a message referencing `.env.example`.

## Q2 Helix connection gate check

Before any Q2 Helix feature work, copy env placeholders and run the gate check from the repository root:

```bash
cp .env.example .env
# Fill Q2_HELIX_API_KEY, Q2_HELIX_API_SECRET, Q2_HELIX_PROGRAM_ID (never commit real secrets)
python3 scripts/q2_gate_check.py
```

The script loads `ext/q2` config, prints SET/MISSING for each required variable (never secret values), then tests Helix connectivity (`GET /`) and `POST /program/get`. Results classify as:

| Result | Meaning |
|--------|---------|
| `PASS` | Credentials present; connectivity and program lookup succeeded |
| `CONFIG_ERROR` | Missing env vars, bad auth (401/403), or network/config failure |
| `API_BUSINESS_ERROR` | Helix returned a business/HTTP error (e.g. 404/5xx) |

Connection structure lives only under `ext/q2/` (`get_q2_config()`, `get_helix_client()`). Downstream services must reuse that client — do not recreate Basic Auth or base URL logic elsewhere. See also `ext/q2/README.md`.

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

## Related documentation

- [FastAPI](https://fastapi.tiangolo.com/)
- [Angular](https://angular.dev/)
- [Docker Compose](https://docs.docker.com/compose/)
