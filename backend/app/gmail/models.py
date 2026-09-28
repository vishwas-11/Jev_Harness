"""Data models for Gmail OAuth, status, and normalized ephemeral email messages."""

from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field


class GmailAuthUrlResponse(BaseModel):
    """Response containing Google OAuth authorization URL."""

    auth_url: str
    state: str


class GmailCallbackRequest(BaseModel):
    """Request payload containing OAuth authorization code."""

    code: str = Field(description="Google OAuth authorization code.")
    state: str | None = Field(default=None, description="OAuth state parameter.")


class GmailStatusResponse(BaseModel):
    """Current connection status for Gmail ingestion."""

    connected: bool
    email: str | None = None
    client_id_configured: bool = False


class GmailFetchRequest(BaseModel):
    """Parameters for querying Gmail inbox."""

    query: str = Field(
        default="label:INBOX",
        description="Gmail search query filter (e.g. label:INBOX, is:unread, newer_than:7d).",
    )
    max_results: int = Field(
        default=10,
        ge=1,
        le=25,
        description="Bounded retrieval limit between 1 and 25 emails for safe inspection.",
    )


class NormalizedGmailMessage(BaseModel):
    """Ephemeral normalized email message extracted from Gmail API."""

    id: str
    thread_id: str
    sender: str
    recipients: list[str] = Field(default_factory=list)
    subject: str
    body: str
    snippet: str
    received_at: str
    labels: list[str] = Field(default_factory=list)


class GmailFetchResponse(BaseModel):
    """Response containing fetched normalized emails held ephemerally in memory."""

    messages: list[NormalizedGmailMessage]
    total_fetched: int
    query: str
