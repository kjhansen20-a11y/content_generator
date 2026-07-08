# Post Generator

Local-first SaaS platform for AI-assisted social media content creation.

## Current status

- **Phase 0** — Auth, multi-tenant foundation, Streamlit dashboard
- **Phase 1 (MVP v0.1)** — Profiles, manual generation, calendar, approve/queue, mock publish, admin
- **Phase 2 (in progress)** — Knowledge base, file uploads, marketing plans, content pillars, posting rules

## Prerequisites

- Python 3.12
- Git

## Setup

```powershell
cd "c:\Users\kjhan\Post generator"
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
copy backend\.env.example backend\.env
```

Edit `backend\.env` and set `JWT_SECRET`, `OPENAI_API_KEY`, and optionally `PLATFORM_ADMIN_EMAIL`.

## Run backend

```powershell
cd backend
..\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
```

API docs: http://127.0.0.1:8001/docs

## Run dashboard

In a second terminal:

```powershell
cd dashboard
..\.venv\Scripts\python.exe -m streamlit run app.py --server.port 8501
```

Dashboard: http://localhost:8501

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| POST | `/api/v1/auth/register` | Register user + create company |
| POST | `/api/v1/auth/login` | Login, returns JWT |
| GET | `/api/v1/auth/me` | Current user + companies |
| GET/PUT | `/api/v1/companies/{id}/profile` | Company profile |
| GET/PUT | `/api/v1/companies/{id}/brand` | Brand profile |
| GET/POST/DELETE | `/api/v1/companies/{id}/knowledge` | Knowledge base entries |
| POST/GET | `/api/v1/companies/{id}/files` | Upload/download files |
| GET/POST/PUT/DELETE | `/api/v1/companies/{id}/marketing-plans` | Marketing plans |
| POST | `/api/v1/companies/{id}/marketing-plans/generate` | AI-generate plan from keywords |
| GET | `/api/v1/companies/{id}/marketing-plans/active` | Active marketing plan |
| GET/POST/PUT/DELETE | `/api/v1/companies/{id}/content-pillars` | Content pillars |
| GET/POST/PUT/DELETE | `/api/v1/companies/{id}/posting-rules` | Posting rules |
| POST | `/api/v1/companies/{id}/generate` | Generate AI post draft |
| GET | `/api/v1/companies/{id}/calendar` | List content calendar |
| PUT | `/api/v1/companies/{id}/calendar/{item_id}` | Edit draft |
| POST | `/api/v1/companies/{id}/calendar/{item_id}/approve` | Approve draft |
| POST | `/api/v1/companies/{id}/calendar/{item_id}/queue` | Queue approved post |
| POST | `/api/v1/companies/{id}/calendar/{item_id}/publish` | Mock-publish |
| POST | `/api/v1/companies/{id}/publishing/publish-all` | Mock-publish all queued |
| GET | `/api/v1/companies/{id}/publishing/queue` | Queued posts |
| GET | `/api/v1/companies/{id}/publishing/jobs` | Publishing jobs |
| GET | `/api/v1/companies/{id}/connected-accounts` | Connected accounts |

### Admin (set `PLATFORM_ADMIN_EMAIL` in `.env`)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/admin/companies` | All companies + usage |
| GET | `/api/v1/admin/usage` | Token/cost summary |
| GET | `/api/v1/admin/users` | All users |
| GET | `/api/v1/admin/prompts` | Prompt templates |
| GET | `/api/v1/admin/jobs` | All publishing jobs |
