import { NavLink, Navigate, Route, Routes } from "react-router-dom";
import DatasetsPage from "../pages/DatasetsPage";
import ClassificationsPlayground from "../pages/ClassificationsPlayground";
import {
  Database,
  Flask,
  Lightning,
} from "@phosphor-icons/react";

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
            <small>Decision Systems Lab</small>
          </div>
        </div>

        <nav aria-label="Primary navigation">
          <NavLink
            to="/"
            end
            className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`}
          >
            <Lightning size={18} weight="fill" />
            <span>Benchmark & Gmail</span>
          </NavLink>
          <NavLink
            to="/datasets"
            className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`}
          >
            <Database size={18} />
            <span>Dataset Pipeline</span>
          </NavLink>
        </nav>

        <footer>
          <div>
            <i className="online" /> Backend Active
          </div>
          <p className="text-[11px] text-zinc-500 mt-2">
            Phase 4: Real Gmail + LLM Baseline
          </p>
        </footer>
      </aside>
      <main className="main-content">{children}</main>
    </div>
  );
}

export default function App() {
  return (
    <Routes>
      <Route
        path="/"
        element={
          <Shell>
            <ClassificationsPlayground />
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
        path="/datasets"
        element={
          <Shell>
            <DatasetsPage />
          </Shell>
        }
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
