export function MetricsPanel({ telemetry, gameMode }) {
  if (gameMode !== 'human_vs_ai') {
    return (
      <div className="metrics-panel metrics-inactive">
        <h3 className="metrics-title">Real-Time AI Telemetry</h3>
        <p className="metrics-empty-hint">
          Telemetry is disabled in Pass & Play (Human vs Human) mode.
        </p>
      </div>
    );
  }

  const { decisionTimeMs, searchDepth, nodesEvaluated, prunedNodes, algorithmName } = telemetry;

  return (
    <div className="metrics-panel">
      <div className="metrics-header">
        <h3 className="metrics-title">Real-Time AI Telemetry</h3>
        <span className="metrics-algorithm-badge">{algorithmName}</span>
      </div>

      <div className="metrics-grid">
        <div className="metric-card">
          <span className="metric-label">Decision Time</span>
          <span className="metric-value">
            {decisionTimeMs !== null ? `${decisionTimeMs} ms` : '—'}
          </span>
          <span className="metric-hint">Client round-trip</span>
        </div>

        <div className="metric-card">
          <span className="metric-label">Search Horizon</span>
          <span className="metric-value">
            {searchDepth !== null ? `Depth ${searchDepth}` : '—'}
          </span>
          <span className="metric-hint">Lookahead plies</span>
        </div>

        <div className="metric-card metric-deferred">
          <span className="metric-label">Nodes Evaluated</span>
          <span className="metric-value">
            {nodesEvaluated !== null ? nodesEvaluated.toLocaleString() : 'N/A'}
          </span>
          <span className="metric-hint">Phase 4/5 agent metric</span>
        </div>

        <div className="metric-card metric-deferred">
          <span className="metric-label">Pruned Branches</span>
          <span className="metric-value">
            {prunedNodes !== null ? prunedNodes.toLocaleString() : 'N/A'}
          </span>
          <span className="metric-hint">Phase 4/5 agent metric</span>
        </div>
      </div>

      <p className="metrics-footnote">
        PRD §10 Integrity: Inapplicable search tree statistics display <code>N/A</code>. Values are never fabricated.
      </p>
    </div>
  );
}
