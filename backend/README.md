# JevScale backend

FastAPI service for datasets, benchmark runs, typed decisions, metrics, and exports.

Phase 1 exposes only health and system-status endpoints. Provider credentials are optional until the corresponding implementation phase.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

