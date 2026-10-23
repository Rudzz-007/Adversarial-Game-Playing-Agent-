# SPEC.md — Project Specification

> **Project**: Adversarial Game-Playing Agent — Connect Four AI  
> **Status**: `FINALIZED`  
> **Primary Source of Truth**: `docs/Adversarial_Game_Playing_Agent_PRD.pdf` (v1.0)  
> **Planning Lock**: RELEASED (Approved for Phase Planning & Execution)

---

## 1. Vision
Build a reliable, interactive, educational full-stack web application that demonstrates classic and modern adversarial game-playing AI techniques through Connect Four (7 columns × 6 rows). The system pairs a responsive browser interface with a modular Python/FastAPI AI engine and an empirical benchmarking suite, enabling users to play against diverse AI agents, observe algorithmic decision-making, and quantitatively compare search efficiency and gameplay performance under controlled, reproducible conditions.

---

## 2. Goals

### 2.1 Primary Goals
1. **Authoritative Game Engine**: Deliver a robust 6×7 Connect Four engine with strict move validation, gravity piece dropping, comprehensive win detection (horizontal, vertical, positive diagonal, negative diagonal), and draw/tie detection.
2. **Modular AI Engine**: Implement a unified, extensible `BaseAgent` interface supporting baseline and adversarial search algorithms:
   - Random Baseline (with reproducible random seed support)
   - Greedy Agent (1-ply win-prioritization and threat-blocking)
   - Minimax (depth-limited recursive search)
   - Alpha-Beta Pruning (preserving minimax value with significant branch pruning)
   - Optimized Alpha-Beta (move ordering center-first, transposition table with Zobrist/board hashing, immediate-win cutoffs)
   - Monte Carlo Tree Search (MCTS) with Upper Confidence Bound for Trees (UCT)
3. **Interactive & Educational Frontend**: Create a modern React (Vite) interface featuring:
   - Central interactive game board with smooth animations, column hover states, and winning cell highlights.
   - Gameplay controls (Human vs AI, Human vs Human, AI vs AI; Restart, New Game, difficulty presets).
   - Real-time AI metric visualization (decision time in ms, nodes evaluated, pruned branches, depth, MCTS iterations/visit counts).
   - Lightweight state-based multi-page navigation across Home, Game, and Analytics views.
4. **Benchmarking & Analytics Suite**: Provide automated head-to-head evaluation alternating starting players, aggregating Win/Draw/Loss records, average decision times, and node metrics, with CSV/JSON export capability.
5. **Quality & Maintainability**: Maintain rigorous automated test suites (unit tests, API route tests, integration sanity tests) and clear architectural layering.

### 2.2 Educational Goals
- Demonstrate game-tree search principles and depth limits.
- Illustrate the quantitative efficiency gains of Alpha-Beta pruning over standard Minimax.
- Show the dramatic impact of move ordering and transposition caching on search branch reduction.
- Introduce simulation-based reasoning via MCTS/UCT, contrasting deterministic evaluation against random playout statistics.

---

## 3. Non-Goals (Out of Scope for Initial Release)
- **Online Multiplayer & Social**: No user accounts, authentication, chat, matchmaking, or social profiles.
- **Native Mobile Apps**: Desktop browser focus (responsive layout, but no standalone iOS/Android package).
- **Machine Learning / Neural Networks**: No deep reinforcement learning (AlphaZero/DQN) or neural network training.
- **Mandatory Database**: No external PostgreSQL dependency for MVP; state maintained in memory with clear API boundaries.
- **Distributed AI Computation**: All computations execute within the local FastAPI backend.

---

## 4. Target Users
- **Students & AI/ML Learners**: Seeking to understand how heuristic search, pruning, and Monte Carlo methods work in practice.
- **Strategy Game Enthusiasts & Casual Players**: Looking for a polished, challenging Connect Four opponent with adjustable difficulty.
- **Developers & Researchers**: Requiring an extensible testbed for comparing game-playing algorithms with reproducible benchmarks.

---

## 5. Functional Requirements (FR-01 to FR-12)

