# Jev Classification Architecture & Guide

## 1. What is Jev?

Jev is a specialized decision model developed by TypeSafe AI. Unlike traditional generative large language models (LLMs) whose core architecture is autoregressive token-by-token text generation, Jev is built specifically to evaluate input state against typed, discrete decision questions and return direct probability distributions and expected values.

Jev acts as a **System 1** decision engine: high-throughput, low-latency, and deterministic in structure, optimized for categorical choices, ordinal scoring, and binary thresholding.

---

## 2. Jev vs Generative LLM Architecture

| Dimension | Generative LLM (Traditional) | Jev (TypeSafe Decision Model) |
| :--- | :--- | :--- |
| **Primary Output** | Autoregressive text tokens | Direct mathematical probability distributions |
| **Output Structure** | Freeform text, JSON string, or grammar-constrained tokens | Strictly typed primitives: `Choice`, `Noul` (boolean), `Score` |
| **Parsing Overhead** | Requires JSON parsing, Pydantic validation, schema repair | Native typed response; zero text parsing required |
| **Hallucination Risk** | Model can generate invalid tokens, nonexistent enum values, or commentary | Structurally impossible to output values outside the question's criteria |
| **Multi-Question Latency** | Sequential token generation per character; token count dictates latency | Parallel evaluation across all questions against the state in one pass |
| **Confidence Signal** | Logprobs require proprietary extraction or token-level averaging | Native posterior probability distribution per categorical choice and rubric tier |
| **Cost Profile** | Input tokens + Output tokens (output tokens are 3-4x more expensive) | Low fixed decision unit cost; minimal output token overhead |

---

## 3. Vercel AI Gateway Integration

Jev is integrated into the system via **Vercel AI Gateway**.

- **Model Identifier**: `typesafe-ai/jev`
- **Gateway Base URL**: `https://ai-gateway.vercel.sh/typesafe`
- **Request Endpoint**: `POST https://ai-gateway.vercel.sh/typesafe/v1/systemone`
- **Authentication**: `Authorization: Bearer <AI_GATEWAY_API_KEY>`

### Why route through Vercel AI Gateway?
1. **Unified Credentialing**: A single `AI_GATEWAY_API_KEY` can manage Jev alongside traditional LLMs (Google Gemini, OpenAI, Anthropic).
2. **Centralized Telemetry & Observability**: Real-time logging of latency, request IDs, token usage, and error rates across all models in one control plane.
3. **Resilience & Rate Limiting**: Gateway-level retries, edge routing, and unified billing.

---

## 4. LangChain Integration (`langchain-typesafe`)

In Python, Jev is invoked using the official LangChain integration `langchain-typesafe` (`TypeSafeClassifier`).

```python
from langchain_typesafe import Choice, Noul, Score, TypeSafeClassifier

classifier = TypeSafeClassifier(
    model="typesafe-ai/jev",
    api_key=settings.ai_gateway_api_key,
    base_url="https://ai-gateway.vercel.sh/typesafe",
    timeout=30.0,
)

response = await classifier.ainvoke({
    "state": {"subject": email.subject, "body": email.body},
    "questions": {
        "intent": Choice(instructions="...", criteria={...}),
        "spam": Noul(instructions="...", criteria=NoulCriteria(...)),
        "priority": Score(instructions="...", criteria=[...]),
    }
})
```

`TypeSafeClassifier` is a standard LangChain `Runnable`, supporting sync (`invoke`), async (`ainvoke`), batching, and LangSmith tracing.

---

## 5. Typed Decision Primitives

### 5.1 Choice (Categorical Decisions)
Used when classifying an input into mutually exclusive categorical options.
- **Criteria**: A dictionary mapping each allowed label to its semantic boundary description:
  ```python
  criteria = {
      "billing_issue": "Invoices, payment failures, subscription renewals, or billing disputes.",
      "technical_issue": "Software bugs, API errors, system crashes, or downtime.",
      "other": "Inquiries that do not fit into predefined categories."
  }
  ```
- **Returns**: `ChoiceAnswer` containing:
  - `choice`: Selected category string with the highest probability.
  - `probabilities`: Dictionary of all allowed categories mapped to their posterior probabilities (summing to 1.0).
  - `confidence`: Highest probability value in the distribution.

