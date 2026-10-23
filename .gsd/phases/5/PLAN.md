---
phase: 5
plan: 1
wave: 1
gap_closure: false
---

# Plan 5.1: Advanced Search Agents (Minimax, Alpha-Beta, Optimized Alpha-Beta & MCTS)

## Objective
Implement the complete advanced adversarial and simulation search agent suite under `backend/app/agents/` conforming strictly to PRD §6.4–6.6, REQ-FR-04, REQ-FR-05, and REQ-FR-09. This establishes:
1. `MinimaxAgent`: Depth-limited full-tree recursive search with accurate tree-node counting and deterministic center-outward tie-breaking.
2. `AlphaBetaAgent`: Minimax-equivalent alpha-beta pruning tracking branch cutoffs, with guaranteed identical move selection to Minimax under the same depth and evaluation function.
3. `OptimizedAlphaBetaAgent`: Concrete algorithmic optimizations over standard Alpha-Beta: center-outward move ordering, transposition table caching (with board hashing and search bounds), and 1-ply immediate-win cutoff logic.
4. `MCTSAgent`: Simulation-based search employing Upper Confidence Bound for Trees (UCT) across Selection, Expansion, Simulation (rollout), and Backpropagation, with configurable iteration budgets and isolated pseudo-random seeding for reproducibility.

All agents guarantee strict board immutability, report authentic telemetry without fabrication, preserve 100% backward compatibility for the legacy `POST /api/ai-move` contract and `backend/ai_agent.py`, and activate the complete agent selector in the React interface.

---

## Context & Architecture Audit

