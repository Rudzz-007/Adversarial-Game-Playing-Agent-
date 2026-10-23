export function HomePage({ onStartPlaying }) {
  const algorithms = [
    {
      id: 'minimax',
      name: 'Minimax Agent',
      status: 'Active (Phase 3)',
      active: true,
      desc: 'Classical depth-limited adversarial search exhaustively exploring alternating maximizing and minimizing plies.',
    },
    {
      id: 'random',
      name: 'Random Agent',
      status: 'Phase 4 Baseline',
      active: false,
      desc: 'Selects uniformly at random from legal columns. Supports seeded pseudo-randomness for benchmark reproducibility.',
    },
    {
      id: 'greedy',
      name: 'Greedy Agent',
      status: 'Phase 4 Baseline',
      active: false,
      desc: 'One-ply heuristic agent prioritizing immediate 4-in-a-row victories and blocking opponent immediate threats.',
    },
    {
      id: 'alphabeta',
      name: 'Alpha-Beta Pruning',
      status: 'Phase 5 Search',
      active: false,
      desc: 'Minimax augmented with branch pruning. Computes identical minimax values while pruning provably suboptimal branches.',
    },
    {
      id: 'optimized',
      name: 'Optimized Alpha-Beta',
      status: 'Phase 5 Search',
      active: false,
      desc: 'High-performance engine featuring center-outward move ordering, transposition table caching, and early cutoffs.',
    },
    {
      id: 'mcts',
      name: 'MCTS / UCT',
      status: 'Phase 5 Simulation',
      active: false,
      desc: 'Monte Carlo Tree Search with selection, expansion, random rollout simulation, and backpropagation via UCB1.',
    },
  ];

  return (
    <div className="home-container">
      <section className="hero-section">
        <h1 className="hero-title">Adversarial Game-Playing Agent</h1>
        <p className="hero-subtitle">
          Connect Four AI laboratory implementing adversarial search, alpha-beta pruning, and
          Monte Carlo tree search against human and AI opponents.
        </p>
        <div className="hero-actions">
          <button className="btn-primary" onClick={onStartPlaying}>
            Start Playing
          </button>
        </div>
      </section>

      <section className="rules-section">
        <h2 className="section-title">Connect Four Rules</h2>
        <div className="rules-grid">
          <div className="rule-card">
            <div className="rule-number">1</div>
            <h3>Gravity Mechanism</h3>
            <p>Discs dropped into any of the 7 columns fall straight down to the lowest unoccupied cell.</p>
          </div>
          <div className="rule-card">
            <div className="rule-number">2</div>
            <h3>Four in a Row</h3>
            <p>The first player to connect 4 consecutive discs horizontally, vertically, or diagonally wins.</p>
          </div>
          <div className="rule-card">
            <div className="rule-number">3</div>
            <h3>Draw Invariant</h3>
            <p>If all 42 cells are filled with no 4-in-a-row, the game terminates in a draw. Win strictly precedes draw.</p>
          </div>
        </div>
      </section>

      <section className="algorithms-section">
        <h2 className="section-title">Modular AI Agents</h2>
        <div className="algorithms-grid">
          {algorithms.map((algo) => (
            <div key={algo.id} className={`algo-card ${algo.active ? 'algo-active' : ''}`}>
              <div className="algo-header">
                <h3>{algo.name}</h3>
                <span className={`algo-status-badge ${algo.active ? 'badge-active' : 'badge-deferred'}`}>
                  {algo.status}
                </span>
              </div>
              <p>{algo.desc}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
