---
phase: 5
plan: 1
wave: 1
gap_closure: false
---

# Plan 5.1 (Revised): Advanced Search Agents (Minimax, Alpha-Beta, Optimized Alpha-Beta & MCTS)

## Objective
Establish the advanced adversarial and simulation search agent suite under `backend/app/agents/` conforming strictly to PRD §6.4–6.6, REQ-FR-04, REQ-FR-05, and REQ-FR-09. Implement:
1. `MinimaxAgent`: Depth-limited full-tree recursive search with accurate tree-node counting and deterministic tie-breaking.
2. `AlphaBetaAgent`: Mathematical value-equivalent alpha-beta pruning tracking branch cutoffs, sharing evaluation and tie-breaking policies with Minimax.
3. `OptimizedAlphaBetaAgent`: Algorithmic optimizations over standard Alpha-Beta: center-outward dynamic move ordering, transposition table caching with typed bound semantics (`EXACT`, `LOWER`, `UPPER`), and 1-ply immediate-win cutoff logic.
4. `MCTSAgent`: Simulation-based search employing Upper Confidence Bound for Trees (UCT) with explicit node-to-move reward perspective, robust visit-count selection, and isolated pseudo-random seeding for reproducibility.

All agents guarantee strict board immutability, report authentic telemetry adhering to the Telemetry Applicability Matrix, preserve 100% backward compatibility for the legacy `POST /api/ai-move` contract and `backend/ai_agent.py`, and activate the complete agent selector in the React interface.

---

## Context & Architecture Audit

