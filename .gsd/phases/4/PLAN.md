---
phase: 4
plan: 1
wave: 1
gap_closure: false
---

# Plan 4.1: Baseline AI Agents (Random & Greedy)

## Objective
Establish the modular AI agent architecture under `backend/app/agents/` conforming strictly to PRD §6.1. Implement the abstract `BaseAgent` interface alongside the two baseline agents: `RandomAgent` (with isolated pseudo-random seeding for benchmarking reproducibility) and `GreedyAgent` (with deterministic 1-ply tactical rules: immediate win, immediate block, heuristic position scoring, and center-outward tie-breaking). Expose agent selection through the backend API while preserving 100% backward compatibility for `backend/ai_agent.py`, the existing `POST /api/ai-move` Minimax contract, and all 31 existing backend tests. Update frontend API integration to activate Random and Greedy selection only after the backend implementation is verified.

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
   - Currently displays `Minimax (Active)` and labels all other algorithms `(Phase 4/5)`.

### Compatibility & Architecture Strategy:
- Introduce `backend/app/agents/` package:
  - `base_agent.py`: Abstract `BaseAgent` base class.
  - `random_agent.py`: `RandomAgent` implementation.
  - `greedy_agent.py`: `GreedyAgent` implementation.
  - `factory.py`: `get_agent(agent_id, **kwargs)` factory managing agent instantiations.
  - `__init__.py`: Package exports.
- **Endpoint Evolution (`POST /api/ai-move`)**:
  - Extend `MoveRequest` in `backend/app/schemas/game_schemas.py` to accept optional `agent: Optional[str] = "minimax"` and `seed: Optional[int] = None`.
  - If `agent` is omitted or `"minimax"`, backend delegates to `minimax` with `depth`, preserving exact existing contract.
  - If `agent == "random"`, backend instantiates `RandomAgent(seed=request.seed)`.
  - If `agent == "greedy"`, backend instantiates `GreedyAgent()`.
  - The response returns `{ "column": col, "row": row, "telemetry": { ... } }`.
  - Existing callers expecting only `{"column", "row"}` continue to work without breakage.

---

## 2. Agent Interface Architecture (`BaseAgent`)

In `backend/app/agents/base_agent.py`:

```python
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Tuple, List

class BaseAgent(ABC):
    """
    Abstract base class for all Connect Four adversarial agents (PRD §6.1).
    Agents are stateless with respect to game sessions; board is supplied to select_move().
    """

    def __init__(self, name: str, player_id: int = 2):
        self.name: str = name
        self.player_id: int = player_id
        self.opp_id: int = 1 if player_id == 2 else 2

    @abstractmethod
    def select_move(self, board: List[List[int]]) -> Tuple[Optional[int], Dict[str, Any]]:
        """
        Evaluate current board state and select best legal column.

        Args:
            board: 6x7 integer matrix (0: empty, 1: player 1, 2: player 2).

        Returns:
            Tuple of:
            - selected_column: Integer in [0..6], or None if no legal moves exist.
            - telemetry: Dictionary conforming to TelemetryMetrics schema.
        """
        pass
```

---

## 3. Algorithmic Specifications

### A. Random Agent (`RandomAgent`)
- **Objective**: Minimal baseline agent for benchmarking and sanity evaluation (PRD §6.2).
- **Behavior**:
  1. Retrieve legal columns via `get_valid_locations(board)`.
  2. If `len(valid_locations) == 0` (board full), return `(None, telemetry)`.
  3. Select a column uniformly at random from `valid_locations`.
- **RNG Isolation & Determinism**:
  - Accept optional `seed: Optional[int] = None` in `__init__(seed=...)`.
  - Instantiate an isolated pseudo-random number generator instance `self.rng = random.Random(seed)` rather than using Python's global `random` module.
  - Allows unit tests and benchmarking harnesses to inject a fixed seed for 100% reproducible, deterministic sequences without contaminating global application RNG.
- **Telemetry**:
  - `decision_time_ms`: Float, measured round-trip execution in milliseconds.
  - `nodes_evaluated`: `None` (`null`).
  - `pruned_nodes`: `None` (`null`).
  - `search_depth`: `None` (`null`).
  - `transposition_hits`: `None` (`null`).
  - `candidate_scores`: `None` (`null`).

