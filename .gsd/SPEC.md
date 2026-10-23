# SPEC.md — Project Specification

> **Project**: Adversarial Game-Playing Agent — Connect Four AI  
> **Status**: `DRAFT` (Awaiting User Review to finalize Planning Lock)  
> **Primary Source of Truth**: `docs/Adversarial_Game_Playing_Agent_PRD.pdf` (v1.0)  
> **Planning Lock**: No implementation code until status is `FINALIZED`.

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
| **FR-03** | Game Modes | Human vs AI (core), Human vs Human (local two-player), and AI vs AI (automated simulation/demonstration). |
| **FR-04** | AI Selection | Dropdown/selector supporting: Random, Greedy, Minimax, Alpha-Beta, Optimized Alpha-Beta, and MCTS/UCT. |
| **FR-05** | Difficulty Settings | Depth limits (Easy: 2 / shallow, Medium: 4 / greedy-moderate, Hard: 6 / alpha-beta, Expert: optimized alpha-beta / MCTS budget). |
| **FR-06** | Move Legality Enforcement | Reject invalid columns (<0 or >=7), full columns, moves when game is terminal, wrong-player turns, and malformed requests with standard error payloads. |
| **FR-07** | Win & Draw Detection | Exhaustive detection of 4 consecutive matching pieces horizontally, vertically, positive diagonal, negative diagonal; full board without winner declared as Draw. |
| **FR-08** | Game Controls | "New Game" (resets state/metrics), "Restart" (resets board with same settings), undo functionality where appropriate, and pause/resume for AI vs AI. |
| **FR-09** | AI Telemetry & Visualization | Per-move telemetry: decision time (ms), nodes visited, pruning count, search depth, candidate scores, and MCTS iteration/visit statistics. |
| **FR-10** | Metrics Dashboard | Aggregate match metrics: W/D/L counters, win percentage, decision time percentiles (avg/median/max), search intensity, and comparative charts. |
| **FR-11** | Head-to-Head Benchmarking | Automated tournament harness between any two chosen agents over $N$ matches (alternating Player 1/2), logging outcomes, time, node metrics; exportable to CSV/JSON. |
| **FR-12** | Resilient Error Handling | Clean frontend handling for network drops, timeouts, invalid moves, and unexpected exceptions with actionable feedback and safe retry. |

---

## 6. Non-Functional Requirements (NFR)

- **NFR-01: Performance & Responsiveness**: AI decision latency bounded by depth/iteration limits; interactive moves feel instantaneous (<200ms for UI updates); long-running benchmarks executed without freezing the UI.
- **NFR-02: Correctness**: Zero tolerance for illegal moves or missed terminal states. Backend validation is authoritative.
- **NFR-03: Architectural Modularity**: Strict separation between core game logic (`core/`), agent algorithms (`agents/`), API orchestration (`api/`, `services/`), and frontend views (`components/`, `pages/`).
- **NFR-04: Usability & Aesthetic Design**: Technical modern dark theme (navy/charcoal background `#0b1120`, cyan/blue accents `#0ea5e9` & `#06b6d4`, high-contrast Red `#ef4444` and Yellow `#eab308` discs, crisp typography via Inter, subtle micro-interactions).
- **NFR-05: Testability**: Minimum 85% coverage on `core/` game logic and agent implementations; comprehensive API integration tests.

---

## 7. System Architecture & Repository Layout

### 7.1 Component Architecture
```
┌────────────────────────────────────────────────────────┐
│             Frontend: React 19 + Vite                  │
│   • Pages: HomePage, GamePage, AnalyticsPage           │
│   • Components: GameBoard, Controls, Status, Metrics   │
│   • State & API: useGame hook, Axios/Fetch Client      │
└────────────────────────┬───────────────────────────────┘
                         │ JSON REST API
                         ▼
┌────────────────────────────────────────────────────────┐
│             Backend API: FastAPI (Python)              │
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

### 7.2 Target Repository Structure (Incremental Migration)
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

## 8. AI Agent Specifications & Shared Interface

### 8.1 Shared `BaseAgent` Contract
All agents inherit from a common abstract base class:
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
            metrics (dict): execution metrics (decision_time_ms, nodes_evaluated, etc.)
        """
        pass
```

### 8.2 Agent Implementations
1. **RandomAgent**: Selects randomly among legal columns using Python's `random.Random` (supports deterministic seeding).
2. **GreedyAgent**: Checks candidate moves for an immediate win for self; if none, blocks any immediate opponent winning move; otherwise evaluates 1-ply board heuristics.
3. **MinimaxAgent**: Classic depth-limited game-tree search alternating maximizing and minimizing players.
4. **AlphaBetaAgent**: Minimax with branch pruning based on $[\alpha, \beta]$ score thresholds. Guarantees the same move evaluation as Minimax while evaluating fewer nodes.
5. **OptimizedAlphaBetaAgent**: Alpha-Beta enhanced with:
   - Center-outward move ordering (columns 3, 2, 4, 1, 5, 0, 6) to maximize early cutoffs.
   - Transposition table (caching exact/lower/upper bounds with board state hashing).
   - Immediate terminal/win detection before deep exploration.
6. **MCTSAgent (UCT)**: Four-phase Monte Carlo Tree Search:
   - **Selection**: Traverse tree using UCB1 formula $Q(s, a) + C \times \sqrt{\frac{\ln N(s)}{N(s, a)}}$ ($C \approx 1.414$).
   - **Expansion**: Add untried legal move nodes to tree.
   - **Simulation / Rollout**: Fast randomized playout to terminal state.
   - **Backpropagation**: Update visit count and win/loss reward back to root.

---

## 9. API Specification Summary

- `GET /api/health` — System status
- `GET /api/agents` — List available agents and parameter configurations
- `POST /api/game/new` — Create new game session (`mode`, `ai_agent`, `difficulty`, `starting_player`)
- `POST /api/game/{game_id}/move` — Submit human move `{ "column": int }`
- `POST /api/game/{game_id}/ai-move` — Trigger AI move calculation and update game state
- `GET /api/game/{game_id}` — Retrieve full current game state and move history
- `POST /api/benchmark/run` — Run automated tournament between agents
- `GET /api/benchmark/{benchmark_id}` — Retrieve benchmark progress or completed results

---

## 10. Success Criteria & Verification Checklist

- [ ] 6×7 Connect Four engine with 100% accurate win detection across all directions and ties.
- [ ] Backend tests passing with `pytest` for game rules, bounds, and edge cases.
- [ ] All 6 AI agents (Random, Greedy, Minimax, Alpha-Beta, Optimized Alpha-Beta, MCTS) operational and accessible via the API.
- [ ] Real-time telemetry displayed after each AI move (latency, nodes, cutoffs / iterations).
- [ ] Multi-match benchmarking functional, generating win rate and search metrics with CSV/JSON export.
- [ ] Clean, responsive dark-themed UI with smooth drop animations, clear game status, and error notifications.
- [ ] Full end-to-end user journey verified in browser without console errors.

---

*Last updated: 2026-10-23 (Drafted from PRD v1.0)*
