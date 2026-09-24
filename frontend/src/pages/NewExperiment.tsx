import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowRight, Database, Flask, Lightning } from "@phosphor-icons/react";
import { datasetApi, Dataset } from "../services/api";

export default function NewExperiment() {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [selected, setSelected] = useState("");

  useEffect(() => {
    datasetApi.list().then(setDatasets);
  }, []);

  const d = datasets.find((x) => x.id === selected);

  return (
    <div className="page space-y-6">
      <header className="topbar">
        <div>
          <label>JevScale / experiment control</label>
          <h1>New experiment</h1>
          <p>Choose the records that will become the input to a future decision benchmark.</p>
        </div>
      </header>

      {/* Phase 3 Jev Classification Playground Callout */}
      <div className="panel p-4 flex flex-wrap items-center justify-between gap-4 bg-[#0d1c1d] border border-[#203f3b]">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-[#14322e] text-[#79e8cf] flex items-center justify-center shrink-0">
            <Lightning size={20} weight="fill" />
          </div>
          <div>
            <strong className="text-xs text-[#e1f3ee] block">
              Jev Classification Engine is Active
            </strong>
            <span className="text-[11px] text-[#749691]">
              Test single emails and small batches interactively in the Jev Playground before launching benchmark runs.
            </span>
          </div>
        </div>
        <Link to="/classifications" className="primary-action-btn text-xs">
          Open Jev Playground <ArrowRight size={14} />
        </Link>
      </div>

      <section className="panel experiment-panel">
        <div className="panel-head">
          <div>
            <label>Dataset foundation</label>
            <h2>Select a dataset</h2>
          </div>
          <Flask size={24} color="#79e8cf" />
        </div>
        <select
          className="experiment-select"
          value={selected}
          onChange={(e) => setSelected(e.target.value)}
        >
          <option value="">Choose a saved dataset</option>
          {datasets.map((x) => (
            <option value={x.id} key={x.id}>
              {x.name} - {x.total_records.toLocaleString()} records
            </option>
          ))}
        </select>
        {d && (
          <div className="selected-dataset">
            <Database size={20} />
            <div>
              <strong>{d.name}</strong>
              <span>
                {d.total_records.toLocaleString()} records - {d.source_format.toUpperCase()} - subject:{" "}
                {d.subject_column} - body: {d.body_column}
              </span>
            </div>
            <ArrowRight size={18} />
          </div>
        )}
        {!datasets.length && (
          <div className="empty compact">
            <div>
              <Database size={22} />
            </div>
            <h2>No datasets available</h2>
            <p>Upload and map a dataset before configuring an experiment.</p>
          </div>
        )}
      </section>
    </div>
  );
}
