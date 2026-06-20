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
| `DATABASE_URL` | Optional SQLAlchemy URL override (defaults to `POSTGRES_*`) |
| `WEB_PORT` | Host port for Angular dev server |
| `CORS_ORIGINS` | Allowed origins for API CORS |

**Required:** `POSTGRES_PASSWORD` must be set (see `.env.example`). If missing, the API fails at startup with a message referencing `.env.example`.

## CRM domain (reserved)

The `apps/api/crm_api/customers/` package is reserved for future customer-registration features. It contains documentation only — **no routes, models, or forms** are exposed.

## Q2 Helix customer sync (JAMESD-4)

Card 1 delivers Q2 Helix connectivity and bulk customer onboarding so every record in the local customer base is represented in Q2.

### Environment variables

Add to `.env` (see `.env.example`):

| Variable | Description |
|----------|-------------|
| `Q2_HELIX_API_URL` | Helix base URL (sandbox default) |
| `Q2_HELIX_API_KEY` | Basic auth username (API key) |
| `Q2_HELIX_API_SECRET` | Basic auth password (API secret) |
| `Q2_HELIX_PROGRAM_ID` | Program identifier |
| `Q2_ENVIRONMENT` | `sandbox` or `production` |
| `Q2_HELIX_DEFAULT_PRODUCT_ID` | Default deposit product for account provisioning |

### Gate check

```bash
python3 scripts/q2_gate_check.py
```

Exits `0` on PASS, `2` on CONFIG_ERROR, `3` on API business error.

### API endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/q2/sync/customers?mode=full\|incremental` | Bulk sync local customers to Q2 |
| `GET` | `/api/v1/q2/sync/customers/status` | Sync status counts |
| `POST` | `/api/v1/q2/customers/onboard` | Onboard one local customer by UUID |
| `GET` | `/api/v1/q2/customers/by-tag/{tag}` | Fetch Q2 customer by tag (local customer UUID) |

Local customers are stored in PostgreSQL (`customers`, `q2_customer_sync`, `q2_account_sync` tables). On startup the API seeds the registry from CRM mock data when empty.

## Q2 Helix account provisioning (JAMESD-4 Card 2)

Card 2 provisions a Q2 deposit account for every customer successfully synced in Card 1.

### Environment variables

| Variable | Description |
|----------|-------------|
| `Q2_HELIX_DEFAULT_PRODUCT_ID` | Required for bulk account sync — Helix product id for `/account/create` |

### API endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/q2/accounts/create` | Provision account for one synced local customer |
| `GET` | `/api/v1/q2/accounts/customer/{customerId}` | List Q2 accounts for a local customer |
| `GET` | `/api/v1/q2/accounts/{id}` | Get account by Q2 account id |
| `POST` | `/api/v1/q2/sync/accounts` | Bulk provision accounts for all synced customers |
| `GET` | `/api/v1/q2/sync/accounts/status` | Account provisioning status counts |
| `POST` | `/api/v1/q2/accounts/{id}/close` | Close account |
| `POST` | `/api/v1/q2/accounts/{id}/lock` | Lock account |
| `POST` | `/api/v1/q2/accounts/{id}/unlock` | Unlock account |
| `POST` | `/api/v1/q2/accounts/{id}/stop-pay` | Create stop payment |
| `GET` | `/api/v1/q2/accounts/{id}/stop-pay` | List stop payments |
| `DELETE` | `/api/v1/q2/accounts/{id}/stop-pay/{stopPayId}` | Cancel stop payment |

Account tags use the pattern `{local_customer_uuid}-primary` for idempotent provisioning.

### Database migrations

```bash
cd apps/api
alembic upgrade head
```

### Tests

```bash
cd apps/api
PYTHONPATH=. pytest tests/ -q
```

## What is NOT in this delivery

For product owners and stakeholders:

- No customer registration UI, listing, editing, or deletion screens
- No Salesforce, email, or payment integrations
- No user authentication flows
- No CI pipeline

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
