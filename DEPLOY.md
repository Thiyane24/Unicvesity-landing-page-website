# Deploying Unicvesity Worldwide with Docker

Everything in this project ships as Docker images that run with a single
`docker compose up -d`. Three services:

| Service     | What it does                            | Exposed to host |
|-------------|-----------------------------------------|-----------------|
| `frontend`  | nginx — serves landing + admin + proxy  | port **80**     |
| `api`       | FastAPI — saves leads                   | only inside the network |
| `db`        | Postgres 16 — opt-in (profile `postgres`)| only inside the network |

```
┌──────────────┐      ┌────────────────┐      ┌────────────┐
│   Browser    │ ───► │  frontend:80   │ ───► │  api:8000  │ ───► SQLite (volume)
└──────────────┘      │ (nginx)        │      │ (FastAPI)  │      or  Postgres (profile)
                      └────────────────┘      └────────────┘
```

---

## 1. One-time setup

```bash
# 1) Get the code onto the server (or your machine) and cd into it.
cd "Unicvesity landing page website"

# 2) Copy the env template and fill in real secrets.
cp .env.example.compose .env       # macOS/Linux
# copy .env.example.compose .env   # Windows PowerShell
```

Open `.env` and replace at minimum:

- `ADMIN_TOKEN` — paste a fresh one. Generate with:
  ```bash
  python -c "import secrets; print(secrets.token_urlsafe(40))"
  ```
- `ALLOWED_ORIGINS` — set to **the exact hostname you'll serve from**, no trailing slash.

---

## 2. Build + run (SQLite, simplest path)

```bash
docker compose build
docker compose up -d
```

That's it. You now have:

- Landing page  → http://localhost
- Admin panel   → http://localhost/admin.html?token=$ADMIN_TOKEN  *(paste the token from `.env`)*
- API docs      → http://localhost/api/docs
- Health check  → http://localhost/api/health

`docker compose logs -f` to tail logs. `docker compose down` to stop; data lives in the named volume `unicvesity_api_data`.

---

## 3. Switching to Postgres (recommended for prod)

```bash
# a) Edit .env and flip DATABASE_URL to:
#    DATABASE_URL=postgresql+psycopg://leads:YOUR_PASSWORD@db:5432/leads
#    (DB_PASSWORD on its own line is what the Postgres container uses.)
#
# b) Make sure psycopg2 is installed — Dockerfile already includes a commented
#    hint; either uncomment the line in backend/requirements.txt, or just
#    rely on Postgres being on the network so the driver resolves it.
#
# c) Start with the postgres profile:
docker compose --profile postgres up -d --build
```

`Base.metadata.create_all(...)` in `app/main.py` auto-creates the `leads` table on first boot. To manage schema migrations later, plug Alembic in (`alembic init`, etc.) — the directory is already Python-importable.

---

## 4. Verifying the deploy

```bash
# Are all containers healthy?
docker compose ps

# Tail logs
docker compose logs -f api
docker compose logs -f frontend

# Hit the API directly (within the network)
docker compose exec api python -c "import requests; print(requests.get('http://127.0.0.1:8000/api/health').json())"
```

Submit a test lead from the landing page, then:

```bash
# Confirm it landed in SQLite (default profile)
docker compose exec api sqlite3 /app/data/leads.db "SELECT id,name,email,destination,created_at FROM leads ORDER BY id DESC LIMIT 5;"
```

Or Postgres:

```bash
docker compose exec db psql -U leads -d leads -c "SELECT id,name,email,destination,created_at FROM leads ORDER BY id DESC LIMIT 5;"
```

---

## 5. Production hardening checklist

This compose file is intentionally minimal to be easy to read. Before
exposing it to real traffic, do these:

- [ ] **HTTPS** — put the stack behind Caddy / Traefik / Cloudflare / nginx-proxy and terminate TLS there. Don't expose 80 publicly without TLS.
- [ ] **Real domain** — set `ALLOWED_ORIGINS` to the public URL (no trailing slash).
- [ ] **Strong `ADMIN_TOKEN`** — random 40+ chars.
- [ ] **Postgres** — switch off SQLite; the volume is fine for staging but Postgres is the prod option.
- [ ] **Backups** — schedule `pg_dump` (or your host's snapshot feature) for `unicvesity_pg_data`.
- [ ] **Auth** — replace the bearer-token guard in `backend/app/deps.py` with JWT/OAuth if you have multiple admins or non-trivial access control.
- [ ] **Rate limiting** — add `slowapi` or a Caddy rate-limit module on `POST /api/leads`.
- [ ] **Image registry** — push `unicvesity/api` and `unicvesity/frontend` to GHCR / Docker Hub so other hosts can pull them, not just build from source.
- [ ] **Reverse proxy logs** — keep `nginx` access logs so you can see which leads reach the server vs the browser side.

---

## 6. Files added by this setup

```
backend/
├── Dockerfile                ← builds api image, runs gunicorn + uvicorn workers
├── healthcheck.py            ← compose uses this for the api container healthcheck
└── .dockerignore             ← keeps secrets / caches out of the image

frontend/
├── nginx.conf                ← static files + /api/* reverse proxy to api:8000
├── Dockerfile                ← builds the static-site image from nginx:alpine
└── .dockerignore

docker-compose.yml            ← api + frontend (+ optional Postgres)
.env.example.compose          ← copy to .env and edit
DEPLOY.md                     ← this file
```

---

## 7. Updating after a code change

```bash
docker compose build          # rebuild only the images whose context changed
docker compose up -d          # recreate containers; volumes survive
```

If you only changed Python code:

```bash
docker compose up -d --build api
```

If you only changed HTML / nginx config:

```bash
docker compose up -d --build frontend
```

---

## 8. Tearing down

```bash
# Stop containers, keep volumes
docker compose down

# Stop + delete volumes (DROPS LEAD DATA)
docker compose down -v
```
