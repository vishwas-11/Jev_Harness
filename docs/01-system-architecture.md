# JevScale system architecture

## Phase 2 boundary

JevScale is a React control plane backed by FastAPI. The browser owns presentation and temporary experiment configuration. FastAPI owns credentials, validation, provider calls, job orchestration, persistence, metrics, and exports.

Phase 2 adds a synchronous dataset service:

```text
React upload/mapping UI
        |
        v
FastAPI dataset routes
        |
        v
DatasetService -> Parser -> Normalizer -> Validator -> Repository
                                                        |
                                                        v
                                             Supabase PostgreSQL / local SQLite
```

Jev, LLM, Hybrid routing, Redis, Celery, and benchmark workers are not implemented yet.

## Dataset architecture

CSV, JSONL, and Parquet are parsed into one normalized `DatasetRecord` contract. `datasets` stores source and mapping metadata; `emails` stores normalized rows with JSON-compatible ground truth and metadata. This keeps future classification code independent of the source file format.

## Frontend information architecture

Dashboard, Datasets, New experiment, Active runs, Classifications, Analytics, Comparison, and Settings are wired as the primary application surfaces. Datasets is now functional: upload, inspect, map columns, save, list, preview, validate, and delete. New Experiment can select saved datasets but does not execute experiments.

## Data flow

1. Browser uploads a bounded file to `/api/datasets/inspect`.
2. Backend detects format, parses rows, and returns columns/sample/report without persistence.
3. Browser submits the chosen mapping to `/api/datasets`.
4. Backend normalizes and validates records, then persists dataset metadata and emails.
5. Browser requests `/preview` pages rather than loading the full dataset.
6. Future experiment configuration selects the dataset ID; classification has not started yet.

## Measurement boundary for future benchmarks

Dataset persistence time must not silently become Jev/LLM model latency. Future runs should retain separate model latency, persistence latency, and end-to-end pipeline latency fields.
