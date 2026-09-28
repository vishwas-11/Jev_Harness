"""Gmail package for OAuth integration and ephemeral message ingestion."""

from .models import (
    GmailAuthUrlResponse,
    GmailCallbackRequest,
    GmailFetchRequest,
    GmailFetchResponse,
    GmailStatusResponse,
    NormalizedGmailMessage,
)
from .router import router
from .service import GmailAuthenticationError, GmailConfigurationError, GmailError, GmailService, get_gmail_service

__all__ = [
    "GmailAuthenticationError",
    "GmailAuthUrlResponse",
    "GmailCallbackRequest",
    "GmailConfigurationError",
    "GmailError",
    "GmailFetchRequest",
    "GmailFetchResponse",
    "GmailService",
    "GmailStatusResponse",
    "NormalizedGmailMessage",
    "get_gmail_service",
    "router",
]
