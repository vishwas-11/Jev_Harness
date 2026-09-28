import React, { useEffect, useState } from "react";
import {
  ArrowRight,
  ArrowsClockwise,
  CheckCircle,
  Clock,
  Cpu,
  Database,
  Envelope,
  EnvelopeOpen,
  FileCode,
  Info,
  Lightning,
  Lock,
  Play,
  Pulse,
  ShieldCheck,
  SignOut,
  Sparkle,
  Tag,
  Warning,
} from "@phosphor-icons/react";
import {
  BatchResponse,
  classificationApi,
  ClassificationDefinition,
  ClassificationResult,
  gmailApi,
  NormalizedGmailMessage,
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
  const [strategy, setStrategy] = useState<"jev" | "llm">("jev");
  const [loading, setLoading] = useState(false);
  const [batchLoading, setBatchLoading] = useState(false);
  const [result, setResult] = useState<ClassificationResult | null>(null);
  const [batchResult, setBatchResult] = useState<BatchResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [providerStatus, setProviderStatus] = useState<ProviderStatus | null>(null);
  const [schema, setSchema] = useState<ClassificationDefinition | null>(null);
  const [showTrace, setShowTrace] = useState(false);
  const [activeTab, setActiveTab] = useState<"single" | "gmail" | "batch" | "schema">("single");

  // Gmail Ingestion State
  const [gmailConnected, setGmailConnected] = useState(false);
  const [gmailEmail, setGmailEmail] = useState<string | null>(null);
  const [gmailQuery, setGmailQuery] = useState("label:INBOX");
  const [gmailMaxResults, setGmailMaxResults] = useState(10);
  const [gmailLoading, setGmailLoading] = useState(false);
  const [gmailMessages, setGmailMessages] = useState<NormalizedGmailMessage[]>([]);
  const [gmailNotice, setGmailNotice] = useState<string | null>(null);

  useEffect(() => {
    fetchProviderStatus();
    classificationApi.getSchema().then(setSchema).catch(() => null);
    checkGmailStatus();
  }, []);

  const fetchProviderStatus = () => {
    classificationApi.getProviderStatus().then(setProviderStatus).catch(() => null);
  };

  const checkGmailStatus = async () => {
    try {
      const st = await gmailApi.getStatus();
      setGmailConnected(st.connected);
      setGmailEmail(st.email);
    } catch {
      setGmailConnected(false);
    }
  };

  const handleConnectGmail = async () => {
    try {
      setError(null);
      const res = await gmailApi.getAuthUrl();
      if (res.auth_url) {
        window.location.href = res.auth_url;
      }
    } catch (err: any) {
      setError(err?.message || "Failed to initialize Gmail OAuth flow.");
    }
  };

  const handleDisconnectGmail = async () => {
    try {
      await gmailApi.disconnect();
      setGmailConnected(false);
      setGmailEmail(null);
      setGmailMessages([]);
      setGmailNotice("Disconnected Gmail session.");
    } catch (err: any) {
      setError(err?.message || "Failed to disconnect Gmail.");
    }
  };

  const handleFetchGmail = async () => {
    setGmailLoading(true);
    setError(null);
    setGmailNotice(null);
    try {
      const msgs = await gmailApi.fetchMessages(gmailQuery, gmailMaxResults);
      setGmailMessages(msgs);
      if (msgs.length === 0) {
        setGmailNotice(`No messages found matching query "${gmailQuery}".`);
      }
    } catch (err: any) {
      setError(err?.message || "Failed to fetch Gmail messages.");
    } finally {
      setGmailLoading(false);
    }
  };

  const handleSelectGmailMessage = (msg: NormalizedGmailMessage, chosenStrategy: "jev" | "llm") => {
    setSubject(msg.subject);
    setBody(msg.body);
    setStrategy(chosenStrategy);
    setActiveTab("single");
    // Classify immediately
    runSingleClassification(msg.subject, msg.body, chosenStrategy);
  };

  const runSingleClassification = async (sub: string, b: string, strat: "jev" | "llm") => {
    if (!sub.trim() && !b.trim()) {
      setError("Please provide a subject or body to classify.");
      return;
    }
    setError(null);
    setLoading(true);
    try {
      const res = await classificationApi.test(sub, b, strat);
      setResult(res);
    } catch (err: any) {
      setError(err?.message || `Failed to classify email using ${strat.toUpperCase()}.`);
    } finally {
      setLoading(false);
    }
  };

  const handleClassify = () => {
    runSingleClassification(subject, body, strategy);
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
      const res = await classificationApi.testBatch(records, strategy, 4);
      setBatchResult(res);
      setActiveTab("batch");
    } catch (err: any) {
      setError(err?.message || `Failed to run batch test using ${strategy.toUpperCase()}.`);
    } finally {
      setBatchLoading(false);
    }
  };

  const applyPreset = (preset: (typeof PRESETS)[0]) => {
    setSubject(preset.subject);
    setBody(preset.body);
    setError(null);
  };

  const isCurrentStrategyConfigured =
    strategy === "jev"
      ? providerStatus?.jev_configured
      : providerStatus?.llm_configured;

  return (
    <div className="page pb-12">
      <header className="topbar">
        <div>
          <label>Control plane / decision engine</label>
          <h1>JevScale Decision & Benchmark Playground</h1>
          <p>
            Compare high-speed Jev typed decisions against OpenAI LLM structured outputs with personal Gmail data.
          </p>
        </div>
        <div className="flex items-center gap-2">
          {providerStatus && (
            <div className="flex gap-2">
              <div
                className={`status-pill ${providerStatus.jev_configured ? "live" : "sandbox"}`}
                title={providerStatus.jev_configured ? "Vercel AI Gateway Active" : "Key missing: AI_GATEWAY_API_KEY"}
              >
                <i />
                <span>Jev: {providerStatus.jev_configured ? providerStatus.jev_model : "Not Configured"}</span>
              </div>
              <div
                className={`status-pill ${providerStatus.llm_configured ? "live" : "sandbox"}`}
                title={providerStatus.llm_configured ? "OpenAI Baseline Active" : "Key missing: OPENAI_API_KEY"}
              >
                <i />
                <span>LLM: {providerStatus.llm_configured ? providerStatus.llm_model : "Not Configured"}</span>
              </div>
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
          onClick={() => setActiveTab("gmail")}
          className={`tab-btn ${activeTab === "gmail" ? "active" : ""}`}
        >
          <Envelope size={16} /> Personal Gmail Ingestion
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

      {/* Missing Credential Loud Warning Banner */}
      {!isCurrentStrategyConfigured && providerStatus && (
        <div className="p-4 rounded-xl bg-amber-950/40 border border-amber-600/50 text-amber-200 flex items-start gap-3 mb-6">
          <Warning size={22} className="text-amber-400 shrink-0 mt-0.5" />
          <div className="text-xs space-y-1">
            <strong className="text-amber-100 block text-sm">
              {strategy === "jev" ? "Jev API Key Not Configured" : "OpenAI API Key Not Configured"}
            </strong>
            <p>
              Runtime mock fallback is strictly disabled in Phase 4. To run live classifications with{" "}
              <strong>{strategy === "jev" ? "Jev" : "LLM"}</strong>, add{" "}
              <code className="bg-amber-900/60 px-1.5 py-0.5 rounded text-amber-300 font-mono">
                {strategy === "jev" ? "AI_GATEWAY_API_KEY" : "OPENAI_API_KEY"}
              </code>{" "}
              to your backend <code className="font-mono">backend/.env</code> file.
            </p>
          </div>
        </div>
      )}

      {error && (
        <div className="error-banner mb-6">
          <Warning size={18} />
          <span className="font-mono text-xs">{error}</span>
          <button onClick={() => setError(null)}>✕</button>
        </div>
      )}

      {/* Mental Model Pipeline Strip */}
      <section className="mental-model-strip">
        <div className="flow-step">
          <span className="step-num">1</span>
          <div>
            <strong>Normalized Input</strong>
            <small>Gmail or Synthetic Email</small>
          </div>
        </div>
        <ArrowRight size={14} className="arrow" />
        <div className="flow-step">
          <span className="step-num">2</span>
          <div>
            <strong>Common Taxonomy</strong>
            <small>Exact 7 Dimensions</small>
          </div>
        </div>
        <ArrowRight size={14} className="arrow" />
        <div className={`flow-step ${strategy === "jev" ? "highlight" : ""}`}>
          <span className="step-num">3A</span>
          <div>
            <strong>TypeSafe Jev</strong>
            <small>Posterior Probabilities</small>
          </div>
        </div>
        <div className="text-[#456461] text-xs font-bold px-1">OR</div>
        <div className={`flow-step ${strategy === "llm" ? "highlight" : ""}`}>
          <span className="step-num">3B</span>
          <div>
            <strong>OpenAI LLM</strong>
            <small>gpt-4o-mini Structured</small>
          </div>
        </div>
        <ArrowRight size={14} className="arrow" />
        <div className="flow-step">
          <span className="step-num">4</span>
          <div>
            <strong>Common Result</strong>
            <small>Identical Metric Contract</small>
          </div>
        </div>
      </section>

      {/* SINGLE EMAIL PLAYGROUND */}
      {activeTab === "single" && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 mt-6">
          {/* Left Column: Form & Strategy Selection */}
          <div className="lg:col-span-5 space-y-4">
            <div className="panel p-5">
              {/* Strategy Selector Toggle */}
              <div className="mb-4">
                <label className="text-xs uppercase tracking-wider text-[#6f8c89] font-bold block mb-2">
                  Classifier Strategy
                </label>
                <div className="grid grid-cols-2 gap-2 p-1 bg-[#0b1415] rounded-xl border border-[#1e3435]">
                  <button
                    type="button"
                    onClick={() => setStrategy("jev")}
                    className={`py-2 px-3 rounded-lg text-xs font-bold flex items-center justify-center gap-2 transition-all ${
                      strategy === "jev"
                        ? "bg-[#183637] text-[#79e8cf] shadow-sm border border-[#2b595a]"
                        : "text-[#7a9793] hover:text-[#cde4e0]"
                    }`}
                  >
                    <Lightning size={16} weight={strategy === "jev" ? "fill" : "regular"} />
                    <span>Jev (typesafe-ai)</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => setStrategy("llm")}
                    className={`py-2 px-3 rounded-lg text-xs font-bold flex items-center justify-center gap-2 transition-all ${
                      strategy === "llm"
                        ? "bg-[#183637] text-[#79e8cf] shadow-sm border border-[#2b595a]"
                        : "text-[#7a9793] hover:text-[#cde4e0]"
                    }`}
                  >
                    <Sparkle size={16} weight={strategy === "llm" ? "fill" : "regular"} />
                    <span>LLM (gpt-4o-mini)</span>
                  </button>
                </div>
              </div>

              {/* Presets */}
              <div className="flex items-center justify-between mb-2">
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

              {/* Inputs */}
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
                      {body.length} chars ({body.trim().split(/\s+/).filter(Boolean).length} words)
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

                <div className="flex gap-3 pt-3">
                  <button
                    onClick={handleClassify}
                    disabled={loading}
                    className="primary-action-btn flex-1"
                  >
                    {loading ? (
                      <>
                        <Pulse className="animate-spin" size={16} /> Evaluating via {strategy.toUpperCase()}...
                      </>
                    ) : (
                      <>
                        <Lightning size={16} weight="fill" /> Classify with {strategy === "jev" ? "Jev" : "LLM"}
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

            {/* Benchmark Note */}
            <div className="info-card">
              <div className="flex items-start gap-2.5">
                <Info size={18} className="text-[#79e8cf] mt-0.5 shrink-0" />
                <div className="text-xs text-[#8da6a2] space-y-1">
                  <strong className="text-[#e2f3ee] block">
                    Strict Semantic Equivalence
                  </strong>
                  <p>
                    Both Jev and the OpenAI baseline share the exact same prompt definition, category choices,
                    rubric, and normalized email inputs.
                  </p>
                  <p className="text-[11px] text-[#6b8581]">
                    Neither strategy falls back to a mock engine on error.
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Right Column: Typed Decisions & Telemetry */}
          <div className="lg:col-span-7 space-y-4">
            {result ? (
              <div className="space-y-4">
                {/* Summary Header */}
                <div className="panel p-4 flex flex-wrap items-center justify-between gap-3 bg-[#0d1819]">
                  <div className="flex items-center gap-2.5">
                    <CheckCircle size={20} className="text-[#79e8cf]" weight="fill" />
                    <div>
                      <h3 className="text-sm font-bold text-[#e1f3ee] flex items-center gap-2">
                        <span>Classification Complete</span>
                        <span className="text-[10px] px-2 py-0.5 rounded-full font-mono uppercase bg-[#183637] text-[#79e8cf] border border-[#2b595a]">
                          {result.strategy.toUpperCase()}
                        </span>
                      </h3>
                      <span className="text-[11px] text-[#6a8783]">
                        Model: {result.trace.model} ({result.trace.provider})
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-xs px-2.5 py-1 rounded bg-[#102724] text-[#80d8c5] font-mono border border-[#20403c]">
                      {result.latency.total_ms.toFixed(1)} ms total
                    </span>
                  </div>
                </div>

                {/* Latency Breakdown Bar */}
                <div className="panel p-4 bg-[#0d1819] border border-[#1b2f30]">
                  <h4 className="text-xs font-bold text-[#8fa8a4] mb-3 flex items-center gap-2">
                    <Clock size={16} /> Latency Breakdown (Instrumented Boundaries)
                  </h4>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
                    <div className="p-2.5 rounded bg-[#101e1f] border border-[#1f3738]">
                      <span className="text-[#6c8682] block text-[10px] uppercase">State Prep</span>
                      <strong className="font-mono text-sm text-[#c8e2de]">
                        {result.latency.state_prep_ms.toFixed(1)} ms
                      </strong>
                    </div>

                    {result.strategy === "jev" ? (
                      <>
                        <div className="p-2.5 rounded bg-[#101e1f] border border-[#1f3738]">
                          <span className="text-[#6c8682] block text-[10px] uppercase">Jev Request</span>
                          <strong className="font-mono text-sm text-[#79e8cf]">
                            {(result.latency.jev_request_ms ?? 0).toFixed(1)} ms
                          </strong>
                        </div>
                        <div className="p-2.5 rounded bg-[#101e1f] border border-[#1f3738]">
                          <span className="text-[#6c8682] block text-[10px] uppercase">Normalization</span>
                          <strong className="font-mono text-sm text-[#c8e2de]">
                            {(result.latency.normalization_ms ?? 0).toFixed(1)} ms
                          </strong>
                        </div>
                      </>
                    ) : (
                      <>
                        <div className="p-2.5 rounded bg-[#101e1f] border border-[#1f3738]">
                          <span className="text-[#6c8682] block text-[10px] uppercase">LLM Request</span>
                          <strong className="font-mono text-sm text-[#79e8cf]">
                            {(result.latency.llm_request_ms ?? 0).toFixed(1)} ms
                          </strong>
                        </div>
                        <div className="p-2.5 rounded bg-[#101e1f] border border-[#1f3738]">
                          <span className="text-[#6c8682] block text-[10px] uppercase">Validation</span>
                          <strong className="font-mono text-sm text-[#c8e2de]">
                            {(result.latency.validation_ms ?? 0).toFixed(1)} ms
                          </strong>
                        </div>
                      </>
                    )}

                    <div className="p-2.5 rounded bg-[#101e1f] border border-[#1f3738]">
                      <span className="text-[#6c8682] block text-[10px] uppercase">Total Time</span>
                      <strong className="font-mono text-sm text-[#80d8c5]">
                        {result.latency.total_ms.toFixed(1)} ms
                      </strong>
                    </div>
                  </div>
                </div>

                {/* Decision Cards Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <ChoiceCard
                    title="Intent"
                    primitive="Choice"
                    choice={result.intent.choice}
                    confidence={result.intent.confidence}
                    probabilities={result.intent.probabilities}
                  />
                  <ChoiceCard
                    title="Department"
                    primitive="Choice"
                    choice={result.department.choice}
                    confidence={result.department.confidence}
                    probabilities={result.department.probabilities}
                  />
                  <ChoiceCard
                    title="Urgency"
                    primitive="Choice"
                    choice={result.urgency.choice}
                    confidence={result.urgency.confidence}
                    probabilities={result.urgency.probabilities}
                  />
                  <ChoiceCard
                    title="Sentiment"
                    primitive="Choice"
                    choice={result.sentiment.choice}
                    confidence={result.sentiment.confidence}
                    probabilities={result.sentiment.probabilities}
                  />
                  <BooleanCard
                    title="Spam Detection"
                    primitive="Boolean / Noul"
                    value={result.spam.value}
                    probability={result.spam.probability}
                    confidence={result.spam.confidence}
                    trueLabel="Spam Detected"
                    falseLabel="Legitimate Email"
                    dangerIfTrue={true}
                  />
                  <BooleanCard
                    title="Requires Human"
                    primitive="Boolean / Noul"
                    value={result.requires_human.value}
                    probability={result.requires_human.probability}
                    confidence={result.requires_human.confidence}
                    trueLabel="Human Review Required"
                    falseLabel="Automated Routing Safe"
                    dangerIfTrue={false}
                  />
                  <ScoreCard priority={result.priority} />
                  <div className="decision-card">
                    <span className="text-[11px] font-bold text-[#6f8d89] uppercase tracking-wider block mb-2">
                      Aggregate Confidence
                    </span>
                    <div className="my-2 flex items-baseline gap-2">
                      <strong className="text-xl font-mono text-[#79e8cf]">
                        {(result.aggregate_confidence * 100).toFixed(1)}%
                      </strong>
                    </div>
                    <p className="text-[11px] text-[#7a9591] pt-1 border-t border-[#182728]">
                      Geometric mean of primary categorical and rubric decisions.
                    </p>
                  </div>
                </div>

                {/* Decision Trace Toggle */}
                <div className="panel p-4 bg-[#0a1314]">
                  <button
                    onClick={() => setShowTrace(!showTrace)}
                    className="flex items-center justify-between w-full text-xs font-mono text-[#789b96] hover:text-[#bde4dd]"
                  >
                    <span>{showTrace ? "Hide Decision Trace Details" : "View Raw Trace & Telemetry"}</span>
                    <span>{showTrace ? "▲" : "▼"}</span>
                  </button>

                  {showTrace && (
                    <pre className="mt-3 p-3 bg-[#060c0d] rounded-lg text-[11px] text-[#78a29b] overflow-x-auto border border-[#1b2f30] font-mono">
                      {JSON.stringify(
                        {
                          id: result.id,
                          strategy: result.strategy,
                          model: result.trace.model,
                          provider: result.trace.provider,
                          request_id: result.trace.request_id,
                          usage: result.trace.usage,
                          finish_reason: result.trace.finish_reason,
                          validation_status: result.trace.validation_status,
                          latency: result.latency,
                        },
                        null,
                        2
                      )}
                    </pre>
                  )}
                </div>
              </div>
            ) : (
              <div className="empty-panel h-96 flex flex-col items-center justify-center text-center p-8">
                <Cpu size={48} className="text-[#2a4544] mb-3" />
                <h3 className="text-base font-semibold text-[#8fa8a4]">No Classification Output Yet</h3>
                <p className="text-xs text-[#5a7672] max-w-sm mt-1">
                  Select a preset or input your own email text on the left, then click{" "}
                  <strong>Classify with {strategy === "jev" ? "Jev" : "LLM"}</strong>.
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* PERSONAL GMAIL INGESTION TAB */}
      {activeTab === "gmail" && (
        <div className="space-y-6 mt-6">
          <div className="panel p-6 bg-[#0c1718] border border-[#1d3536]">
            <div className="flex flex-wrap items-center justify-between gap-4 border-b border-[#1b3233] pb-4 mb-4">
              <div>
                <h2 className="text-base font-bold text-[#e1f3ee] flex items-center gap-2">
                  <EnvelopeOpen size={20} className="text-[#79e8cf]" />
                  <span>Personal Gmail Ingestion Pipeline</span>
                </h2>
                <p className="text-xs text-[#7b9994] mt-0.5">
                  Fetch live emails from your Gmail account via Google OAuth 2.0 with read-only access.
                </p>
              </div>

              {gmailConnected ? (
                <div className="flex items-center gap-3">
                  <div className="px-3 py-1.5 rounded-lg bg-emerald-950/60 border border-emerald-800/60 text-emerald-300 text-xs flex items-center gap-2">
                    <ShieldCheck size={16} />
                    <span>Connected: <strong>{gmailEmail}</strong></span>
                  </div>
                  <button
                    onClick={handleDisconnectGmail}
                    className="px-3 py-1.5 rounded-lg bg-[#142324] hover:bg-[#1c3233] border border-[#223d3e] text-xs text-[#8daaa5] flex items-center gap-1.5"
                  >
                    <SignOut size={14} /> Disconnect
                  </button>
                </div>
              ) : (
                <button
                  onClick={handleConnectGmail}
                  className="px-4 py-2 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-500 hover:from-emerald-500 hover:to-teal-400 text-[#071313] font-bold text-xs flex items-center gap-2 shadow-lg"
                >
                  <Lock size={16} weight="fill" /> Connect Gmail Account
                </button>
              )}
            </div>

            {/* Privacy Guarantee Banner */}
            <div className="p-3.5 rounded-xl bg-[#091415] border border-[#193233] text-xs text-[#7d9b96] flex items-start gap-2.5 mb-6">
              <ShieldCheck size={18} className="text-[#79e8cf] shrink-0 mt-0.5" />
              <div>
                <strong className="text-[#c7e5df] block mb-0.5">🔒 Ephemeral In-Memory Storage Only</strong>
                <span>
                  Emails fetched from Gmail are decoded in ephemeral session memory for benchmarking and
                  classification testing. <strong>Raw email bodies are never persisted</strong> to the SQLite database
                  or leaked into system logs.
                </span>
              </div>
            </div>

            {/* Fetch Filter Controls */}
            {gmailConnected ? (
              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-12 gap-3 items-end">
                  <div className="md:col-span-7">
                    <label className="field-label">Gmail Search Query</label>
                    <input
                      type="text"
                      value={gmailQuery}
                      onChange={(e) => setGmailQuery(e.target.value)}
                      placeholder="e.g. label:INBOX, label:UNREAD, or is:important"
                      className="w-full bg-[#101d1e] text-[#dce7e6] border border-[#28403f] rounded-lg p-2.5 text-xs outline-none focus:border-[#79e8cf]"
                    />
                  </div>
                  <div className="md:col-span-2">
                    <label className="field-label">Max Count</label>
                    <select
                      value={gmailMaxResults}
                      onChange={(e) => setGmailMaxResults(Number(e.target.value))}
                      className="w-full bg-[#101d1e] text-[#dce7e6] border border-[#28403f] rounded-lg p-2.5 text-xs outline-none focus:border-[#79e8cf]"
                    >
                      <option value={5}>5 emails</option>
                      <option value={10}>10 emails</option>
                      <option value={25}>25 emails</option>
                    </select>
                  </div>
                  <div className="md:col-span-3">
                    <button
                      onClick={handleFetchGmail}
                      disabled={gmailLoading}
                      className="primary-action-btn w-full"
                    >
                      {gmailLoading ? (
                        <>
                          <Pulse className="animate-spin" size={16} /> Fetching...
                        </>
                      ) : (
                        <>
                          <EnvelopeOpen size={16} /> Fetch Recent Emails
                        </>
                      )}
                    </button>
                  </div>
                </div>

                {gmailNotice && (
                  <div className="p-3 rounded-lg bg-[#112224] text-xs text-[#89aca6] border border-[#1f3b3c]">
                    {gmailNotice}
                  </div>
                )}

                {/* Fetched Messages Table */}
                {gmailMessages.length > 0 && (
                  <div className="mt-6 space-y-3">
                    <h3 className="text-xs font-bold text-[#8fa8a4] uppercase tracking-wider">
                      Fetched Messages ({gmailMessages.length})
                    </h3>
                    <div className="space-y-3">
                      {gmailMessages.map((msg) => (
                        <div
                          key={msg.id}
                          className="p-4 rounded-xl bg-[#0f1d1e] border border-[#1c3536] hover:border-[#2f5556] transition-all flex flex-col md:flex-row md:items-center justify-between gap-4"
                        >
                          <div className="space-y-1 max-w-2xl">
                            <div className="flex items-center gap-2 flex-wrap">
                              <span className="font-bold text-xs text-[#dbeae7]">{msg.subject || "(No Subject)"}</span>
                              <span className="text-[10px] text-[#5b7a76]">{msg.received_at}</span>
                            </div>
                            <div className="text-[11px] text-[#71918c]">From: {msg.sender}</div>
                            <p className="text-xs text-[#8daaa5] line-clamp-2">{msg.snippet}</p>
                          </div>

                          <div className="flex items-center gap-2 shrink-0">
                            <button
                              onClick={() => handleSelectGmailMessage(msg, "jev")}
                              className="px-3 py-1.5 rounded-lg bg-[#132d2e] hover:bg-[#1b3d3e] text-[#79e8cf] text-xs font-bold border border-[#275354] flex items-center gap-1.5 transition-all"
                            >
                              <Lightning size={14} weight="fill" /> Classify Jev
                            </button>
                            <button
                              onClick={() => handleSelectGmailMessage(msg, "llm")}
                              className="px-3 py-1.5 rounded-lg bg-[#132d2e] hover:bg-[#1b3d3e] text-[#80d8c5] text-xs font-bold border border-[#275354] flex items-center gap-1.5 transition-all"
                            >
                              <Sparkle size={14} weight="fill" /> Classify LLM
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="p-8 text-center bg-[#091314] rounded-xl border border-[#172c2d]">
                <Envelope size={40} className="text-[#2b4b4c] mx-auto mb-3" />
                <h3 className="text-sm font-bold text-[#b6d6d0]">Gmail Account Not Connected</h3>
                <p className="text-xs text-[#62827e] max-w-md mx-auto mt-1 mb-4">
                  Connect your Google account with read-only permissions to test real personal emails
                  against the benchmark pipeline.
                </p>
                <button
                  onClick={handleConnectGmail}
                  className="px-4 py-2 rounded-xl bg-[#1b3839] hover:bg-[#254c4e] text-[#79e8cf] text-xs font-bold inline-flex items-center gap-2 border border-[#2d585a]"
                >
                  <Lock size={16} /> Authorize with Google
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* BATCH EVALUATION TAB */}
      {activeTab === "batch" && (
        <div className="space-y-4 mt-6">
          <div className="panel p-5">
            <div className="flex flex-wrap items-center justify-between gap-4 mb-4">
              <div>
                <h3 className="text-sm font-bold text-[#e1f3ee] flex items-center gap-2">
                  <span>Batch Playground Results</span>
                  <span className="text-[10px] px-2 py-0.5 rounded-full font-mono uppercase bg-[#183637] text-[#79e8cf] border border-[#2b595a]">
                    Strategy: {batchResult?.strategy.toUpperCase() || strategy.toUpperCase()}
                  </span>
                </h3>
                <p className="text-xs text-[#6e8a86]">
                  Evaluates concurrency, aggregate throughput, and distribution of results.
                </p>
              </div>
              <button
                onClick={handleBatchTest}
                disabled={batchLoading}
                className="primary-action-btn"
              >
                {batchLoading ? (
                  <>
                    <Pulse className="animate-spin" size={16} /> Running Batch...
                  </>
                ) : (
                  <>
                    <Play size={16} /> Run 4-Email Batch ({strategy.toUpperCase()})
                  </>
                )}
              </button>
            </div>

            {batchResult && (
              <div className="space-y-4">
                <div className="grid grid-cols-3 gap-4">
                  <div className="p-3 bg-[#0d1819] rounded-lg border border-[#1b2f30]">
                    <span className="text-[10px] text-[#5f7a77] uppercase block">Total Records</span>
                    <strong className="text-base font-mono text-[#dbeae7]">
                      {batchResult.total_count}
                    </strong>
                  </div>
                  <div className="p-3 bg-[#0d1819] rounded-lg border border-[#1b2f30]">
                    <span className="text-[10px] text-[#5f7a77] uppercase block">Total Duration</span>
                    <strong className="text-base font-mono text-[#79e8cf]">
                      {batchResult.total_latency_ms.toFixed(1)} ms
                    </strong>
                  </div>
                  <div className="p-3 bg-[#0d1819] rounded-lg border border-[#1b2f30]">
                    <span className="text-[10px] text-[#5f7a77] uppercase block">Mean Latency</span>
                    <strong className="text-base font-mono text-[#80d8c5]">
                      {batchResult.avg_latency_ms.toFixed(1)} ms / record
                    </strong>
                  </div>
                </div>

                <div className="space-y-2 mt-4">
                  {batchResult.results.map((r, i) => (
                    <div
                      key={r.id || i}
                      className="p-3.5 bg-[#0e1b1c] rounded-lg border border-[#1a2d2e] flex flex-col md:flex-row md:items-center justify-between gap-3 text-xs"
                    >
                      <div className="space-y-1">
                        <strong className="text-[#d8eae6] block">{r.subject}</strong>
                        <p className="text-[11px] text-[#698884] line-clamp-1">{r.body_snippet}</p>
                      </div>
                      <div className="flex items-center gap-2 shrink-0">
                        <span className="px-2 py-0.5 rounded bg-[#102324] text-[#79e8cf] font-mono text-[10px]">
                          {r.intent.choice}
                        </span>
                        <span className="px-2 py-0.5 rounded bg-[#102324] text-[#80d8c5] font-mono text-[10px]">
                          {r.department.choice}
                        </span>
                        <span className="px-2 py-0.5 rounded bg-[#102324] text-[#78a29b] font-mono text-[10px]">
                          {r.latency.total_ms.toFixed(0)} ms
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAXONOMY SCHEMA TAB */}
      {activeTab === "schema" && schema && (
        <div className="space-y-4 mt-6">
          <div className="panel p-5">
            <h3 className="text-sm font-bold text-[#e1f3ee] mb-1">
              Active Taxonomy Schema (v{schema.version})
            </h3>
            <p className="text-xs text-[#6e8a86] mb-4">
              Defines the questions, allowed choices, and rubric shared identically by Jev and LLM classifiers.
            </p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <SchemaQuestionCard
                title="1. Customer Intent"
                type="Choice (8 Categories)"
                instructions={schema.intent.instructions}
                options={schema.intent.options}
              />
              <SchemaQuestionCard
                title="2. Department Routing"
                type="Choice (7 Departments)"
                instructions={schema.department.instructions}
                options={schema.department.options}
              />
              <SchemaQuestionCard
                title="3. Urgency Level"
                type="Choice (4 Levels)"
                instructions={schema.urgency.instructions}
                options={schema.urgency.options}
              />
              <SchemaQuestionCard
                title="4. Customer Sentiment"
                type="Choice (5 Sentiments)"
                instructions={schema.sentiment.instructions}
                options={schema.sentiment.options}
              />
              <SchemaBooleanCard
                title="5. Spam Detection"
                type="Noul / Boolean Decision"
                instructions={schema.spam.instructions}
                trueCriteria={schema.spam.true_criteria}
                falseCriteria={schema.spam.false_criteria}
              />
              <SchemaBooleanCard
                title="6. Requires Human Review"
                type="Noul / Boolean Decision"
                instructions={schema.requires_human.instructions}
                trueCriteria={schema.requires_human.true_criteria}
                falseCriteria={schema.requires_human.false_criteria}
              />
              <div className="p-4 bg-[#0a1415] rounded-xl border border-[#1b2d2e] md:col-span-2">
                <span className="text-[11px] font-bold text-[#79e8cf] uppercase tracking-wider block mb-1">
                  7. Operational Priority Rubric
                </span>
                <p className="text-xs text-[#7e9995] mb-3">{schema.priority.instructions}</p>
                <div className="grid grid-cols-1 md:grid-cols-5 gap-2 text-xs">
                  {schema.priority.rubric.map((desc, idx) => (
                    <div key={idx} className="p-2.5 bg-[#0f1d1e] rounded-lg border border-[#1f3738]">
                      <strong className="text-[#79e8cf] font-mono block mb-1">P{5 - idx} ({idx})</strong>
                      <p className="text-[10px] text-[#718d89] leading-snug">{desc}</p>
                    </div>
                  ))}
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
  primitive,
  choice,
  confidence,
  probabilities,
}: {
  title: string;
  primitive: string;
  choice: string;
  confidence: number;
  probabilities: Record<string, number>;
}) {
  const sortedProbabilities = Object.entries(probabilities || {}).sort((a, b) => b[1] - a[1]);

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

      <div className="my-2 flex items-baseline justify-between">
        <strong className="text-base text-[#e1f3ee] font-mono capitalize">
          {choice.replace(/_/g, " ")}
        </strong>
        <span className="text-xs font-mono text-[#79e8cf]">
          {(confidence * 100).toFixed(1)}% conf
        </span>
      </div>

      <div className="space-y-1.5 pt-2 border-t border-[#182728]">
        {sortedProbabilities.slice(0, 3).map(([key, p]) => (
          <div key={key} className="flex items-center justify-between text-[11px]">
            <span className="text-[#7e9995] truncate max-w-[120px] capitalize">
              {key.replace(/_/g, " ")}
            </span>
            <div className="flex-1 mx-2 bg-[#101c1d] rounded-full h-1.5 overflow-hidden">
              <div
                className="bg-[#2a6860] h-full rounded-full transition-all"
                style={{ width: `${Math.min(100, Math.max(2, p * 100))}%` }}
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

function SchemaQuestionCard({
  title,
  type,
  instructions,
  options,
}: {
  title: string;
  type: string;
  instructions: string;
  options: Record<string, string>;
}) {
  return (
    <div className="p-4 bg-[#0a1415] rounded-xl border border-[#1b2d2e] space-y-2">
      <div className="flex justify-between items-center">
        <strong className="text-xs text-[#79e8cf] font-mono">{title}</strong>
        <span className="text-[10px] text-[#557370] font-mono">{type}</span>
      </div>
      <p className="text-xs text-[#7f9c97]">{instructions}</p>
      <div className="flex flex-wrap gap-1.5 pt-2">
        {Object.entries(options).map(([k, desc]) => (
          <span
            key={k}
            title={desc}
            className="text-[10px] px-2 py-0.5 rounded bg-[#102022] text-[#8db1ab] border border-[#1b3436]"
          >
            {k}
          </span>
        ))}
      </div>
    </div>
  );
}

function SchemaBooleanCard({
  title,
  type,
  instructions,
  trueCriteria,
  falseCriteria,
}: {
  title: string;
  type: string;
  instructions: string;
  trueCriteria: string;
  falseCriteria: string;
}) {
  return (
    <div className="p-4 bg-[#0a1415] rounded-xl border border-[#1b2d2e] space-y-2">
      <div className="flex justify-between items-center">
        <strong className="text-xs text-[#79e8cf] font-mono">{title}</strong>
        <span className="text-[10px] text-[#557370] font-mono">{type}</span>
      </div>
      <p className="text-xs text-[#7f9c97]">{instructions}</p>
      <div className="text-[11px] space-y-1 pt-1 text-[#698884]">
        <div>
          <span className="text-emerald-400 font-bold">True:</span> {trueCriteria}
        </div>
        <div>
          <span className="text-[#84a39f] font-bold">False:</span> {falseCriteria}
        </div>
      </div>
    </div>
  );
}
