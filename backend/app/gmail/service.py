"""Gmail OAuth and API integration service for ephemeral email ingestion."""

from __future__ import annotations

import base64
import logging
import re
import urllib.parse
from html import unescape
from typing import Any
from uuid import uuid4

import httpx

from ..config import Settings, get_settings
from .models import NormalizedGmailMessage

logger = logging.getLogger(__name__)

GMAIL_SCOPE = "https://www.googleapis.com/auth/gmail.readonly"
GOOGLE_AUTH_BASE = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GMAIL_API_BASE = "https://gmail.googleapis.com/gmail/v1/users/me"


class GmailError(Exception):
    """Base exception for Gmail integration errors."""

    def __init__(self, message: str, status_code: int = 500) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class GmailConfigurationError(GmailError):
    def __init__(self, message: str = "Google OAuth credentials not configured.") -> None:
        super().__init__(message, status_code=400)


class GmailAuthenticationError(GmailError):
    def __init__(self, message: str = "Gmail not authenticated or token expired.") -> None:
        super().__init__(message, status_code=401)


class GmailService:
    """Manages ephemeral Google OAuth authentication and Gmail API reads."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._tokens: dict[str, Any] | None = None
        self._connected_email: str | None = None
        self._auth_state: str = ""

    @property
    def is_connected(self) -> bool:
        return bool(self._tokens and self._tokens.get("access_token"))

    @property
    def connected_email(self) -> str | None:
        return self._connected_email

    def get_auth_url(self) -> tuple[str, str]:
        """Generate Google OAuth 2.0 authorization URL."""
        if not self.settings.has_gmail_credentials:
            raise GmailConfigurationError(
                "GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET must be configured in backend/.env."
            )

        self._auth_state = uuid4().hex
        params = {
            "client_id": self.settings.google_client_id,
            "redirect_uri": self.settings.google_redirect_uri,
            "response_type": "code",
            "scope": GMAIL_SCOPE,
            "access_type": "offline",
            "prompt": "consent",
            "state": self._auth_state,
        }
        url = f"{GOOGLE_AUTH_BASE}?{urllib.parse.urlencode(params)}"
        return url, self._auth_state

    async def exchange_code(self, code: str) -> str:
        """Exchange authorization code for OAuth tokens and verify connected email."""
        if not self.settings.has_gmail_credentials:
            raise GmailConfigurationError("Google credentials missing.")

        data = {
            "code": code,
            "client_id": self.settings.google_client_id,
            "client_secret": self.settings.google_client_secret,
            "redirect_uri": self.settings.google_redirect_uri,
            "grant_type": "authorization_code",
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(GOOGLE_TOKEN_URL, data=data)
            if not resp.is_success:
                logger.error("OAuth token exchange failed: %s", resp.text)
                raise GmailAuthenticationError("Failed to exchange authorization code for tokens.")

            self._tokens = resp.json()

            # Retrieve user's email address
            profile_resp = await client.get(
                f"{GMAIL_API_BASE}/profile",
                headers={"Authorization": f"Bearer {self._tokens.get('access_token')}"},
            )
            if profile_resp.is_success:
                self._connected_email = profile_resp.json().get("emailAddress")

        return self._connected_email or "connected@gmail.com"

    def disconnect(self) -> None:
        """Clear ephemeral token data from memory."""
        self._tokens = None
        self._connected_email = None

    async def fetch_messages(
        self, query: str = "label:INBOX", max_results: int = 10
    ) -> list[NormalizedGmailMessage]:
        """Fetch real emails matching query held ephemerally in memory without DB persistence."""
        if not self.is_connected or not self._tokens:
            raise GmailAuthenticationError("Gmail account is not connected.")

        access_token = self._tokens.get("access_token")
        headers = {"Authorization": f"Bearer {access_token}"}
        limit = min(25, max(1, max_results))

        async with httpx.AsyncClient(timeout=20.0) as client:
            # Step 1: List matching message IDs
            list_url = f"{GMAIL_API_BASE}/messages"
            params = {"q": query, "maxResults": limit}
            resp = await client.get(list_url, headers=headers, params=params)

            if resp.status_code == 401:
                self.disconnect()
                raise GmailAuthenticationError("Gmail access token has expired. Please reconnect.")
            if not resp.is_success:
                logger.error("Gmail list messages failed: %s", resp.text)
                raise GmailError("Failed to fetch messages from Gmail API.")

            msg_refs = resp.json().get("messages", [])
            normalized_messages: list[NormalizedGmailMessage] = []

            # Step 2: Fetch message details
            for ref in msg_refs:
                msg_id = ref.get("id")
                msg_resp = await client.get(
                    f"{GMAIL_API_BASE}/messages/{msg_id}",
                    headers=headers,
                    params={"format": "full"},
                )
                if not msg_resp.is_success:
                    continue

                raw_msg = msg_resp.json()
                norm = self._parse_gmail_message(raw_msg)
                normalized_messages.append(norm)

        return normalized_messages

    def _parse_gmail_message(self, raw: dict[str, Any]) -> NormalizedGmailMessage:
        """Parse raw Gmail API message dictionary into clean NormalizedGmailMessage."""
        msg_id = raw.get("id", "")
        thread_id = raw.get("threadId", "")
        snippet = unescape(raw.get("snippet", ""))
        labels = raw.get("labelIds", [])

        payload = raw.get("payload", {})
        headers_list = payload.get("headers", [])
        headers = {h.get("name", "").lower(): h.get("value", "") for h in headers_list}

        subject = headers.get("subject", "(No Subject)")
        sender = headers.get("from", "unknown")
        recipient = headers.get("to", "")
        recipients = [r.strip() for r in recipient.split(",") if r.strip()]
        date_str = headers.get("date", "")

        # Extract plain text body
        body = self._extract_body(payload)
        if not body.strip():
            body = snippet

        return NormalizedGmailMessage(
            id=msg_id,
            thread_id=thread_id,
            sender=sender,
            recipients=recipients,
            subject=subject,
            body=body,
            snippet=snippet,
            received_at=date_str,
            labels=labels,
        )

    def _extract_body(self, payload: dict[str, Any]) -> str:
        """Recursively extract plain text body content from MIME parts."""
        # Case 1: Direct body on payload
        body_obj = payload.get("body", {})
        data = body_obj.get("data")
        if data:
            try:
                decoded = base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
                return self._clean_text(decoded)
            except Exception:
                pass

        # Case 2: Multipart traversal
        parts = payload.get("parts", [])
        text_parts: list[str] = []
        html_parts: list[str] = []

        def _traverse(part_list: list[dict[str, Any]]):
            for part in part_list:
                mime_type = part.get("mimeType", "")
                part_body = part.get("body", {})
                bdata = part_body.get("data")
                if bdata:
                    try:
                        text_val = base64.urlsafe_b64decode(bdata).decode("utf-8", errors="replace")
                        if mime_type == "text/plain":
                            text_parts.append(text_val)
                        elif mime_type == "text/html":
                            html_parts.append(text_val)
                    except Exception:
                        pass
                if "parts" in part:
                    _traverse(part["parts"])

        _traverse(parts)

        if text_parts:
            return self._clean_text("\n".join(text_parts))
        elif html_parts:
            # Strip basic HTML tags
            raw_html = "\n".join(html_parts)
            clean = re.sub(r"<[^>]+>", " ", raw_html)
            clean = re.sub(r"\s+", " ", clean)
            return unescape(clean).strip()

        return ""

    def _clean_text(self, text: str) -> str:
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        # Collapse excessive newlines
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()


_gmail_singleton: GmailService | None = None


def get_gmail_service(settings: Settings | None = None) -> GmailService:
    global _gmail_singleton
    if _gmail_singleton is None:
        _gmail_singleton = GmailService(settings=settings)
    return _gmail_singleton
