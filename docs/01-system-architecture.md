# JevScale system architecture

## Phase 1 boundary

JevScale is a React control plane backed by FastAPI. The browser owns presentation and temporary experiment configuration. FastAPI owns credentials, validation, provider calls, job orchestration, persistence, metrics, and exports.

```text
React/Vite control plane -> FastAPI application -> repositories -> Supabase PostgreSQL
                                      |-> provider adapters (Jev / LLM)
                                      |-> bounded async benchmark engine
```

The provider boundary is explicit. Jev is not treated as a text-generation chat model: the Phase 3 adapter will call `langchain_typesafe.TypeSafeClassifier` with typed `Choice`, `Score`, and `Noul` questions. The LLM adapter will use equivalent Pydantic structured output. Both feed a common `ClassificationDecision` contract.

## Frontend information architecture

Dashboard, Datasets, New experiment, Active runs, Classifications, Analytics, Comparison, and Settings are wired as the primary application surfaces. Phase 1 provides the shell and a dashboard that clearly labels illustrative values as shell state.

## Data flow

1. Dataset upload creates dataset metadata and normalized email rows.
2. Experiment configuration becomes an immutable run configuration.
3. A run is queued and processed by bounded workers.
4. Each record emits a classification trace and measured timing/cost data.
5. Aggregators compute metrics only from measured records; projections are labeled separately.
6. The UI polls run status initially. The API contract will later support SSE without changing domain models.