| ID | Title | Summary |
|---|---|---|
| **FR-01** | Game Board UI | 7 columns × 6 rows grid; distinct player colors; column hover highlight; piece drop animations; full-column locking; winning 4-in-a-row highlight; post-game lock. |
| **FR-02** | Game-State Management | Authoritative backend tracking of board matrix, active player (1 or 2), legal moves, move count, history, status (`active`, `won`, `draw`), and winning coordinates. |
| **FR-03** | Game Modes | Human vs AI (core), Human vs Human (local two-player), and AI vs AI (automated simulation/demonstration with pacing interval). |
| **FR-04** | AI Selection | Dropdown/selector supporting: Random, Greedy, Minimax, Alpha-Beta, Optimized Alpha-Beta, and MCTS/UCT. |
| **FR-05** | Difficulty Settings | Depth limits (Easy: 2 / shallow, Medium: 4 / greedy-moderate, Hard: 6 / alpha-beta, Expert: optimized alpha-beta / MCTS iteration budget). |
| **FR-06** | Move Legality Enforcement | Reject invalid columns (<0 or >=7), full columns, moves when game is terminal, wrong-player turns, and malformed requests with standard error payloads. |
| **FR-07** | Win & Draw Detection | Exhaustive detection of 4 consecutive matching pieces horizontally, vertically, positive diagonal, negative diagonal; full board without winner declared as Draw. |
| **FR-08** | Game Controls | "New Game" (resets state/metrics), "Restart" (resets board with same settings), undo functionality where appropriate, and pause/resume for AI vs AI. |
| **FR-09** | AI Telemetry & Visualization | Per-move telemetry: decision time (ms), nodes visited, pruning count, search depth, candidate scores, and MCTS iteration/visit statistics. Inapplicable fields returned as `null` and displayed as `N/A`. Concrete measurements only; no claim to expose a complete internal reasoning trace. |
| **FR-10** | Metrics Dashboard | Aggregate match metrics: W/D/L counters, win percentage, decision time percentiles (avg/median/max), search intensity, and comparative charts. |
| **FR-11** | Head-to-Head Benchmarking | Automated tournament harness between any two chosen agents over $N$ matches (alternating Player 1/2), logging outcomes, time, node metrics; exportable to CSV/JSON. |
| **FR-12** | Standardized Error Handling | Strict error response format: `{"error": {"code": "...", "message": "..."}}`. Backend suppresses stack traces. Frontend displays actionable feedback with safe recovery. |

---

## 6. Non-Functional Requirements (NFR)

- **NFR-01: Performance & Responsiveness**: AI decision latency bounded by depth/iteration limits; interactive moves feel instantaneous (<200ms for UI updates); long-running benchmarks executed without freezing the UI.
- **NFR-02: Correctness**: Zero tolerance for illegal moves or missed terminal states. Backend validation is authoritative.
- **NFR-03: Architectural Modularity**: Strict separation between core game logic (`core/`), agent algorithms (`agents/`), API orchestration (`api/`, `services/`), and frontend views (`components/`, `pages/`).
- **NFR-04: Usability & Aesthetic Design**: Technical modern dark theme (navy/charcoal background `#0b1120`, cyan/blue accents `#0ea5e9` & `#06b6d4`, high-contrast Red `#ef4444` and Yellow `#eab308` discs, crisp typography via Inter, subtle micro-interactions).
- **NFR-05: Testability**: Minimum 85% coverage on `core/` game logic and agent implementations; comprehensive API integration tests.
- **NFR-06: Security & Robustness**: All incoming payloads validated via Pydantic; backend errors transformed to standardized error responses; internal stack traces never exposed in HTTP responses.

---

## 7. System Architecture & Frontend Navigation

