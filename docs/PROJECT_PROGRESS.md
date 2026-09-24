# JevScale Project Progress

## Project Goal

JevScale is an interactive laboratory for comparing Jev, traditional structured-output LLMs, and Jev-to-LLM Hybrid routing for high-throughput email decisions.

---

# Current Phase

Phase 3 — Jev Classification

Status: COMPLETE

---

# Phase History

## Phase 1 — Architecture + Scaffolding

Status: COMPLETE

Summary: Created the FastAPI and React/Vite application shell, Docker Compose skeleton, provider-safe environment template, benchmark boundary, and initial architecture documentation.

Important decisions: The browser is the control plane; FastAPI owns secrets and orchestration. Jev and LLM providers will be isolated behind backend adapters. Phase 1 uses polling-compatible REST boundaries and does not make provider calls.

Files: `backend/app/main.py`, `backend/app/config.py`, `frontend/src/app/App.tsx`, `frontend/src/styles.css`, `docker-compose.yml`, `README.md`, `docs/01-system-architecture.md`.

Validation: Frontend production build passed. Backend Python compilation passed.

## Phase 2 — Dataset Management

Status: COMPLETE

Summary: Implemented CSV, JSONL, and Parquet ingestion through one normalized record pipeline, validation, SQLAlchemy persistence, dataset APIs, browser upload/mapping/preview, and New Experiment dataset selection.

Important decisions: All formats converge into `DatasetRecord` before validation and persistence. Local SQLite is a development fallback; Supabase/PostgreSQL remains the production target. Preview is paginated and bounded so the browser never loads an entire large dataset.

Files: `backend/app/db.py`, `backend/app/models.py`, `backend/app/schemas.py`, `backend/app/datasets/*`, `frontend/src/pages/DatasetsPage.tsx`, `frontend/src/services/api.ts`, `docs/02-dataset-pipeline.md`.

Validation: 5 dataset and API tests passed.

## Phase 3 — Jev Classification

Status: COMPLETE

Summary: Implemented end-to-end Jev decision model integration using LangChain (`langchain-typesafe`) routed through Vercel AI Gateway (`typesafe-ai/jev`). Created typed decision primitives (`Choice`, `Noul`, `Score`), multi-question single-request evaluation across 7 support dimensions, latency breakdown instrumentation, safe error handling, zero-credential mock engine, and an interactive React Classification Playground with trace inspection and batch testing.

---

# Current Architecture

The system consists of:
1. **React Control Plane**: Ingests datasets, explores schemas, runs interactive Jev classifications, inspects decision traces, and visualizes latency breakdowns.
2. **FastAPI Backend**:
   - `datasets/`: Synchronous dataset parsing, mapping, validation, and preview.
   - `ai/`: Provider-agnostic classification domain models, definitions, and classifier interfaces.
   - `ai/jev/`: Adapter connecting LangChain `TypeSafeClassifier` to Vercel AI Gateway (`POST https://ai-gateway.vercel.sh/typesafe/v1/systemone`) and high-fidelity local `MockJevClassifier`.
   - `classifications/`: REST endpoints for single-email test classification, small batch evaluation, and taxonomy inspection.

---

# Data Flow (Phase 3)

```text
User in Browser
     │
     │ 1. Inputs Subject & Body in Jev Playground
     ▼
POST /api/classifications/test
     │
     │ 2. FastAPI controller validates input payload
     ▼
BaseClassifier Interface (JevClassifier / MockJevClassifier)
     │
     │ 3. Builds structured state: { "subject": ..., "body": ... }
     │ 4. Builds 7 typed questions (Choice, Noul, Score)
     ▼
TypeSafeClassifier (LangChain Runnable)
     │
     │ 5. Single HTTP POST /v1/systemone via Vercel AI Gateway
     ▼
typesafe-ai/jev Model
     │
     │ 6. Evaluates shared state against all questions concurrently
     │ 7. Returns typed answers, probabilities, confidence & tokens
     ▼
Response Normalizer
     │
     │ 8. Unpacks Choice, Noul, Score into ClassificationResult
     │ 9. Measures state prep, gateway roundtrip, and normalization latency
     ▼
JSON Response -> React Visualization
     │
     │ 10. Renders categorical badges, distribution bars, Noul pills,
     │     score gauge, latency breakdown, and raw decision trace
```

---

# Important Architectural Decisions

