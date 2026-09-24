from datetime import UTC, datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from .config import get_settings
from .db import init_db
from .datasets.router import router as datasets_router
from .classifications.router import router as classifications_router

settings = get_settings()
init_db()

app = FastAPI(
    title="JevScale API",
    version="0.3.0",
    description="Control plane for high-throughput AI decision benchmarks and Jev classification.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(datasets_router)
app.include_router(classifications_router)


class HealthResponse(BaseModel):
    status: str
    service: str
    environment: str
    timestamp: datetime


@app.get("/api/health", response_model=HealthResponse, tags=["system"])
async def health():
    return HealthResponse(
        status="ok",
        service="jevscale-api",
        environment=settings.app_env,
        timestamp=datetime.now(UTC),
    )


@app.get("/api/v1/system/status", tags=["system"])
async def system_status():
    return {
        "database_configured": bool(settings.supabase_db_url),
        "jev_configured": settings.has_jev_credentials,
        "jev_provider": "vercel-ai-gateway" if settings.has_jev_credentials else "mock-sandbox",
        "llm_configured": bool(settings.llm_api_key),
        "phase": "jev-classification",
    }
