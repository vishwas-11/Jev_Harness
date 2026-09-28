"""Tests for GmailService: OAuth generation, error states, and MIME parsing."""

import base64

import pytest

from app.config import Settings
from app.gmail.models import NormalizedGmailMessage
from app.gmail.service import GmailConfigurationError, GmailService


def test_gmail_service_missing_credentials_raises():
    """Ensure missing Google credentials raise GmailConfigurationError (status 400)."""
    settings = Settings(
        google_client_id="",
        google_client_secret="",
        google_redirect_uri="",
    )
    service = GmailService(settings=settings)
    with pytest.raises(GmailConfigurationError) as exc_info:
        service.get_auth_url()
    assert exc_info.value.status_code == 400
    assert "GOOGLE_CLIENT_ID" in exc_info.value.message


def test_gmail_service_auth_url_generated():
    """Ensure auth URL generation produces valid Google OAuth endpoint and state."""
    settings = Settings(
        google_client_id="test-client-id",
        google_client_secret="test-client-secret",
        google_redirect_uri="http://localhost:8000/api/gmail/callback",
    )
    service = GmailService(settings=settings)
    auth_url, state = service.get_auth_url()
    assert "https://accounts.google.com/o/oauth2/v2/auth" in auth_url
    assert "client_id=test-client-id" in auth_url
    assert state != ""
    assert service.is_connected is False


def test_gmail_normalize_message():
    """Verify MIME parsing extracts headers, decodes base64 payload, and constructs NormalizedGmailMessage."""
    settings = Settings(
        google_client_id="test-client-id",
        google_client_secret="test-client-secret",
    )
    service = GmailService(settings=settings)

    body_text = "Hello, please cancel my account immediately."
    encoded_body = base64.urlsafe_b64encode(body_text.encode("utf-8")).decode("utf-8")

    raw_msg = {
        "id": "msg_abc123",
        "threadId": "thread_xyz789",
        "snippet": "Hello, please cancel my account...",
        "labelIds": ["INBOX", "UNREAD"],
        "internalDate": "1711600000000",
        "payload": {
            "headers": [
                {"name": "Subject", "value": "Account Cancellation Request"},
                {"name": "From", "value": "customer@example.com"},
                {"name": "To", "value": "support@mycompany.com"},
                {"name": "Date", "value": "Wed, 28 Mar 2026 10:00:00 +0000"},
            ],
            "body": {"data": encoded_body},
        },
    }

    normalized = service._parse_gmail_message(raw_msg)
    assert isinstance(normalized, NormalizedGmailMessage)
    assert normalized.id == "msg_abc123"
    assert normalized.thread_id == "thread_xyz789"
    assert normalized.subject == "Account Cancellation Request"
    assert normalized.sender == "customer@example.com"
    assert normalized.body == body_text
    assert normalized.labels == ["INBOX", "UNREAD"]
