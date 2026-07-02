# Demo Store — Cloud Platform Payload

A deliberately small FastAPI + PostgreSQL application. It is **the payload** for the
larger GCP platform project: its only job is to prove the infrastructure underneath
it works (private networking, a managed database, CI/CD, monitoring).

This phase runs **100% locally — no cloud account required.**

## What's inside

| Route | Purpose |
|-------|---------|
| `GET /` | HTML storefront; lists products read live from the DB, shows a DB-status pill |
| `GET /api/products` | JSON list of products |
| `POST /api/products` | Add a product (proves the DB is writable) |
| `GET /healthz` | Health check used later by the load balancer / Cloud Run |
| `GET /docs` | Auto-generated API docs (Swagger) |

## Run it locally (recommended: Docker)

You only need Docker installed.

```bash
docker compose up --build
```

Then open <http://localhost:8080>. Compose starts a local PostgreSQL **and** the app,
seeds a few products, and wires them together. Stop with `Ctrl+C`; remove everything
with `docker compose down -v`.

## Run it locally (without Docker)

You need a local PostgreSQL running, then:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # edit DB_HOST=localhost
export $(grep -v '^#' .env | xargs)
uvicorn app.main:app --reload --port 8080
```

## The key design decision (why this matters for the cloud phase)

The database connection is built **entirely from environment variables**
(`app/database.py`). Nothing about the connection is hard-coded.

That means moving to Google Cloud later changes **only environment variables —
never the application code or the container image**:

| Variable | Local value | Cloud value (next phase) |
|----------|-------------|--------------------------|
| `DB_HOST` | `db` (compose service) | Cloud SQL **private IP** |
| `DB_PASSWORD` | `localpass` | injected from **Secret Manager** |
| `DB_USER` / `DB_NAME` | `store` | your Cloud SQL user / db |
| `PORT` | `8080` | injected by Cloud Run |

The exact same `Dockerfile` image runs locally and in the cloud. This is what lets
us "just swap env vars" in the next step.

## Project layout

```
store-app/
├── app/
│   ├── main.py          # FastAPI routes + health check
│   ├── database.py      # env-driven DB connection (the swap point)
│   ├── models.py        # Product model + seed data
│   └── templates/
│       └── index.html   # single clean storefront page
├── Dockerfile           # same image local + cloud
├── docker-compose.yml   # local Postgres + app, one command
├── requirements.txt
└── .env.example
```

## Next step

Once you're happy running this locally, the cloud phase wraps it with:
private VPC → Cloud SQL (HA) → Cloud Run → Cloud Build CI/CD → monitoring & alerts,
all provisioned with Terraform.
