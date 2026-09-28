import React, { useEffect, useState } from "react";
import {
  ArrowRight,
  ArrowsClockwise,
  CheckCircle,
  Clock,
  Cpu,
  Envelope,
  EnvelopeOpen,
  Info,
  Lightning,
  Lock,
  PencilSimple,
  Play,
  Pulse,
  ShieldCheck,
  SignOut,
  Sparkle,
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

export default function ClassificationsPlayground() {
  // Classification Input State
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");
  const [selectedEmailId, setSelectedEmailId] = useState<string | null>(null);
  const [isManualInput, setIsManualInput] = useState(false);

  // Strategy State
  const [strategy, setStrategy] = useState<"jev" | "llm">("jev");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ClassificationResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Status & Telemetry
  const [providerStatus, setProviderStatus] = useState<ProviderStatus | null>(null);
  const [showTrace, setShowTrace] = useState(false);

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
    checkGmailStatus();

    // Handle OAuth redirect with ?code=...
    const urlParams = new URLSearchParams(window.location.search);
    const code = urlParams.get("code");
    if (code) {
      window.history.replaceState({}, document.title, window.location.pathname);
      setGmailNotice("Authenticating with Google...");
      gmailApi
        .exchangeCode(code)
        .then((st) => {
          setGmailConnected(st.connected);
          setGmailEmail(st.email);
          setGmailNotice(`Connected successfully as ${st.email}`);
          // Auto-fetch first batch of inbox emails
          loadInboxMessages();
        })
        .catch((err: any) => {
          setError(err?.message || "Failed to complete Google OAuth exchange.");
          setGmailNotice(null);
        });
    }
  }, []);

  const fetchProviderStatus = () => {
    classificationApi.getProviderStatus().then(setProviderStatus).catch(() => null);
  };

  const checkGmailStatus = async () => {
    try {
      const st = await gmailApi.getStatus();
      setGmailConnected(st.connected);
      setGmailEmail(st.email);
      if (st.connected) {
        loadInboxMessages();
      }
    } catch {
      setGmailConnected(false);
    }
  };

  const loadInboxMessages = async () => {
    setGmailLoading(true);
    try {
      const msgs = await gmailApi.fetchMessages(gmailQuery, gmailMaxResults);
      setGmailMessages(msgs);
      if (msgs.length > 0) {
        // Auto-select the first real email
        selectEmail(msgs[0]);
      }
    } catch (err: any) {
      setError(err?.message || "Failed to load Gmail messages.");
    } finally {
      setGmailLoading(false);
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
      setSelectedEmailId(null);
      setSubject("");
      setBody("");
      setGmailNotice("Gmail disconnected.");
    } catch (err: any) {
      setError(err?.message || "Failed to disconnect Gmail.");
    }
  };

  const selectEmail = (msg: NormalizedGmailMessage) => {
    setSelectedEmailId(msg.id);
    setSubject(msg.subject || "(No Subject)");
    setBody(msg.body || msg.snippet);
    setError(null);
  };

  const handleClassify = async () => {
    if (!subject.trim() && !body.trim()) {
      setError("Please select a Gmail message or enter an email subject/body to classify.");
      return;
    }
    setError(null);
    setLoading(true);
    try {
      const res = await classificationApi.test(subject, body, strategy);
      setResult(res);
    } catch (err: any) {
      setError(err?.message || `Failed to classify email using ${strategy.toUpperCase()}.`);
    } finally {
      setLoading(false);
    }
  };

  const isCurrentStrategyConfigured =
    strategy === "jev"
      ? providerStatus?.jev_configured
      : providerStatus?.llm_configured;

  return (
    <div className="space-y-8 pb-16">
      {/* Top Header */}
      <header className="topbar">
        <div>
          <label>AI Benchmark Laboratory</label>
          <h1>JevScale Evaluation Playground</h1>
          <p>
            Evaluate typed decision models against generative LLMs on real customer support emails.
          </p>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          {providerStatus && (
            <>
              <div
                className={`status-pill ${providerStatus.jev_configured ? "live" : "sandbox"}`}
                title={providerStatus.jev_configured ? "Vercel AI Gateway Active" : "Missing AI_GATEWAY_API_KEY"}
              >
                <i />
                <span>Jev: {providerStatus.jev_configured ? providerStatus.jev_model : "Unconfigured"}</span>
              </div>
              <div
                className={`status-pill ${providerStatus.llm_configured ? "live" : "sandbox"}`}
                title={providerStatus.llm_configured ? "OpenAI Baseline Active" : "Missing OPENAI_API_KEY"}
              >
                <i />
                <span>LLM: {providerStatus.llm_configured ? providerStatus.llm_model : "Unconfigured"}</span>
              </div>
            </>
          )}
        </div>
      </header>

      {/* Global Error Banner */}
      {error && (
        <div className="error-banner">
          <Warning size={20} className="shrink-0 text-red-400" />
          <div className="flex-1">
            <strong className="block text-red-200 font-semibold mb-0.5">Execution Error</strong>
            <span className="font-mono text-xs text-red-300">{error}</span>
          </div>
          <button onClick={() => setError(null)}>✕</button>
        </div>
      )}

      {/* Unconfigured Provider Loud Alert */}
      {!isCurrentStrategyConfigured && providerStatus && (
        <div className="p-4 rounded-xl bg-amber-950/40 border border-amber-500/40 text-amber-200 flex items-start gap-3">
          <Warning size={22} className="text-amber-400 shrink-0 mt-0.5" />
          <div className="text-xs space-y-1">
            <strong className="text-amber-100 text-sm block">
              {strategy === "jev" ? "Jev API Key Not Configured" : "OpenAI API Key Not Configured"}
            </strong>
            <p>
              Runtime mock fallback is strictly disabled. Please add{" "}
              <code className="bg-amber-900/60 px-1.5 py-0.5 rounded text-amber-200 font-mono">
                {strategy === "jev" ? "AI_GATEWAY_API_KEY" : "OPENAI_API_KEY"}
              </code>{" "}
              to <code className="font-mono">backend/.env</code> to run live classifications.
            </p>
          </div>
        </div>
      )}

      {/* STEP 1: GMAIL INGESTION */}
      <section className="panel p-6">
        <div className="flex items-center justify-between border-b border-zinc-800 pb-4 mb-5">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-emerald-950/80 border border-emerald-500/40 text-emerald-400 flex items-center justify-center font-bold text-sm">
              1
            </div>
            <div>
              <h2 className="text-base font-bold text-zinc-100 flex items-center gap-2">
                <span>Personal Gmail Ingestion</span>
                {gmailConnected && (
                  <span className="text-xs font-normal text-emerald-400 bg-emerald-950/80 border border-emerald-800/80 px-2 py-0.5 rounded-full flex items-center gap-1.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 inline-block" />
                    {gmailEmail}
                  </span>
                )}
              </h2>
              <p className="text-xs text-zinc-400">
                Connect your personal Gmail account to benchmark against real-world customer messages.
              </p>
            </div>
          </div>

          <div>
            {gmailConnected ? (
              <button onClick={handleDisconnectGmail} className="secondary-btn text-xs">
                <SignOut size={14} /> Disconnect
              </button>
            ) : (
              <button onClick={handleConnectGmail} className="primary-btn text-xs">
                <Lock size={14} weight="fill" /> Connect Gmail Account
              </button>
            )}
          </div>
        </div>

        {/* Ephemeral Privacy Guarantee Notice */}
        <div className="p-3 rounded-lg bg-zinc-900/80 border border-zinc-800 text-xs text-zinc-400 flex items-start gap-2.5 mb-5">
          <ShieldCheck size={18} className="text-emerald-400 shrink-0 mt-0.5" />
          <div>
            <strong className="text-zinc-200 block">🔒 Ephemeral In-Memory Retrieval Only</strong>
            <span>
              Emails are fetched into temporary server memory for benchmark evaluation. Raw email content is never
              written to the SQLite database or logged to disk.
            </span>
          </div>
        </div>

        {gmailConnected ? (
          <div className="space-y-4">
            {/* Filter Bar */}
            <div className="flex flex-wrap items-center gap-3 bg-zinc-900/50 p-3 rounded-xl border border-zinc-800">
              <div className="flex-1 min-w-[200px]">
                <input
                  type="text"
                  value={gmailQuery}
                  onChange={(e) => setGmailQuery(e.target.value)}
                  placeholder="Search query (e.g. label:INBOX, label:UNREAD)"
                  className="w-full text-xs"
                />
              </div>
              <div className="w-28">
                <select
                  value={gmailMaxResults}
                  onChange={(e) => setGmailMaxResults(Number(e.target.value))}
                  className="text-xs"
                >
                  <option value={5}>5 emails</option>
                  <option value={10}>10 emails</option>
                  <option value={25}>25 emails</option>
                </select>
              </div>
              <button
                onClick={loadInboxMessages}
                disabled={gmailLoading}
                className="secondary-btn text-xs"
              >
                {gmailLoading ? <Pulse className="animate-spin" size={14} /> : <ArrowsClockwise size={14} />}
                Fetch Emails
              </button>
            </div>

            {/* Email List */}
            {gmailMessages.length > 0 ? (
              <div className="space-y-2 mt-4">
                <label className="text-xs font-bold text-zinc-400 uppercase tracking-wider block mb-1">
                  Select an Email to Classify ({gmailMessages.length} retrieved):
                </label>
                <div className="grid grid-cols-1 gap-2 max-h-80 overflow-y-auto pr-1">
                  {gmailMessages.map((msg) => {
                    const isSelected = selectedEmailId === msg.id;
                    return (
                      <div
                        key={msg.id}
                        onClick={() => selectEmail(msg)}
                        className={`p-3.5 rounded-xl border cursor-pointer transition-all ${
                          isSelected
                            ? "bg-zinc-800/90 border-emerald-500 shadow-md"
                            : "bg-zinc-900/60 border-zinc-800/80 hover:border-zinc-700"
                        }`}
                      >
                        <div className="flex items-center justify-between gap-2 mb-1">
                          <strong className={`text-xs font-semibold ${isSelected ? "text-emerald-300" : "text-zinc-200"}`}>
                            {msg.subject || "(No Subject)"}
                          </strong>
                          <span className="text-[11px] text-zinc-400 font-mono shrink-0">
                            {msg.received_at}
                          </span>
                        </div>
                        <div className="text-[11px] text-zinc-400 mb-1">From: {msg.sender}</div>
                        <p className="text-xs text-zinc-300 line-clamp-2 leading-relaxed">
                          {msg.snippet}
                        </p>
                      </div>
                    );
                  })}
                </div>
              </div>
            ) : (
              <div className="p-8 text-center bg-zinc-900/40 rounded-xl border border-zinc-800 text-zinc-400 text-xs">
                No emails fetched yet. Click <strong>Fetch Emails</strong> above to retrieve messages from your inbox.
              </div>
            )}
          </div>
        ) : (
          <div className="p-6 text-center bg-zinc-900/40 rounded-xl border border-zinc-800/80 space-y-3">
            <EnvelopeOpen size={36} className="text-zinc-500 mx-auto" />
            <h3 className="text-sm font-bold text-zinc-200">Connect Gmail to Ingest Real Data</h3>
            <p className="text-xs text-zinc-400 max-w-md mx-auto">
              Click below to grant read-only authorization so JevScale can inspect and benchmark real support messages.
            </p>
            <button onClick={handleConnectGmail} className="primary-btn text-xs mx-auto">
              <Lock size={14} weight="fill" /> Connect Gmail Account
            </button>
          </div>
        )}

        {/* Manual Fallback Toggle */}
        <div className="mt-4 pt-4 border-t border-zinc-800/80 flex items-center justify-between text-xs">
          <button
            onClick={() => setIsManualInput(!isManualInput)}
            className="text-zinc-400 hover:text-zinc-200 flex items-center gap-1.5 underline"
          >
            <PencilSimple size={14} />
            {isManualInput ? "Hide manual email editor" : "Or enter / edit custom email text manually"}
          </button>
          {subject && (
            <span className="text-zinc-400">
              Active: <strong className="text-zinc-200">{subject.slice(0, 40)}...</strong>
            </span>
          )}
        </div>

        {isManualInput && (
          <div className="mt-4 space-y-3 bg-zinc-900/70 p-4 rounded-xl border border-zinc-800">
            <div>
              <label className="field-label">Subject</label>
              <input
                type="text"
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
                placeholder="e.g. Refund not received"
              />
            </div>
            <div>
              <label className="field-label">Body</label>
              <textarea
                rows={4}
                value={body}
                onChange={(e) => setBody(e.target.value)}
                placeholder="Paste email content..."
              />
            </div>
          </div>
        )}
      </section>

      {/* STEP 2: CHOOSE CLASSIFIER STRATEGY */}
      <section className="panel p-6">
        <div className="flex items-center gap-3 border-b border-zinc-800 pb-4 mb-5">
          <div className="w-8 h-8 rounded-lg bg-emerald-950/80 border border-emerald-500/40 text-emerald-400 flex items-center justify-center font-bold text-sm">
            2
          </div>
          <div>
            <h2 className="text-base font-bold text-zinc-100">Select Classifier Strategy</h2>
            <p className="text-xs text-zinc-400">
              Choose the decision engine to evaluate against the active email.
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Strategy A: Jev */}
          <div
            onClick={() => setStrategy("jev")}
            className={`p-5 rounded-xl border cursor-pointer transition-all ${
              strategy === "jev"
                ? "bg-zinc-800/90 border-emerald-500 shadow-md ring-1 ring-emerald-500"
                : "bg-zinc-900/60 border-zinc-800 hover:border-zinc-700"
            }`}
          >
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-bold px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800 font-mono">
                typesafe-ai/jev
              </span>
              <span className="text-[11px] text-zinc-400 font-mono">
                {providerStatus?.jev_configured ? "Ready" : "Missing Key"}
              </span>
            </div>
            <h3 className="text-base font-bold text-zinc-100 flex items-center gap-2 mb-1.5">
              <Lightning size={18} weight="fill" className="text-emerald-400" />
              <span>Jev Decision Engine</span>
            </h3>
            <p className="text-xs text-zinc-300 leading-relaxed mb-4">
              TypeSafe decision model evaluated via Vercel AI Gateway. Generates direct posterior probability distributions
              across Choice, Noul (Boolean), and Score dimensions concurrently.
            </p>
            <div className="flex items-center justify-between text-xs text-zinc-400 pt-3 border-t border-zinc-800">
              <span>Latency profile: <strong>Fast (Sub-second)</strong></span>
              <span className="text-emerald-400 font-bold">{strategy === "jev" ? "● Selected" : "Select"}</span>
            </div>
          </div>

          {/* Strategy B: LLM Baseline */}
          <div
            onClick={() => setStrategy("llm")}
            className={`p-5 rounded-xl border cursor-pointer transition-all ${
              strategy === "llm"
                ? "bg-zinc-800/90 border-emerald-500 shadow-md ring-1 ring-emerald-500"
                : "bg-zinc-900/60 border-zinc-800 hover:border-zinc-700"
            }`}
          >
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-bold px-2 py-0.5 rounded bg-zinc-800 text-zinc-300 border border-zinc-700 font-mono">
                gpt-4o-mini
              </span>
              <span className="text-[11px] text-zinc-400 font-mono">
                {providerStatus?.llm_configured ? "Ready" : "Missing Key"}
              </span>
            </div>
            <h3 className="text-base font-bold text-zinc-100 flex items-center gap-2 mb-1.5">
              <Sparkle size={18} weight="fill" className="text-cyan-400" />
              <span>Generative LLM Baseline</span>
            </h3>
            <p className="text-xs text-zinc-300 leading-relaxed mb-4">
              OpenAI LLM baseline with native JSON schema structured output (<code className="font-mono text-zinc-200">strict=True</code>).
              Enforces the exact same 7-dimension taxonomy for rigorous, 1:1 benchmark parity.
            </p>
            <div className="flex items-center justify-between text-xs text-zinc-400 pt-3 border-t border-zinc-800">
              <span>Latency profile: <strong>Generative Tokens</strong></span>
              <span className="text-emerald-400 font-bold">{strategy === "llm" ? "● Selected" : "Select"}</span>
            </div>
          </div>
        </div>
      </section>

      {/* STEP 3: RUN CLASSIFICATION & INSPECT */}
      <section className="panel p-6">
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-zinc-800 pb-4 mb-5">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-emerald-950/80 border border-emerald-500/40 text-emerald-400 flex items-center justify-center font-bold text-sm">
              3
            </div>
            <div>
              <h2 className="text-base font-bold text-zinc-100">Run Classification & Inspect</h2>
              <p className="text-xs text-zinc-400">
                Execute live decision against the selected email using{" "}
                <strong className="text-zinc-200">{strategy === "jev" ? "Jev" : "OpenAI LLM"}</strong>.
              </p>
            </div>
          </div>

          <button
            onClick={handleClassify}
            disabled={loading || (!subject && !body)}
            className="primary-btn px-6 py-3 text-sm shadow-lg"
          >
            {loading ? (
              <>
                <Pulse className="animate-spin" size={18} /> Evaluating via {strategy.toUpperCase()}...
              </>
            ) : (
              <>
                <Lightning size={18} weight="fill" /> Run Classification ({strategy.toUpperCase()})
              </>
            )}
          </button>
        </div>

        {/* Results Area */}
        {result ? (
          <div className="space-y-6">
            {/* Latency & Metadata Summary Bar */}
            <div className="p-4 rounded-xl bg-zinc-900 border border-zinc-800 flex flex-wrap items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <CheckCircle size={24} weight="fill" className="text-emerald-400" />
                <div>
                  <h3 className="text-sm font-bold text-zinc-100 flex items-center gap-2">
                    <span>Classification Succeeded</span>
                    <span className="text-xs px-2 py-0.5 rounded font-mono uppercase bg-zinc-800 text-emerald-400 border border-zinc-700">
                      {result.strategy.toUpperCase()}
                    </span>
                  </h3>
                  <span className="text-xs text-zinc-400">
                    Model: {result.trace.model} ({result.trace.provider})
                  </span>
                </div>
              </div>

              {/* Latency Breakdown Metric Tiles */}
              <div className="flex items-center gap-2 flex-wrap">
                <div className="px-3 py-1.5 rounded-lg bg-zinc-800/80 border border-zinc-700 text-xs">
                  <span className="text-zinc-400 block text-[10px] uppercase font-semibold">Prep</span>
                  <strong className="font-mono text-zinc-200">{result.latency.state_prep_ms.toFixed(1)} ms</strong>
                </div>

                {result.strategy === "jev" ? (
                  <>
                    <div className="px-3 py-1.5 rounded-lg bg-emerald-950/60 border border-emerald-800 text-xs">
                      <span className="text-emerald-400 block text-[10px] uppercase font-semibold">Jev Request</span>
                      <strong className="font-mono text-emerald-300">
                        {(result.latency.jev_request_ms ?? 0).toFixed(1)} ms
                      </strong>
                    </div>
                    <div className="px-3 py-1.5 rounded-lg bg-zinc-800/80 border border-zinc-700 text-xs">
                      <span className="text-zinc-400 block text-[10px] uppercase font-semibold">Normalize</span>
                      <strong className="font-mono text-zinc-200">
                        {(result.latency.normalization_ms ?? 0).toFixed(1)} ms
                      </strong>
                    </div>
                  </>
                ) : (
                  <>
                    <div className="px-3 py-1.5 rounded-lg bg-cyan-950/60 border border-cyan-800 text-xs">
                      <span className="text-cyan-400 block text-[10px] uppercase font-semibold">LLM Request</span>
                      <strong className="font-mono text-cyan-300">
                        {(result.latency.llm_request_ms ?? 0).toFixed(1)} ms
                      </strong>
                    </div>
                    <div className="px-3 py-1.5 rounded-lg bg-zinc-800/80 border border-zinc-700 text-xs">
                      <span className="text-zinc-400 block text-[10px] uppercase font-semibold">Validation</span>
                      <strong className="font-mono text-zinc-200">
                        {(result.latency.validation_ms ?? 0).toFixed(1)} ms
                      </strong>
                    </div>
                  </>
                )}

                <div className="px-3 py-1.5 rounded-lg bg-zinc-800 border border-zinc-700 text-xs">
                  <span className="text-zinc-400 block text-[10px] uppercase font-semibold">Total</span>
                  <strong className="font-mono text-white font-bold">{result.latency.total_ms.toFixed(1)} ms</strong>
                </div>
              </div>
            </div>

            {/* 7 Dimensions Cards Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <ChoiceCard
                title="Customer Intent"
                choice={result.intent.choice}
                confidence={result.intent.confidence}
                probabilities={result.intent.probabilities}
              />
              <ChoiceCard
                title="Department"
                choice={result.department.choice}
                confidence={result.department.confidence}
                probabilities={result.department.probabilities}
              />
              <ChoiceCard
                title="Urgency"
                choice={result.urgency.choice}
                confidence={result.urgency.confidence}
                probabilities={result.urgency.probabilities}
              />
              <ChoiceCard
                title="Sentiment"
                choice={result.sentiment.choice}
                confidence={result.sentiment.confidence}
                probabilities={result.sentiment.probabilities}
              />
              <BooleanCard
                title="Spam Detection"
                value={result.spam.value}
                probability={result.spam.probability}
                confidence={result.spam.confidence}
                trueLabel="Spam Flagged"
                falseLabel="Legitimate"
                dangerIfTrue={true}
              />
              <BooleanCard
                title="Human Review"
                value={result.requires_human.value}
                probability={result.requires_human.probability}
                confidence={result.requires_human.confidence}
                trueLabel="Human Escalation"
                falseLabel="Automated Safe"
                dangerIfTrue={false}
              />
              <ScoreCard priority={result.priority} />
              <div className="decision-card flex flex-col justify-between">
                <div>
                  <span className="text-xs font-bold text-zinc-400 uppercase tracking-wider block mb-2">
                    Confidence Signal
                  </span>
                  <div className="my-2 flex items-baseline gap-2">
                    <strong className="text-2xl font-mono text-emerald-400 font-bold">
                      {(result.aggregate_confidence * 100).toFixed(1)}%
                    </strong>
                  </div>
                </div>
                <p className="text-[11px] text-zinc-400 pt-2 border-t border-zinc-800">
                  Geometric mean posterior probability across all questions.
                </p>
              </div>
            </div>

            {/* Collapsible Telemetry / Trace */}
            <div className="p-4 rounded-xl bg-zinc-900/60 border border-zinc-800">
              <button
                onClick={() => setShowTrace(!showTrace)}
                className="w-full text-xs font-mono text-zinc-400 hover:text-zinc-200 flex items-center justify-between"
              >
                <span>{showTrace ? "▲ Hide Raw Telemetry & Decision Trace" : "▼ View Raw Telemetry & Decision Trace"}</span>
                <span className="text-zinc-500">Request: {result.trace.request_id || "N/A"}</span>
              </button>

              {showTrace && (
                <pre className="mt-3 p-3 bg-zinc-950 rounded-lg text-xs font-mono text-zinc-300 overflow-x-auto border border-zinc-800">
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
          <div className="p-10 text-center bg-zinc-900/30 rounded-xl border border-zinc-800 text-zinc-500 text-xs">
            Select an email and click <strong>Run Classification</strong> to view decision metrics and latency breakdown.
          </div>
        )}
      </section>
    </div>
  );
}

