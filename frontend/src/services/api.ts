export type ValidationIssue = {
  severity: string;
  code: string;
  message: string;
  row?: number | null;
};

export type ValidationReport = {
  valid: boolean;
  errors: ValidationIssue[];
  warnings: ValidationIssue[];
  record_count: number;
  columns: string[];
};

export type Dataset = {
  id: string;
  name: string;
  source_filename: string;
  source_format: string;
  total_records: number;
  columns: string[];
  subject_column: string;
  body_column: string;
  ground_truth_columns: Record<string, string>;
  file_size: number;
  status: string;
  created_at: string;
  updated_at: string;
};

export type Inspect = {
  source_filename: string;
  source_format: string;
  file_size: number;
  columns: string[];
  sample_records: Record<string, unknown>[];
  report: ValidationReport;
};

export type Preview = {
  dataset: Dataset;
  records: {
    id: string;
    external_id: string;
    subject: string;
    body: string;
    ground_truth: Record<string, unknown>;
    metadata: Record<string, unknown>;
  }[];
  page: number;
  page_size: number;
  total: number;
};

export type ChoiceDecision = {
  question_id: string;
  choice: string;
  confidence: number;
  probabilities: Record<string, number>;
};

export type BooleanDecision = {
  question_id: string;
  value: boolean;
  probability: number;
  confidence: number;
};

export type ScoreDecision = {
  question_id: string;
  score: number;
  max_score: number;
  confidence: number;
  legend: Record<number, string>;
  probabilities: Record<number, number>;
};

export type LatencyBreakdown = {
  state_prep_ms: number;
  jev_request_ms: number;
  normalization_ms: number;
  total_ms: number;
};

export type DecisionTrace = {
  request_id: string | null;
  model: string;
  provider: string;
  timestamp: string;
  latency: LatencyBreakdown;
  usage: {
    input_tokens: number | null;
    output_tokens: number | null;
  };
  raw_decisions: Record<string, unknown>;
};

export type ClassificationResult = {
  id: string;
  subject: string;
  body_snippet: string;
  intent: ChoiceDecision;
  department: ChoiceDecision;
  urgency: ChoiceDecision;
  sentiment: ChoiceDecision;
  spam: BooleanDecision;
  requires_human: BooleanDecision;
  priority: ScoreDecision;
  aggregate_confidence: number;
  latency: LatencyBreakdown;
  trace: DecisionTrace;
  is_mock: boolean;
};

export type BatchItem = {
  id?: string;
  subject: string;
  body: string;
};

export type BatchResponse = {
  results: ClassificationResult[];
  total_count: number;
  total_latency_ms: number;
  avg_latency_ms: number;
};

export type ProviderStatus = {
  configured: boolean;
  mode: string;
  provider: string;
  gateway_url: string;
  model: string;
};

export type ClassificationDefinition = {
  version: string;
  intent: { instructions: string; options: Record<string, string> };
  department: { instructions: string; options: Record<string, string> };
  urgency: { instructions: string; options: Record<string, string> };
  sentiment: { instructions: string; options: Record<string, string> };
  spam: { instructions: string; true_criteria: string; false_criteria: string };
  requires_human: { instructions: string; true_criteria: string; false_criteria: string };
  priority: { instructions: string; rubric: string[] };
};

const base = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${base}${path}`, init);
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail));
  }
  return res.status === 204 ? (undefined as T) : res.json();
}

export const datasetApi = {
  list: () => request<Dataset[]>("/datasets"),
  inspect: (file: File) => {
    const f = new FormData();
    f.append("file", file);
    return request<Inspect>("/datasets/inspect", { method: "POST", body: f });
  },
  create: (
    file: File,
    data: {
      name: string;
      subject_column: string;
      body_column: string;
      id_column: string;
      ground_truth_columns: Record<string, string>;
    }
  ) => {
    const f = new FormData();
    f.append("file", file);
    Object.entries(data).forEach(([k, v]) =>
      f.append(k, typeof v === "string" ? v : JSON.stringify(v))
    );
    return request<Dataset>("/datasets", { method: "POST", body: f });
  },
  preview: (id: string, page = 1) =>
    request<Preview>(`/datasets/${id}/preview?page=${page}&page_size=25`),
  validate: (id: string) =>
    request<ValidationReport>(`/datasets/${id}/validate`, { method: "POST" }),
  remove: (id: string) => request<void>(`/datasets/${id}`, { method: "DELETE" }),
};

export const classificationApi = {
  test: (subject: string, body: string, forceMock = false) =>
    request<ClassificationResult>("/classifications/test", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ subject, body, force_mock: forceMock }),
    }),
  testBatch: (records: BatchItem[], forceMock = false, maxConcurrency = 5) =>
    request<BatchResponse>("/classifications/test-batch", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ records, force_mock: forceMock, max_concurrency: maxConcurrency }),
    }),
  getSchema: () => request<ClassificationDefinition>("/classifications/schema"),
  getProviderStatus: () => request<ProviderStatus>("/classifications/provider-status"),
};