### 7.1 Component Architecture
```
┌────────────────────────────────────────────────────────┐
│             Frontend: React 19 + Vite                  │
│   • Navigation: Lightweight state-based view switching │
│     ('home' | 'game' | 'analytics')                    │
│   • Pages: HomePage, GamePage, AnalyticsPage           │
│   • Components: GameBoard, Controls, Status, Metrics   │
│   • State & API: useGame hook, API Client              │
└────────────────────────┬───────────────────────────────┘
                         │ JSON REST API
                         ▼
┌────────────────────────────────────────────────────────┐
│             Backend API: FastAPI (Python)              │
│   • Canonical Health: GET /api/health                  │
│   • Compat Health: GET /health                         │
│   • Standardized Exception Handlers (PRD §12.9)        │
│   • Routers: /api/game, /api/agents, /api/benchmark    │
│   • In-Memory Game Store & Benchmark Orchestration     │
└───────────┬────────────────────────────────┬───────────┘
            │                                │
            ▼                                ▼
┌────────────────────────┐      ┌────────────────────────┐
│   Core Game Engine     │      │   Modular AI Agents    │
│ • Board Matrix (6x7)   │      │ • BaseAgent Interface  │
│ • Drop Physics         │      │ • Random, Greedy       │
│ • Win/Draw Evaluator   │      │ • Minimax, Alpha-Beta  │
│ • Legal Move Validator │      │ • Optimized AB, MCTS   │
└────────────────────────┘      └────────────────────────┘
```

### 7.2 Frontend Navigation Strategy
To avoid heavyweight external routing dependencies while maintaining a lean bundle, the frontend will employ **React state-based navigation**:
- A root navigation bar provides tab switching between `'home'`, `'game'`, and `'analytics'`.
- Sub-components are rendered conditionally based on `activePage`.
- Fast, zero-bundle-overhead, and completely fulfills PRD §13 requirements.

### 7.3 Target Repository Structure (Incremental Migration)
```
Adversarial-Game-Playing-Agent-/
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   ├── app/
│   │   ├── api/
│   │   │   ├── game_routes.py
│   │   │   ├── ai_routes.py
│   │   │   └── benchmark_routes.py
│   │   ├── core/
│   │   │   ├── game_engine.py
│   │   │   ├── game_state.py
│   │   │   └── validation.py
│   │   ├── agents/
│   │   │   ├── base_agent.py
│   │   │   ├── random_agent.py
│   │   │   ├── greedy_agent.py
│   │   │   ├── minimax_agent.py
│   │   │   ├── alphabeta_agent.py
│   │   │   ├── optimized_agent.py
│   │   │   └── mcts_agent.py
│   │   ├── services/
│   │   │   ├── game_service.py
│   │   │   └── benchmark_service.py
│   │   └── schemas/
│   │       ├── game_schemas.py
│   │       └── benchmark_schemas.py
│   └── tests/
│       ├── test_game_engine.py
│       ├── test_agents.py
│       └── test_api.py
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   └── src/
│       ├── components/
│       │   ├── Navbar.jsx
│       │   ├── GameBoard.jsx
│       │   ├── GameCell.jsx
│       │   ├── GameControls.jsx
│       │   ├── AgentSelector.jsx
│       │   ├── GameStatus.jsx
│       │   ├── MetricsPanel.jsx
│       │   └── BenchmarkCharts.jsx
│       ├── pages/
│       │   ├── HomePage.jsx
│       │   ├── GamePage.jsx
│       │   └── AnalyticsPage.jsx
│       ├── services/
│       │   └── api.js
│       ├── hooks/
│       │   └── useGame.js
│       ├── App.jsx
│       ├── App.css
│       └── main.jsx
├── docs/
│   ├── Adversarial_Game_Playing_Agent_PRD.pdf
│   ├── API_SPECIFICATION.md
│   └── runbook.md
└── .gsd/
    ├── SPEC.md
    ├── REQUIREMENTS.md
    ├── ROADMAP.md
    ├── ARCHITECTURE.md
    └── STACK.md
```

---

## 8. AI Agent Specifications & Telemetry Contract

### 8.1 Shared `BaseAgent` Contract
```python
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Tuple

class BaseAgent(ABC):
    def __init__(self, name: str, player_id: int = 2):
        self.name = name
        self.player_id = player_id

    @abstractmethod
    def select_move(self, board: list[list[int]], **kwargs) -> Tuple[int, Dict[str, Any]]:
        """
        Returns:
            selected_column (int): column index 0-6
            metrics (dict): execution metrics adhering to the telemetry schema
        """
        pass
```

### 8.2 Telemetry Applicability Matrix
Metrics returned by agents must strictly distinguish between **measured zeros** and **inapplicable metrics** (`null`). Inapplicable metrics render as `N/A` in the UI:

