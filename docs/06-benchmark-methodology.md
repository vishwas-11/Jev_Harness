# Benchmark methodology

The research unit is a dataset/configuration/run tuple. A fair comparison requires identical records and enabled dimensions, equivalent task instructions and output schema, documented model and prompt configuration, explicit concurrency/batch/retry settings, the same measurement boundaries, repeated controlled runs where variance matters, and separate measured, estimated, and projected metrics.

Accuracy metrics are computed only when ground truth exists. Without ground truth, the UI reports agreement, confidence, latency, throughput, cost, and human-evaluation fields without fabricating accuracy.

Hybrid is evaluated as a routing policy: Jev first, then LLM only when the configured confidence threshold is not met. Fallback rate, final quality, latency, and cost are measured independently.

