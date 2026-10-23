import { useState, useEffect } from 'react';
import { fetchAgents } from '../services/api.js';

export function GameControls({
  gameMode,
  onGameModeChange,
  depth,
  onDepthChange,
  iterations,
  onIterationsChange,
  startingPlayer,
  onStartingPlayerChange,
  selectedAlgorithm,
  onAlgorithmChange,
  onReset,
  disabled,
}) {
  const [agentsList, setAgentsList] = useState([]);

  useEffect(() => {
    let isMounted = true;
    fetchAgents().then((agents) => {
      if (isMounted && agents.length > 0) {
        setAgentsList(agents);
      }
    });
    return () => {
      isMounted = false;
    };
  }, []);

  const defaultAgents = [
    { id: 'minimax', name: 'Minimax Agent' },
    { id: 'random', name: 'Random Agent' },
    { id: 'greedy', name: 'Greedy Agent' },
    { id: 'alphabeta', name: 'Alpha-Beta Pruning Agent' },
    { id: 'optimized', name: 'Optimized Alpha-Beta Agent' },
    { id: 'mcts', name: 'Monte Carlo Tree Search (UCT)' },
  ];

  const displayAgents = agentsList.length > 0 ? agentsList : defaultAgents;

  return (
    <div className="game-controls-panel">
      <div className="control-group">
        <label htmlFor="mode-select" className="control-label">
          Game Mode
        </label>
        <select
          id="mode-select"
          className="control-select"
          value={gameMode}
          onChange={(e) => onGameModeChange(e.target.value)}
          disabled={disabled}
        >
          <option value="human_vs_ai">Human vs AI</option>
          <option value="human_vs_human">Pass & Play (2 Players)</option>
        </select>
      </div>

      {gameMode === 'human_vs_ai' && (
        <>
          <div className="control-group">
            <label htmlFor="algo-select" className="control-label">
              AI Algorithm
            </label>
            <select
              id="algo-select"
              className="control-select"
              value={selectedAlgorithm}
              onChange={(e) => onAlgorithmChange(e.target.value)}
              disabled={disabled}
            >
              {displayAgents.map((agent) => {
                const isActive = [
                  'minimax',
                  'random',
                  'greedy',
                  'alphabeta',
                  'optimized',
                  'mcts',
                ].includes(agent.id);
                const label = isActive ? `${agent.name} (Active)` : `${agent.name} (Phase 6)`;
                return (
                  <option key={agent.id} value={agent.id} disabled={!isActive}>
                    {label}
                  </option>
                );
              })}
            </select>
          </div>

          <div className="control-group">
            <label htmlFor="difficulty-select" className="control-label">
              AI Difficulty
            </label>
            {selectedAlgorithm === 'mcts' ? (
              <select
                id="difficulty-select"
                className="control-select"
                value={iterations || 1000}
                onChange={(e) => onIterationsChange?.(Number(e.target.value))}
                disabled={disabled}
              >
                <option value={200}>Easy (200 Iterations)</option>
                <option value={1000}>Medium (1,000 Iterations)</option>
                <option value={3000}>Hard (3,000 Iterations)</option>
              </select>
            ) : selectedAlgorithm === 'random' || selectedAlgorithm === 'greedy' ? (
              <select
                id="difficulty-select"
                className="control-select"
                value={1}
                disabled
              >
                <option value={1}>Standard (Baseline)</option>
              </select>
            ) : (
              <select
                id="difficulty-select"
                className="control-select"
                value={depth}
                onChange={(e) => onDepthChange(Number(e.target.value))}
                disabled={disabled}
              >
                <option value={2}>Easy (Search Depth 2)</option>
                <option value={4}>Medium (Search Depth 4)</option>
                <option value={6}>Hard (Search Depth 6)</option>
              </select>
            )}
          </div>

          <div className="control-group">
            <label htmlFor="starter-select" className="control-label">
              Starting Player
            </label>
            <select
              id="starter-select"
              className="control-select"
              value={startingPlayer}
              onChange={(e) => onStartingPlayerChange(Number(e.target.value))}
              disabled={disabled}
            >
              <option value={1}>Human First (Player 1 — Red)</option>
              <option value={2}>AI First (Player 2 — Yellow)</option>
            </select>
          </div>
        </>
      )}

      <div className="control-actions">
        <button
          className="btn-reset"
          onClick={onReset}
          disabled={disabled}
          aria-label="Start a new Connect Four game"
        >
          New Game / Reset
        </button>
      </div>
    </div>
  );
}
