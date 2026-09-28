# Phase 4 — Real Gmail Ingestion & LLM Baseline

## 1. Overview & Objective

Phase 4 of JevScale establishes an empirical baseline for comparing **Jev** (`typesafe-ai/jev` via Vercel AI Gateway) against a standard **Generative LLM baseline** (`gpt-4o-mini` with strict structured outputs) on identical email data.

In addition, Phase 4 introduces **ephemeral personal Gmail ingestion** via Google OAuth 2.0 (`gmail.readonly`), enabling evaluation of classification decisions on real-world customer support messages without violating data privacy or persisting raw email bodies.

---

## 2. Architecture & Data Flow

```text
       Personal Gmail Account                Synthetic / Uploaded Datasets
                │                                         │
                ▼ (OAuth 2.0 / Read-Only)                 │
          Gmail API Read                                  │
                │                                         │
                └───────────────┬─────────────────────────┘
                                ▼
                       Normalized Email Input
                      (Subject + Body + Metadata)
                                │
                                ▼
                    ClassificationDefinition
                  (Strict 7-Dimension Taxonomy)
                                │
                ┌───────────────┴───────────────┐
                ▼                               ▼
       Strategy A: Real Jev            Strategy B: Real LLM
     (LangChain TypeSafeClassifier)   (LangChain ChatOpenAI)
     (Endpoint: Vercel AI Gateway)    (with_structured_output strict)
                │                               │
                └───────────────┬───────────────┘
                                ▼
                    Common ClassificationResult
                    ├── strategy ("jev" | "llm")
                    ├── intent, department, urgency, sentiment (Choice)
                    ├── spam, requires_human (Boolean)
                    ├── priority (Score 0-4)
                    ├── aggregate_confidence
                    ├── latency breakdown (prep, request, validation, total)
                    └── decision trace & telemetry
```

### Key Architectural Tenet: No Runtime Mock Fallbacks
The system **never** silently falls back to a mock classifier when API credentials are missing or upstream requests fail. Missing API keys fail immediately and loudly with HTTP 400 (`JevConfigurationError` or `LLMConfigurationError`). Upstream errors (401, 429, 504) propagate as structured backend errors directly to the frontend.

---

## 3. Ephemeral Gmail Ingestion

### Authentication: Google OAuth 2.0
- **Scope**: `https://www.googleapis.com/auth/gmail.readonly` (strictly read-only).
- **Flow**: User clicks "Connect Gmail Account" in the React Playground, completes Google consent, and returns via redirect.
- **Token Handling**: Access tokens are held exclusively in volatile server session memory (`GmailService._tokens`). Refresh tokens are never persisted to SQLite or written to disk.
- **Disconnect**: Clicking "Disconnect" immediately purges all in-memory OAuth tokens.

### Bounded Ingestion
- Configurable search query (default: `label:INBOX`, with support for queries like `label:UNREAD`, `is:starred`).
- Bounded batch size: 5, 10, or 25 emails.
- Extracts plain text from MIME parts (or strips HTML tags when plain text is absent) and decodes Base64URL payloads.

---

## 4. Privacy & Security Constraints

1. **No Database Persistence of Raw Bodies**: Gmail messages are fetched ephemerally for benchmark execution and are never saved to the `emails` or `datasets` tables.
2. **Zero Plaintext Logging**: Full email bodies, authorization codes, bearer tokens, and client secrets are banned from server logs.
3. **No Frontend Exposure**: Credentials (`AI_GATEWAY_API_KEY`, `OPENAI_API_KEY`, `GOOGLE_CLIENT_SECRET`) are read strictly by FastAPI from `backend/.env`. No `VITE_` variables expose secrets.
4. **Git Protection**: `.env` and `.env.*` are excluded by `.gitignore`.

---

## 5. Strict Benchmark Fairness & Common Taxonomy

To ensure an unbiased evaluation between Jev and the generative LLM, both classifiers evaluate identical inputs against the exact same 7 dimensions:

