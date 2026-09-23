from datetime import UTC, datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .config import get_settings

settings = get_settings()
app = FastAPI(title="JevScale API", version="0.1.0", description="Control plane for high-throughput AI decision benchmarks.")
app.add_middleware(CORSMiddleware, allow_origins=[settings.frontend_origin], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


class HealthResponse(BaseModel):
    status: str
    service: str
    environment: str
    timestamp: datetime


@app.get("/api/health", response_model=HealthResponse, tags=["system"])
async def health() -> HealthResponse:
    return HealthResponse(status="ok", service="jevscale-api", environment=settings.app_env, timestamp=datetime.now(UTC))


@app.get("/api/v1/system/status", tags=["system"])
async def system_status() -> dict[str, str | bool]:
    return {"database_configured": bool(settings.supabase_db_url), "jev_configured": bool(settings.typesafe_api_key), "llm_configured": bool(settings.llm_api_key), "phase": "scaffolding"}

