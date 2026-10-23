---
phase: 4
plan: 1
wave: 1
gap_closure: false
---

# Plan 4.1 (Revised): Baseline AI Agents (Random & Greedy)

## Objective
Establish the modular AI agent architecture under `backend/app/agents/` conforming strictly to PRD §6.1. Implement the abstract `BaseAgent` interface alongside the two baseline agents: `RandomAgent` (with isolated pseudo-random seeding for benchmarking reproducibility) and `GreedyAgent` (with deterministic 1-ply tactical rules: immediate win, immediate block, full-reply blunder avoidance, static position scoring, and center-outward tie-breaking). Enforce board immutability during evaluation, report authentic server-side decision telemetry without data fabrication, validate API requests with standard error envelopes, and preserve 100% backward compatibility for `backend/ai_agent.py`, the existing `POST /api/ai-move` contract, and all 31 existing backend tests.

## Context & Architecture Audit
Load these files for context:
- [.gsd/SPEC.md](file:///c:/Users/MANAV/Desktop/FAI-project/Adversarial-Game-Playing-Agent-/.gsd/SPEC.md)
- [.gsd/REQUIREMENTS.md](file:///c:/Users/MANAV/Desktop/FAI-project/Adversarial-Game-Playing-Agent-/.gsd/REQUIREMENTS.md)
- [backend/ai_agent.py](file:///c:/Users/MANAV/Desktop/FAI-project/Adversarial-Game-Playing-Agent-/backend/ai_agent.py)
- [backend/app/core/game_engine.py](file:///c:/Users/MANAV/Desktop/FAI-project/Adversarial-Game-Playing-Agent-/backend/app/core/game_engine.py)
- [backend/app/schemas/agent_schemas.py](file:///c:/Users/MANAV/Desktop/FAI-project/Adversarial-Game-Playing-Agent-/backend/app/schemas/agent_schemas.py)
- [backend/app/schemas/game_schemas.py](file:///c:/Users/MANAV/Desktop/FAI-project/Adversarial-Game-Playing-Agent-/backend/app/schemas/game_schemas.py)
- [backend/main.py](file:///c:/Users/MANAV/Desktop/FAI-project/Adversarial-Game-Playing-Agent-/backend/main.py#L86-L99)
- [frontend/src/services/api.js](file:///c:/Users/MANAV/Desktop/FAI-project/Adversarial-Game-Playing-Agent-/frontend/src/services/api.js)
- [frontend/src/components/GameControls.jsx](file:///c:/Users/MANAV/Desktop/FAI-project/Adversarial-Game-Playing-Agent-/frontend/src/components/GameControls.jsx)

---

## 1. Existing System Audit & Compatibility Strategy

### Existing Codebase Status:
1. `backend/ai_agent.py`:
   - Contains legacy functions `evaluate_window`, `score_position`, and depth-limited `minimax(board, depth, alpha, beta, maximizing_player)`.
   - Imports canonical engine symbols from `game_engine`.
   - Must remain **100% untouched** to preserve legacy imports and regression tests.
2. `backend/main.py`:
   - Contains `POST /api/ai-move` expecting `{ "board": list[list[int]], "depth": int = 4 }` and returning `{ "column": int, "row": int }`.
3. `backend/app/schemas/game_schemas.py`:
   - Defines `TelemetryMetrics` supporting `None` for inapplicable metrics.
   - Defines `MoveRequest(column=None, board=None, depth=4)`.
4. `frontend/src/components/GameControls.jsx`:
   - Fetches agent metadata from `GET /api/agents`.
   - Displays `Minimax (Active)` and labels other algorithms `(Phase 4/5)`.

### Compatibility & Modular Strategy:
- Introduce `backend/app/agents/` package:
  - `base_agent.py`: Abstract `BaseAgent` base class.
  - `random_agent.py`: `RandomAgent` implementation with isolated RNG.
  - `greedy_agent.py`: `GreedyAgent` implementation with 1-ply tactical rules and blunder avoidance.
  - `factory.py`: `get_agent(agent_id, **kwargs)` factory managing agent instantiations and input validation.
  - `__init__.py`: Package exports.
- **Endpoint Evolution (`POST /api/ai-move`)**:
  - Extend `MoveRequest` to accept optional `agent: Optional[str] = "minimax"` and `seed: Optional[int] = None`.
  - Defaulting to `"minimax"` when `agent` is omitted guarantees 100% backward compatibility for existing callers.
  - Preserves exact row/column response semantics:
    - `column`: Selected column index $[0..6]$ (or `None` if full).
    - `row`: `get_next_open_row(board, column)` (or `-1` if `column` is `None`).
    - `telemetry`: Optional dictionary conforming to `TelemetryMetrics`.

---

## 2. Board Immutability Guarantee

- **Strict Invariant**: Evaluation must **never** mutate the caller's board matrix.
- **Implementation**:
  - In `BaseAgent`, before any hypothetical piece drop or simulated branch evaluation, copy the board using list comprehensions (`[r[:] for r in board]`).
  - Neither `RandomAgent` nor `GreedyAgent` will apply in-place mutations to the input board argument.
  - Pytest assertions will capture a deep copy of the board before `select_move()` and verify cell-by-cell equality after execution.

---

## 3. Algorithmic Specifications

### A. Random Agent (`RandomAgent`)
- **Objective**: Baseline benchmark agent (PRD §6.2).
- **Behavior**:
  1. Deep-copy input board to guarantee immutability.
  2. Query legal columns via `get_valid_locations(board)`.
  3. If `len(valid_locations) == 0` (board full), return `(None, telemetry)`.
  4. Select a column uniformly at random from `valid_locations`.
- **RNG Isolation & Determinism**:
  - Accept optional `seed: Optional[int] = None` in `__init__(seed=...)`.
  - Reject boolean seeds explicitly (`isinstance(seed, bool)`).
  - Use an isolated pseudo-random number generator instance (`self.rng = random.Random(seed)`), avoiding mutation of Python's global `random` state.
  - Guarantees 100% reproducible sequences for unit tests and benchmarking tournaments without flaky statistical assertions.
- **Server-Side Telemetry**:
  - `decision_time_ms`: Float, measured server-side execution time via `time.perf_counter()`.
  - `nodes_evaluated`: `None` (`null`).
  - `pruned_nodes`: `None` (`null`).
  - `search_depth`: `None` (`null`).
  - `transposition_hits`: `None` (`null`).
  - `candidate_scores`: `None` (`null`).

### B. Greedy Agent (`GreedyAgent`)
- **Objective**: One-ply tactical lookahead agent with opponent reply checking and blunder avoidance (PRD §6.3).
- **Decision Hierarchy (Strict Priority Order)**:

  1. **Priority 1: Immediate Winning Move (Win First)**
     - For each legal column $c \in \text{valid\_locations}$:
       - Simulate dropping agent's piece (`self.player_id`) on a board copy.
       - If `check_win` evaluates to `True`:
         - **Immediate Cutoff**: Select column $c$ immediately.
         - Return $c$ with telemetry annotation `"reason": "immediate_win"`.
         - **Invariant**: If both an immediate win and an immediate opponent block exist, the agent **always takes the win**.

  2. **Priority 2: Immediate Opponent Threat Block**
     - If no immediate winning move exists for the agent:
     - Check for columns where the opponent could immediately win on their next turn:
       - For each legal column $c \in \text{valid\_locations}$:
         - Simulate dropping opponent's piece (`self.opp_id`) on a board copy.
         - If `check_win` evaluates to `True`, column $c$ is a blocking move.
     - **Handling Multiple Opponent Threats (Split Threat / Fork)**:
       - If the opponent threatens immediate wins in two or more distinct columns simultaneously (a fork), the agent cannot prevent the opponent's victory on their next turn (a loss is technically unavoidable).
       - In this scenario, the agent blocks one of the threats, choosing the column appearing earliest in the center-outward tie-break order (`[3, 2, 4, 1, 5, 0, 6]`), and annotates telemetry with `"reason": "split_threat_block"`.

  3. **Priority 3: Full-Reply Blunder Avoidance & Heuristic Evaluation**
     - If neither Priority 1 nor Priority 2 applies:
     - For every legal candidate move $c \in \text{valid\_locations}$:
       - Simulate dropping agent's piece at `row = getNextOpenRow(board, c)` on a copy `b_cand`.
       - **All-Column Opponent Reply Check**:
         - Check every legal opponent reply column $c_{opp} \in \text{get\_valid\_locations}(b\_cand)$.
         - Simulate opponent dropping at `getNextOpenRow(b_cand, c_opp)`.
         - If `check_win(b_cand_with_opp, self.opp_id)` is `True`:
           - Tag candidate move $c$ as **UNSAFE** (permits an immediate opponent win in column $c_{opp}$).
         - Else:
           - Tag candidate move $c$ as **SAFE**.
       - **Score Position on `b_cand`**:
         - Center column weighting: pieces in column 3 receive $+3.0$ each.
         - 4-cell window scoring across all horizontal, vertical, and diagonal windows:
           - 4 pieces of `player_id`: $+100.0$
           - 3 pieces of `player_id` + 1 empty: $+5.0$
           - 2 pieces of `player_id` + 2 empty: $+2.0$
           - 3 pieces of `opp_id` + 1 empty: $-4.0$
           - 2 pieces of `opp_id` + 2 empty: $-1.0$
     - **Candidate Filtering**:
       - If at least one **SAFE** candidate move exists, the agent **strictly disqualifies all UNSAFE candidate moves**, choosing only among the SAFE candidates.
       - If **NO safe move exists** (all legal moves allow an immediate opponent win on reply), the agent evaluates all candidate moves using their heuristic scores.
     - **Deterministic Tie-Breaking**:
       - Candidate moves are ranked by:
         1. Safety (`SAFE` > `UNSAFE`).
         2. Heuristic score (highest score first).
         3. Center-outward column preference: `[3, 2, 4, 1, 5, 0, 6]`.
       - When two or more safe moves share the identical highest heuristic score, the tie is broken deterministically by selecting the column appearing earliest in the center-outward preference list.

- **Server-Side Telemetry**:
  - `decision_time_ms`: Float, measured backend execution time via `time.perf_counter()`.
  - `search_depth`: `1` (documented strictly as 1-ply candidate evaluation with 1-ply tactical opponent reply checking).
  - `candidate_scores`: List of evaluated candidate breakdowns:
    `[{"column": c, "score": float, "is_safe": bool, "reason": str}]`.
  - `nodes_evaluated`, `pruned_nodes`, `transposition_hits`: Strictly `None` (`null`).

---

## 4. API Validation, Error Envelopes & Compatibility

### Request Validation Rules:
1. **Agent Parameter Validation**:
   - `agent` must be a string in `{"random", "greedy", "minimax"}`.
   - If `agent` is omitted, defaults to `"minimax"`.
   - If `agent` is unknown (e.g. `agent="deep_q"` or `agent="invalid"`), raise `GameRuleException`:
     - Status: HTTP 400
     - Response: `{"error": {"code": "INVALID_AGENT", "message": "Unknown agent '...'. Supported: 'random', 'greedy', 'minimax'."}}`
2. **Seed Parameter Validation**:
   - `seed` must be an integer, rejecting booleans explicitly (`isinstance(seed, bool)`).
   - If non-integer or boolean, return HTTP 422 `VALIDATION_ERROR`: `{"error": {"code": "VALIDATION_ERROR", "message": "Seed must be an integer, not boolean."}}`.
3. **Board Validation**:
   - Conforms to existing `validate_board_structure`: 6x7 integer matrix with values in $\{0, 1, 2\}$.
4. **Full Board Handling**:
   - If `is_board_full(board)` is `True` when calling `POST /api/ai-move`, return:
     `{"column": None, "row": -1, "telemetry": { ... }}`
     with HTTP 200, matching existing legacy response semantics without crashing.
5. **No State Mutation**:
   - Invalid requests return the standard error envelope and never mutate any server or session state.

### Telemetry Semantic Distinction:
- **`telemetry.decision_time_ms`**: Algorithmic decision time measured server-side inside `select_move()` via high-precision `time.perf_counter()`.
- **Frontend `latencyMs`**: Client-side network round-trip time measured in browser via `performance.now()`.
- Both are documented distinctly to prevent conflation between network latency and agent calculation duration.

---

## 5. Comprehensive Test Strategy (`backend/tests/test_agents.py`)

### A. Board Immutability Tests
1. `test_random_agent_board_immutability`:
   - Deep-copy board before `select_move()`; assert input board is cell-by-cell identical after move.
2. `test_greedy_agent_board_immutability`:
   - Deep-copy board before `select_move()`; assert input board is cell-by-cell identical after move across tactical and heuristic evaluations.

### B. Random Agent Determinism & Legality
1. `test_random_agent_isolated_seed_reproducibility`:
   - Two `RandomAgent(seed=42)` instances execute moves on identical boards; assert sequences are 100% identical.
2. `test_random_agent_controlled_single_column`:
   - Fill 6 columns; assert RandomAgent returns the only open column in 100% of calls.
3. `test_random_agent_full_board_returns_none`:
   - Call on full board; asserts `(None, telemetry)` returned without exception.
4. `test_random_agent_rejects_boolean_seed`:
   - Verify `RandomAgent(seed=True)` raises `TypeError` or `ValueError`.
5. `test_random_agent_telemetry_invariants`:
   - Verify `decision_time_ms > 0` and all tree search metrics (`nodes_evaluated`, `pruned_nodes`) are strictly `None`.

### C. Greedy Tactical & Reply-Checking Tests
1. `test_greedy_immediate_wins`:
   - Test immediate horizontal win: 3 agent pieces in row 5, open 4th cell $\to$ selects winning column.
   - Test immediate vertical win: 3 agent pieces stacked in column $\to$ selects winning column.
   - Test immediate positive diagonal ($/$) win $\to$ selects winning column.
   - Test immediate negative diagonal ($\backslash$) win $\to$ selects winning column.
2. `test_greedy_immediate_blocks`:
   - Test immediate horizontal block: opponent threatens 4-in-a-row $\to$ blocks.
   - Test immediate vertical block: opponent threatens vertical 4-in-a-row $\to$ blocks.
   - Test immediate diagonal block $\to$ blocks.
3. `test_greedy_priority_win_over_block`:
   - Fixture where Agent has an immediate win in col 5 AND Opponent has an immediate win in col 1.
   - Asserts Greedy chooses col 5 (Win strictly precedes Block).
4. `test_greedy_multiple_opponent_threats_fork`:
   - Opponent creates a fork with winning threats in two columns.
   - Asserts Greedy blocks one threat according to center-outward preference list and returns valid move.
5. `test_greedy_all_reply_blunder_avoidance`:
   - Candidate col 2 places a disc allowing opponent to win directly above in col 2 $\to$ avoided.
   - Candidate col 1 places a disc allowing opponent to complete an adjacent horizontal/diagonal win $\to$ avoided.
   - Greedy selects a safe candidate column over an unsafe candidate column.
6. `test_greedy_no_safe_moves_fallback`:
   - Fixture where every single legal move permits an immediate opponent win on reply.
   - Asserts Greedy falls back to highest heuristic score with center-outward tie-breaking without crashing.
7. `test_greedy_center_outward_tie_breaking`:
   - Symmetrical opening board: asserts center column 3 is chosen.
8. `test_greedy_telemetry_contract`:
   - `search_depth == 1`, `candidate_scores` populated with `column`, `score`, `is_safe`, and `reason`.
   - `nodes_evaluated` and `pruned_nodes` are strictly `None`.

### D. API Validation & Legacy Compatibility Tests
1. `test_api_unknown_agent_error_envelope`:
   - `client.post("/api/ai-move", json={"board": empty, "agent": "unknown_ai"})`
   - Status 400, `code == "INVALID_AGENT"`.
2. `test_api_invalid_seed_error_envelope`:
   - `client.post("/api/ai-move", json={"board": empty, "agent": "random", "seed": True})`
   - Status 422 or 400, `code == "VALIDATION_ERROR"`.
3. `test_api_random_agent_execution`:
   - `client.post("/api/ai-move", json={"board": empty, "agent": "random", "seed": 100})`
   - Returns 200 with valid `column`, `row`, and telemetry.
4. `test_api_greedy_agent_execution`:
   - `client.post("/api/ai-move", json={"board": win_setup, "agent": "greedy"})`
   - Returns 200 with the exact winning column and telemetry.
5. `test_api_legacy_minimax_contract_unbroken`:
   - `client.post("/api/ai-move", json={"board": empty, "depth": 2})` (without `agent`)
   - Returns 200 with keys `{"column", "row"}` using Minimax.
6. `test_api_full_board_returns_none_column`:
   - `client.post("/api/ai-move", json={"board": DRAW_BOARD_FIXTURE, "agent": "greedy"})`
   - Returns 200 with `column: None`, `row: -1`.
7. `test_existing_backend_regression_suite`:
   - All 31 existing tests in `test_game_engine.py`, `test_game_state.py`, `test_foundation.py` pass without modification.

---

## 6. Verification Pipeline & Acceptance Criteria

### Exact Verification Commands:
```powershell
# 1. Run all Agent unit tests + existing backend regression suite (31 tests)
python -m pytest backend/tests/test_agents.py backend/tests/test_game_engine.py backend/tests/test_game_state.py backend/tests/test_foundation.py -v

# 2. Run frontend unit tests
cd frontend; npm test

# 3. Run frontend linter
cd frontend; npm run lint

# 4. Run frontend production build
cd frontend; npm run build
```

### Acceptance Criteria:
- [ ] **AC-1**: `BaseAgent` created with standardized `select_move(board)` signature and strict board immutability.
- [ ] **AC-2**: `RandomAgent` implemented with uniform selection and isolated RNG seeding (`random.Random(seed)`), rejecting boolean seeds.
- [ ] **AC-3**: `GreedyAgent` strictly prioritizes immediate win > immediate block > safe heuristic evaluation.
- [ ] **AC-4**: `GreedyAgent` evaluates all legal opponent replies for every candidate move, strictly preferring safe moves over unsafe moves whenever safe moves exist.
- [ ] **AC-5**: `GreedyAgent` deterministically handles unavoidable loss forks and center-outward tie-breaking (`[3, 2, 4, 1, 5, 0, 6]`).
- [ ] **AC-6**: `POST /api/ai-move` accepts optional `agent` and `seed` parameters while defaulting to Minimax with legacy response semantics.
- [ ] **AC-7**: Unknown agents return HTTP 400 with `INVALID_AGENT`; invalid seeds return `VALIDATION_ERROR`; full boards return `column: null, row: -1`.
- [ ] **AC-8**: Telemetry strictly measures backend `decision_time_ms`, documents `search_depth=1` for Greedy, and leaves inapplicable tree stats as `null`.
- [ ] **AC-9**: Legacy `ai_agent.py` functions and all 31 existing backend tests remain 100% unbroken.
- [ ] **AC-10**: Frontend agent selector is updated to activate Random and Greedy only after backend verification succeeds.
- [ ] **AC-11**: Frontend test suite (10/10), lint (0 errors), and build succeed cleanly.

---

## 7. Scope Boundaries & Files Expected to Change

### Scope Boundaries:
- **Included**: Abstract `BaseAgent`, `RandomAgent`, `GreedyAgent`, `AgentFactory`, `test_agents.py`, `POST /api/ai-move` optional `agent` parameter, and frontend activation of Random and Greedy.
- **Excluded**: Alpha-Beta, Optimized Alpha-Beta, MCTS, transposition tables, and Head-to-Head Benchmarking tournament runners.

### Files to Create:
- `backend/app/agents/__init__.py`
- `backend/app/agents/base_agent.py`
- `backend/app/agents/random_agent.py`
- `backend/app/agents/greedy_agent.py`
- `backend/app/agents/factory.py`
- `backend/tests/test_agents.py`
- `.gsd/phases/4/PLAN.md`

### Files to Modify:
- `backend/app/schemas/game_schemas.py`
- `backend/main.py`
- `frontend/src/services/api.js`
- `frontend/src/hooks/useGame.js`
- `frontend/src/components/GameControls.jsx`
- `.gsd/STATE.md`
- `.gsd/TODO.md`
