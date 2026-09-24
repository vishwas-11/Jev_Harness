# JevScale

JevScale is an interactive laboratory for studying high-throughput AI decision systems. It compares Jev, traditional structured-output LLMs, and a Jev-to-LLM Hybrid policy across latency, throughput, cost, reliability, confidence, and quality.

## Phase 2 status

The current application supports dataset management end to end:

- CSV, JSONL, and Parquet inspection;
- subject/body, ID, and optional ground-truth column mapping;
- parser and validation reports with errors versus warnings;
- SQLAlchemy persistence to Supabase-compatible PostgreSQL or local SQLite fallback;
- paginated dataset previews;
- dataset deletion;
- saved dataset selection in New Experiment.

Jev, LLM, Hybrid routing, benchmark execution, Redis, and Celery remain future phases. No benchmark values are fabricated.

## Run locally

Backend:

```powershell
cd backend
..\backend\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload
```

Frontend:

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. The API health endpoint is `http://localhost:8000/api/health`.

Run backend tests:

```powershell
backend\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider backend/tests
```

Or use `docker compose up --build`.

## Environment

Copy `.env.example` to `.env` when credentials are available. `SUPABASE_DB_URL` is backend-only. Provider keys remain backend-only and are not needed for Phase 2.

## Next phase

Phase 3 will verify the current official LangChain Jev integration and implement typed multi-question classification behind a provider adapter.
