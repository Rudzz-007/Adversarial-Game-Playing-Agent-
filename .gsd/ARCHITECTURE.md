# Architecture

> Updated on 2026-10-23 (Incorporating PRD v1.0 and Planning Clarifications)

## Overview

Connect Four adversarial game-playing system comprising a React 19 + Vite frontend and a Python + FastAPI backend featuring modular baseline and adversarial search algorithms (Random, Greedy, Minimax, Alpha-Beta, Optimized Alpha-Beta, MCTS/UCT) and an empirical benchmarking engine.

```
┌────────────────────────────────────────────────────────┐
│      Frontend (React 19 + Vite) - Port 5173            │
│   • Multi-View Navigation: State-Based Switching       │
│     ('home', 'game', 'analytics')                      │
│   • Board UI, Piece Drop Animations, Win Highlights    │
│   • Telemetry Panel (real-time empirical metrics)      │
│   • Benchmark & Comparison Dashboard (CSV/JSON export) │
└────────────────────────┬───────────────────────────────┘
                         │ JSON REST API
                         ▼
┌────────────────────────────────────────────────────────┐
│      Backend API Server (FastAPI + Uvicorn) - Port 8000│
│   • Canonical Health: GET /api/health                  │
│   • Compatibility Health: GET /health                  │
│   • Game Sessions: /api/game/new, /move, /ai-move      │
│   • Metadata & Benchmarks: /api/agents, /benchmark     │
│   • Standardized Error Envelope: {"error": {...}}      │
│   • In-Memory Session & Tournament Manager             │
└───────────┬────────────────────────────────┬───────────┘
            │                                │
            ▼                                ▼
┌────────────────────────┐      ┌────────────────────────┐
│      Game Engine       │      │   Modular AI Agents    │
│ • 6x7 Grid Board       │      │ • BaseAgent Interface  │
│ • Gravity Piece Drop   │      │ • Random, Greedy       │
│ • 4-in-a-row Win Check │      │ • Minimax, Alpha-Beta  │
│ • Full-Board Draw Check│      │ • Optimized AB, MCTS   │
│ • Coordinate Reporting │      │ • Explicit Telemetry   │
└────────────────────────┘      └────────────────────────┘
```

## Target Component Structure

### 1. Frontend Layer (`frontend/src/`)
- **Navigation Architecture**: State-based navigation managed via `activePage` state (`'home'`, `'game'`, `'analytics'`) in `App.jsx`, avoiding external routing dependencies for a lean MVP.
- **Pages**:
  - `HomePage`: Product overview, algorithm introduction cards, quick start buttons.
  - `GamePage`: $7 \times 6$ board, game controls (New Game, Restart, Human vs AI, Human vs Human, AI vs AI), difficulty options, and live metrics panel.
  - `AnalyticsPage`: Head-to-head tournament runner, outcome charts, performance statistics, and CSV/JSON export.
- **Components**: `Navbar`, `GameBoard`, `GameCell`, `GameControls`, `AgentSelector`, `GameStatus`, `MetricsPanel`, `BenchmarkCharts`.
- **Services & Hooks**: `services/api.js` client and `hooks/useGame.js` state coordinator.

### 2. Backend Layer (`backend/app/`)
- **API Routers (`api/`)**:
  - `game_routes.py`: Game session creation, human moves, AI moves, and state retrieval.
  - `ai_routes.py`: Agent metadata, descriptions, and configuration options.
  - `benchmark_routes.py`: Tournament execution and status polling.
- **Core Domain (`core/`)**:
  - `game_engine.py`: Immutable board evaluations, piece drops, legal moves, win coordinate extraction, and draw checks.
  - `game_state.py`: Game session representation with move history.
  - `validation.py`: Turn, column, and terminal state validators.
- **Agent Subsystem (`agents/`)**:
  - `base_agent.py`: Unified `BaseAgent` abstract class.
  - `random_agent.py`, `greedy_agent.py`, `minimax_agent.py`, `alphabeta_agent.py`, `optimized_agent.py`, `mcts_agent.py`.
- **Services (`services/`)**: `game_service.py` (session store) and `benchmark_service.py` (automated match runner).
- **Schemas (`schemas/`)**: Pydantic models for all requests, responses, and the standardized error model.

---

## Architectural & Integration Standards

### Standardized Error Format (PRD §12.9)
All API endpoints return errors strictly adhering to:
```json
{
  "error": {
    "code": "INVALID_MOVE",
    "message": "The selected column is full."
  }
}
```
FastAPI exception handlers intercept `RequestValidationError`, `HTTPException`, and unhandled server errors to guarantee this schema and suppress internal tracebacks.

### Health Check Compatibility
- **Primary / Canonical**: `GET /api/health` returning `{"status": "ok"}`
- **Compatibility Alias**: `GET /health` returning `{"status": "ok"}`

### Telemetry Contract
AI move responses deliver algorithm-specific metrics while cleanly distinguishing measured zeros from inapplicable values:
- Inapplicable metrics are set to `null` and displayed in the frontend as `"—"` or `"N/A"`.
- Real zero values (such as `pruned_nodes: 0` or `transposition_hits: 0`) are preserved.
- The system presents concrete measurements and candidate move evaluations; it explicitly does not claim to expose complete internal reasoning traces.
