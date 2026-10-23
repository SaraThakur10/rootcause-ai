
import { useEffect, useState } from "react";
import "./App.css";

type LogEntry = {
  timestamp: string;
  service: string;
  level: string;
  message: string;
};

type TopError = {
  message: string;
  service: string;
  count: number;
};

type Analysis = {
  total_logs: number;
  error_count: number;
  warning_count: number;
  critical_count: number;
  severity_counts: Record<string, number>;
  service_error_counts: Record<string, number>;
  top_errors: TopError[];
  logs: LogEntry[];
};

type Anomaly = {
  timestamp: string;
  total_logs: number;
  error_count: number;
  warning_count: number;
  active_services: number;
  error_rate: number;
  reasons: string[];
};

type AnomalyResult = {
  windows_analyzed: number;
  anomalies_detected: number;
  method: string;
  ml_status: string;
  anomalies: Anomaly[];
  notice?: string;
};

type Correlation = {
  anomaly_timestamp: string;
  anomaly_error_count: number;
  event_timestamp: string;
  event_service: string;
  event_type: string;
  version: string;
  description: string;
  time_difference_minutes: number;
  same_service: boolean;
  evidence: string;
  interpretation: string;
};

type CorrelationResult = {
  anomalies_analyzed: number;
  correlations_found: number;
  correlation_window_minutes: number;
  correlations: Correlation[];
  notice?: string;
};

type Hypothesis = {
  title: string;
  service: string;
  confidence: string;
  priority: string;
  evidence: string[];
  recommended_checks: string[];
  limitation: string;
};

type RootCauseResult = {
  anomalies_analyzed: number;
  deployment_correlations: number;
  hypotheses_generated: number;
  hypotheses: Hypothesis[];
  notice?: string;
};

type InvestigationResult = {
  dataset_name: string;
  analysis: Analysis;
  anomalies: AnomalyResult;
  correlation: CorrelationResult;
  root_cause: RootCauseResult;
  notice?: string;
};

const API_URL = "http://127.0.0.1:8000";

async function getJson<T>(url: string): Promise<T> {
  const response = await fetch(url);

  const result = await response.json();

  if (!response.ok) {
    throw new Error(
      result.detail || `Request failed with status ${response.status}`
    );
  }

  return result as T;
}