| Dimension | Type | Categories / Rubric |
| :--- | :--- | :--- |
| **Intent** | Choice (8 options) | `billing_issue`, `technical_issue`, `account_issue`, `sales`, `refund`, `general_question`, `complaint`, `other` |
| **Department** | Choice (7 options) | `billing`, `support`, `sales`, `account_management`, `security`, `operations`, `other` |
| **Urgency** | Choice (4 levels) | `low`, `medium`, `high`, `critical` |
| **Sentiment** | Choice (5 options) | `positive`, `neutral`, `frustrated`, `angry`, `negative` |
| **Spam** | Boolean / Noul | True = promotional blast, lottery, phishing, irrelevant advertising |
| **Requires Human** | Boolean / Noul | True = refund discretion, credential resets, legal escalation, outages |
| **Priority** | Score (0 - 4) | P5 (Trivial: 0) to P1 (Critical Outage / Revenue Blocker: 4) |

---

## 6. LLM Baseline Implementation

- **Provider**: OpenAI (`gpt-4o-mini`).
- **Integration**: LangChain `ChatOpenAI` coupled with native structured output (`with_structured_output(LLMSupportClassification, method="json_schema", strict=True)`).
- **Prompt Engineering**: System prompt dynamically embeds the identical instructions and criteria from `DEFAULT_CLASSIFICATION_DEFINITION`.
- **Parsing Guarantee**: Native JSON Schema validation enforces non-empty choices and bounded values. Invalid model responses raise `LLMValidationError` (HTTP 502) rather than attempting lossy string parsing.

---

## 7. Latency Boundaries & Instrumentation

Each classifier records a discrete latency breakdown so that model latency is never conflated with application serialization or network overhead:

| Metric | Meaning for Jev | Meaning for LLM Baseline |
| :--- | :--- | :--- |
| `state_prep_ms` | Question and payload packaging | System and user prompt formatting |
| `jev_request_ms` | Roundtrip to Vercel AI Gateway (`typesafe-ai/jev`) | N/A |
| `llm_request_ms` | N/A | Roundtrip to OpenAI API (`gpt-4o-mini`) |
| `normalization_ms` | Unpacking Choice, Noul, Score distributions | N/A |
| `validation_ms` | N/A | Pydantic JSON Schema validation |
| `total_ms` | End-to-end execution time | End-to-end execution time |

---

## 8. Error Handling Specification

Backend exceptions map deterministically to HTTP error codes:

| Error Type | Exception Class | HTTP Code | Cause |
| :--- | :--- | :--- | :--- |
| Missing Key | `JevConfigurationError`, `LLMConfigurationError` | 400 | Environment variable unset in `backend/.env` |
| Auth Failure | `JevAuthenticationError`, `LLMAuthenticationError` | 401 | Upstream rejected API key |
| Rate Limit | `JevRateLimitError`, `LLMRateLimitError` | 429 | Upstream quota or rate limit exceeded |
| Timeout | `JevTimeoutError`, `LLMTimeoutError` | 504 | Upstream call exceeded 30s timeout |
| Malformed Output | `LLMValidationError` | 502 | LLM produced output violating schema |
| Upstream Error | `JevProviderError`, `LLMProviderError` | 502 | Upstream server 5xx error |

---

## 9. Environment Configuration

Variables in `backend/.env`:

```env
# Vercel AI Gateway / TypeSafe Jev
AI_GATEWAY_API_KEY=your_vercel_gateway_key_here
AI_GATEWAY_BASE_URL=https://ai-gateway.vercel.sh/typesafe
JEV_MODEL=typesafe-ai/jev
JEV_TIMEOUT=30.0

# LLM Baseline (OpenAI)
OPENAI_API_KEY=your_openai_key_here
LLM_MODEL=gpt-4o-mini
LLM_TIMEOUT=30.0

# Google OAuth 2.0 (Gmail Read-Only)
GOOGLE_CLIENT_ID=your_google_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=http://localhost:5173/classifications
```

---

## 10. How to Run Tests & Verification

### Run Automated Backend Unit Tests (Offline / Test Fakes Only)
```bash
cd backend
.venv\Scripts\pytest -v
```
All 28 tests run using test fakes (`FakeTestJevClassifier`, mock runnables, and mock OAuth data) and do not incur paid API charges.

### Verify Loud Unconfigured Error (Live Pre-Flight)
Before keys are configured, calling the API returns a structured HTTP 400:
```bash
curl -X POST http://localhost:8000/api/classifications/test \
  -H "Content-Type: application/json" \
  -d '{"subject": "Refund inquiry", "body": "Please refund my invoice.", "strategy": "jev"}'
```
Response:
```json
{
  "detail": "AI_GATEWAY_API_KEY is not configured. Add your Vercel AI Gateway key to backend/.env."
}
```
