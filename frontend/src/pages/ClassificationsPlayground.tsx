import React, { useEffect, useState } from "react";
import {
  ArrowRight,
  ArrowsClockwise,
  ChartBar,
  CheckCircle,
  Clock,
  Cpu,
  Database,
  FileCode,
  Flask,
  Info,
  Lightning,
  Play,
  Pulse,
  ShieldCheck,
  Tag,
  Warning,
} from "@phosphor-icons/react";
import {
  BatchResponse,
  classificationApi,
  ClassificationDefinition,
  ClassificationResult,
  ProviderStatus,
} from "../services/api";

const PRESETS = [
  {
    label: "Refund Request",
    subject: "Refund still hasn't arrived for double charge",
    body: "I was charged twice on invoice #9401 for my subscription five days ago. Support promised a refund within 48 hours but I still have not received it. Please fix this and return my funds immediately.",
  },
  {
    label: "Critical Outage",
    subject: "Production API returning 500 errors across all endpoints",
    body: "Our payment checkout pipeline is completely down because your API is throwing 500 Internal Server Error on every tokenization call. This is blocking all our end-user transactions. We need an urgent fix ASAP.",
  },
  {
    label: "Account Lockout",
    subject: "Cannot access admin portal - 2FA code invalid",
    body: "My authenticator app codes are being rejected on login and now my account shows locked due to too many attempts. Please reset my 2FA authentication so I can log back in.",
  },
  {
    label: "Sales Demo",
    subject: "Enterprise licensing quote for 500 seats",
    body: "We are evaluating your platform for our global customer support team of 500 agents. Could you schedule a product demo this Thursday and send over enterprise tier pricing?",
  },
  {
    label: "Spam Blast",
    subject: "GUARANTEED 10X LEADS IN 24 HOURS!!!",
    body: "Dear CEO, buy our verified email lead list with 50,000 corporate decision makers! Limited time 90% discount. Click here to claim your free leads now: http://spam-example.biz",
  },
  {
    label: "Angry Escalation",
    subject: "Unacceptable downtime - speaking with our legal counsel",
    body: "This is the third service disruption this month. Your team has breached our contractual SLA. If this is not resolved today with full service credits, we will terminate the agreement and take formal legal action.",
  },
];