Load these key project artifacts for complete context:
- [.gsd/SPEC.md](file:///c:/Users/MANAV/Desktop/FAI-project/Adversarial-Game-Playing-Agent-/.gsd/SPEC.md) (Sections 2.1, 7.3, 8.2 Telemetry Matrix)
- [.gsd/REQUIREMENTS.md](file:///c:/Users/MANAV/Desktop/FAI-project/Adversarial-Game-Playing-Agent-/.gsd/REQUIREMENTS.md) (REQ-FR-04, REQ-FR-05, REQ-FR-09, REQ-NFR-01)
- [.gsd/ROADMAP.md](file:///c:/Users/MANAV/Desktop/FAI-project/Adversarial-Game-Playing-Agent-/.gsd/ROADMAP.md) (Phase 5 specifications)
- [backend/ai_agent.py](file:///c:/Users/MANAV/Desktop/FAI-project/Adversarial-Game-Playing-Agent-/backend/ai_agent.py) (legacy Minimax function to preserve)
- [backend/app/core/game_engine.py](file:///c:/Users/MANAV/Desktop/FAI-project/Adversarial-Game-Playing-Agent-/backend/app/core/game_engine.py) (canonical rules)
- [backend/app/agents/base_agent.py](file:///c:/Users/MANAV/Desktop/FAI-project/Adversarial-Game-Playing-Agent-/backend/app/agents/base_agent.py) (BaseAgent contract)
- [backend/app/agents/factory.py](file:///c:/Users/MANAV/Desktop/FAI-project/Adversarial-Game-Playing-Agent-/backend/app/agents/factory.py) (agent factory)
- [backend/app/schemas/game_schemas.py](file:///c:/Users/MANAV/Desktop/FAI-project/Adversarial-Game-Playing-Agent-/backend/app/schemas/game_schemas.py) (TelemetryMetrics)
- [backend/main.py](file:///c:/Users/MANAV/Desktop/FAI-project/Adversarial-Game-Playing-Agent-/backend/main.py) (API route and schema)
- [frontend/src/components/GameControls.jsx](file:///c:/Users/MANAV/Desktop/FAI-project/Adversarial-Game-Playing-Agent-/frontend/src/components/GameControls.jsx) (agent selector)
- [frontend/src/components/MetricsPanel.jsx](file:///c:/Users/MANAV/Desktop/FAI-project/Adversarial-Game-Playing-Agent-/frontend/src/components/MetricsPanel.jsx) (real-time telemetry HUD)

---

## 1. Phase 5 Scope Verification & Agent Identification

### A. Requirements & Roadmap Alignment
Cross-referencing `.gsd/ROADMAP.md`, `.gsd/REQUIREMENTS.md`, and `docs/Adversarial_Game_Playing_Agent_PRD.pdf`:
- **Phase 5 Scope**: Explicitly defines **Minimax**, **Alpha-Beta Pruning**, **Optimized Alpha-Beta**, and **Monte Carlo Tree Search (MCTS/UCT)**.
- **Why MCTS belongs in Phase 5**:
  - PRD §6.6 explicitly specifies Monte Carlo Tree Search as the primary simulation-based algorithm under the Core Agent Catalog.
  - REQ-FR-04 and REQ-FR-05 group advanced agent selection (Minimax, Alpha-Beta, Optimized, MCTS) into Phase 5.
  - Phase 6 is strictly reserved for the Head-to-Head Tournament Benchmarking Runner (`/api/benchmark/run`) and the Analytics Dashboard view. MCTS must be functional before Phase 6 tournaments can execute.
- **Scope Inclusions**:
  1. `MinimaxAgent` (`backend/app/agents/minimax_agent.py`)
  2. `AlphaBetaAgent` (`backend/app/agents/alphabeta_agent.py`)
  3. `OptimizedAlphaBetaAgent` (`backend/app/agents/optimized_agent.py`)
  4. `MCTSAgent` (`backend/app/agents/mcts_agent.py`)
  5. Shared evaluation module `backend/app/core/evaluation.py` for consistent positional scoring across all game-tree agents.
  6. Factory registration in `backend/app/agents/factory.py` and `__init__.py`.
  7. API integration in `backend/main.py` and `backend/app/schemas/game_schemas.py`.
  8. Activation of all agents in frontend `GameControls.jsx` and dynamic telemetry in `MetricsPanel.jsx`.
  9. Comprehensive test suite `backend/tests/test_advanced_search.py`.
- **Scope Exclusions (Reserved for Phase 6/7)**:
  - Multi-match tournament runners, background batch execution, and CSV/JSON export (strictly Phase 6).
  - Analytics comparison charts and aggregate win rate calculations (strictly Phase 6).
  - Production packaging and end-to-end stress testing (strictly Phase 7).

---

## 2. Board Immutability & Shared Evaluation Architecture

### A. Strict Board Immutability Invariant
- Every hypothetical move, recursive tree expansion, simulation rollout, and static evaluation must operate strictly on copied boards or board state representations (`[r[:] for r in board]`).
- The caller's input board argument supplied to `select_move(board)` will **never** be mutated in-place.
- Enforced by automated cell-by-cell pre/post assertion tests for all 4 advanced agents.

### B. Shared Evaluation Module (`backend/app/core/evaluation.py`)
To guarantee exact mathematical equivalence between Minimax, Alpha-Beta, and Optimized Alpha-Beta:
- Extract and standardize the heuristic evaluation logic into `backend/app/core/evaluation.py`:
  - `evaluate_window(window: List[int], piece: int, opp_piece: int) -> float`: Evaluates a 4-cell window (4-in-a-row: $+100.0$, 3 pieces + 1 empty: $+5.0$, 2 pieces + 2 empty: $+2.0$, opponent 3 pieces + 1 empty: $-4.0$, opponent 2 pieces + 2 empty: $-1.0$).
  - `score_position(board: List[List[int]], piece: int, opp_piece: int) -> float`: Evaluates center column weighting ($+3.0$ per disc) plus all horizontal, vertical, and diagonal windows.
  - `is_terminal_state(board: List[List[int]], player_id: int, opp_id: int) -> Tuple[bool, Optional[int]]`: Returns `(is_terminal, winner)`.
- Eliminates duplicate evaluation code and ensures that differences in node counts between algorithms arise purely from pruning and search optimizations, not differing heuristic functions.

---

## 3. Algorithmic Specifications

### A. Minimax Agent (`MinimaxAgent`)
- **Objective**: Canonical depth-limited adversarial game-tree search (PRD §6.4).
- **Core Architecture**:
  - Class: `MinimaxAgent(BaseAgent)` in `backend/app/agents/minimax_agent.py`.
  - Configurable parameter: `depth: int = 4` (default 4; Easy: 2, Medium: 4, Hard: 6).
  - Recursively maximizes for `self.player_id` and minimizes for `self.opp_id`.
  - Terminal conditions: win detected for either player, board full (draw), or `depth == 0`.
  - Terminal rewards: $+10,000,000$ for agent win, $-10,000,000$ for opponent win, $0$ for draw, `score_position()` at depth cutoff.
- **Deterministic Tie-Breaking**:
  - When multiple columns achieve identical minimax scores, tie-break deterministically using center-outward order: `[3, 2, 4, 1, 5, 0, 6]`.
  - Replaces legacy non-deterministic `random.choice()` for reproducible testing.
- **Node Tracking**:
  - Accurately counts every search-tree node visited during recursion (`nodes_evaluated += 1`).
  - `pruned_nodes`: Strictly `None` (`null`).
  - `transposition_hits`: Strictly `None` (`null`).
  - `mcts_iterations` / `mcts_simulations`: Strictly `None` (`null`).
  - `candidate_scores`: List of `{"column": c, "score": score}` for root candidate moves.

### B. Alpha-Beta Pruning Agent (`AlphaBetaAgent`)
- **Objective**: Depth-limited minimax with $\alpha$-$\beta$ branch pruning, exploring fewer nodes while guaranteeing the exact same optimal value as Minimax (PRD §6.5).
- **Core Architecture**:
  - Class: `AlphaBetaAgent(BaseAgent)` in `backend/app/agents/alphabeta_agent.py`.
  - Configurable parameter: `depth: int = 4`.
  - Tracks $\alpha$ (maximizing lower bound) and $\beta$ (minimizing upper bound).
- **Mathematical Equivalence & Pruning**:
  - Uses the identical `score_position` heuristic and terminal rewards as `MinimaxAgent`.
  - When evaluating candidate moves, maintains left-to-right default order ($0..6$) for baseline comparison with Minimax.
  - **Pruning Condition**:
    - At maximizing nodes: $\alpha = \max(\alpha, \text{score})$. If $\alpha \ge \beta$, cutoff occurs.
    - At minimizing nodes: $\beta = \min(\beta, \text{score})$. If $\alpha \ge \beta$, cutoff occurs.
  - **Pruned Branch Counting**:
    - When a cutoff occurs at index $i$ among $K$ legal sibling moves, the number of pruned branches is $(K - 1 - i)$.
    - `pruned_nodes += (K - 1 - i)` (or count of cutoff events, explicitly defined: `pruned_nodes += 1` per cutoff event and optionally tracks skipped branches; standard PRD §13 definition is cutoff occurrences `pruned_nodes += 1`). Real 0 (no cutoffs) is preserved as `0`.
- **Equivalence Invariant**:
  - For any identical board, depth, and move ordering, `alphabeta_agent.select_move(board)[0]` produces the identical minimax value and move as `minimax_agent.select_move(board)[0]`.
  - `alphabeta_nodes <= minimax_nodes` in 100% of non-trivial positions.

### C. Optimized Alpha-Beta Agent (`OptimizedAlphaBetaAgent`)
- **Objective**: Enhanced Alpha-Beta search incorporating concrete optimizations proven to reduce search tree size from $O(b^d)$ towards $O(b^{d/2})$ (PRD §6.5).
- **Optimization 1: Center-Outward Dynamic Move Ordering**:
  - Evaluates legal candidate moves ordered by distance from center: `[3, 2, 4, 1, 5, 0, 6]`.
  - Connect Four center columns participate in exponentially more potential winning lines (up to 7 horizontal, 4 vertical, and 12 diagonal lines). Searching center moves first establishes tight $\alpha$ and $\beta$ bounds early, triggering massive cutoffs in subsequent outer branches.
- **Optimization 2: Transposition Table (Board Caching)**:
  - Connect Four has heavy path transpositions (e.g. sequence $(c_1, c_2)$ yields the identical board state as $(c_2, c_1)$).
  - Implementation:
    - 64-bit board hashing or canonical tuple key `tuple(tuple(r) for r in board) + (turn,)`.
    - Table entry stores: `{ "depth": int, "score": float, "flag": "EXACT" | "LOWERBOUND" | "UPPERBOUND", "best_move": int }`.
    - Lookup: If entry exists with `entry.depth >= current_depth`:
      - If `entry.flag == "EXACT"`: return `entry.score`.
      - If `entry.flag == "LOWERBOUND"`: $\alpha = \max(\alpha, \text{entry.score})$.
      - If `entry.flag == "UPPERBOUND"`: $\beta = \min(\beta, \text{entry.score})$.
      - If $\alpha \ge \beta$: increment `transposition_hits += 1` and return `entry.score`.
    - If entry helps order moves: probe `entry.best_move` and evaluate it first!
  - `transposition_hits`: Measured integer (preserves `0` if no hits occurred).
- **Optimization 3: Immediate-Win Pre-Search Cutoff**:
  - At root and 1-ply: If a candidate move immediately wins for the agent, return it without searching remaining branches.
  - If opponent threatens an immediate win, evaluate the blocking move first.
- **Telemetry Verification**:
  - Asserts `optimized_nodes < alphabeta_nodes` on symmetrical opening and midgame boards.

### D. Monte Carlo Tree Search Agent (`MCTSAgent`)
- **Objective**: Simulation-based search algorithm with selection, expansion, random rollout simulation, and backpropagation using Upper Confidence Bound for Trees (PRD §6.6).
- **Core Architecture**:
  - Class: `MCTSAgent(BaseAgent)` in `backend/app/agents/mcts_agent.py`.
  - Configurable parameters:
    - `iterations: int = 1000` (default 1000; Easy: 200, Medium: 1000, Hard: 3000).
    - `exploration_constant: float = 1.41421356` ($c = \sqrt{2}$).
    - `seed: Optional[int] = None` (isolated pseudo-random generator `random.Random(seed)` for 100% reproducible benchmarking and unit tests).
- **MCTS Node Structure (`MCTSNode`)**:
  - `board`: Deep-copied 6x7 state.
  - `parent`: Reference to parent `MCTSNode`.
  - `move`: Column index that led to this node.
  - `player_just_moved`: Player ID who executed `move`.
  - `children`: List of child `MCTSNode` instances.
  - `untried_moves`: List of legal columns not yet expanded.
  - `visits`: Integer ($n$).
  - `wins`: Float ($w$, accumulated reward).
- **Four-Phase MCTS Cycle**:
  1. **Selection**:
     - Starting from root, traverse through fully expanded nodes using the UCT formula:
       $$\text{UCT}(child) = \frac{child.wins}{child.visits} + c \sqrt{\frac{\ln(node.visits)}{child.visits}}$$
     - Stop traversal when reaching a node with `untried_moves` or a terminal node.
  2. **Expansion**:
     - Pick an untried legal column from `untried_moves`.
     - Simulate dropping piece for the active player on a copied board.
     - Create a new `MCTSNode` child, add to `node.children`, and return it.
  3. **Simulation (Rollout)**:
     - From the newly expanded node, execute a lightweight rollout simulation until terminal state (win, loss, or draw).
     - Move selection policy: Uniform random legal move via `self.rng.choice(valid_locations)`.
     - Evaluate outcome:
       - Agent wins: reward $= 1.0$.
       - Opponent wins: reward $= 0.0$.
       - Draw: reward $= 0.5$.
  4. **Backpropagation**:
     - Traverse up the tree from the expanded node to root.
     - For each node:
       - `node.visits += 1`
       - Update `node.wins += reward` (from the perspective of `node.player_just_moved`).
- **Final Move Selection**:
  - Robust child policy: Choose child with the **highest visit count** ($\max_i n_i$), which is mathematically proven to be more resilient to outliers than raw win percentage.
- **Telemetry Separation**:
  - `mcts_iterations`: Exactly counts UCT iterations executed.
  - `mcts_simulations`: Exactly counts rollout simulations executed (equal to iterations for 1 rollout/iteration).
  - `nodes_evaluated`: Strictly `None` (`null`). MCTS simulation rollouts are never confused with game-tree search nodes.
  - `pruned_nodes`: Strictly `None` (`null`).
  - `search_depth`: Strictly `None` (`null`).
  - `candidate_scores`: `[{"column": c, "visits": n, "win_rate": round(w/n, 4)}]`.

---

## 4. Authentic Telemetry Contract & Inapplicability Matrix

### A. Telemetry Applicability Matrix (PRD §13.3)

| Telemetry Field | Random | Greedy | Minimax | Alpha-Beta | Optimized AB | MCTS / UCT |
|---|---|---|---|---|---|---|
| `decision_time_ms` | Measured | Measured | Measured | Measured | Measured | Measured |
| `nodes_evaluated` | `null` | `null` | Measured | Measured | Measured | `null` |
| `pruned_nodes` | `null` | `null` | `null` | Measured (can be 0) | Measured (can be 0) | `null` |
| `search_depth` | `null` | 1 | Configured | Configured | Configured | `null` |
| `transposition_hits` | `null` | `null` | `null` | `null` | Measured (can be 0) | `null` |
| `mcts_iterations` | `null` | `null` | `null` | `null` | `null` | Measured |
| `mcts_simulations` | `null` | `null` | `null` | `null` | `null` | Measured |
| `candidate_scores` | `null` | 1-ply scores | Root scores | Root scores | Root scores | Visit counts & win % |

### B. Precision Standards & Transparency
1. **Measured Zeros vs Nulls**: If an algorithm supports a metric (e.g. `pruned_nodes` in Alpha-Beta) but no branches happened to be pruned on a shallow board, it returns `0`, **not** `null`. If a metric does not apply (e.g. `nodes_evaluated` in MCTS), it returns `null` (`None`).
2. **Server Time vs Client Latency**:
   - `telemetry.decision_time_ms`: Backend calculation time measured via `time.perf_counter()`.
   - Frontend `latencyMs`: Network round-trip measured via `performance.now()`.
   - Displayed distinctly in the UI to prevent conflating network overhead with algorithmic complexity.
3. **Transparency Note**: Telemetry reports genuine empirical measurements; no claim is made to expose full reasoning traces.

---

## 5. API Validation, Factory Integration & Backward Compatibility

### A. Factory Module (`backend/app/agents/factory.py`)
- Update `SUPPORTED_AGENTS = {"random", "greedy", "minimax", "alphabeta", "optimized", "mcts"}`.
- Update `get_agent(agent_id, **kwargs)`:
  - `"minimax"`: returns `MinimaxAgent(player_id=player_id, depth=depth)`.
  - `"alphabeta"`: returns `AlphaBetaAgent(player_id=player_id, depth=depth)`.
  - `"optimized"`: returns `OptimizedAlphaBetaAgent(player_id=player_id, depth=depth)`.
  - `"mcts"`: returns `MCTSAgent(player_id=player_id, iterations=iterations, seed=seed)`.
  - Rejects unknown agents with HTTP 400 `INVALID_AGENT`.

### B. Endpoint Evolution (`POST /api/ai-move` in `backend/main.py`)
- Update `MoveRequest` schema:
  ```python
  class MoveRequest(BaseModel):
      board: list[list[int]]
      depth: Optional[int] = 4
      agent: Optional[str] = "minimax"
      seed: Optional[int] = None
      iterations: Optional[int] = None
  ```
- **Backward Compatibility Contract**:
  - When `agent` is omitted (or `"minimax"` called via legacy request): executes legacy Minimax and returns `{ "column": col, "row": row }` with 100% contract preservation.
  - When `agent` is explicitly provided: returns `{ "column": col, "row": row, "telemetry": telemetry }`.
  - Full board handling returns `{"column": None, "row": -1, "telemetry": ...}` without crashing.

### C. Frontend Interface Activation
- `frontend/src/components/GameControls.jsx`:
  - Update algorithm selector so all 6 agents (`Minimax`, `Random`, `Greedy`, `Alpha-Beta`, `Optimized Alpha-Beta`, `MCTS`) are active and selectable (`(Active)`).
  - Adjust difficulty selector to map appropriately (depths 2, 4, 6 for tree search; iteration budgets 200, 1000, 3000 for MCTS).
- `frontend/src/components/MetricsPanel.jsx`:
  - Dynamically display relevant metrics based on `telemetry`:
    - Tree search: Decision Time, Search Depth, Nodes Evaluated, Pruned Branches, Transposition Hits.
    - MCTS: Decision Time, MCTS Iterations, Simulations, Top Candidate Visit Counts.
    - Baselines: Decision Time, `N/A` for tree stats.

---

## 6. Comprehensive Test Strategy (`backend/tests/test_advanced_search.py`)

### A. Board Immutability Tests
1. `test_minimax_agent_board_immutability`: Assert input board identical before and after search.
2. `test_alphabeta_agent_board_immutability`: Assert input board identical before and after search.
3. `test_optimized_agent_board_immutability`: Assert input board identical before and after search.
4. `test_mcts_agent_board_immutability`: Assert input board identical before and after simulations.

### B. Mathematical Equivalence & Pruning Tests
1. `test_minimax_and_alphabeta_equivalence`:
   - On 5 diverse midgame positions at depth 3 and 4, assert `minimax_agent.select_move(b)[0] == alphabeta_agent.select_move(b)[0]`.
2. `test_alphabeta_pruning_efficiency`:
   - Assert `alphabeta_telemetry["nodes_evaluated"] < minimax_telemetry["nodes_evaluated"]`.
   - Assert `alphabeta_telemetry["pruned_nodes"] > 0`.
3. `test_alphabeta_deterministic_tie_breaking`:
   - On symmetrical board, assert consistent deterministic column selection.

### C. Optimized Alpha-Beta Tests
1. `test_optimized_alphabeta_move_ordering_efficiency`:
   - Symmetrical opening board: Assert `optimized_nodes < alphabeta_nodes` due to center-outward ordering.
2. `test_optimized_alphabeta_transposition_caching`:
   - Search depth 4 on midgame board: Assert `transposition_hits > 0`.
3. `test_optimized_alphabeta_immediate_win_cutoff`:
   - Setup board with immediate win: Assert agent chooses winning column at depth 1/2 with minimal node evaluations.

### D. MCTS Tests
1. `test_mcts_immediate_win_discovery`:
   - Agent has 3 discs aligned with open winning cell: With 500 iterations, MCTS selects winning column with highest visit count.
2. `test_mcts_immediate_block_discovery`:
   - Opponent has 3 discs aligned with open winning cell: MCTS selects blocking column.
3. `test_mcts_seed_reproducibility`:
   - Two `MCTSAgent(seed=42)` instances on identical board return 100% identical move and visit distribution.
4. `test_mcts_iteration_budget_enforcement`:
   - With `iterations=350`, assert `telemetry["mcts_iterations"] == 350`.
5. `test_mcts_telemetry_isolation`:
   - Assert `nodes_evaluated` and `pruned_nodes` are strictly `None`.

### E. API & Legacy Compatibility Tests
1. `test_api_advanced_agents_execution`:
   - Test `POST /api/ai-move` with `agent="alphabeta"`, `agent="optimized"`, and `agent="mcts"`.
   - Verify status 200, valid column/row, and compliant telemetry dictionaries.
2. `test_api_full_board_handling`:
   - Call all advanced agents on full board fixture: returns `column: None, row: -1`.
3. `test_existing_regression_suite_unbroken`:
   - All 60 existing tests in `test_agents.py`, `test_game_engine.py`, `test_game_state.py`, `test_foundation.py` pass without modification.

---

## 7. Verification Pipeline & Acceptance Criteria

### Exact Verification Commands:
```powershell
# 1. Run all advanced search unit tests + existing regression suite (60 tests)
python -m pytest backend/tests/test_advanced_search.py backend/tests/test_agents.py backend/tests/test_game_engine.py backend/tests/test_game_state.py backend/tests/test_foundation.py -v

# 2. Run frontend unit tests
cd frontend; npm test

# 3. Run frontend linter
cd frontend; npm run lint

# 4. Run frontend production build
cd frontend; npm run build
```

### Acceptance Criteria Checklist:
- [ ] **AC-1**: `MinimaxAgent` implemented with full depth-limited tree search, accurate `nodes_evaluated` counting, deterministic center-outward tie-breaking, and board immutability.
- [ ] **AC-2**: `AlphaBetaAgent` implemented with $\alpha$-$\beta$ branch pruning, guaranteed mathematical equivalence with Minimax value, accurate `pruned_nodes` counting, and `nodes_evaluated < minimax_nodes`.
- [ ] **AC-3**: `OptimizedAlphaBetaAgent` implemented with center-outward move ordering `[3, 2, 4, 1, 5, 0, 6]`, transposition table caching with board hashing, `transposition_hits` tracking, and immediate-win cutoffs.
- [ ] **AC-4**: `MCTSAgent` implemented with complete 4-step cycle (UCT Selection, Expansion, Simulation/rollout with isolated RNG seed, Backpropagation), robust visit-count move selection, and configurable iteration budgets.
- [ ] **AC-5**: Shared evaluation function `backend/app/core/evaluation.py` guarantees consistent heuristic position scoring across Minimax, Alpha-Beta, and Optimized Alpha-Beta.
- [ ] **AC-6**: Telemetry contract strictly adheres to PRD §13.3: tree node metrics are tracked only for game-tree agents, simulation metrics are tracked only for MCTS, measured 0s are preserved, and inapplicable metrics return `null`.
- [ ] **AC-7**: All hypothetical evaluations across all 4 agents operate on copied boards without mutating the input board.
- [ ] **AC-8**: `backend/app/agents/factory.py` supports all 6 agents (`random`, `greedy`, `minimax`, `alphabeta`, `optimized`, `mcts`).
- [ ] **AC-9**: `POST /api/ai-move` preserves exact legacy Minimax contract (`{"column": col, "row": row}`) when `agent` is omitted.
- [ ] **AC-10**: Frontend agent selector activates all 6 agents; `MetricsPanel.jsx` dynamically renders algorithm-specific metrics.
- [ ] **AC-11**: Complete backend test suite passes (all 60 existing tests + new advanced search tests).
- [ ] **AC-12**: Frontend test suite (10/10), lint (0 errors/warnings), and production build succeed cleanly.

---

## 8. Scope Boundaries & Files Expected to Change

### Scope Boundaries:
- **Included**: `MinimaxAgent`, `AlphaBetaAgent`, `OptimizedAlphaBetaAgent`, `MCTSAgent`, shared `evaluation.py`, factory registration, API schema extension, frontend controls and telemetry HUD activation, and automated unit/integration test suite.
- **Excluded**: Benchmarking tournament runner (`POST /api/benchmark/run`), multi-match aggregate analytics, CSV/JSON export, and release packaging (strictly Phase 6 & 7).

### Files to Create:
- `backend/app/core/evaluation.py`
- `backend/app/agents/minimax_agent.py`
- `backend/app/agents/alphabeta_agent.py`
- `backend/app/agents/optimized_agent.py`
- `backend/app/agents/mcts_agent.py`
- `backend/tests/test_advanced_search.py`
- `.gsd/phases/5/PLAN.md`

### Files to Modify:
- `backend/app/agents/__init__.py`
- `backend/app/agents/factory.py`
- `backend/app/schemas/game_schemas.py`
- `backend/main.py`
- `frontend/src/components/GameControls.jsx`
- `frontend/src/components/MetricsPanel.jsx`
- `frontend/src/hooks/useGame.js`
- `.gsd/STATE.md`
- `.gsd/TODO.md`
- `.gsd/ROADMAP.md`