### B. Greedy Agent (`GreedyAgent`)
- **Objective**: 1-ply tactical lookahead agent prioritizing immediate tactical wins and threat blocks (PRD §6.3).
- **Decision Hierarchy (Strict Priority Order)**:
  1. **Tactical Priority 1: Immediate Winning Move**
     - For each legal column $c \in \text{valid\_locations}$:
       - Simulate dropping agent's piece (`self.player_id`) at `getNextOpenRow(board, c)`.
       - If `check_win(b_sim, self.player_id)` is `True`:
         - **Immediate Cutoff**: Select column $c$ immediately.
         - Return $c$ with telemetry annotation `"reason": "immediate_win"`.
  2. **Tactical Priority 2: Immediate Opponent Threat Block**
     - If no immediate winning move exists for the agent:
     - For each legal column $c \in \text{valid\_locations}$:
       - Simulate dropping opponent's piece (`self.opp_id`) at `getNextOpenRow(board, c)`.
       - If `check_win(b_sim, self.opp_id)` is `True`:
         - **Immediate Cutoff**: Select column $c$ immediately to block the opponent.
         - Return $c$ with telemetry annotation `"reason": "immediate_block"`.
         - If multiple columns block opponent wins (opponent has a split threat), select the first one according to center-outward tie-breaking.
  3. **Tactical Priority 3: Static Board Heuristic Evaluation**
     - If neither Priority 1 nor Priority 2 applies:
     - For each legal column $c \in \text{valid\_locations}$:
       - Simulate dropping piece (`self.player_id`) at `row = getNextOpenRow(board, c)`.
       - **Blunder Avoidance Check**: If placing a disc at $(row, c)$ allows the opponent to drop at $(row - 1, c)$ on their immediate next ply and win (`check_win` on $row - 1$), penalize this move severely (penalty: $-50.0$) unless no other safe move exists.
       - **Positional Scoring**:
         - Center column preference: pieces in column 3 receive a bonus weight of $+3.0$ each.
         - Window evaluation across all 4-cell horizontal, vertical, and diagonal windows:
           - 4 pieces of `player_id`: $+100.0$
           - 3 pieces of `player_id` + 1 empty: $+5.0$
           - 2 pieces of `player_id` + 2 empty: $+2.0$
           - 3 pieces of `opp_id` + 1 empty: $-4.0$ (penalizes setting up opponent 3-in-a-rows)
           - 2 pieces of `opp_id` + 2 empty: $-1.0$
- **Deterministic Tie-Breaking**:
  - Center-outward preference list: `[3, 2, 4, 1, 5, 0, 6]`.
  - When two or more columns have identical highest heuristic scores, the tie is broken deterministically by choosing the column that appears earlier in the center-outward list.
  - This guarantees 100% deterministic, testable behavior for the Greedy agent.
- **Telemetry**:
  - `decision_time_ms`: Float, measured evaluation time in milliseconds.
  - `candidate_scores`: List of `{ "column": c, "score": float, "reason": "win" | "block" | "heuristic" }` for all evaluated columns.
  - `search_depth`: `1` (1-ply lookahead).
  - `nodes_evaluated`: `None` (`null`).
  - `pruned_nodes`: `None` (`null`).
  - `transposition_hits`: `None` (`null`).

---

## 4. API Schema & Endpoint Integration

### Request Schema (`backend/app/schemas/game_schemas.py`):
```python
class MoveRequest(BaseModel):
    column: Optional[int] = Field(None, description="Selected column index")
    board: Optional[List[List[int]]] = Field(None, description="Current 6x7 board state")
    depth: Optional[int] = Field(4, description="Search depth for minimax algorithms")
    agent: Optional[str] = Field("minimax", description="AI algorithm identifier: 'random', 'greedy', 'minimax'")
    seed: Optional[int] = Field(None, description="Optional seed for random agent reproducibility")
```

### Response Schema:
```python
class AIMoveResponse(BaseModel):
    column: Optional[int] = Field(..., description="Selected column index (0-6) or null if full")
    row: int = Field(..., description="Target row index (0-5) or -1 if full")
    telemetry: Optional[TelemetryMetrics] = Field(None, description="Authentic telemetry metrics")
```

