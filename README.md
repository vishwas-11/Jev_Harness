# JevScale

JevScale is an interactive laboratory for studying high-throughput AI decision systems. It compares Jev, traditional structured-output LLMs, and a Jev-to-LLM Hybrid policy across latency, throughput, cost, reliability, confidence, and quality.

## Phase 1 status

- FastAPI backend with health and system-status endpoints;
- React + TypeScript + Vite control-plane shell;
- Tailwind design foundation and responsive navigation;
- Docker Compose for frontend and backend;
- provider-safe environment template;
- architecture, integration-boundary, and benchmark-methodology docs.

No benchmark values in the interface are presented as real results. The dashboard contains clearly labeled shell-state examples until the run engine is implemented.

## Run locally

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

In another terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. The API health endpoint is `http://localhost:8000/api/health`.

Or use `docker compose up --build`.

Provider keys and database credentials belong only in the backend environment and are never exposed through Vite.

## Next phase

Phase 2 will implement dataset upload, CSV/JSONL/Parquet inspection, validation, preview, and persistence behind the Supabase repository boundary.