| Metric | Random | Greedy | Minimax | Alpha-Beta | Optimized AB | MCTS / UCT |
|---|---|---|---|---|---|---|
| `decision_time_ms` | Measured | Measured | Measured | Measured | Measured | Measured |
| `nodes_evaluated` | `null` | `null` | Measured | Measured | Measured | `null` |
| `pruned_nodes` | `null` | `null` | `null` | Measured (can be 0) | Measured (can be 0) | `null` |
| `search_depth` | `null` | 1 | Configured | Configured | Configured | `null` |
| `transposition_hits` | `null` | `null` | `null` | `null` | Measured (can be 0) | `null` |
| `mcts_iterations` | `null` | `null` | `null` | `null` | `null` | Measured |
| `mcts_simulations` | `null` | `null` | `null` | `null` | `null` | Measured |
| `candidate_scores` | `null` | 1-ply scores | Minimax scores | AB scores | AB scores | Visit counts & win % |

#### Metric Definition Standards:
- **`nodes_evaluated`**: Strictly defined as the number of search-tree nodes evaluated by game-tree algorithms for which this metric is implemented (Minimax, Alpha-Beta, Optimized Alpha-Beta).
- **MCTS Metrics Separation**: MCTS iteration counts (`mcts_iterations`) and simulation/rollout counts (`mcts_simulations`) are discrete simulation metrics. They are strictly tracked independently and are **never** combined or confused with search-tree node counts.
- **Transparency Note**: Telemetry represents concrete empirical measurements and candidate scores. It does **not** claim to provide a full internal reasoning trace.

---

## 9. API Specification & Error Format

### 9.1 Standardized Error Format (PRD §12.9)
All API endpoints return errors according to the following strict schema:
```json
{
  "error": {
    "code": "INVALID_MOVE",
    "message": "The selected column is full."
  }
}
```

#### Standard Error Codes:
- `INVALID_MOVE`: Column out of range or selected column is full.
- `INVALID_TURN`: Move attempted out of turn.
- `GAME_TERMINAL`: Move attempted after game is won or drawn.
- `GAME_NOT_FOUND`: Specified `game_id` does not exist.
- `INVALID_CONFIG`: Unsupported agent, invalid depth, or invalid player settings.
- `VALIDATION_ERROR`: Malformed JSON or schema validation failure.
- `AI_TIMEOUT`: Search calculation exceeded allotted execution time.
- `INTERNAL_ERROR`: Unexpected internal server error (internal tracebacks suppressed).

### 9.2 Endpoint Summary
- `GET /api/health` — **Canonical** health check returning `{"status": "ok"}`
- `GET /health` — **Backward-compatible alias** returning `{"status": "ok"}`
- `GET /api/agents` — List available agents and parameter configurations
- `POST /api/game/new` — Create new game session (`mode`, `ai_agent`, `difficulty`, `starting_player`)
- `POST /api/game/{game_id}/move` — Submit human move `{ "column": int }`
- `POST /api/game/{game_id}/ai-move` — Trigger AI move calculation and update game state
- `GET /api/game/{game_id}` — Retrieve full current game state, winning coordinates, and move history
- `POST /api/benchmark/run` — Run automated tournament between agents
- `GET /api/benchmark/{benchmark_id}` — Retrieve benchmark progress or completed results

---

## 10. Success Criteria & Verification Checklist

- [ ] 6×7 Connect Four engine with 100% accurate win detection across all directions and ties.
- [ ] Backend tests passing with `pytest` for game rules, bounds, and edge cases.
- [ ] All 6 AI agents (Random, Greedy, Minimax, Alpha-Beta, Optimized Alpha-Beta, MCTS) operational and accessible via the API.
- [ ] Real-time telemetry displayed after each AI move with explicit `null`/`N/A` distinction.
- [ ] Multi-match benchmarking functional, generating win rate and search metrics with CSV/JSON export.
- [ ] Clean, responsive dark-themed UI with smooth drop animations, clear game status, and error notifications.
- [ ] Canonical `GET /api/health` and compatibility `GET /health` responding with `{"status": "ok"}`.
- [ ] Standardized error format `{ "error": { "code": "...", "message": "..." } }` verified across all error conditions.

---

*Last updated: 2026-10-23 (Drafted from PRD v1.0 with review clarifications)*