### Frontend Agent Selector Activation Timeline:
- **Phase 3 State**: `Minimax` is labeled `(Active)`, while other agents are labeled `(Phase 4/5)` because the backend only supported Minimax.
- **Phase 4 Implementation**:
  1. Once `backend/app/agents/` and the updated `POST /api/ai-move` endpoint are implemented and verified via unit tests, update `frontend/src/services/api.js` to pass `{ board, depth, agent: selectedAlgorithm }`.
  2. Update `frontend/src/components/GameControls.jsx` so `Random Agent` and `Greedy Agent` are promoted to `(Active)`.
  3. `Alpha-Beta Pruning`, `Optimized Alpha-Beta`, and `MCTS` remain labeled `(Phase 5)`.
- **Constraint**: We will not claim the frontend selector is functional for Random/Greedy until backend support is verified.

---

## 5. Telemetry Accuracy & Anti-Fabrication Invariants

| Telemetry Metric | `RandomAgent` | `GreedyAgent` | Phase 3 Legacy Minimax |
|---|---|---|---|
| `decision_time_ms` | **Measured float** | **Measured float** | **Measured client round-trip** |
| `search_depth` | `null` (`N/A`) | `1` (1-ply) | `depth` (2, 4, 6) |
| `candidate_scores` | `null` (`N/A`) | **Dict list** (evaluated columns) | `null` (`N/A`) |
| `nodes_evaluated` | `null` (`N/A`) | `null` (`N/A`) | `null` (`N/A` until Phase 5) |
| `pruned_nodes` | `null` (`N/A`) | `null` (`N/A`) | `null` (`N/A` until Phase 5) |
| `transposition_hits` | `null` (`N/A`) | `null` (`N/A`) | `null` (`N/A` until Phase 5) |
| `mcts_iterations` | `null` (`N/A`) | `null` (`N/A`) | `null` (`N/A`) |

- **Strict Invariant**: No synthetic numbers will be returned. Inapplicable metrics are explicitly `null` in JSON and render as `N/A` in the frontend UI.

---

## 6. Comprehensive Pytest Test Suite (`backend/tests/test_agents.py`)

### A. Random Agent Tests
1. `test_random_agent_isolated_seed_reproducibility`:
   - Instantiates two `RandomAgent(seed=42)` instances.
   - Verifies they select identical column sequences across 10 distinct board states.
2. `test_random_agent_only_selects_legal_columns`:
   - Fill columns 0, 1, 2, 4, 5, 6 so only column 3 is open.
   - Run 50 trials; assert `RandomAgent` returns column 3 in 100% of trials.
3. `test_random_agent_full_board_returns_none`:
   - Call `select_move()` on `DRAW_BOARD_FIXTURE`.
   - Asserts returned column is `None` without raising unhandled exceptions.
4. `test_random_agent_telemetry_schema`:
   - Asserts `decision_time_ms > 0` and all tree metrics are strictly `None`.

### B. Greedy Agent Tests
1. `test_greedy_immediate_horizontal_win`:
   - Agent has 3 pieces at `(5, 0), (5, 1), (5, 2)`. Column 3 is open.
   - Asserts Greedy selects column 3 immediately.
2. `test_greedy_immediate_vertical_win`:
   - Agent has 3 pieces at `(5, 4), (4, 4), (3, 4)`. Column 4 has row 2 open.
   - Asserts Greedy selects column 4 immediately.
3. `test_greedy_immediate_diagonal_win`:
   - Agent has positive and negative diagonal 3-in-a-row opportunities.
   - Asserts Greedy drops into the winning column.
4. `test_greedy_immediate_block_horizontal`:
   - Opponent has 3 pieces at `(5, 1), (5, 2), (5, 3)`. Column 0 and Column 4 are open.
   - Asserts Greedy blocks in column 0 or 4.
5. `test_greedy_immediate_block_vertical`:
   - Opponent has 3 pieces at `(5, 2), (4, 2), (3, 2)`. Row 2 in col 2 is open.
   - Asserts Greedy blocks in column 2 immediately.