function ChoiceCard({
  title,
  choice,
  confidence,
  probabilities,
}: {
  title: string;
  choice: string;
  confidence: number;
  probabilities: Record<string, number>;
}) {
  const sortedProbabilities = Object.entries(probabilities || {}).sort((a, b) => b[1] - a[1]);

  return (
    <div className="decision-card">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-bold text-zinc-400 uppercase tracking-wider">{title}</span>
        <span className="text-[11px] font-mono text-emerald-400 font-semibold">
          {(confidence * 100).toFixed(0)}%
        </span>
      </div>

      <div className="my-2">
        <strong className="text-base text-zinc-100 font-semibold capitalize">
          {choice.replace(/_/g, " ")}
        </strong>
      </div>

      <div className="space-y-1.5 pt-2 border-t border-zinc-800">
        {sortedProbabilities.slice(0, 3).map(([key, p]) => (
          <div key={key} className="flex items-center justify-between text-[11px]">
            <span className="text-zinc-400 truncate max-w-[100px] capitalize">
              {key.replace(/_/g, " ")}
            </span>
            <div className="flex-1 mx-2 bg-zinc-800 rounded-full h-1.5 overflow-hidden">
              <div
                className="bg-emerald-500 h-full rounded-full transition-all"
                style={{ width: `${Math.min(100, Math.max(2, p * 100))}%` }}
              />
            </div>
            <span className="font-mono text-zinc-500 w-8 text-right">{(p * 100).toFixed(0)}%</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function BooleanCard({
  title,
  value,
  probability,
  confidence,
  trueLabel,
  falseLabel,
  dangerIfTrue,
}: {
  title: string;
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
        <span className="text-xs font-bold text-zinc-400 uppercase tracking-wider">{title}</span>
        <span className="text-[11px] font-mono text-emerald-400 font-semibold">
          {(confidence * 100).toFixed(0)}%
        </span>
      </div>

      <div className="my-2">
        <span
          className={`px-2.5 py-1 rounded text-xs font-semibold inline-flex items-center gap-1.5 border ${
            value
              ? isDanger
                ? "bg-red-950/80 text-red-300 border-red-800"
                : "bg-emerald-950/80 text-emerald-300 border-emerald-800"
              : "bg-zinc-800 text-zinc-300 border-zinc-700"
          }`}
        >
          {value ? trueLabel : falseLabel}
        </span>
      </div>

      <div className="space-y-1 text-[11px] text-zinc-400 pt-2 border-t border-zinc-800">
        <div className="flex justify-between">
          <span>P(True):</span>
          <span className="font-mono text-zinc-300">{(probability * 100).toFixed(1)}%</span>
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
        <span className="text-xs font-bold text-zinc-400 uppercase tracking-wider">Priority Score</span>
        <span className="text-[11px] font-mono text-emerald-400 font-semibold">
          {(priority.confidence * 100).toFixed(0)}%
        </span>
      </div>

      <div className="my-2 flex items-baseline gap-2">
        <strong className="text-xl font-mono text-emerald-400 font-bold">
          {priority.score.toFixed(2)}
        </strong>
        <span className="text-xs text-zinc-500">/ {priority.max_score.toFixed(0)}</span>
      </div>

      <div className="bg-zinc-800 rounded-full h-2 overflow-hidden mb-2">
        <div
          className="bg-gradient-to-r from-sky-400 via-amber-400 to-red-500 h-full rounded-full"
          style={{ width: `${Math.min(100, Math.max(5, percentage))}%` }}
        />
      </div>

      <p className="text-[11px] text-zinc-400 line-clamp-2 pt-1 border-t border-zinc-800">
        {rubricText}
      </p>
    </div>
  );
}
