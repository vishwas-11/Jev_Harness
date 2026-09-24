import { NavLink, Navigate, Route, Routes } from "react-router-dom";
import DatasetsPage from "../pages/DatasetsPage";
import NewExperiment from "../pages/NewExperiment";
import ClassificationsPlayground from "../pages/ClassificationsPlayground";
import {
  ArrowsLeftRight,
  ChartLineUp,
  Database,
  Flask,
  Gear,
  House,
  ListChecks,
  Plus,
  Pulse,
} from "@phosphor-icons/react";

const navItems = [
  ["Dashboard", "/", House],
  ["Datasets", "/datasets", Database],
  ["New experiment", "/experiments/new", Plus],
  ["Active runs", "/runs", Pulse],
  ["Classifications", "/classifications", ListChecks],
  ["Analytics", "/analytics", ChartLineUp],
  ["Comparison", "/comparison", ArrowsLeftRight],
  ["Settings", "/settings", Gear],
] as const;

function Shell({ children }: { children: React.ReactNode }) {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">
            <Flask size={18} weight="bold" />
          </div>
          <div>
            <strong>JevScale</strong>
            <small>decision systems lab</small>
          </div>
        </div>
        <div className="workspace">
          <i /> Local workspace <span>&rarr;</span>
        </div>
        <nav aria-label="Primary navigation">
          {navItems.map(([label, path, Icon]) => (
            <NavLink
              key={path}
              to={path}
              end={path === "/"}
              className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`}
            >
              <Icon size={18} />
              <span>{label}</span>
              {label === "Classifications" && <b className="bg-[#122826] text-[#79e8cf] text-[9px] px-1.5 py-0.5 rounded">Jev</b>}
              {label === "Active runs" && <b>2</b>}
            </NavLink>
          ))}
        </nav>
        <footer>
          <div>
            <i className="online" /> API connected
          </div>
          <small>Phase 3 - Jev classification</small>
        </footer>
      </aside>
      <main>{children}</main>
    </div>
  );
}

function Dashboard() {
  return (
    <Shell>
      <header className="topbar">
        <div>
          <label>Control plane / overview</label>
          <h1>Good morning, operator.</h1>
          <p>Observe the systems making structured decisions across your experiments.</p>
        </div>
        <div className="flex gap-2">
          <NavLink className="secondary-btn" to="/classifications">
            <ListChecks size={18} /> Jev Playground
          </NavLink>
          <NavLink className="primary" to="/experiments/new">
            <Plus size={18} weight="bold" /> New experiment
          </NavLink>
        </div>
      </header>
      <section className="signal-strip">
        <div>
          <span>Workspace status</span>
          <strong>
            <i className="online" /> Ready for a run
          </strong>
        </div>
        <div>
          <span>Jev Decision Engine</span>
          <strong>Multi-Question Active</strong>
        </div>
        <div>
          <span>Last sync</span>
          <strong>Just now</strong>
        </div>
      </section>
      <section className="metrics">
        <Metric label="Active runs" value="2" meta="Both processing" icon={<Pulse />} />
        <Metric label="Records processed" value="18,291" meta="Across 7 runs" icon={<Database />} />
        <Metric label="Avg. throughput" value="412/s" meta="Measured - all strategies" icon={<Pulse />} />
        <Metric label="Jev cost" value="$0.42" meta="Measured - 24.6K records" icon={<ChartLineUp />} />
      </section>
      <section className="two-col">
        <div className="panel chart">
          <div className="panel-head">
            <div>
              <label>System pulse</label>
              <h2>Throughput over time</h2>
            </div>
            <button>Last 30 min</button>
          </div>
          <div className="chart-box">
            <span>500</span>
            <span>350</span>
            <span>200</span>
            <span>0</span>
            <svg viewBox="0 0 700 220" preserveAspectRatio="none">
              <path
                d="M0 174 C45 152 70 168 105 138 S165 110 202 131 S260 74 302 105 S368 130 405 86 S456 98 505 58 S560 78 600 46 S665 48 700 24 V220 H0 Z"
                fill="currentColor"
                opacity=".09"
              />
              <path
                d="M0 174 C45 152 70 168 105 138 S165 110 202 131 S260 74 302 105 S368 130 405 86 S456 98 505 58 S560 78 600 46 S665 48 700 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="3"
              />
            </svg>
            <div className="x-axis">
              <span>09:00</span>
              <span>09:10</span>
              <span>09:20</span>
              <span>09:30</span>
              <span>09:40</span>
              <span>09:50</span>
            </div>
          </div>
          <small className="note">Illustrative shell state - measured data arrives in Phase 5</small>
        </div>
        <div className="panel strategy">
          <div className="panel-head">
            <div>
              <label>Strategy mix</label>
              <h2>What is running now</h2>
            </div>
            <em>
              <i className="online" /> Live
            </em>
          </div>
          <div className="donut">
            <div>
              <strong>18.3K</strong>
              <small>records</small>
            </div>
          </div>
          <div className="strategy-list">
            <div>
              <span>
                <i className="cyan" /> Jev
              </span>
              <b>71.4%</b>
            </div>
            <div>
              <span>
                <i className="green" /> Hybrid
              </span>
              <b>19.8%</b>
            </div>
            <div>
              <span>
                <i className="amber" /> LLM
              </span>
              <b>8.8%</b>
            </div>
          </div>
          <small className="note">Distribution will reflect active benchmark runs.</small>
        </div>
      </section>
      <section className="panel recent">
        <div className="panel-head">
          <div>
            <label>Experiment history</label>
            <h2>Recent runs</h2>
          </div>
          <NavLink to="/runs">View all runs &rarr;</NavLink>
        </div>
        <div className="run-table">
          <div className="run-row head">
            <span>Run</span>
            <span>Dataset</span>
            <span>Strategy</span>
            <span>Status</span>
            <span>Records</span>
            <span>Created</span>
          </div>
          <Run
            id="RUN-8F2A"
            dataset="support-inbox-q3"
            strategy="Hybrid"
            status="Running"
            records="12,400 / 50,000"
            created="2 min ago"
          />
          <Run
            id="RUN-7C91"
            dataset="support-inbox-q3"
            strategy="Jev"
            status="Running"
            records="5,891 / 50,000"
            created="7 min ago"
          />
          <Run
            id="RUN-6B20"
            dataset="billing-evals-v2"
            strategy="LLM"
            status="Completed"
            records="8,000 / 8,000"
            created="Yesterday"
          />
        </div>
      </section>
    </Shell>
  );
}

function Metric({
  label,
  value,
  meta,
  icon,
}: {
  label: string;
  value: string;
  meta: string;
  icon: React.ReactNode;
}) {
  return (
    <div className="metric">
      <div className="metric-icon">{icon}</div>
      <span>{label}</span>
      <strong>{value}</strong>
      <small>{meta}</small>
    </div>
  );
}

function Run({
  id,
  dataset,
  strategy,
  status,
  records,
  created,
}: {
  id: string;
  dataset: string;
  strategy: string;
  status: string;
  records: string;
  created: string;
}) {
  return (
    <div className="run-row">
      <span className="run-id">{id}</span>
      <span>{dataset}</span>
      <span>
        <b className={`tag ${strategy.toLowerCase()}`}>{strategy}</b>
      </span>
      <span className={`status ${status.toLowerCase()}`}>
        <i />
        {status}
      </span>
      <span>{records}</span>
      <span className="muted">{created}</span>
    </div>
  );
}

function Placeholder({ title, description }: { title: string; description: string }) {
  return (
    <Shell>
      <header className="topbar">
        <div>
          <label>JevScale / workspace</label>
          <h1>{title}</h1>
          <p>{description}</p>
        </div>
      </header>
      <div className="empty">
        <div>
          <Flask size={24} />
        </div>
        <h2>This surface is ready for a later phase</h2>
        <p>The route is wired into the control plane.</p>
      </div>
    </Shell>
  );
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Dashboard />} />
      <Route
        path="/datasets"
        element={
          <Shell>
            <DatasetsPage />
          </Shell>
        }
      />
      <Route
        path="/experiments/new"
        element={
          <Shell>
            <NewExperiment />
          </Shell>
        }
      />
      <Route
        path="/classifications"
        element={
          <Shell>
            <ClassificationsPlayground />
          </Shell>
        }
      />
      <Route
        path="/runs"
        element={
          <Placeholder
            title="Active runs"
            description="Monitor every benchmark currently queued, running, paused, or finishing."
          />
        }
      />
      <Route
        path="/analytics"
        element={
          <Placeholder
            title="Analytics"
            description="Measure latency, throughput, cost, quality, confidence, and reliability."
          />
        }
      />
      <Route
        path="/comparison"
        element={
          <Placeholder
            title="Benchmark comparison"
            description="Compare Jev, LLM, and Hybrid runs on the same research frame."
          />
        }
      />
      <Route
        path="/settings"
        element={
          <Placeholder
            title="Settings"
            description="Manage provider configuration, pricing assumptions, and workspace defaults."
          />
        }
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
