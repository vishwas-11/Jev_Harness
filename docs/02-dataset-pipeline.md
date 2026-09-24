# JevScale dataset pipeline

Phase 2 turns external files into stable experiment inputs:

```text
Upload -> Parse -> Normalize -> Validate -> Persist -> Preview -> Experiment selection
```

## Parse

CSV, JSONL, and Parquet have format-specific readers, but they return the same `ParsedDataset` shape: format, column names, and a list of row dictionaries. Parser errors are reported before persistence.

## Normalize

The selected subject/body columns become a `DatasetRecord` with `external_id`, `subject`, `body`, `ground_truth`, and `metadata`. Ground truth is a dictionary because different datasets use different label names.

## Validate

Missing required mappings, empty datasets, malformed JSONL, unsupported formats, missing ground-truth mappings, and duplicate IDs are errors. Empty subjects and bodies are warnings so data quality is visible without rejecting every imperfect dataset.

## Persist

`Dataset` stores source metadata and column mappings. `Email` stores normalized records linked by `dataset_id`. SQLAlchemy uses PostgreSQL/Supabase when `SUPABASE_DB_URL` is configured and SQLite locally otherwise. Alembic owns the permanent schema migration.

## Preview

The API returns a bounded page of normalized records. The browser never receives the entire dataset, which matters for 100K and 1M record sources.

## Scaling notes

- 1K records: synchronous parsing and inserts are comfortable.
- 10K records: batch insertion remains reasonable, but request time and memory should be monitored.
- 100K records: move ingestion to a background job and use streaming/chunked parsing.
- 1M records: use object storage, COPY/bulk-load strategies, resumable ingestion, and asynchronous progress reporting.

Those larger-scale mechanisms are deliberately not introduced in Phase 2.
