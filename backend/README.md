# Unicvesity Worldwide — Lead Capture Backend

A FastAPI service that saves leads from the landing-page form to a SQL database
and exposes admin endpoints to list, view, and export them.

> Sibling project: `../index.html` (landing page) → `../admin.html` (admin panel).

---

## Stack

- **FastAPI** — HTTP API + auto-generated docs at `/docs`
- **SQLAlchemy 2.x** — ORM
- **SQLite by default** (zero-config). Swap `DATABASE_URL` to Postgres for prod.
- **pydantic v2** — request/response validation
- **Bearer-token auth** — protects `/api/admin/*` (swap for JWT when you outgrow it)

---

## Quick start (Windows / macOS / Linux)

```bash
cd backend

# 1. Create a virtual env (one-time)
python -m venv .venv

# 2. Activate it
# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# macOS / Linux:
source .venv/bin/activate

# 3. Install deps
pip install -r requirements.txt

# 4. Configure
copy .env.example .env       # Windows
# cp .env.example .env      # macOS/Linux
# Edit .env and set a strong ADMIN_TOKEN.

# 5. Run the server (dev mode with auto-reload)
uvicorn app.main:app --reload --port 8000
```

The server will:

1. Auto-create a `leads.db` file with a `leads` table on first run.
2. Print `✅ Database connection OK` in the terminal.

Visit:

- API docs: <http://127.0.0.1:8000/docs>
- Health: <http://127.0.0.1:8000/api/health>

---

## Connecting the landing page

`index.html` is already wired to POST to `http://127.0.0.1:8000/api/leads`.

To override the URL (e.g. when you deploy the API), edit one line in the HTML:

```html
<script type="application/json" id="app-config">
{ "apiBaseUrl": "https://api.unicvesity.worldwide" }
</script>
```

The same override exists in `admin.html` (`#app-config-admin`).

---

## API reference

### Public

| Method | Path           | Body                          | Result                       |
|-------:|----------------|-------------------------------|------------------------------|
| POST   | `/api/leads`   | `LeadCreate` JSON             | `LeadSubmitResponse` (201)   |
| GET    | `/api/health`  | —                             | `{ ok, db }`                 |

**`POST /api/leads` body**

```json
{
  "name": "Jane Doe",
  "whatsapp": "+44 7000 000000",
  "email": "jane@example.com",
  "destination": "UK",
  "source": "unicvesity-landing-page"
}
```

`destination` must be one of: `UK`, `USA`, `Australia`, `Canada`, `Europe`, `Other`.

### Admin (requires `Authorization: Bearer <ADMIN_TOKEN>`)

| Method | Path                          | Description                              |
|-------:|-------------------------------|------------------------------------------|
| GET    | `/api/admin/leads`            | List, with `q`, `destination`, `limit`, `offset` |
| GET    | `/api/admin/leads/{id}`       | One lead                                 |
| DELETE | `/api/admin/leads/{id}`       | Remove a lead                            |
| GET    | `/api/admin/leads.csv`        | Stream all leads as CSV                  |

Open the admin UI: `../admin.html?token=<ADMIN_TOKEN>`.

---

## Files

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI entrypoint, CORS, startup
│   ├── config.py        # pydantic-settings, env loader
│   ├── db.py            # SQLAlchemy engine / session / Base
│   ├── models.py        # ORM: Lead
│   ├── schemas.py       # Pydantic validation, allowed destinations
│   ├── deps.py          # require_admin bearer-token guard
│   └── routes/
│       ├── __init__.py
│       └── leads.py     # POST /api/leads + admin endpoints
├── requirements.txt
├── .env.example
└── README.md
```

---

## Going to production

1. **Change the database** — set `DATABASE_URL=postgresql+psycopg://user:pass@host/db` in `.env`. SQLAlchemy handles the rest.
2. **Generate a strong admin token** — at least 32 random bytes, stored in `.env`. Never commit it.
3. **Run a real server** — replace `uvicorn` with `gunicorn -k uvicorn.workers.UvicornWorker`:
   ```bash
   gunicorn -k uvicorn.workers.UvicornWorker -w 4 -b 0.0.0.0:8000 app.main:app
   ```
4. **Lock down CORS** — replace `ALLOWED_ORIGINS` with your real domain(s) (no trailing slash).
5. **Put it behind TLS** — Caddy / Cloudflare / nginx.
6. **Backups** — your job; schedule `pg_dump` or `BACKUP` on your Postgres host.

That's it. The same JS on the landing page keeps working — just point `apiBaseUrl` at your prod hostname.
