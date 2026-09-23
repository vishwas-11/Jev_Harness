# Why Jev in this benchmark

Jev is a typed decision model, not a prose-generating LLM. Its useful comparison point is high-volume, closed-set structured decision work where the application needs choices, scores, or boolean probabilities rather than a narrative answer.

The benchmark must test the claim, not assume it. It therefore holds the dataset, task definition, concurrency conditions, and measurement boundaries constant. Jev, LLM, and Hybrid runs are reported as measured, estimated, or projected values with those labels preserved in the UI.

The current LangChain integration boundary is `langchain-typesafe` and exposes `TypeSafeClassifier`, `Choice`, `Score`, and `Noul`. This remains an experimental dependency, so it will be pinned and covered by adapter tests before live use.