Load these key project artifacts for complete context:
- [.gsd/SPEC.md](file:///c:/Users/MANAV/Desktop/FAI-project/Adversarial-Game-Playing-Agent-/.gsd/SPEC.md) (Sections 2.1, 7.3, 8.2 Telemetry Matrix)
- [.gsd/REQUIREMENTS.md](file:///c:/Users/MANAV/Desktop/FAI-project/Adversarial-Game-Playing-Agent-/.gsd/REQUIREMENTS.md) (REQ-FR-04, REQ-FR-05, REQ-FR-09, REQ-NFR-01)
- [.gsd/ROADMAP.md](file:///c:/Users/MANAV/Desktop/FAI-project/Adversarial-Game-Playing-Agent-/.gsd/ROADMAP.md) (Phase 5 specifications)
- [backend/ai_agent.py](file:///c:/Users/MANAV/Desktop/FAI-project/Adversarial-Game-Playing-Agent-/backend/ai_agent.py) (legacy Minimax function to preserve)
- [backend/app/core/game_engine.py](file:///c:/Users/MANAV/Desktop/FAI-project/Adversarial-Game-Playing-Agent-/backend/app/core/game_engine.py) (canonical engine rules)
- [backend/app/agents/base_agent.py](file:///c:/Users/MANAV/Desktop/FAI-project/Adversarial-Game-Playing-Agent-/backend/app/agents/base_agent.py) (BaseAgent contract)
- [backend/app/agents/factory.py](file:///c:/Users/MANAV/Desktop/FAI-project/Adversarial-Game-Playing-Agent-/backend/app/agents/factory.py) (agent factory)
- [backend/app/schemas/game_schemas.py](file:///c:/Users/MANAV/Desktop/FAI-project/Adversarial-Game-Playing-Agent-/backend/app/schemas/game_schemas.py) (TelemetryMetrics & MoveRequest)
- [backend/main.py](file:///c:/Users/MANAV/Desktop/FAI-project/Adversarial-Game-Playing-Agent-/backend/main.py) (API route and schema)
- [frontend/src/components/GameControls.jsx](file:///c:/Users/MANAV/Desktop/FAI-project/Adversarial-Game-Playing-Agent-/frontend/src/components/GameControls.jsx) (agent selector)
- [frontend/src/components/MetricsPanel.jsx](file:///c:/Users/MANAV/Desktop/FAI-project/Adversarial-Game-Playing-Agent-/frontend/src/components/MetricsPanel.jsx) (real-time telemetry HUD)

---

## 1. Phase 5 Scope & Agent Architecture

### A. Requirements & Roadmap Alignment
Cross-referencing `.gsd/ROADMAP.md`, `.gsd/REQUIREMENTS.md`, and `docs/Adversarial_Game_Playing_Agent_PRD.pdf`:
- **Phase 5 Scope**: Explicitly defines **Minimax**, **Alpha-Beta Pruning**, **Optimized Alpha-Beta**, and **Monte Carlo Tree Search (MCTS/UCT)**.
- **Why MCTS belongs in Phase 5**:
  - PRD §6.6 explicitly specifies Monte Carlo Tree Search as the primary simulation-based algorithm under the Core Agent Catalog.
  - REQ-FR-04 and REQ-FR-05 group advanced agent selection (Minimax, Alpha-Beta, Optimized, MCTS) into Phase 5.
  - Phase 6 is strictly reserved for the Head-to-Head Tournament Benchmarking Runner (`/api/benchmark/run`) and the Analytics Dashboard view. MCTS must be functional before Phase 6 tournaments can execute.
- **Scope Inclusions**:
  1. Shared evaluation module `backend/app/core/evaluation.py` for consistent positional scoring across all game-tree agents.
  2. `MinimaxAgent` (`backend/app/agents/minimax_agent.py`)
  3. `AlphaBetaAgent` (`backend/app/agents/alphabeta_agent.py`)
  4. `OptimizedAlphaBetaAgent` (`backend/app/agents/optimized_agent.py`)
  5. `MCTSAgent` (`backend/app/agents/mcts_agent.py`)
  6. Factory registration in `backend/app/agents/factory.py` and `__init__.py`.
  7. API integration in `backend/main.py` and `backend/app/schemas/game_schemas.py`.
  8. Activation of all agents in frontend `GameControls.jsx` and dynamic telemetry in `MetricsPanel.jsx`.
  9. Comprehensive test suite `backend/tests/test_advanced_search.py`.
- **Scope Exclusions (Reserved for Phase 6/7)**:
  - Multi-match tournament runners, background batch execution, and CSV/JSON export (strictly Phase 6).
  - Analytics comparison charts and aggregate win rate calculations (strictly Phase 6).
  - Production packaging and end-to-end stress testing (strictly Phase 7).

---

## 2. Shared Evaluation, Scoring Invariants & Board Immutability

### A. Strict Board Immutability Invariant
- Every hypothetical move, recursive tree expansion, simulation rollout, and static evaluation operates strictly on copied boards (`[r[:] for r in board]`).
- The caller's input board argument supplied to `select_move(board)` is **never** mutated in-place.
- Enforced by automated cell-by-cell pre/post assertion tests for all 4 advanced agents.

### B. Shared Evaluation Module (`backend/app/core/evaluation.py`)
To guarantee exact mathematical equivalence between Minimax, Alpha-Beta, and Optimized Alpha-Beta:
- Standardize the heuristic evaluation logic into `backend/app/core/evaluation.py`:
  - `evaluate_window(window: List[int], piece: int, opp_piece: int) -> float`:
    - 4 pieces of `piece`: $+100.0$
    - 3 pieces of `piece` + 1 empty: $+5.0$
    - 2 pieces of `piece` + 2 empty: $+2.0$
    - 3 pieces of `opp_piece` + 1 empty: $-4.0$
    - 2 pieces of `opp_piece` + 2 empty: $-1.0$
  - `score_position(board: List[List[int]], piece: int, opp_piece: int) -> float`:
    - Center column bonus: pieces in column 3 receive $+3.0$ each.
    - Window evaluations across all horizontal, vertical, and diagonal windows.
- **Terminal Scoring Policy (Consistent Across All Three Deterministic Search Agents)**:
  - Win for `player_id`: $+10,000,000.0$
  - Win for `opp_id`: $-10,000,000.0$
  - Draw (full board with no winner): $0.0$
  - Leaf node (depth limit reached): `score_position(board, player_id, opp_id)`
- By sharing this exact evaluation module, differences in node counts between algorithms arise purely from pruning and search optimizations, not differing heuristic functions.

---

## 3. Minimax & Alpha-Beta Correctness, Equivalence & Tie-Breaking

### A. Resolution of Move Order & Tie-Breaking
In adversarial search, when two moves yield different minimax scores, the move with the strictly higher score is always chosen regardless of traversal order. However, when two or more moves yield the **exact same maximal score** (a tie), move traversal order dictates which move is retained.

To ensure deterministic correctness:
1. **Shared Traversal Order for Minimax & Alpha-Beta**:
   - Both `MinimaxAgent` and `AlphaBetaAgent` traverse legal moves in the **exact same default order**: natural column order `[0, 1, 2, 3, 4, 5, 6]` (filtered for open columns).
   - Both agents use the **exact same tie-breaking rule**: strictly retain the first candidate that achieves a strictly greater score (`>` for maximizing, `<` for minimizing).
   - This guarantees that `minimax_agent.select_move(board)` and `alphabeta_agent.select_move(board)` select the **exact same column** and compute the **exact same root score** across all test boards and search depths.
2. **Move Equivalence Expectations with Optimized Alpha-Beta**:
   - `OptimizedAlphaBetaAgent` deliberately evaluates moves in center-outward order (`[3, 2, 4, 1, 5, 0, 6]`) to trigger earlier cutoffs.
   - **Score Equivalence Invariant**: The root minimax score computed by `OptimizedAlphaBetaAgent` is mathematically identical to that of `MinimaxAgent` and `AlphaBetaAgent` at the same depth:
     $$\text{score}(\text{OptimizedAB}) == \text{score}(\text{AlphaBeta}) == \text{score}(\text{Minimax})$$
   - **Move Selection Expectations**:
     - Where the optimal move is unique: `OptimizedAlphaBetaAgent` selects the **exact same move** as Minimax and Alpha-Beta.
     - Where multiple moves tie for the exact same maximal score: `OptimizedAlphaBetaAgent` selects the tied optimal move appearing earliest in center-outward order, which is strategically superior in Connect Four.

---

## 4. Transposition Table Correctness (`OptimizedAlphaBetaAgent`)

### A. Table Entry Structure
The transposition table caches evaluated positions using an in-memory dictionary. Each entry stores:
- **`key`**: Immutable, collision-free position tuple:
  `tuple(tuple(row) for row in board) + (active_player,)`
- **`searched_depth`**: Integer remaining search horizon (plies) at this node when the entry was recorded.
- **`score`**: Minimax score computed for this position.
- **`bound_type`**: String in `{"EXACT", "LOWER", "UPPER"}`:
  - `"EXACT"`: The exact minimax score was determined ($\alpha_{\text{orig}} < \text{score} < \beta$).
  - `"LOWER"`: A $\beta$-cutoff occurred ($\text{score} \ge \beta$); the true minimax value is at least `score`.
  - `"UPPER"`: An all-nodes fail-low occurred ($\text{score} \le \alpha_{\text{orig}}$ for all candidate moves); the true minimax value is at most `score`.
- **`best_move`**: Best column index identified for this position, used to order moves first on future visits.

### B. Alpha-Beta Bound Storage and Reuse Rules
When probing the transposition table at state $(B, \text{turn})$ with remaining depth $d$:
1. If an entry exists and `entry.searched_depth >= d`:
   - If `entry.bound_type == "EXACT"`:
     - Increment `transposition_hits += 1`.
     - Return `entry.score` immediately (exact cutoff).
   - If `entry.bound_type == "LOWER"`:
     - $\alpha = \max(\alpha, \text{entry.score})$.
   - If `entry.bound_type == "UPPER"`:
     - $\beta = \min(\beta, \text{entry.score})$.
   - **Cutoff Check**:
     - If $\alpha \ge \beta$:
       - Increment `transposition_hits += 1`.
       - Return `entry.score` (cutoff achieved through tightened bounds).
   - **Critical Bound Safety**:
     - If $\alpha < \beta$, a bound is **NEVER** returned directly as an exact score! The search proceeds recursively with the tightened $\alpha$ and $\beta$.
2. **Move Ordering Reuse**:
   - If `entry.best_move` is known, place `entry.best_move` at the front of candidate move evaluations to maximize immediate cutoff probability.

### C. Cache Lifetime and Hit-Count Semantics
- **Lifetime**: The transposition table persists for the lifetime of the agent session. It can be cleared explicitly via `agent.clear_cache()`.
- **Hit-Count Definition**: `transposition_hits` is incremented **only** when a cached entry with `entry.searched_depth >= d` directly causes a search cutoff (either via `"EXACT"` match or via tightened $\alpha \ge \beta$ bound).
- **Correctness Tests**:
  - Compare `OptimizedAlphaBetaAgent(use_tt=True)` vs `OptimizedAlphaBetaAgent(use_tt=False)`: assert both return identical minimax scores and valid optimal moves.
  - Bound safety test: Assert a `"LOWER"` or `"UPPER"` bound with $\alpha < \beta$ is not returned as an exact score.
  - Cache reuse test: Verify `transposition_hits > 0` on positions with known transposition paths (e.g. sequence $(c_1, c_2)$ vs $(c_2, c_1)$).

---

## 5. MCTS Reward Perspective & Algorithmic Cycle (`MCTSAgent`)

### A. Node-to-Move Reward Perspective
In 2-player zero-sum games, storing rewards from the perspective of the player who made the move to reach the node is mathematically standard, symmetric, and robust:
- **`node.player_just_moved`**: Player ID (1 or 2) who executed the move that created `node`.
- **`node.visits`**: Total visit count ($n$).
- **`node.wins`**: Accumulated reward ($w$) evaluated strictly from `node.player_just_moved`'s perspective.
- **Rollout Outcome Evaluation**:
  - At the terminal state of a rollout simulation with result `winner`:
    - If `winner == node.player_just_moved`: reward is $+1.0$ (win).
    - If `winner is None` (draw): reward is $+0.5$ (draw).
    - If `winner != node.player_just_moved`: reward is $0.0$ (loss).
- **Backpropagation**:
  - Traverse up the tree from the newly expanded node to the root.
  - At each node:
    - `node.visits += 1`
    - `node.wins += reward` (evaluated with respect to that node's `player_just_moved`).
- **UCT Selection**:
  - When parent node $u$ (turn is $P_{\text{turn}}$) selects among its children:
    - Each child $c$ represents a move made by $P_{\text{turn}}$.
    - Therefore, `c.player_just_moved == P_turn`.
    - Hence, $c$'s win rate $c.wins / c.visits$ is **directly** the win rate for $P_{\text{turn}}$!
    - The UCT formula applies uniformly across all tree nodes:
      $$\text{UCT}(c) = \frac{c.wins}{c.visits} + C \sqrt{\frac{\ln(u.visits)}{c.visits}} \quad (C = \sqrt{2} \approx 1.414)$$

### B. Move Selection Policy at Root
- Once the iteration budget is exhausted, select the root child with the **highest visit count** ($\max_c c.visits$).
- Visit count is mathematically proven to be significantly more stable and resilient to rollout noise than raw win rate.

### C. MCTS Corner Cases & Test Fixtures
1. **Immediate Win**: If root has an immediate winning move, rollout simulations and UCT rapidly converge visits onto the winning column.
2. **Forced Block**: If opponent threatens an immediate win, simulations that fail to block lose immediately, concentrating visits on the blocking column.
3. **Terminal Root**: If the board supplied to `select_move()` is already full or terminal, return `(None, telemetry)` without entering the MCTS loop.
4. **Reproducibility**: Use an isolated `self.rng = random.Random(seed)` instance within rollouts. Two `MCTSAgent(seed=42)` runs on identical boards produce 100% identical move choices and visit distributions.

---

## 6. Search Metrics & Performance Test Specifications

### A. Metric Definitions (PRD §13.3)
- **`nodes_evaluated`**:
  - Strictly defined as: the number of search-tree nodes for which the recursive search function is invoked and evaluated (depth, terminal checks, or leaf heuristics).
  - Incremented at the entry of each recursive call: `nodes_evaluated += 1`.
  - Applicable to: `MinimaxAgent`, `AlphaBetaAgent`, `OptimizedAlphaBetaAgent`.
  - Strictly `null` (`None`) for: `RandomAgent`, `GreedyAgent`, `MCTSAgent`.
- **`pruned_nodes`**:
  - Strictly defined as: the number of branch cutoffs triggered by $\alpha \ge \beta$.
  - When $\alpha \ge \beta$ occurs, increment `pruned_nodes += 1`.
  - Applicable to: `AlphaBetaAgent`, `OptimizedAlphaBetaAgent` (preserves measured `0` if no cutoffs occur).
  - Strictly `null` for: `MinimaxAgent`, `RandomAgent`, `GreedyAgent`, `MCTSAgent`.
- **`search_depth`**:
  - Configured search ply horizon for `MinimaxAgent`, `AlphaBetaAgent`, `OptimizedAlphaBetaAgent`.
  - Fixed `1` for `GreedyAgent`.
  - Strictly `null` for `RandomAgent` and `MCTSAgent`.
- **`transposition_hits`**:
  - Number of table lookups that directly produced a cutoff or exact value.
  - Applicable only to `OptimizedAlphaBetaAgent` (preserves measured `0`).
  - Strictly `null` for all other agents.
- **`mcts_iterations` & `mcts_simulations`**:
  - `mcts_iterations`: Count of UCT selection-expansion-rollout-backpropagation cycles executed.
  - `mcts_simulations`: Total rollout simulations executed (equal to iterations for 1 rollout/iteration).
  - Strictly `null` for all tree-search agents and baseline agents (never mixed with search-tree nodes).

### B. Performance Tests (Avoiding Unsound Assumptions)
- We do **not** assert that Optimized Alpha-Beta visits fewer nodes than Alpha-Beta on every arbitrary board. Instead, performance assertions use **deterministic board fixtures**:
  1. **Symmetrical Opening Fixture** (`empty_board`): Center-outward move ordering evaluated at depth 4 is mathematically guaranteed to visit fewer nodes than left-to-right Alpha-Beta (`optimized_nodes < alphabeta_nodes`).
  2. **Transposition-Rich Midgame Fixture**: Board with reachable transpositions evaluated at depth 4 asserts `transposition_hits > 0`.
  3. **Pruning Fixture**: Midgame position evaluated at depth 4 asserts `alphabeta_nodes < minimax_nodes` and `pruned_nodes > 0`.

---

## 7. API Schema, Validation & Compatibility

### A. Request Schema (`backend/main.py`)
```python
class MoveRequest(BaseModel):
    board: list[list[int]]
    depth: Optional[int] = 4
    agent: Optional[str] = "minimax"
    seed: Optional[int] = None
    iterations: Optional[int] = None

    @field_validator("seed", mode="before")
    @classmethod
    def validate_seed(cls, v):
        if v is not None:
            if isinstance(v, bool) or not isinstance(v, int):
                raise ValueError("Seed must be an integer, not boolean.")
        return v

    @field_validator("depth", mode="before")
    @classmethod
    def validate_depth(cls, v):
        if v is not None:
            if isinstance(v, bool) or not isinstance(v, int) or v < 1 or v > 8:
                raise ValueError("Depth must be an integer between 1 and 8.")
        return v

    @field_validator("iterations", mode="before")
    @classmethod
    def validate_iterations(cls, v):
        if v is not None:
            if isinstance(v, bool) or not isinstance(v, int) or v < 10 or v > 10000:
                raise ValueError("Iterations must be an integer between 10 and 10000.")
        return v
```

### B. Backward Compatibility Guarantees
- When `agent` is omitted from `POST /api/ai-move`, the response returns `{ "column": col, "row": row }` without extra keys, preserving the exact legacy Minimax contract.
- When `agent` is explicitly provided, the response returns `{ "column": col, "row": row, "telemetry": telemetry }`.
- Unknown agents raise `GameRuleException(code="INVALID_AGENT", status_code=400)`.
- Full boards return `{"column": None, "row": -1, "telemetry": ...}` gracefully.

### C. Frontend Alignment
- `GameControls.jsx`:
  - Activates all 6 agents (`Minimax`, `Random`, `Greedy`, `Alpha-Beta`, `Optimized Alpha-Beta`, `MCTS`) with `(Active)` status.
  - Adapts difficulty selector: Depth options (Easy: 2, Medium: 4, Hard: 6) for tree search; Iteration options (Easy: 200, Medium: 1000, Hard: 3000) when MCTS is selected.
- `MetricsPanel.jsx`:
  - Dynamically renders metrics supplied by backend:
    - Tree search: Decision Time, Depth, Nodes Evaluated, Pruned Branches, Transposition Hits.
    - MCTS: Decision Time, MCTS Iterations, Simulations, Top Candidate Breakdown.
    - Baselines: Decision Time, `N/A` for tree stats.

---

## 8. Comprehensive Test Strategy (`backend/tests/test_advanced_search.py`)

### A. Board Immutability Tests
1. `test_minimax_agent_board_immutability`: Assert input board identical before and after search.
2. `test_alphabeta_agent_board_immutability`: Assert input board identical before and after search.
3. `test_optimized_agent_board_immutability`: Assert input board identical before and after search.
4. `test_mcts_agent_board_immutability`: Assert input board identical before and after simulations.

### B. Minimax & Alpha-Beta Equivalence & Correctness Tests
1. `test_minimax_and_alphabeta_score_equivalence`:
   - On 5 diverse test positions at depth 2, 3, and 4, assert `minimax_score == alphabeta_score`.
2. `test_minimax_and_alphabeta_unique_move_equivalence`:
   - Positions where one move is strictly optimal: assert `minimax_move == alphabeta_move`.
3. `test_alphabeta_pruning_efficiency`:
   - On midgame test fixtures, assert `alphabeta_nodes < minimax_nodes` and `pruned_nodes > 0`.
4. `test_terminal_scoring_consistency`:
   - Assert win, loss, and draw return identical scores across Minimax, Alpha-Beta, and Optimized Alpha-Beta.

### C. Optimized Alpha-Beta & Transposition Table Tests
1. `test_optimized_alphabeta_score_equivalence`:
   - Assert `optimized_agent.root_score == alphabeta_agent.root_score`.
2. `test_optimized_alphabeta_unique_move_equivalence`:
   - Positions with a unique best move: assert `optimized_move == alphabeta_move`.
3. `test_optimized_alphabeta_move_ordering_efficiency`:
   - Symmetrical opening board: assert `optimized_nodes < alphabeta_nodes` due to center-outward ordering.
4. `test_transposition_table_enabled_vs_disabled`:
   - Assert `OptimizedAlphaBetaAgent(use_tt=True)` and `OptimizedAlphaBetaAgent(use_tt=False)` return identical scores and valid optimal moves.
5. `test_transposition_table_cache_hits`:
   - Symmetrical opening board searched at depth 4 asserts `transposition_hits > 0`.
6. `test_transposition_bound_safety`:
   - Assert that non-exact bounds (`LOWER`, `UPPER`) where $\alpha < \beta$ are never returned as exact scores.
7. `test_optimized_immediate_win_cutoff`:
   - Setup board with immediate win: assert agent chooses winning column immediately.

### D. MCTS Correctness & Perspective Tests
1. `test_mcts_immediate_win_discovery`:
   - Agent has 3 discs aligned with open winning cell: MCTS with 500 iterations selects winning column.
2. `test_mcts_immediate_block_discovery`:
   - Opponent has 3 discs aligned with open winning cell: MCTS selects blocking column.
3. `test_mcts_seed_reproducibility`:
   - Two `MCTSAgent(seed=42)` instances on identical board return 100% identical moves and visit distributions.
4. `test_mcts_iteration_budget_enforcement`:
   - With `iterations=350`, assert `telemetry["mcts_iterations"] == 350` and `telemetry["mcts_simulations"] == 350`.
5. `test_mcts_terminal_root_handling`:
   - Calling on full board returns `(None, telemetry)` without crashing.
6. `test_mcts_telemetry_isolation`:
   - Assert `nodes_evaluated`, `pruned_nodes`, `search_depth`, and `transposition_hits` are strictly `None`.

### E. API & Legacy Compatibility Tests
1. `test_api_advanced_agents_execution`:
   - Test `POST /api/ai-move` with `agent="alphabeta"`, `agent="optimized"`, and `agent="mcts"`.
   - Verify status 200, valid column/row, and compliant telemetry dictionaries.
2. `test_api_legacy_minimax_contract_unbroken`:
   - Calling `POST /api/ai-move` without `agent` returns `{ "column": col, "row": row }` without extra keys.
3. `test_api_full_board_handling`:
   - Call all advanced agents on full board fixture: returns `column: None, row: -1`.
4. `test_existing_regression_suite_unbroken`:
   - All 60 existing tests in `test_agents.py`, `test_game_engine.py`, `test_game_state.py`, `test_foundation.py` pass without modification.

---

## 9. Verification Pipeline & Acceptance Criteria

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
- [ ] **AC-1**: `MinimaxAgent` implemented with full depth-limited tree search, accurate `nodes_evaluated` counting, deterministic tie-breaking, and board immutability.
- [ ] **AC-2**: `AlphaBetaAgent` implemented with $\alpha$-$\beta$ branch pruning, guaranteed mathematical equivalence with Minimax value, accurate `pruned_nodes` counting, and `nodes_evaluated < minimax_nodes` on non-trivial positions.
- [ ] **AC-3**: `OptimizedAlphaBetaAgent` implemented with center-outward move ordering `[3, 2, 4, 1, 5, 0, 6]`, transposition table caching with typed bounds (`EXACT`, `LOWER`, `UPPER`), `transposition_hits` tracking, and immediate-win cutoffs.
- [ ] **AC-4**: `MCTSAgent` implemented with complete 4-step cycle (UCT Selection, Expansion, Rollout Simulation with isolated RNG seed, Backpropagation), node-to-move reward perspective, robust visit-count move selection, and configurable iteration budgets.
- [ ] **AC-5**: Shared evaluation module `backend/app/core/evaluation.py` guarantees consistent heuristic position scoring and terminal values across Minimax, Alpha-Beta, and Optimized Alpha-Beta.
- [ ] **AC-6**: Telemetry contract strictly adheres to PRD §13.3: tree node metrics are tracked only for game-tree agents, simulation metrics are tracked only for MCTS, measured 0s are preserved, and inapplicable metrics return `null`.
- [ ] **AC-7**: All hypothetical evaluations across all 4 agents operate on copied boards without mutating the input board.
- [ ] **AC-8**: `backend/app/agents/factory.py` supports all 6 agents (`random`, `greedy`, `minimax`, `alphabeta`, `optimized`, `mcts`).
- [ ] **AC-9**: `POST /api/ai-move` preserves exact legacy Minimax contract (`{"column": col, "row": row}`) when `agent` is omitted.
- [ ] **AC-10**: Frontend agent selector activates all 6 agents; `MetricsPanel.jsx` dynamically renders algorithm-specific metrics.
- [ ] **AC-11**: Complete backend test suite passes (all 60 existing tests + new advanced search tests).
- [ ] **AC-12**: Frontend test suite (10/10), lint (0 errors/warnings), and production build succeed cleanly.

---

## 10. Scope Boundaries & Files Expected to Change

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
