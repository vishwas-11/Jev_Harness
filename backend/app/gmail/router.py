"""FastAPI routes for Gmail OAuth flow and ephemeral email retrieval."""

from __future__ import annotations

import logging
from fastapi import APIRouter, Depends, HTTPException, status

from ..config import Settings, get_settings
from .models import (
    GmailAuthUrlResponse,
    GmailCallbackRequest,
    GmailFetchRequest,
    GmailFetchResponse,
    GmailStatusResponse,
)
from .service import GmailError, GmailService, get_gmail_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/gmail", tags=["gmail"])


@router.get("/status", response_model=GmailStatusResponse)
async def get_status(
    settings: Settings = Depends(get_settings),
    service: GmailService = Depends(get_gmail_service),
) -> GmailStatusResponse:
    """Return Gmail integration connection status."""
    return GmailStatusResponse(
        connected=service.is_connected,
        email=service.connected_email,
        client_id_configured=settings.has_gmail_credentials,
    )


@router.get("/auth-url", response_model=GmailAuthUrlResponse)
async def get_auth_url(
    service: GmailService = Depends(get_gmail_service),
) -> GmailAuthUrlResponse:
    """Generate Google OAuth 2.0 authorization URL for read-only Gmail access."""
    try:
        url, state = service.get_auth_url()
        return GmailAuthUrlResponse(auth_url=url, state=state)
    except GmailError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.post("/callback", response_model=GmailStatusResponse)
async def oauth_callback(
    req: GmailCallbackRequest,
    service: GmailService = Depends(get_gmail_service),
) -> GmailStatusResponse:
    """Exchange authorization code from Google OAuth redirect for access token."""
    try:
        email = await service.exchange_code(req.code)
        return GmailStatusResponse(
            connected=True,
            email=email,
            client_id_configured=service.settings.has_gmail_credentials,
        )
    except GmailError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.post("/disconnect")
async def disconnect(
    service: GmailService = Depends(get_gmail_service),
) -> dict[str, str]:
    """Disconnect Gmail session and clear all in-memory token data."""
    service.disconnect()
    return {"status": "disconnected"}


@router.get("/fetch", response_model=GmailFetchResponse)
async def fetch_messages_get(
    query: str = "label:INBOX",
    max_results: int = 10,
    service: GmailService = Depends(get_gmail_service),
) -> GmailFetchResponse:
    """Fetch real emails via GET query parameters held ephemerally in memory."""
    try:
        messages = await service.fetch_messages(
            query=query, max_results=max_results
        )
        return GmailFetchResponse(
            messages=messages,
            total_fetched=len(messages),
            query=query,
        )
    except GmailError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.post("/fetch", response_model=GmailFetchResponse)
async def fetch_messages_post(
    req: GmailFetchRequest,
    service: GmailService = Depends(get_gmail_service),
) -> GmailFetchResponse:
    """Fetch real emails via POST body held ephemerally in memory."""
    try:
        messages = await service.fetch_messages(
            query=req.query, max_results=req.max_results
        )
        return GmailFetchResponse(
            messages=messages,
            total_fetched=len(messages),
            query=req.query,
        )
    except GmailError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