### 5.2 Noul (Boolean Decisions)
Used for binary true/false judgments (e.g. spam detection, human review escalation).
- **Criteria**: `NoulCriteria(true="...", false="...")` clarifying what constitutes a positive vs negative outcome.
- **Returns**: `NoulAnswer` containing `noul: float` between `0.0` and `1.0`.
  - `noul` represents $P(\text{true})$.
  - Application logic resolves `value = (noul >= 0.5)`.
  - Decision confidence is computed as $\max(p, 1 - p)$.

### 5.3 Score (Ordinal Rubric Evaluation)
Used when the decision exists along an ordered continuum (e.g. priority triage, severity).
- **Criteria**: An ordered list of descriptions representing levels 0, 1, 2, ...
- **Returns**: `ScoreAnswer` containing:
  - `score`: The **expected value** across the rubric levels ($\sum i \cdot P(\text{level}_i)$).
  - `legend`: Mapping of integer index to rubric description.
  - `probabilities`: Probability distribution across each rubric tier.
  - `confidence`: Certainty in the score estimation.

---

## 6. Question Design & The 7 Dimensions

| Dimension | Primitive | Levels / Options | Semantic Purpose |
| :--- | :--- | :--- | :--- |
| **Intent** | `Choice` | 8 options: `billing_issue`, `technical_issue`, `account_issue`, `sales`, `refund`, `general_question`, `complaint`, `other` | Customer goal classification |
| **Department** | `Choice` | 7 targets: `billing`, `support`, `sales`, `account_management`, `security`, `operations`, `other` | Internal routing assignment |
| **Urgency** | `Choice` | 4 tiers: `low`, `medium`, `high`, `critical` | Timeframe sensitivity |
| **Sentiment** | `Choice` | 5 tones: `positive`, `neutral`, `frustrated`, `angry`, `negative` | Customer affective tone |
| **Spam** | `Noul` | Boolean ($P(\text{spam})$) | Filtering automated noise |
| **Human Review** | `Noul` | Boolean ($P(\text{review})$) | Discernment & safety threshold |
| **Priority** | `Score` | 5 tiers: `0: P5` to `4: P1` | Operational queue ordering |

---

## 7. Multi-Question Evaluation (Single Request)

A critical architectural capability of Jev is multi-question batching against shared state in a single HTTP request:

```text
                  Incoming Email
                        │
                        ▼
               Shared State Object
            { subject: "...", body: "..." }
                        │
                        ▼
             Single POST /v1/systemone
                        │
   ┌─────────┬──────────┼──────────┬──────────┬─────────┐
   ▼         ▼          ▼          ▼          ▼         ▼
Intent   Department  Urgency   Sentiment     Spam    Priority
(Choice)  (Choice)   (Choice)   (Choice)    (Noul)   (Score)
```

### Why this matters:
1. **Network Overhead**: 1 HTTP round-trip (~40ms) instead of 7 sequential round-trips (~300ms).
2. **Cost Efficiency**: Shared context is processed once; state token encoding is not repeated 7 times.
3. **Internal Consistency**: All questions evaluate the exact same model representation of the state.

---

## 8. Confidence vs Probability vs Accuracy

In AI Engineering, these three concepts must never be conflated:

1. **Probability**: The mathematical posterior distribution assigned by the model over discrete labels:
   $$P(\text{intent} = \text{refund} \mid \text{state}) = 0.94$$
2. **Confidence**: The model's internal assessment of certainty, typically taken as the maximum class probability or distance from threshold.
3. **Accuracy**: Empirical agreement between the model's decision and verified ground-truth human annotations across a test set:
   $$\text{Accuracy} = \frac{\text{Correct Predictions}}{\text{Total Predictions}}$$

> **Important**: A model can be 99% confident while being 0% accurate if the question criteria are poorly specified, if the input is adversarial, or if out-of-distribution data is presented. In Phase 5, we test **model calibration** (Expected Calibration Error).

---

## 9. Testing & Safe Isolation

1. **Zero-Credential Testing**: The entire test suite (`pytest`) runs without requiring live API keys.
2. **Mock Adapter**: `MockJevClassifier` provides deterministic responses, realistic latencies, and valid probability distributions for local testing.
3. **Pydantic Isolation**: The backend normalizes all raw provider responses into `ClassificationResult`, isolating the rest of FastAPI and the frontend from provider-specific SDK changes.