6. `test_greedy_prefers_win_over_block`:
   - Board setup where Agent has an immediate winning move in col 5, AND Opponent has an immediate winning move in col 1.
   - Asserts Greedy selects column 5 (win takes strict priority over block!).
7. `test_greedy_center_outward_tie_breaking`:
   - On an empty board, all columns evaluate symmetrically.
   - Asserts Greedy selects center column 3.
8. `test_greedy_avoids_blunder_setup`:
   - Board where dropping in column 2 sets up an immediate winning cell above it for the opponent.
   - Asserts Greedy avoids column 2 when safe alternatives exist.
9. `test_greedy_full_board_returns_none`:
   - Call `select_move()` on full board fixture; asserts `(None, telemetry)` returned.

### C. Agent Factory & API Integration Tests
1. `test_agent_factory_instantiation`:
   - `create_agent("random")` returns `RandomAgent`.
   - `create_agent("greedy")` returns `GreedyAgent`.
   - `create_agent("unknown")` raises `ValueError` or `GameRuleException`.
2. `test_api_ai_move_agent_selection_random`:
   - `client.post("/api/ai-move", json={"board": empty_board, "agent": "random", "seed": 42})` returns 200 with valid column and row.
3. `test_api_ai_move_agent_selection_greedy`:
   - `client.post("/api/ai-move", json={"board": winning_setup_board, "agent": "greedy"})` returns 200 with the exact winning column.
4. `test_api_ai_move_backward_compatibility_preserved`:
   - Calling `POST /api/ai-move` without `agent` parameter returns 200 using Minimax with keys `{"column", "row"}`.

---

## 7. Verification Commands & Acceptance Criteria

### Verification Commands:
```powershell
# 1. Run all new Agent unit tests and existing backend test suite
python -m pytest backend/tests/test_agents.py backend/tests/test_game_engine.py backend/tests/test_game_state.py backend/tests/test_foundation.py -v

# 2. Run frontend unit tests
cd frontend; npm test

# 3. Run frontend linter
cd frontend; npm run lint

# 4. Run frontend production build
cd frontend; npm run build
```

### Acceptance Criteria:
- [ ] **AC-1**: Abstract `BaseAgent` created with standardized `select_move(board)` signature and player ID support.
- [ ] **AC-2**: `RandomAgent` implemented with uniform selection and isolated RNG seeding (`random.Random(seed)`).
- [ ] **AC-3**: `GreedyAgent` implemented with strict priority hierarchy: immediate win > immediate block > heuristic evaluation with blunder avoidance.
- [ ] **AC-4**: `GreedyAgent` implements deterministic center-outward tie-breaking (`[3, 2, 4, 1, 5, 0, 6]`).
- [ ] **AC-5**: `POST /api/ai-move` accepts optional `agent` parameter (`"random"`, `"greedy"`, `"minimax"`) while defaulting to `"minimax"`.
- [ ] **AC-6**: Telemetry is authentic: `decision_time_ms` is measured; inapplicable metrics strictly return `None`/`null`.
- [ ] **AC-7**: Legacy `ai_agent.py` and existing `POST /api/ai-move` contract remain completely unbroken.
- [ ] **AC-8**: All new agent tests in `test_agents.py` pass; all 31 existing backend tests pass (zero regressions).
- [ ] **AC-9**: Frontend `GameControls.jsx` and `api.js` updated to activate Random and Greedy selection only after backend verification.
- [ ] **AC-10**: Frontend tests (10/10), lint (0 errors), and build succeed cleanly.

---

## 8. Files Expected to Change
- **New Files**:
  - `backend/app/agents/__init__.py`
  - `backend/app/agents/base_agent.py`
  - `backend/app/agents/random_agent.py`
  - `backend/app/agents/greedy_agent.py`
  - `backend/app/agents/factory.py`
  - `backend/tests/test_agents.py`
  - `.gsd/phases/4/PLAN.md`
- **Modified Files**:
  - `backend/app/schemas/game_schemas.py`
  - `backend/main.py`
  - `frontend/src/services/api.js`
  - `frontend/src/hooks/useGame.js`
  - `frontend/src/components/GameControls.jsx`
  - `.gsd/STATE.md`
  - `.gsd/TODO.md`
  - `.gsd/ROADMAP.md`