export default function ClassificationsPlayground() {
  const [subject, setSubject] = useState(PRESETS[0].subject);
  const [body, setBody] = useState(PRESETS[0].body);
  const [forceMock, setForceMock] = useState(false);
  const [loading, setLoading] = useState(false);
  const [batchLoading, setBatchLoading] = useState(false);
  const [result, setResult] = useState<ClassificationResult | null>(null);
  const [batchResult, setBatchResult] = useState<BatchResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [providerStatus, setProviderStatus] = useState<ProviderStatus | null>(null);
  const [schema, setSchema] = useState<ClassificationDefinition | null>(null);
  const [showTrace, setShowTrace] = useState(false);
  const [activeTab, setActiveTab] = useState<"single" | "batch" | "schema">("single");

  useEffect(() => {
    classificationApi.getProviderStatus().then(setProviderStatus).catch(() => null);
    classificationApi.getSchema().then(setSchema).catch(() => null);
  }, []);

  const handleClassify = async () => {
    if (!subject.trim() && !body.trim()) {
      setError("Please provide a subject or body to classify.");
      return;
    }
    setError(null);
    setLoading(true);
    try {
      const res = await classificationApi.test(subject, body, forceMock);
      setResult(res);
      setActiveTab("single");
    } catch (err: any) {
      setError(err?.message || "Failed to classify email.");
    } finally {
      setLoading(false);
    }
  };

  const handleBatchTest = async () => {
    setError(null);
    setBatchLoading(true);
    try {
      const records = PRESETS.slice(0, 4).map((p, i) => ({
        id: `sample-${i + 1}`,
        subject: p.subject,
        body: p.body,
      }));
      const res = await classificationApi.testBatch(records, forceMock, 4);
      setBatchResult(res);
      setActiveTab("batch");
    } catch (err: any) {
      setError(err?.message || "Failed to run batch test.");
    } finally {
      setBatchLoading(false);
    }
  };

  const applyPreset = (preset: (typeof PRESETS)[0]) => {
    setSubject(preset.subject);
    setBody(preset.body);
    setError(null);
  };

  return (
    <div className="page pb-12">
      <header className="topbar">
        <div>
          <label>Control plane / decision engine</label>
          <h1>Jev Classification Playground</h1>
          <p>
            Evaluate typed decision primitives (Choice, Noul, Score) via Vercel AI Gateway against customer support emails.
          </p>
        </div>
        <div className="flex items-center gap-3">
          {providerStatus && (
            <div className={`status-pill ${providerStatus.configured ? "live" : "sandbox"}`}>
              <i />
              <span>
                {providerStatus.configured
                  ? `Live Gateway: ${providerStatus.model}`
                  : "Development Sandbox (Mock Engine)"}
              </span>
            </div>
          )}
        </div>
      </header>

      {/* Tabs */}
      <div className="flex gap-4 border-b border-[#203031] pb-3 mb-6">
        <button
          onClick={() => setActiveTab("single")}
          className={`tab-btn ${activeTab === "single" ? "active" : ""}`}
        >
          <Cpu size={16} /> Single Email Playground
        </button>
        <button
          onClick={() => setActiveTab("batch")}
          className={`tab-btn ${activeTab === "batch" ? "active" : ""}`}
        >
          <Database size={16} /> Batch Evaluation
        </button>
        <button
          onClick={() => setActiveTab("schema")}
          className={`tab-btn ${activeTab === "schema" ? "active" : ""}`}
        >
          <Tag size={16} /> 7-Dimension Taxonomy Schema
        </button>
      </div>

      {error && (
        <div className="error-banner">
          <Warning size={18} />
          <span>{error}</span>
          <button onClick={() => setError(null)}>✕</button>
        </div>
      )}

      {/* Educational Mental Model Banner */}
      <section className="mental-model-strip">
        <div className="flow-step">
          <span className="step-num">1</span>
          <div>
            <strong>Input State</strong>
            <small>Subject & Body JSON</small>
          </div>
        </div>
        <ArrowRight size={14} className="arrow" />
        <div className="flow-step">
          <span className="step-num">2</span>
          <div>
            <strong>7 Typed Questions</strong>
            <small>Choice, Noul, Score</small>
          </div>
        </div>
        <ArrowRight size={14} className="arrow" />
        <div className="flow-step highlight">
          <span className="step-num">3</span>
          <div>
            <strong>Vercel AI Gateway</strong>
            <small>typesafe-ai/jev</small>
          </div>
        </div>
        <ArrowRight size={14} className="arrow" />
        <div className="flow-step">
          <span className="step-num">4</span>
          <div>
            <strong>Direct Probabilities</strong>
            <small>No token generation / regex</small>
          </div>
        </div>
        <ArrowRight size={14} className="arrow" />
        <div className="flow-step">
          <span className="step-num">5</span>
          <div>
            <strong>ClassificationResult</strong>
            <small>Normalized application state</small>
          </div>
        </div>
      </section>

      {activeTab === "single" && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 mt-6">
          {/* Left Column: Input Form & Presets */}
          <div className="lg:col-span-5 space-y-4">
            <div className="panel p-5">
              <div className="flex items-center justify-between mb-3">
                <label className="text-xs uppercase tracking-wider text-[#6f8c89] font-bold">
                  Preset Scenarios
                </label>
                <small className="text-[#55716d]">Click to populate</small>
              </div>
              <div className="flex flex-wrap gap-2 mb-4">
                {PRESETS.map((p) => (
                  <button
                    key={p.label}
                    onClick={() => applyPreset(p)}
                    className="preset-chip"
                  >
                    {p.label}
                  </button>
                ))}
              </div>

              <div className="space-y-3">
                <div>
                  <label className="field-label">Subject</label>
                  <input
                    type="text"
                    value={subject}
                    onChange={(e) => setSubject(e.target.value)}
                    placeholder="e.g. Refund not received"
                    className="w-full bg-[#101d1e] text-[#dce7e6] border border-[#28403f] rounded-lg p-2.5 text-xs outline-none focus:border-[#79e8cf]"
                  />
                </div>

                <div>
                  <div className="flex justify-between items-center mb-1">
                    <label className="field-label">Email Body</label>
                    <span className="text-[10px] text-[#55716d]">
                      {body.length} characters ({body.trim().split(/\s+/).filter(Boolean).length} words)
                    </span>
                  </div>
                  <textarea
                    rows={7}
                    value={body}
                    onChange={(e) => setBody(e.target.value)}
                    placeholder="Paste email text here..."
                    className="w-full bg-[#101d1e] text-[#dce7e6] border border-[#28403f] rounded-lg p-2.5 text-xs outline-none focus:border-[#79e8cf] font-sans"
                  />
                </div>

                <div className="flex items-center justify-between pt-2">
                  <label className="flex items-center gap-2 cursor-pointer text-xs text-[#7e9995]">
                    <input
                      type="checkbox"
                      checked={forceMock}
                      onChange={(e) => setForceMock(e.target.checked)}
                      className="rounded bg-[#101d1e] border-[#28403f] text-[#79e8cf] focus:ring-0"
                    />
                    <span>Force local mock engine</span>
                  </label>
                </div>

                <div className="flex gap-3 pt-2">
                  <button
                    onClick={handleClassify}
                    disabled={loading}
                    className="primary-action-btn flex-1"
                  >
                    {loading ? (
                      <>
                        <Pulse className="animate-spin" size={16} /> Evaluating via Jev...
                      </>
                    ) : (
                      <>
                        <Lightning size={16} weight="fill" /> Classify with Jev
                      </>
                    )}
                  </button>
                  <button
                    onClick={handleBatchTest}
                    disabled={batchLoading}
                    className="secondary-btn"
                    title="Run small 4-email batch test"
                  >
                    {batchLoading ? <Pulse className="animate-spin" size={16} /> : <Play size={16} />} Batch test
                  </button>
                </div>
              </div>
            </div>

            {/* Educational Callout */}
            <div className="info-card">
              <div className="flex items-start gap-2.5">
                <Info size={18} className="text-[#79e8cf] mt-0.5 shrink-0" />
                <div className="text-xs text-[#8da6a2] space-y-1">
                  <strong className="text-[#e2f3ee] block">
                    Confidence vs Accuracy Calibration
                  </strong>
                  <p>
                    Confidence reflects the model's posterior probability/uncertainty signal; it is <em>not proof</em> that the classification matches human ground truth.
                  </p>
                  <p className="text-[11px] text-[#6b8581]">
                    In Phase 5, we measure whether confidence is calibrated across 10,000+ benchmark emails.
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Right Column: Typed Decisions & Telemetry */}
          <div className="lg:col-span-7 space-y-4">
            {result ? (
              <div className="space-y-4">
                {/* Summary Header with Latency & Engine Pill */}
                <div className="panel p-4 flex flex-wrap items-center justify-between gap-3 bg-[#0d1819]">
                  <div className="flex items-center gap-2.5">
                    <CheckCircle size={20} className="text-[#79e8cf]" weight="fill" />
                    <div>
                      <h3 className="text-sm font-bold text-[#e1f3ee]">
                        Multi-Question Evaluation Complete
                      </h3>
                      <span className="text-[11px] text-[#6a8783]">
                        7 typed dimensions evaluated in a single request
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-xs px-2.5 py-1 rounded bg-[#102724] text-[#80d8c5] font-mono border border-[#20403c]">
                      {result.latency.total_ms.toFixed(1)} ms total
                    </span>
                    <span
                      className={`text-xs px-2.5 py-1 rounded font-medium ${
                        result.is_mock
                          ? "bg-[#252014] text-[#e0b259] border border-[#483c1e]"
                          : "bg-[#0f2a24] text-[#79e8cf] border border-[#20473e]"
                      }`}
                    >
                      {result.is_mock ? "Mock Engine" : "Vercel AI Gateway"}
                    </span>
                  </div>
                </div>

                {/* Latency Breakdown Bar */}
                <div className="panel p-4 space-y-2">
                  <div className="flex justify-between text-xs text-[#7c9793]">
                    <span className="flex items-center gap-1.5 font-bold uppercase tracking-wider text-[10px]">
                      <Clock size={14} /> Latency Breakdown
                    </span>
                    <span className="font-mono text-[11px]">
                      Jev Network: {result.latency.jev_request_ms.toFixed(1)}ms | Prep:{" "}
                      {result.latency.state_prep_ms.toFixed(1)}ms | Norm:{" "}
                      {result.latency.normalization_ms.toFixed(1)}ms
                    </span>
                  </div>
                  <div className="latency-bar">
                    <div
                      className="bar-prep"
                      style={{
                        width: `${Math.max(
                          2,
                          (result.latency.state_prep_ms / result.latency.total_ms) * 100
                        )}%`,
                      }}
                      title={`State Prep: ${result.latency.state_prep_ms}ms`}
                    />
                    <div
                      className="bar-jev"
                      style={{
                        width: `${Math.max(
                          5,
                          (result.latency.jev_request_ms / result.latency.total_ms) * 100
                        )}%`,
                      }}
                      title={`Jev AI Gateway: ${result.latency.jev_request_ms}ms`}
                    />
                    <div
                      className="bar-norm"
                      style={{
                        width: `${Math.max(
                          2,
                          (result.latency.normalization_ms / result.latency.total_ms) * 100
                        )}%`,
                      }}
                      title={`Normalization: ${result.latency.normalization_ms}ms`}
                    />
                  </div>
                </div>

                {/* Categorical Dimensions (Choice Primitive) */}
                <div className="panel p-4 space-y-3">
                  <div className="flex items-center justify-between border-b border-[#1b2b2c] pb-2">
                    <div className="flex items-center gap-2">
                      <Tag size={16} className="text-[#79e8cf]" />
                      <h4 className="text-xs font-bold uppercase tracking-wider text-[#a0bbb6]">
                        Categorical Decisions (Choice Primitive)
                      </h4>
                    </div>
                    <span className="text-[10px] text-[#5b7571]">
                      Evaluated as normalized probability distributions
                    </span>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-1">
                    <ChoiceCard
                      title="Primary Intent"
                      choice={result.intent.choice}
                      confidence={result.intent.confidence}
                      probabilities={result.intent.probabilities}
                    />
                    <ChoiceCard
                      title="Department Routing"
                      choice={result.department.choice}
                      confidence={result.department.confidence}
                      probabilities={result.department.probabilities}
                    />
                    <ChoiceCard
                      title="Urgency Level"
                      choice={result.urgency.choice}
                      confidence={result.urgency.confidence}
                      probabilities={result.urgency.probabilities}
                      colorMap={{
                        critical: "text-red-400 bg-red-950/40 border-red-800/50",
                        high: "text-amber-400 bg-amber-950/40 border-amber-800/50",
                        medium: "text-sky-400 bg-sky-950/40 border-sky-800/50",
                        low: "text-slate-400 bg-slate-900 border-slate-700",
                      }}
                    />
                    <ChoiceCard
                      title="Customer Sentiment"
                      choice={result.sentiment.choice}
                      confidence={result.sentiment.confidence}
                      probabilities={result.sentiment.probabilities}
                      colorMap={{
                        angry: "text-red-400 bg-red-950/40 border-red-800/50",
                        frustrated: "text-amber-400 bg-amber-950/40 border-amber-800/50",
                        positive: "text-emerald-400 bg-emerald-950/40 border-emerald-800/50",
                        neutral: "text-slate-400 bg-slate-900 border-slate-700",
                        negative: "text-orange-400 bg-orange-950/40 border-orange-800/50",
                      }}
                    />
                  </div>
                </div>

                {/* Binary & Ordinal Dimensions (Noul & Score Primitives) */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  {/* Spam Noul */}
                  <BooleanCard
                    title="Spam Detection"
                    primitive="Noul"
                    value={result.spam.value}
                    probability={result.spam.probability}
                    confidence={result.spam.confidence}
                    trueLabel="Spam / Noise"
                    falseLabel="Legitimate"
                    dangerIfTrue={true}
                  />

                  {/* Human Review Noul */}
                  <BooleanCard
                    title="Human Review"
                    primitive="Noul"
                    value={result.requires_human.value}
                    probability={result.requires_human.probability}
                    confidence={result.requires_human.confidence}
                    trueLabel="Escalate to Human"
                    falseLabel="Automate"
                    dangerIfTrue={true}
                  />

                  {/* Priority Score */}
                  <ScoreCard priority={result.priority} />
                </div>

                {/* Trace Inspector Toggle */}
                <div className="panel p-3 bg-[#0c1617]">
                  <button
                    onClick={() => setShowTrace(!showTrace)}
                    className="flex items-center justify-between w-full text-xs text-[#7e9c97] hover:text-[#b0d8d0]"
                  >
                    <span className="flex items-center gap-2">
                      <FileCode size={15} />
                      <strong>Decision Trace & Telemetry</strong>
                      <span className="text-[10px] text-[#55716d]">
                        ({result.trace.request_id || "mock"})
                      </span>
                    </span>
                    <span>{showTrace ? "Hide ▲" : "Inspect ▼"}</span>
                  </button>

                  {showTrace && (
                    <div className="mt-3 pt-3 border-t border-[#1b2b2c] space-y-2">
                      <div className="grid grid-cols-3 gap-2 text-[11px] text-[#7c9a95] font-mono">
                        <div>
                          <span className="text-[#55716d] block">Model</span>
                          <strong className="text-[#d8ebe6]">{result.trace.model}</strong>
                        </div>
                        <div>
                          <span className="text-[#55716d] block">Tokens (In / Out)</span>
                          <strong className="text-[#d8ebe6]">
                            {result.trace.usage.input_tokens ?? "N/A"} in /{" "}
                            {result.trace.usage.output_tokens ?? "N/A"} out
                          </strong>
                        </div>
                        <div>
                          <span className="text-[#55716d] block">Mean Confidence</span>
                          <strong className="text-[#79e8cf]">
                            {(result.aggregate_confidence * 100).toFixed(1)}%
                          </strong>
                        </div>
                      </div>
                      <pre className="bg-[#081112] text-[#86a6a1] p-3 rounded text-[10px] overflow-auto max-h-48 border border-[#192728]">
                        {JSON.stringify(result.trace, null, 2)}
                      </pre>
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div className="empty p-12 text-center border border-[#1c2c2d] rounded-xl bg-[#0d1819]">
                <div className="mx-auto mb-3 w-12 h-12 rounded-full bg-[#102523] flex items-center justify-center text-[#79e8cf]">
                  <Flask size={24} />
                </div>
                <h3 className="text-sm font-bold text-[#d6ede7] mb-1">
                  Ready to evaluate decision primitives
                </h3>
                <p className="text-xs text-[#6e8a86] max-w-sm mx-auto mb-4">
                  Select a preset scenario on the left or paste customer email text, then click{" "}
                  <strong>Classify with Jev</strong>.
                </p>
                <div className="inline-flex gap-2">
                  <button onClick={handleClassify} className="primary-action-btn text-xs">
                    Run first test
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Batch Tab */}
      {activeTab === "batch" && (
        <div className="space-y-4 mt-6">
          <div className="panel p-4 flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-[#e1f3ee]">Small Batch Playground</h3>
              <p className="text-xs text-[#688581]">
                Demonstrates bounded-concurrency multi-question evaluation across multiple incoming support records.
              </p>
            </div>
            <button
              onClick={handleBatchTest}
              disabled={batchLoading}
              className="primary-action-btn text-xs"
            >
              {batchLoading ? (
                <>
                  <Pulse className="animate-spin" size={16} /> Evaluating batch...
                </>
              ) : (
                <>
                  <ArrowsClockwise size={16} /> Run 4-Email Test Batch
                </>
              )}
            </button>
          </div>

          {batchResult && (
            <div className="panel p-4 space-y-4">
              <div className="flex items-center justify-between text-xs text-[#7c9793] border-b border-[#1b2b2c] pb-3">
                <span className="font-bold text-[#e1f3ee]">
                  Processed {batchResult.total_count} records
                </span>
                <span className="font-mono">
                  Total Latency: {batchResult.total_latency_ms.toFixed(1)} ms | Average:{" "}
                  {batchResult.avg_latency_ms.toFixed(1)} ms/email
                </span>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs text-[#a0b6b2]">
                  <thead>
                    <tr className="border-b border-[#1f3132] text-[10px] uppercase tracking-wider text-[#5f7e7a]">
                      <th className="py-2 px-3">Subject</th>
                      <th className="py-2 px-3">Intent (Choice)</th>
                      <th className="py-2 px-3">Dept (Choice)</th>
                      <th className="py-2 px-3">Urgency</th>
                      <th className="py-2 px-3">Priority (Score)</th>
                      <th className="py-2 px-3">Spam</th>
                      <th className="py-2 px-3">Human</th>
                      <th className="py-2 px-3">Latency</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#172728]">
                    {batchResult.results.map((r) => (
                      <tr key={r.id} className="hover:bg-[#102021]">
                        <td className="py-2.5 px-3 font-medium text-[#dcebe7] max-w-[200px] truncate">
                          {r.subject}
                        </td>
                        <td className="py-2.5 px-3">
                          <span className="px-2 py-0.5 rounded bg-[#102724] text-[#80d8c5] font-mono text-[11px]">
                            {r.intent.choice}
                          </span>
                        </td>
                        <td className="py-2.5 px-3">{r.department.choice}</td>
                        <td className="py-2.5 px-3">
                          <span
                            className={`px-1.5 py-0.5 rounded text-[10px] ${
                              r.urgency.choice === "critical"
                                ? "bg-red-950 text-red-300"
                                : r.urgency.choice === "high"
                                ? "bg-amber-950 text-amber-300"
                                : "bg-[#112323] text-[#7ca29c]"
                            }`}
                          >
                            {r.urgency.choice}
                          </span>
                        </td>
                        <td className="py-2.5 px-3 font-mono font-bold text-[#79e8cf]">
                          {r.priority.score.toFixed(1)} / 4
                        </td>
                        <td className="py-2.5 px-3">
                          {r.spam.value ? (
                            <span className="text-red-400 font-bold">Yes</span>
                          ) : (
                            <span className="text-[#55716d]">No</span>
                          )}
                        </td>
                        <td className="py-2.5 px-3">
                          {r.requires_human.value ? (
                            <span className="text-amber-400 font-bold">Yes</span>
                          ) : (
                            <span className="text-[#55716d]">No</span>
                          )}
                        </td>
                        <td className="py-2.5 px-3 font-mono text-[#688581]">
                          {r.latency.total_ms.toFixed(0)}ms
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Schema Tab */}
      {activeTab === "schema" && schema && (
        <div className="panel p-5 space-y-5 mt-6">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <ShieldCheck size={20} className="text-[#79e8cf]" />
              <h3 className="text-sm font-bold text-[#e1f3ee]">
                Active 7-Dimension Taxonomy (v{schema.version})
              </h3>
            </div>
            <p className="text-xs text-[#6e8a86]">
              This taxonomy specification is provider-agnostic. The exact same questions, criteria, and rubrics will be provided to the future LLM baseline in Phase 4 for benchmark fairness.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-3.5 rounded-lg bg-[#0e1b1c] border border-[#1d2f30] space-y-2">
              <strong className="text-xs text-[#79e8cf] block uppercase tracking-wider">
                1. Intent (Choice - 8 categories)
              </strong>
              <small className="text-[#64807c] block italic">{schema.intent.instructions}</small>
              <ul className="text-xs space-y-1 text-[#8ba6a2] pt-1">
                {Object.entries(schema.intent.options).map(([k, desc]) => (
                  <li key={k} className="flex gap-2">
                    <span className="font-mono text-[#cde2de]">{k}:</span>
                    <span className="text-[#6c8784]">{desc}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div className="p-3.5 rounded-lg bg-[#0e1b1c] border border-[#1d2f30] space-y-2">
              <strong className="text-xs text-[#79e8cf] block uppercase tracking-wider">
                2. Department (Choice - 7 routing targets)
              </strong>
              <small className="text-[#64807c] block italic">{schema.department.instructions}</small>
              <ul className="text-xs space-y-1 text-[#8ba6a2] pt-1">
                {Object.entries(schema.department.options).map(([k, desc]) => (
                  <li key={k} className="flex gap-2">
                    <span className="font-mono text-[#cde2de]">{k}:</span>
                    <span className="text-[#6c8784]">{desc}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div className="p-3.5 rounded-lg bg-[#0e1b1c] border border-[#1d2f30] space-y-2">
              <strong className="text-xs text-[#79e8cf] block uppercase tracking-wider">
                3 & 4. Urgency & Sentiment (Choice)
              </strong>
              <div className="text-xs space-y-2 text-[#8ba6a2]">
                <div>
                  <span className="font-bold text-[#cde2de]">Urgency:</span>{" "}
                  {Object.keys(schema.urgency.options).join(", ")}
                </div>
                <div>
                  <span className="font-bold text-[#cde2de]">Sentiment:</span>{" "}
                  {Object.keys(schema.sentiment.options).join(", ")}
                </div>
              </div>
            </div>

            <div className="p-3.5 rounded-lg bg-[#0e1b1c] border border-[#1d2f30] space-y-2">
              <strong className="text-xs text-[#79e8cf] block uppercase tracking-wider">
                5, 6 & 7. Noul & Score Rubric
              </strong>
              <div className="text-xs space-y-2 text-[#8ba6a2]">
                <div>
                  <span className="font-bold text-[#cde2de]">Spam (Noul):</span> Evaluates P(true) for unsolicited spam noise.
                </div>
                <div>
                  <span className="font-bold text-[#cde2de]">Human Review (Noul):</span> Evaluates P(true) for operational escalation.
                </div>
                <div>
                  <span className="font-bold text-[#cde2de]">Priority (Score):</span> 5-tier rubric from P5 (trivial) to P1 (critical).
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function ChoiceCard({
  title,
  choice,
  confidence,
  probabilities,
  colorMap,
}: {
  title: string;
  choice: string;
  confidence: number;
  probabilities: Record<string, number>;
  colorMap?: Record<string, string>;
}) {
  const sorted = Object.entries(probabilities)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 3);

  const customColor = colorMap ? colorMap[choice] : "text-[#79e8cf] bg-[#102724] border-[#224842]";

  return (
    <div className="decision-card">
      <div className="flex items-center justify-between mb-2">
        <span className="text-[11px] font-bold text-[#6f8d89] uppercase tracking-wider">
          {title}
        </span>
        <span className="text-[11px] font-mono text-[#79e8cf]" title="Model confidence in selected label">
          {(confidence * 100).toFixed(0)}% conf
        </span>
      </div>

      <div className="flex items-center gap-2 mb-3">
        <span className={`px-2.5 py-1 rounded text-xs font-mono font-bold border ${customColor}`}>
          {choice}
        </span>
      </div>

      {/* Mini Probability Distribution */}
      <div className="space-y-1.5 pt-1 border-t border-[#182728]">
        {sorted.map(([k, p]) => (
          <div key={k} className="flex items-center gap-2 text-[10px]">
            <span className="w-20 truncate text-[#66827f] font-mono">{k}</span>
            <div className="flex-1 bg-[#101c1d] rounded-full h-1.5 overflow-hidden">
              <div
                className="bg-[#79e8cf] h-full rounded-full opacity-70"
                style={{ width: `${Math.min(100, Math.round(p * 100))}%` }}
              />
            </div>
            <span className="font-mono text-[#57726e] w-8 text-right">
              {(p * 100).toFixed(0)}%
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

function BooleanCard({
  title,
  primitive,
  value,
  probability,
  confidence,
  trueLabel,
  falseLabel,
  dangerIfTrue,
}: {
  title: string;
  primitive: string;
  value: boolean;
  probability: number;
  confidence: number;
  trueLabel: string;
  falseLabel: string;
  dangerIfTrue?: boolean;
}) {
  const isDanger = value && dangerIfTrue;

  return (
    <div className="decision-card">
      <div className="flex items-center justify-between mb-2">
        <span className="text-[11px] font-bold text-[#6f8d89] uppercase tracking-wider">
          {title}
        </span>
        <span className="text-[9px] px-1.5 py-0.5 rounded bg-[#102021] text-[#5e7c78] font-mono">
          {primitive}
        </span>
      </div>

      <div className="my-2">
        <span
          className={`px-3 py-1 rounded text-xs font-bold inline-flex items-center gap-1.5 border ${
            value
              ? isDanger
                ? "bg-amber-950/60 text-amber-300 border-amber-800/60"
                : "bg-emerald-950/60 text-emerald-300 border-emerald-800/60"
              : "bg-[#112324] text-[#86a6a1] border-[#22393a]"
          }`}
        >
          {value ? trueLabel : falseLabel}
        </span>
      </div>

      <div className="space-y-1 text-[11px] text-[#6b8581] pt-1 border-t border-[#182728]">
        <div className="flex justify-between">
          <span>P(True):</span>
          <span className="font-mono text-[#b3ccc7]">{(probability * 100).toFixed(1)}%</span>
        </div>
        <div className="flex justify-between">
          <span>Confidence:</span>
          <span className="font-mono text-[#79e8cf]">{(confidence * 100).toFixed(0)}%</span>
        </div>
      </div>
    </div>
  );
}

function ScoreCard({ priority }: { priority: ClassificationResult["priority"] }) {
  const percentage = (priority.score / priority.max_score) * 100;
  const rubricText = priority.legend[Math.round(priority.score)] || "Priority Level";

  return (
    <div className="decision-card">
      <div className="flex items-center justify-between mb-2">
        <span className="text-[11px] font-bold text-[#6f8d89] uppercase tracking-wider">
          Priority Rating
        </span>
        <span className="text-[9px] px-1.5 py-0.5 rounded bg-[#102021] text-[#5e7c78] font-mono">
          Score
        </span>
      </div>

      <div className="my-2 flex items-baseline gap-2">
        <strong className="text-xl font-mono text-[#79e8cf]">
          {priority.score.toFixed(2)}
        </strong>
        <span className="text-xs text-[#55716d]">/ {priority.max_score.toFixed(0)}</span>
      </div>

      {/* Progress Gauge */}
      <div className="bg-[#101c1d] rounded-full h-2 overflow-hidden mb-2">
        <div
          className="bg-gradient-to-r from-sky-500 via-amber-500 to-red-500 h-full rounded-full"
          style={{ width: `${Math.min(100, Math.max(5, percentage))}%` }}
        />
      </div>

      <p className="text-[10px] text-[#7a9591] line-clamp-2 italic pt-1 border-t border-[#182728]">
        {rubricText}
      </p>
    </div>
  );
}