function App() {
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [levelFilter, setLevelFilter] = useState("ALL");
  const [uploadName, setUploadName] = useState("");
  const [currentFile, setCurrentFile] = useState<File | null>(null);

  const [anomalyResult, setAnomalyResult] =
    useState<AnomalyResult | null>(null);
  const [correlationResult, setCorrelationResult] =
    useState<CorrelationResult | null>(null);
  const [rootCauseResult, setRootCauseResult] =
    useState<RootCauseResult | null>(null);

  const [investigationLoading, setInvestigationLoading] = useState(false);
  const [investigationError, setInvestigationError] = useState("");


  function applyInvestigationResult(result: InvestigationResult) {
    setAnalysis(result.analysis);
    setAnomalyResult(result.anomalies);
    setCorrelationResult(result.correlation);
    setRootCauseResult(result.root_cause);
  }

  async function loadSample() {
    setLoading(true);
    setInvestigationLoading(true);
    setError("");
    setInvestigationError("");

    try {
      const result = await getJson<InvestigationResult>(
        `${API_URL}/api/investigation/sample`
      );

      applyInvestigationResult(result);
      setCurrentFile(null);
      setUploadName("Sample dataset");
      setSearch("");
      setLevelFilter("ALL");
    } catch (err) {
      const message =
        err instanceof Error
          ? err.message
          : "Could not load the sample investigation.";

      setError(message);
      setInvestigationError(message);
    } finally {
      setLoading(false);
      setInvestigationLoading(false);
    }
  }

  async function uploadCSV(file: File) {
    setLoading(true);
    setInvestigationLoading(true);
    setError("");
    setInvestigationError("");

    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch(
        `${API_URL}/api/investigation/analyze`,
        {
          method: "POST",
          body: formData,
        }
      );

      const result = await response.json();

      if (!response.ok) {
        throw new Error(
          result.detail || "CSV investigation failed."
        );
      }

      applyInvestigationResult(result as InvestigationResult);
      setCurrentFile(file);
      setUploadName(file.name);
      setSearch("");
      setLevelFilter("ALL");
    } catch (err) {
      const message =
        err instanceof Error
          ? err.message
          : "Could not investigate the CSV file.";

      setError(message);
      setInvestigationError(message);
    } finally {
      setLoading(false);
      setInvestigationLoading(false);
    }
  }

  async function loadInvestigationData() {
    await refreshAll();
  }

  async function refreshAll() {
    if (currentFile) {
      await uploadCSV(currentFile);
    } else {
      await loadSample();
    }
  }

  useEffect(() => {
    void loadSample();
  }, []);

 
  const visibleLogs = (analysis?.logs ?? []).filter((log) => {
    const logLevel = String(log.level ?? "").trim().toUpperCase();
    const selectedLevel = String(levelFilter).trim().toUpperCase();

    const matchesLevel =
      selectedLevel === "ALL" || logLevel === selectedLevel;

    const searchText =
      `${log.timestamp} ${log.service} ${log.level} ${log.message}`
        .toLowerCase();

    return matchesLevel && searchText.includes(search.toLowerCase());
  });

  const services = Object.entries(analysis?.service_error_counts ?? {});
  const maxServiceErrors = Math.max(
    1,
    ...services.map(([, count]) => count)
  );

  return (
    <main className="app">
      <header className="topbar">
        <div className="brand">
          <div className="brand-icon">RC</div>
          <div>
            <h1>RootCause AI</h1>
            <p>Production Incident Investigator</p>
          </div>
        </div>

        <div className="header-actions">
          <span className="live-indicator">API CONNECTED</span>
          <button
            className="secondary-button"
            onClick={() => void refreshAll()}
            disabled={loading || investigationLoading}
          >
            Refresh dashboard
          </button>
        </div>
      </header>

      <section className="hero">
        <p className="eyebrow">OBSERVABILITY INTELLIGENCE</p>
        <h2>Understand incidents.<br />Find the root cause.</h2>
        <p className="hero-description">
          Explore application logs, detect unusual activity, correlate
          operational changes, and investigate possible root causes
          using supporting evidence.
        </p>

        <label className="upload-button">
          {loading ? "Processing..." : "Upload CSV logs"}
          <input
            type="file"
            accept=".csv,text/csv"
            disabled={loading}
            onChange={(event) => {
              const file = event.target.files?.[0];
              if (file) void uploadCSV(file);
              event.target.value = "";
            }}
          />
        </label>

        <span className="dataset-name">
          Current log dataset: {uploadName || "Loading..."}
        </span>
      </section>

      {error && (
        <div className="error-banner" role="alert">
          <strong>Log analysis failed:</strong> {error}
          <button className="text-button" onClick={() => void loadSample()}>
            Load sample data
          </button>
        </div>
      )}

      <section className="stats">
        <article className="stat-card">
          <span className="stat-label">Total log entries</span>
          <strong>{analysis?.total_logs ?? "—"}</strong>
          <p>Records processed</p>
        </article>

        <article className="stat-card">
          <span className="stat-label">Errors + critical</span>
          <strong>{analysis?.error_count ?? "—"}</strong>
          <p>Events requiring investigation</p>
        </article>

        <article className="stat-card">
          <span className="stat-label">Warnings</span>
          <strong>{analysis?.warning_count ?? "—"}</strong>
          <p>Potentially concerning events</p>
        </article>

        <article className="stat-card">
          <span className="stat-label">Critical events</span>
          <strong>{analysis?.critical_count ?? "—"}</strong>
          <p>Highest severity level</p>
        </article>
      </section>

      <section className="analysis-grid">
        <article className="panel">
          <p className="eyebrow">SERVICE HEALTH SIGNALS</p>
          <h3>Error counts by service</h3>

          {services.length === 0 ? (
            <p className="muted">No error events in this dataset.</p>
          ) : (
            <div className="service-list">
              {services.map(([service, count]) => (
                <div className="service-row" key={service}>
                  <div className="service-label">
                    <span>{service}</span>
                    <strong>{count}</strong>
                  </div>
                  <div className="bar-track">
                    <div
                      className="bar-fill"
                      style={{
                        width: `${(count / maxServiceErrors) * 100}%`,
                      }}
                    />
                  </div>
                </div>
              ))}
            </div>
          )}
        </article>

        <article className="panel">
          <p className="eyebrow">REPEATED FAILURES</p>
          <h3>Most common errors</h3>

          {(analysis?.top_errors ?? []).length === 0 ? (
            <p className="muted">No error messages found.</p>
          ) : (
            <div className="top-error-list">
              {analysis?.top_errors.map((item, index) => (
                <div
                  className="top-error"
                  key={`${item.service}-${item.message}`}
                >
                  <div className="error-rank">{index + 1}</div>
                  <div className="error-details">
                    <strong>{item.message}</strong>
                    <span>{item.service}</span>
                  </div>
                  <span className="error-count">{item.count}×</span>
                </div>
              ))}
            </div>
          )}
        </article>
      </section>

      <section className="investigation-section">
        <div className="section-heading">
          <p className="eyebrow">AI-ASSISTED INVESTIGATION</p>
          <h2>Incident investigation</h2>
          <p className="muted">
            These panels use the same log dataset as the summary above.
            Deployment events come from the saved deployment events file,
            so correlations depend on matching timestamps and services.
          </p>
          <button
            className="secondary-button"
            onClick={() => void loadInvestigationData()}
            disabled={investigationLoading}
          >
            {investigationLoading ? "Analyzing..." : "Refresh investigation"}
          </button>
        </div>

        {investigationError && (
          <div className="error-banner" role="alert">
            <strong>Investigation data unavailable:</strong>{" "}
            {investigationError}
            <p className="muted">
              Check that the backend is running and the three investigation
              endpoints are responding.
            </p>
            <button
              className="text-button"
              onClick={() => void loadInvestigationData()}
            >
              Retry
            </button>
          </div>
        )}

        {investigationLoading && !anomalyResult && (
          <article className="panel">
            <p className="muted">Loading investigation results...</p>
          </article>
        )}

        {anomalyResult && (
          <article className="panel investigation-panel">
            <p className="eyebrow">PHASE 4 · ANOMALY DETECTION</p>
            <h3>Detected unusual activity</h3>

            <div className="mini-stats">
              <div>
                <span className="stat-label">Windows analyzed</span>
                <strong>{anomalyResult.windows_analyzed}</strong>
              </div>
              <div>
                <span className="stat-label">Anomalies flagged</span>
                <strong>{anomalyResult.anomalies_detected}</strong>
              </div>
              <div>
                <span className="stat-label">ML status</span>
                <strong className="small-value">
                  {anomalyResult.ml_status}
                </strong>
              </div>
            </div>

            <p className="muted">Method: {anomalyResult.method}</p>

            {anomalyResult.anomalies.length === 0 ? (
              <p className="empty-state">
                No anomaly windows were flagged in this dataset.
              </p>
            ) : (
              <div className="result-list">
                {anomalyResult.anomalies.map((item) => (
                  <div
                    className="result-item"
                    key={item.timestamp}
                  >
                    <div className="result-item-heading">
                      <strong>{item.timestamp}</strong>
                      <span className="priority priority-high">
                        Flagged
                      </span>
                    </div>
                    <p className="muted">
                      {item.error_count} errors · {item.total_logs} logs ·{" "}
                      {(item.error_rate * 100).toFixed(1)}% error rate
                    </p>
                    <ul>
                      {item.reasons.map((reason) => (
                        <li key={reason}>{reason}</li>
                      ))}
                    </ul>
                  </div>
                ))}
              </div>
            )}

            {anomalyResult.notice && (
              <p className="notice">{anomalyResult.notice}</p>
            )}
          </article>
        )}

        {correlationResult && (
          <article className="panel investigation-panel">
            <p className="eyebrow">PHASE 5 · EVENT CORRELATION</p>
            <h3>Deployment and configuration events</h3>
            <p className="muted">
              {correlationResult.correlations_found} temporal correlations
              found within a ±{correlationResult.correlation_window_minutes}
              -minute window.
            </p>

            {correlationResult.correlations.length === 0 ? (
              <p className="empty-state">
                No matching anomaly and event timestamps were found.
              </p>
            ) : (
              <div className="result-list">
                {correlationResult.correlations.map((item, index) => (
                  <div
                    className="result-item"
                    key={`${item.anomaly_timestamp}-${item.event_timestamp}-${index}`}
                  >
                    <div className="result-item-heading">
                      <strong>{item.event_type}</strong>
                      <span
                        className={
                          item.same_service
                            ? "priority priority-medium"
                            : "priority"
                        }
                      >
                        {item.same_service
                          ? "Same service"
                          : "Service not matched"}
                      </span>
                    </div>
                    <p>{item.description}</p>
                    <p className="muted">
                      Service: {item.event_service} · Version: {item.version}
                    </p>
                    <p className="muted">
                      Event: {item.event_timestamp}
                    </p>
                    <p className="muted">
                      Anomaly: {item.anomaly_timestamp}
                    </p>
                    <p className="muted">
                      Time difference: {item.time_difference_minutes} minutes
                    </p>
                    <p className="notice">{item.interpretation}</p>
                  </div>
                ))}
              </div>
            )}

            {correlationResult.notice && (
              <p className="notice">{correlationResult.notice}</p>
            )}
          </article>
        )}

        {rootCauseResult && (
          <article className="panel investigation-panel">
            <p className="eyebrow">PHASE 6 · ROOT CAUSE HYPOTHESES</p>
            <h3>Investigation leads</h3>
            <p className="muted">
              {rootCauseResult.hypotheses_generated} hypotheses generated
              from available evidence.
            </p>

            {rootCauseResult.hypotheses.length === 0 ? (
              <p className="empty-state">
                No hypotheses met the current evidence rules. This does not
                necessarily mean the system has no incident.
              </p>
            ) : (
              <div className="result-list">
                {rootCauseResult.hypotheses.map((item, index) => (
                  <div
                    className="result-item"
                    key={`${item.title}-${item.service}-${index}`}
                  >
                    <div className="result-item-heading">
                      <strong>{item.title}</strong>
                      <span
                        className={`priority priority-${item.priority.toLowerCase()}`}
                      >
                        {item.priority} priority
                      </span>
                    </div>

                    <p className="muted">
                      Service: {item.service} · Evidence level:{" "}
                      {item.confidence}
                    </p>

                    <h4>Supporting evidence</h4>
                    <ul>
                      {item.evidence.map((evidence) => (
                        <li key={evidence}>{evidence}</li>
                      ))}
                    </ul>

                    <h4>Recommended checks</h4>
                    <ul>
                      {item.recommended_checks.map((check) => (
                        <li key={check}>{check}</li>
                      ))}
                    </ul>

                    <p className="notice">{item.limitation}</p>
                  </div>
                ))}
              </div>
            )}

            {rootCauseResult.notice && (
              <p className="notice">{rootCauseResult.notice}</p>
            )}
          </article>
        )}
      </section>

      <section className="panel log-panel">
        <div className="table-heading">
          <div>
            <p className="eyebrow">RAW EVIDENCE</p>
            <h3>Application logs</h3>
            <p className="muted">
              Showing {visibleLogs.length} of {analysis?.total_logs ?? 0} records
            </p>
          </div>
        </div>

        <div className="filters">
          <input
            type="search"
            placeholder="Search service, message, timestamp..."
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            aria-label="Search logs"
          />

          <select
            value={levelFilter}
            onChange={(event) => setLevelFilter(event.target.value)}
            aria-label="Filter by severity"
          >
            <option value="ALL">All levels</option>
            <option value="DEBUG">Debug</option>
            <option value="INFO">Info</option>
            <option value="WARNING">Warning</option>
            <option value="ERROR">Error</option>
            <option value="CRITICAL">Critical</option>
          </select>
        </div>

        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Timestamp</th>
                <th>Service</th>
                <th>Severity</th>
                <th>Message</th>
              </tr>
            </thead>
            <tbody>
              {visibleLogs.map((log, index) => (
                <tr key={`${log.timestamp}-${index}`}>
                  <td className="timestamp">{log.timestamp}</td>
                  <td>{log.service}</td>
                  <td>
                    <span
                      className={`severity severity-${log.level.toLowerCase()}`}
                    >
                      {log.level}
                    </span>
                  </td>
                  <td>{log.message}</td>
                </tr>
              ))}

              {visibleLogs.length === 0 && (
                <tr>
                  <td colSpan={4} className="empty-state">
                    No logs match your filters.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

      <footer>
        RootCause AI · Incident investigation dashboard · 0.3.0
      </footer>
    </main>
  );
}

export default App;

      