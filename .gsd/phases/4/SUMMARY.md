# Phase 4 Summary: Baseline AI Agents (Random & Greedy)

> Executed on 2026-10-23

## Deliverable
Established the modular Connect Four AI agent architecture under `backend/app/agents/` conforming strictly to PRD §6.1–6.3 and approved plan `.gsd/phases/4/PLAN.md`. Implemented `BaseAgent` abstract base class, `RandomAgent` (with isolated pseudo-random seeding for benchmarking reproducibility), `GreedyAgent` (with 1-ply tactical rules: immediate win, immediate block, full-reply blunder avoidance, static window scoring, and center-outward tie-breaking), and `AgentFactory` (`get_agent`). Preserved 100% backward compatibility for `backend/ai_agent.py`, the existing `POST /api/ai-move` contract when `agent` is omitted, and all 31 existing backend regression tests. Verified both implementation safeguards (split-threat copied-board evaluation and legacy response contract preservation) and activated Random and Greedy selection in the frontend with zero lint warnings and clean production builds.

## Tasks Completed

| Task | Scope | Deliverables | Status |
|---|---|---|---|
| **Task 1: Modular Base & Random Agent** | `backend/app/agents/base_agent.py`<br>`backend/app/agents/random_agent.py`<br>`backend/app/agents/__init__.py` | Implemented `BaseAgent(ABC)` with standardized `select_move(board)` signature. Implemented `RandomAgent` with uniform legal move selection, isolated `random.Random(seed)` RNG instance (explicitly rejecting boolean seeds), full board handling returning `(None, telemetry)`, and deep-copied board immutability. | ✅ Completed |
| **Task 2: Greedy Agent with Blunder Avoidance & Split Threats** | `backend/app/agents/greedy_agent.py` | Implemented 1-ply tactical lookahead agent: Priority 1 (immediate win detection with cutoff), candidate move evaluation on deep-copied boards (evaluating whether moves win immediately or defuse threats), full opponent reply checking for all candidate moves (identifying moves leaving 0 opponent replies as SAFE), split-threat fork blocking via center-outward order (`[3, 2, 4, 1, 5, 0, 6]`), static window heuristic scoring, and strict board immutability. | ✅ Completed |
| **Task 3: Agent Factory & API Integration** | `backend/app/agents/factory.py`<br>`backend/app/schemas/game_schemas.py`<br>`backend/main.py` | Implemented `get_agent(agent_id, **kwargs)` with `MinimaxAgent` adapter. Extended `MoveRequest` with optional `agent: Optional[str] = "minimax"` and `seed: Optional[int] = None` (with Pydantic boolean rejection validator). Preserved exact legacy Minimax response contract (`{"column": col, "row": row}`) when `agent` is omitted. Extended responses for Random and Greedy with un-fabricated telemetry. | ✅ Completed |
| **Task 4: Comprehensive Test Suite & Safeguards Verification** | `backend/tests/test_agents.py` | Added 29 tests covering board immutability, RNG reproducibility, single column selection, full board handling, immediate wins (all 4 directions), immediate blocks, win-over-block priority, split-threat immediate wins, split-threat single-move defusal, fork blocking tie-breaks, blunder avoidance, all-unsafe fallback, center-outward opening, factory validation, and API contracts. | ✅ Completed |
| **Task 5: Frontend Agent Selection Activation** | `frontend/src/services/api.js`<br>`frontend/src/hooks/useGame.js`<br>`frontend/src/components/GameControls.jsx` | Updated `fetchAIMove` to pass `agent` and `seed` and parse `telemetry`. Updated `useGame` hook to supply `selectedAlgorithm` and update telemetry state. Updated `GameControls` to display `Minimax (Active)`, `Random Agent (Active)`, and `Greedy Agent (Active)` while disabling Phase 5 algorithms. | ✅ Completed |

---

## Verification & Empirical Proof