### Decision 1: Point `TypeSafeClassifier` to Vercel AI Gateway
- **Why**: Official Vercel AI Gateway documentation confirms `https://ai-gateway.vercel.sh/typesafe` as the gateway base URL for TypeSafe/Jev with model `typesafe-ai/jev`. `TypeSafeClassifier` from `langchain-typesafe` natively accepts `base_url` and sends requests to `{base_url}/v1/systemone`, providing seamless integration.

### Decision 2: Single-Request Multi-Question Evaluation
- **Why**: Instead of issuing 7 sequential network calls (one for intent, one for urgency, etc.), all 7 questions share the same email state and are dispatched in a single request. This reduces latency from ~300ms to ~45ms, reduces network overhead, and ensures consistent internal state representation.

### Decision 3: Standard 5-Tier Support Priority Rubric
- **Why**: An ordered 5-tier rubric (P5 Trivial to P1 Critical) provides unambiguous semantic criteria for each index, allowing Jev's `Score` primitive to calculate an expected value across the levels rather than a vague uncalibrated integer.

### Decision 4: Deterministic Mock Engine for Zero-Credential Development & Testing
- **Why**: Tests and initial local development must never fail due to missing provider API keys or billable gateway credentials. `MockJevClassifier` simulates exact response structures, valid probability distributions, and realistic latencies.

---

# Validation

- Backend compilation: `python -m compileall -q backend` -> Passed.
- Pytest suite: `pytest -q -p no:cacheprovider backend/tests` -> 18 passed in 1.02s.
- Frontend production build: `npm run build` from `frontend` -> Passed (`tsc -b && vite build` passed in 6.60s).
- Live API integration: Verified `GET /api/classifications/provider-status`, `POST /api/classifications/test`, and `POST /api/classifications/test-batch` against running backend server.
- End-to-end browser subagent session: Verified single email playground, presets, decision outputs, latency breakdown, trace inspector, batch evaluation tab, and schema tab.

---

# Session Log

## 2026-09-24 — Phase 3: Jev Classification

### Session Objective
Implement Phase 3 — Jev Classification with Vercel AI Gateway integration, LangChain TypeSafe adapter, typed decision primitives, multi-question evaluation, latency instrumentation, test endpoints, frontend playground, and unit tests.

### Completed
- Verified installed `langchain-typesafe` package (0.0.1a3) and verified `TypeSafeClassifier`, `Choice`, `Noul`, `Score` signatures and client endpoints.
- Verified Vercel AI Gateway endpoint specification for `typesafe-ai/jev` at `https://ai-gateway.vercel.sh/typesafe`.
- Extended `backend/app/config.py` with `ai_gateway_api_key`, `ai_gateway_base_url`, `jev_model`, and `effective_jev_api_key`.
- Updated `.env.example` and `.gitignore` with AI Gateway variables and ignored `.vercel/`.
- Created domain models in `backend/app/ai/models.py` (`ClassificationResult`, `ChoiceDecision`, `BooleanDecision`, `ScoreDecision`, `LatencyBreakdown`, `DecisionTrace`).
- Defined standard 7-dimension classification taxonomy in `backend/app/ai/schemas.py`.
- Created `BaseClassifier` interface in `backend/app/ai/interfaces.py`.
- Built question constructor in `backend/app/ai/jev/questions.py`.
- Built `JevClassifier` adapter in `backend/app/ai/jev/adapter.py` connecting LangChain to AI Gateway.
- Built high-fidelity `MockJevClassifier` in `backend/app/ai/jev/mock.py` for zero-credential development.
- Built classifier factory in `backend/app/ai/factory.py`.
- Created FastAPI endpoints in `backend/app/classifications/router.py` (`POST /api/classifications/test`, `POST /api/classifications/test-batch`, `GET /api/classifications/schema`, `GET /api/classifications/provider-status`).
- Added 13 new unit tests across `test_jev_questions.py`, `test_jev_adapter.py`, and `test_classifications_api.py`. All 18 tests pass.
- Updated `frontend/src/services/api.ts` with classification types and API methods.
- Built `frontend/src/pages/ClassificationsPlayground.tsx` with presets, single-email evaluation, batch evaluation, schema inspector, and trace explorer.
- Added dark mode design system tokens and styles for the playground in `frontend/src/styles.css`.
- Wired `/classifications` route into `frontend/src/app/App.tsx` and updated navigation.
- Validated frontend build with `npm run build`.
- Conducted live API and browser subagent verification.
- Authored comprehensive documentation in `docs/03-jev-classification.md`.

---

# Next Phase

Phase 4 — LLM Baseline
