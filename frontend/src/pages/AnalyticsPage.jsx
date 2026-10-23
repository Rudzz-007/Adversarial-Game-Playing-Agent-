export function AnalyticsPage() {
  return (
    <div className="analytics-container">
      <div className="analytics-header">
        <h1 className="analytics-title">Benchmarking & Analytics Dashboard</h1>
        <p className="analytics-subtitle">
          Automated tournament evaluation, search-tree efficiency, and comparative telemetry.
        </p>
      </div>

      <div className="analytics-phase-notice">
        <div className="notice-icon">📊</div>
        <div className="notice-text">
          <h3>Phase 6 Feature Preview</h3>
          <p>
            The full benchmarking tournament suite will be unlocked in Phase 6, executing automated
            round-robin matches between all 6 AI agents with exportable CSV and JSON reports.
          </p>
        </div>
      </div>

      <div className="analytics-grid">
        <div className="analytics-card">
          <div className="card-badge">PRD §11.1</div>
          <h3>Head-to-Head Tournaments</h3>
          <p>
            Executes N-game matches between selected agent pairings with alternating first-mover
            advantages to eliminate bias.
          </p>
          <ul className="card-features">
            <li>Win / Draw / Loss aggregates</li>
            <li>First-move win rate analysis</li>
            <li>Configurable match counts (10 to 100)</li>
          </ul>
        </div>

        <div className="analytics-card">
          <div className="card-badge">PRD §11.2</div>
          <h3>Search Tree Analytics</h3>
          <p>
            Empirical comparison of node expansion efficiency across Minimax, Alpha-Beta, Optimized,
            and MCTS algorithms.
          </p>
          <ul className="card-features">
            <li>Nodes evaluated per move</li>
            <li>Alpha-Beta pruning percentage</li>
            <li>Transposition cache hit rate</li>
          </ul>
        </div>

        <div className="analytics-card">
          <div className="card-badge">PRD §11.3</div>
          <h3>Export & Telemetry</h3>
          <p>
            Download structured datasets conforming to the PRD §12 schema for offline analysis and
            academic reporting.
          </p>
          <ul className="card-features">
            <li>Complete CSV match logs</li>
            <li>Hierarchical JSON telemetry export</li>
            <li>Move-by-move timing breakdowns</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