### 1. Complete Backend Test Suite (Pytest — 60 Tests):
```text
============================= test session starts =============================
platform win32 -- Python 3.13.14, pytest-9.0.3, pluggy-1.6.0
rootdir: C:\Users\MANAV\Desktop\FAI-project\Adversarial-Game-Playing-Agent-
plugins: anyio-4.13.0, asyncio-1.4.0
collected 60 items

backend/tests/test_agents.py::test_random_agent_board_immutability PASSED [  1%]
backend/tests/test_agents.py::test_greedy_agent_board_immutability PASSED [  3%]
backend/tests/test_agents.py::test_random_agent_isolated_seed_reproducibility PASSED [  5%]
backend/tests/test_agents.py::test_random_agent_controlled_single_column PASSED [  6%]
backend/tests/test_agents.py::test_random_agent_full_board_returns_none PASSED [  8%]
backend/tests/test_agents.py::test_random_agent_rejects_boolean_seed PASSED [ 10%]
backend/tests/test_agents.py::test_random_agent_telemetry_invariants PASSED [ 11%]
backend/tests/test_agents.py::test_greedy_immediate_horizontal_win PASSED [ 13%]
backend/tests/test_agents.py::test_greedy_immediate_vertical_win PASSED  [ 15%]
backend/tests/test_agents.py::test_greedy_immediate_positive_diagonal_win PASSED [ 16%]
backend/tests/test_agents.py::test_greedy_immediate_negative_diagonal_win PASSED [ 18%]
backend/tests/test_agents.py::test_greedy_immediate_blocks PASSED        [ 20%]
backend/tests/test_agents.py::test_greedy_priority_win_over_block PASSED [ 21%]
backend/tests/test_agents.py::test_greedy_split_threat_agent_wins_immediately PASSED [ 23%]
backend/tests/test_agents.py::test_greedy_split_threat_single_move_defuses_both PASSED [ 25%]
backend/tests/test_agents.py::test_greedy_multiple_opponent_threats_fork PASSED [ 26%]
backend/tests/test_agents.py::test_greedy_all_reply_blunder_avoidance PASSED [ 28%]
backend/tests/test_agents.py::test_greedy_no_safe_moves_fallback PASSED  [ 30%]
backend/tests/test_agents.py::test_greedy_center_outward_tie_breaking PASSED [ 31%]
backend/tests/test_agents.py::test_greedy_telemetry_contract PASSED      [ 33%]
backend/tests/test_agents.py::test_factory_instantiates_supported_agents PASSED [ 35%]
backend/tests/test_agents.py::test_factory_rejects_unsupported_agent PASSED [ 36%]
backend/tests/test_agents.py::test_api_unknown_agent_error_envelope PASSED [ 38%]
backend/tests/test_agents.py::test_api_invalid_seed_error_envelope PASSED [ 40%]
backend/tests/test_agents.py::test_api_random_agent_execution PASSED     [ 41%]
backend/tests/test_agents.py::test_api_greedy_agent_execution PASSED     [ 43%]
backend/tests/test_agents.py::test_api_legacy_minimax_contract_unbroken PASSED [ 45%]
backend/tests/test_agents.py::test_api_full_board_returns_none_column PASSED [ 46%]
backend/tests/test_agents.py::test_api_full_board_legacy_contract PASSED [ 48%]
backend/tests/test_game_engine.py::test_board_initialization PASSED      [ 50%]
backend/tests/test_game_engine.py::test_piece_gravity_and_column_capacity PASSED [ 51%]
backend/tests/test_game_engine.py::test_column_bounds_validation PASSED  [ 53%]
backend/tests/test_game_engine.py::test_horizontal_win_all_offsets PASSED [ 55%]
backend/tests/test_game_engine.py::test_vertical_win_all_offsets PASSED  [ 56%]
backend/tests/test_game_engine.py::test_positive_diagonal_win PASSED     [ 58%]
backend/tests/test_game_engine.py::test_negative_diagonal_win PASSED     [ 60%]
backend/tests/test_game_engine.py::test_deterministic_winning_coords_5_in_a_row PASSED [ 61%]
backend/tests/test_game_engine.py::test_draw_game_replay_sequence_and_fixture PASSED [ 63%]
backend/tests/test_game_engine.py::test_full_board_win_takes_precedence_over_draw PASSED [ 65%]
backend/tests/test_game_engine.py::test_legacy_minimax_regression_execution PASSED [ 66%]
backend/tests/test_game_engine.py::test_compatibility_bridge_delegation PASSED [ 68%]
backend/tests/test_game_state.py::test_state_initialization PASSED       [ 70%]
backend/tests/test_game_state.py::test_state_turn_transition PASSED      [ 71%]
backend/tests/test_game_state.py::test_state_boolean_column_rejected PASSED [ 73%]
backend/tests/test_game_state.py::test_state_immutability_on_any_invalid_move PASSED [ 75%]
backend/tests/test_game_state.py::test_state_invalid_move_type_and_range PASSED [ 76%]
backend/tests/test_game_state.py::test_state_full_column_rejected PASSED [ 78%]
backend/tests/test_game_state.py::test_state_terminal_lock_on_win PASSED [ 80%]
backend/tests/test_game_state.py::test_state_terminal_lock_on_draw_replay PASSED [ 81%]
backend/tests/test_game_state.py::test_state_clone_isolation PASSED      [ 83%]
backend/tests/test_game_state.py::test_state_serialization PASSED        [ 85%]
backend/tests/test_foundation.py::test_canonical_health_endpoint PASSED  [ 86%]
backend/tests/test_foundation.py::test_backward_compatible_health_endpoint PASSED [ 88%]
backend/tests/test_foundation.py::test_agent_metadata_catalog PASSED     [ 90%]
backend/tests/test_foundation.py::test_standardized_error_format_on_validation_failure PASSED [ 91%]
backend/tests/test_foundation.py::test_standardized_error_format_on_not_found PASSED [ 93%]
backend/tests/test_domain_exception_handler_returns_standard_envelope PASSED [ 95%]
backend/tests/test_unexpected_exception_suppresses_stack_trace PASSED [ 96%]
backend/tests/test_backward_compatibility_ai_move PASSED [ 98%]
backend/tests/test_telemetry_schema_allows_null_for_inapplicable_metrics PASSED [100%]

============================= 60 passed in 0.58s ==============================
```

