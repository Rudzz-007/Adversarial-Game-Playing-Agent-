/**
 * API Service layer for backend communication.
 * Communicates with FastAPI backend conforming to PRD §12 contracts and error schemas.
 */

const API_BASE = 'http://localhost:8000';

/**
 * Check backend health status.
 * Tries canonical /api/health with fallback to /health.
 */
export async function checkHealth() {
  try {
    const res = await fetch(`${API_BASE}/api/health`, {
      method: 'GET',
      headers: { Accept: 'application/json' },
    });
    if (res.ok) {
      const data = await res.json();
      return data.status === 'ok';
    }
  } catch {
    // Try fallback
  }

  try {
    const fallback = await fetch(`${API_BASE}/health`, {
      method: 'GET',
      headers: { Accept: 'application/json' },
    });
    if (fallback.ok) {
      const data = await fallback.json();
      return data.status === 'ok';
    }
  } catch {
    // Both endpoints unreachable
  }

  return false;
}

/**
 * Fetch catalog of available AI agents and metadata from GET /api/agents.
 */
export async function fetchAgents() {
  try {
    const res = await fetch(`${API_BASE}/api/agents`, {
      method: 'GET',
      headers: { Accept: 'application/json' },
    });
    if (!res.ok) {
      throw new Error(`Failed to fetch agents: HTTP ${res.status}`);
    }
    const data = await res.json();
    return data.agents || [];
  } catch (error) {
    console.warn('Failed to load agent catalog:', error.message);
    return [];
  }
}

/**
 * Request an AI move from POST /api/ai-move.
 * Preserves exact existing success contract: returns { column, row, telemetry, latencyMs }.
 * Measures real round-trip latency in milliseconds.
 *
 * @param {number[][]} board - Current 6x7 board grid.
 * @param {number} depth - Search depth (2, 4, 6).
 * @param {string} agent - Algorithm ID ('minimax', 'random', 'greedy', 'alphabeta', 'optimized', 'mcts').
 * @param {number|null} seed - Optional integer seed for reproducible random agent.
 * @param {number|null} iterations - Optional integer iteration budget for MCTS.
 * @returns {Promise<{ column: number, row: number, telemetry?: object, latencyMs: number }>}
 */
export async function fetchAIMove(board, depth = 4, agent = 'minimax', seed = null, iterations = null) {
  const startTime = performance.now();

  try {
    const payload = { board, depth, agent };
    if (seed !== null && seed !== undefined) {
      payload.seed = seed;
    }
    if (iterations !== null && iterations !== undefined) {
      payload.iterations = iterations;
    }

    const response = await fetch(`${API_BASE}/api/ai-move`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
      },
      body: JSON.stringify(payload),
    });

    const latencyMs = Math.round(performance.now() - startTime);

    if (!response.ok) {
      let errorCode = 'API_ERROR';
      let errorMessage = `Server returned status ${response.status}`;

      try {
        const errorJson = await response.json();
        if (errorJson && errorJson.error) {
          errorCode = errorJson.error.code || errorCode;
          errorMessage = errorJson.error.message || errorMessage;
        }
      } catch {
        // Response was not JSON
      }

      const err = new Error(errorMessage);
      err.code = errorCode;
      err.status = response.status;
      throw err;
    }

    const data = await response.json();
    return {
      column: data.column,
      row: data.row,
      telemetry: data.telemetry || null,
      latencyMs,
    };
  } catch (error) {
    if (!error.code) {
      error.code = 'NETWORK_ERROR';
      error.message = error.message || 'Network error: could not connect to backend server.';
    }
    throw error;
  }
}