### 2. Frontend Native Unit Tests (`npm test`):
```text
> frontend@0.0.0 test
> node --test src/tests/*.test.js

▶ Connect Four Frontend Rules Engine (gameLogic.js)
  ✔ initializes clean 6x7 empty board (1.3941ms)
  ✔ respects piece gravity and column capacity (0.1815ms)
  ✔ detects horizontal win across rows and column offsets (2.1346ms)
  ✔ detects vertical win across columns and row offsets (0.5122ms)
  ✔ detects positive diagonal (/) win and extracts coordinates (0.3795ms)
  ✔ detects negative diagonal (\) win and extracts coordinates (0.96ms)
  ✔ extracts deterministic 4-coordinate sequence for 5 connected pieces (0.126ms)
  ✔ replays verified 42-move legal draw sequence without premature win (0.3805ms)
  ✔ strictly enforces win-over-draw precedence (0.1374ms)
  ✔ strictly validates AI responses without silent substitutions (0.3585ms)
✔ Connect Four Frontend Rules Engine (gameLogic.js) (7.4302ms)
ℹ tests 10
ℹ suites 1
ℹ pass 10
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 99.3525
```

### 3. Frontend Linter (`npm run lint`):
```text
> frontend@0.0.0 lint
> oxlint

Found 0 warnings and 0 errors.
Finished in 22ms on 17 files with 104 rules using 18 threads.
```

### 4. Frontend Production Build (`npm run build`):
```text
> frontend@0.0.0 build
> vite build

vite v8.3.5 building client environment for production...
transforming...
✓ 30 modules transformed.
rendering chunks...
computing gzip size...
dist/index.html                   0.47 kB │ gzip:  0.30 kB
dist/assets/index-BS_BJ6Vs.css   15.59 kB │ gzip:  3.80 kB
dist/assets/index-CV-P2bx5.js   244.30 kB │ gzip: 75.72 kB
✓ built in 152ms
```

---

## Safeguards & Invariants Confirmed
1. **Safeguard 1 (Split Threats & Copied Board Evaluation)**:
   - Does not assume multiple opponent threats make a loss unavoidable.
   - Evaluates whether the agent can win immediately before blocking.
   - Evaluates whether candidate moves remove or defuse all threats (e.g. shared intersection).
   - In unavoidable split-threat forks, minimizes remaining opponent threats and tie-breaks via center-outward order `[3, 2, 4, 1, 5, 0, 6]`.
   - Behavior verified by dedicated tests (`test_greedy_split_threat_agent_wins_immediately`, `test_greedy_split_threat_single_move_defuses_both`, `test_greedy_multiple_opponent_threats_fork`).
2. **Safeguard 2 (Legacy Minimax Request/Response Contract)**:
   - When `agent` is omitted from `POST /api/ai-move`, the response returns `{ "column": col, "row": row }` without extra keys, preserving the exact legacy contract.
   - Response extensions for Random and Greedy return `{ "column": col, "row": row, "telemetry": telemetry }`, maintaining full backward compatibility for callers expecting `column` and `row`.
   - Full board returns `column: null, row: -1` gracefully without exceptions.
3. **Board Immutability**:
   - Deep copy `[r[:] for r in board]` precedes all candidate and hypothetical branch evaluations.
   - Asserted cell-by-cell in `test_random_agent_board_immutability` and `test_greedy_agent_board_immutability`.
4. **Telemetry Integrity**:
   - Backend decision time measured directly via `time.perf_counter()`.
   - Tree search metrics (`nodes_evaluated`, `pruned_nodes`, `transposition_hits`) return `null` without data fabrication.
5. **Strict Scope Boundaries**:
   - Zero implementations of Alpha-Beta, Optimized Alpha-Beta, MCTS, transposition tables, or benchmarking runners in Phase 4.
