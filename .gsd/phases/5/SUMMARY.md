# Phase 5 Summary: Advanced Search Agents (Minimax, Alpha-Beta, Optimized Alpha-Beta & MCTS)

> Executed on 2026-10-23

## Deliverable
Implemented the complete advanced adversarial and simulation search agent suite under `backend/app/agents/` conforming strictly to PRD §6.4–6.6, REQ-FR-04, REQ-FR-05, REQ-FR-09, and approved plan `.gsd/phases/5/PLAN.md`.
Delivered:
1. `backend/app/core/evaluation.py`: Centralized heuristic scoring (`evaluate_window`, `score_position`) and terminal values (`WIN_SCORE`, `LOSS_SCORE`, `DRAW_SCORE`) shared across all game-tree search agents.
2. `MinimaxAgent` (`backend/app/agents/minimax_agent.py`): Full depth-limited tree recursion, accurate `nodes_evaluated` counting, deterministic column tie-breaking `[0..6]`, and board immutability.
3. `AlphaBetaAgent` (`backend/app/agents/alphabeta_agent.py`): Alpha-beta branch pruning, mathematically guaranteed score equivalence with Minimax, accurate `pruned_nodes` counting, and shared natural column ordering.
4. `OptimizedAlphaBetaAgent` (`backend/app/agents/optimized_agent.py`): Center-outward move ordering `[3, 2, 4, 1, 5, 0, 6]`, transposition table caching with typed bounds (`EXACT`, `LOWER`, `UPPER`), bound safety (never treating lower/upper bounds as exact when $\alpha < \beta$), and 1-ply immediate-win cutoff logic.
5. `MCTSAgent` (`backend/app/agents/mcts_agent.py`): 4-step cycle (UCT Selection, Expansion, Rollout Simulation, Backpropagation), symmetric node-to-move reward perspective (`player_just_moved`), visit-count root selection, isolated pseudo-random seeding, and authentic `mcts_iterations` / `mcts_simulations` telemetry.
6. Unified factory registration in `backend/app/agents/factory.py` and `backend/app/agents/__init__.py` supporting all 6 agents.
7. Backward-compatible API integration in `backend/main.py` and `backend/app/schemas/game_schemas.py` preserving the exact legacy Minimax contract (`{"column": col, "row": row}`) when `agent` is omitted.
8. Interactive frontend integration in `frontend/src/components/GameControls.jsx`, `MetricsPanel.jsx`, and `useGame.js` activating all 6 agents with dynamic telemetry for both tree search and simulation agents.
9. Comprehensive test suite `backend/tests/test_advanced_search.py` with 27 rigorous unit and integration tests.

---

## Tasks Completed

| Task | Scope | Deliverables | Status |
|---|---|---|---|
| **Task 1: Shared Evaluation Module** | `backend/app/core/evaluation.py` | Implemented centralized heuristic scoring with 4-cell window weights (+100 for 4, +5 for 3, +2 for 2, -4 for opp 3, -1 for opp 2), center column preference (+3 per disc), and standardized terminal constants (`WIN_SCORE = 10_000_000.0`, `LOSS_SCORE = -10_000_000.0`, `DRAW_SCORE = 0.0`). | ✅ Completed |
| **Task 2: Minimax Agent** | `backend/app/agents/minimax_agent.py` | Implemented `MinimaxAgent(BaseAgent)` with depth-limited full-tree recursive search, entry-level `nodes_evaluated` tracking, deterministic tie-breaking on natural column order `[0..6]`, and strict board immutability. | ✅ Completed |
| **Task 3: Alpha-Beta Agent** | `backend/app/agents/alphabeta_agent.py` | Implemented `AlphaBetaAgent(BaseAgent)` with $\alpha$-$\beta$ branch cutoffs, `pruned_nodes` counting, identical move ordering and tie-breaking to Minimax, guaranteeing exact mathematical score equivalence while pruning branches. | ✅ Completed |
| **Task 4: Optimized Alpha-Beta Agent** | `backend/app/agents/optimized_agent.py` | Implemented `OptimizedAlphaBetaAgent(BaseAgent)` with center-outward dynamic move ordering, typed transposition table caching (`EXACT`, `LOWER`, `UPPER`), bound safety checks, `transposition_hits` tracking, and 1-ply immediate-win cutoffs. | ✅ Completed |
| **Task 5: MCTS Agent** | `backend/app/agents/mcts_agent.py` | Implemented `MCTSAgent(BaseAgent)` with full 4-step cycle, symmetric UCT child selection across player turns, backpropagation from `player_just_moved` perspective, visit-count move selection, isolated `random.Random(seed)` instance, and PRD §13.3 compliant telemetry. | ✅ Completed |
| **Task 6: Factory Registration & API Integration** | `backend/app/agents/factory.py`<br>`backend/app/agents/__init__.py`<br>`backend/app/schemas/game_schemas.py`<br>`backend/main.py` | Registered all 6 agents (`random`, `greedy`, `minimax`, `alphabeta`, `optimized`, `mcts`). Added Pydantic field validators for `depth`, `seed`, and `iterations`. Preserved exact legacy Minimax contract when `agent` is omitted. | ✅ Completed |
| **Task 7: Comprehensive Test Suite** | `backend/tests/test_advanced_search.py` | Added 27 tests covering board immutability, score/move equivalence, pruning efficiency, transposition table bound safety and cache hits, MCTS immediate win/block/seed reproducibility, alternating-player reward perspective, and API contracts. | ✅ Completed |
| **Task 8: Frontend Controls & Telemetry HUD** | `frontend/src/services/api.js`<br>`frontend/src/components/GameControls.jsx`<br>`frontend/src/components/MetricsPanel.jsx`<br>`frontend/src/hooks/useGame.js`<br>`frontend/src/pages/GamePage.jsx` | Activated all 6 agents as `(Active)`. Adapted difficulty select for MCTS iterations vs tree depth. Dynamically rendered decision time, search horizon, nodes evaluated, pruned branches, transposition hits, and MCTS iterations/simulations. | ✅ Completed |

---

## Verification & Empirical Proof

### 1. Complete Backend Test Suite (Pytest — 87 Tests):
```text
============================= test session starts =============================
platform win32 -- Python 3.13.14, pytest-9.0.3, pluggy-1.6.0
rootdir: C:\Users\MANAV\Desktop\FAI-project\Adversarial-Game-Playing-Agent-
plugins: anyio-4.13.0, asyncio-1.4.0
collected 87 items

backend/tests/test_advanced_search.py::test_minimax_agent_board_immutability PASSED [  1%]
backend/tests/test_advanced_search.py::test_alphabeta_agent_board_immutability PASSED [  2%]
backend/tests/test_advanced_search.py::test_optimized_agent_board_immutability PASSED [  3%]
backend/tests/test_advanced_search.py::test_mcts_agent_board_immutability PASSED [  4%]
backend/tests/test_advanced_search.py::test_minimax_and_alphabeta_score_equivalence PASSED [  5%]
backend/tests/test_advanced_search.py::test_minimax_and_alphabeta_unique_move_equivalence PASSED [  6%]
backend/tests/test_advanced_search.py::test_alphabeta_pruning_efficiency PASSED [  8%]
backend/tests/test_advanced_search.py::test_terminal_scoring_consistency PASSED [  9%]
backend/tests/test_advanced_search.py::test_optimized_alphabeta_score_equivalence PASSED [ 10%]
backend/tests/test_advanced_search.py::test_optimized_alphabeta_unique_move_equivalence PASSED [ 11%]
backend/tests/test_advanced_search.py::test_optimized_alphabeta_move_ordering_validation PASSED [ 12%]
backend/tests/test_advanced_search.py::test_transposition_table_enabled_vs_disabled PASSED [ 13%]
backend/tests/test_advanced_search.py::test_transposition_table_cache_hits PASSED [ 14%]
backend/tests/test_advanced_search.py::test_transposition_bound_safety PASSED [ 16%]
backend/tests/test_advanced_search.py::test_optimized_immediate_win_cutoff PASSED [ 17%]
backend/tests/test_advanced_search.py::test_mcts_immediate_win_discovery PASSED [ 18%]
backend/tests/test_advanced_search.py::test_mcts_immediate_block_discovery PASSED [ 19%]
backend/tests/test_advanced_search.py::test_mcts_seed_reproducibility PASSED [ 20%]
backend/tests/test_advanced_search.py::test_mcts_iteration_budget_enforcement PASSED [ 21%]
backend/tests/test_advanced_search.py::test_mcts_terminal_root_handling PASSED [ 22%]
backend/tests/test_advanced_search.py::test_mcts_telemetry_isolation PASSED [ 24%]
backend/tests/test_advanced_search.py::test_mcts_alternating_player_selection_and_rewards PASSED [ 25%]
backend/tests/test_advanced_search.py::test_api_advanced_agents_execution PASSED [ 26%]
backend/tests/test_advanced_search.py::test_api_legacy_minimax_contract_unbroken PASSED [ 27%]
backend/tests/test_advanced_search.py::test_api_full_board_handling PASSED [ 28%]
backend/tests/test_advanced_search.py::test_api_iterations_validation PASSED [ 29%]
backend/tests/test_advanced_search.py::test_api_depth_validation PASSED  [ 31%]
backend/tests/test_agents.py::test_random_agent_board_immutability PASSED [ 32%]
backend/tests/test_agents.py::test_greedy_agent_board_immutability PASSED [ 33%]
backend/tests/test_agents.py::test_random_agent_isolated_seed_reproducibility PASSED [ 34%]
backend/tests/test_agents.py::test_random_agent_controlled_single_column PASSED [ 35%]
backend/tests/test_agents.py::test_random_agent_full_board_returns_none PASSED [ 36%]
backend/tests/test_agents.py::test_random_agent_rejects_boolean_seed PASSED [ 37%]
backend/tests/test_agents.py::test_random_agent_telemetry_invariants PASSED [ 39%]
backend/tests/test_agents.py::test_greedy_immediate_horizontal_win PASSED [ 40%]
backend/tests/test_agents.py::test_greedy_immediate_vertical_win PASSED  [ 41%]
backend/tests/test_agents.py::test_greedy_immediate_positive_diagonal_win PASSED [ 42%]
backend/tests/test_agents.py::test_greedy_immediate_negative_diagonal_win PASSED [ 43%]
backend/tests/test_agents.py::test_greedy_immediate_blocks PASSED        [ 44%]
backend/tests/test_agents.py::test_greedy_priority_win_over_block PASSED [ 45%]
backend/tests/test_agents.py::test_greedy_split_threat_agent_wins_immediately PASSED [ 47%]
backend/tests/test_agents.py::test_greedy_split_threat_single_move_defuses_both PASSED [ 48%]
backend/tests/test_agents.py::test_greedy_multiple_opponent_threats_fork PASSED [ 49%]
backend/tests/test_agents.py::test_greedy_all_reply_blunder_avoidance PASSED [ 50%]
backend/tests/test_agents.py::test_greedy_no_safe_moves_fallback PASSED  [ 51%]
backend/tests/test_agents.py::test_greedy_center_outward_tie_breaking PASSED [ 52%]
backend/tests/test_agents.py::test_greedy_telemetry_contract PASSED      [ 54%]
backend/tests/test_agents.py::test_factory_instantiates_supported_agents PASSED [ 55%]
backend/tests/test_agents.py::test_factory_rejects_unsupported_agent PASSED [ 56%]
backend/tests/test_agents.py::test_api_unknown_agent_error_envelope PASSED [ 57%]
backend/tests/test_agents.py::test_api_invalid_seed_error_envelope PASSED [ 58%]
backend/tests/test_agents.py::test_api_random_agent_execution PASSED     [ 59%]
backend/tests/test_agents.py::test_api_greedy_agent_execution PASSED     [ 60%]
backend/tests/test_agents.py::test_api_legacy_minimax_contract_unbroken PASSED [ 62%]
backend/tests/test_agents.py::test_api_full_board_returns_none_column PASSED [ 63%]
backend/tests/test_agents.py::test_api_full_board_legacy_contract PASSED [ 64%]
backend/tests/test_foundation.py::test_canonical_health_endpoint PASSED  [ 65%]
backend/tests/test_foundation.py::test_backward_compatible_health_endpoint PASSED [ 66%]
backend/tests/test_foundation.py::test_agent_metadata_catalog PASSED     [ 67%]
backend/tests/test_foundation.py::test_standardized_error_format_on_validation_failure PASSED [ 68%]
backend/tests/test_foundation.py::test_standardized_error_format_on_not_found PASSED [ 70%]
backend/tests/test_foundation.py::test_domain_exception_handler_returns_standard_envelope PASSED [ 71%]
backend/tests/test_foundation.py::test_unexpected_exception_suppresses_stack_trace PASSED [ 72%]
backend/tests/test_foundation.py::test_backward_compatibility_ai_move PASSED [ 73%]
backend/tests/test_foundation.py::test_telemetry_schema_allows_null_for_inapplicable_metrics PASSED [ 74%]
backend/tests/test_game_engine.py::test_board_initialization PASSED      [ 75%]
backend/tests/test_game_engine.py::test_piece_gravity_and_column_capacity PASSED [ 77%]
backend/tests/test_game_engine.py::test_column_bounds_validation PASSED  [ 78%]
backend/tests/test_game_engine.py::test_horizontal_win_all_offsets PASSED [ 79%]
backend/tests/test_game_engine.py::test_vertical_win_all_offsets PASSED  [ 80%]
backend/tests/test_game_engine.py::test_positive_diagonal_win PASSED     [ 81%]
backend/tests/test_game_engine.py::test_negative_diagonal_win PASSED     [ 82%]
backend/tests/test_game_engine.py::test_deterministic_winning_coords_5_in_a_row PASSED [ 83%]
backend/tests/test_game_engine.py::test_draw_game_replay_sequence_and_fixture PASSED [ 85%]
backend/tests/test_game_engine.py::test_full_board_win_takes_precedence_over_draw PASSED [ 86%]
backend/tests/test_game_engine.py::test_legacy_minimax_regression_execution PASSED [ 87%]
backend/tests/test_game_engine.py::test_compatibility_bridge_delegation PASSED [ 88%]
backend/tests/test_game_state.py::test_state_initialization PASSED       [ 89%]
backend/tests/test_game_state.py::test_state_turn_transition PASSED      [ 90%]
backend/tests/test_game_state.py::test_state_boolean_column_rejected PASSED [ 91%]
backend/tests/test_game_state.py::test_state_immutability_on_any_invalid_move PASSED [ 93%]
backend/tests/test_game_state.py::test_state_invalid_move_type_and_range PASSED [ 94%]
backend/tests/test_game_state.py::test_state_full_column_rejected PASSED [ 95%]
backend/tests/test_game_state.py::test_state_terminal_lock_on_win PASSED [ 96%]
backend/tests/test_game_state.py::test_state_terminal_lock_on_draw_replay PASSED [ 97%]
backend/tests/test_game_state.py::test_state_clone_isolation PASSED      [ 98%]
backend/tests/test_game_state.py::test_state_serialization PASSED        [100%]

============================= 87 passed in 1.07s ==============================
```

### 2. Frontend Native Unit Tests (`npm test`):
```text
> frontend@0.0.0 test
> node --test src/tests/*.test.js

▶ Connect Four Frontend Rules Engine (gameLogic.js)
  ✔ initializes clean 6x7 empty board (2.1909ms)
  ✔ respects piece gravity and column capacity (0.3577ms)
  ✔ detects horizontal win across rows and column offsets (1.9603ms)
  ✔ detects vertical win across columns and row offsets (0.7777ms)
  ✔ detects positive diagonal (/) win and extracts coordinates (0.4392ms)
  ✔ detects negative diagonal (\) win and extracts coordinates (1.073ms)
  ✔ extracts deterministic 4-coordinate sequence for 5 connected pieces (0.2203ms)
  ✔ replays verified 42-move legal draw sequence without premature win (0.6326ms)
  ✔ strictly enforces win-over-draw precedence (1.6054ms)
  ✔ strictly validates AI responses without silent substitutions (0.4262ms)
✔ Connect Four Frontend Rules Engine (gameLogic.js) (11.2575ms)
ℹ tests 10
ℹ suites 1
ℹ pass 10
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 96.7097
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
dist/assets/index-Q_KbZyJr.js   246.64 kB │ gzip: 76.08 kB
✓ built in 159ms
```

---

## Safeguards & Key Invariants Confirmed
1. **Minimax & Alpha-Beta Correctness & Tie-Breaking**:
   - `MinimaxAgent` and `AlphaBetaAgent` share identical default move traversal `[0, 1, 2, 3, 4, 5, 6]` and identical tie-breaking (first strictly superior candidate).
   - Mathematical score equivalence `score(Minimax) == score(AlphaBeta)` and move equivalence `move(Minimax) == move(AlphaBeta)` are confirmed on diverse test positions and depths.
   - On non-trivial positions, `AlphaBetaAgent` evaluates strictly fewer nodes and records positive pruned cutoffs.
2. **Transposition Table Bound Safety (`OptimizedAlphaBetaAgent`)**:
   - Transposition table entries store `searched_depth`, `score`, `bound_type` (`EXACT`, `LOWER`, `UPPER`), and `best_move`.
   - Bounds are verified never to be returned directly as exact scores when $\alpha < \beta$.
   - Cache hit tracking (`transposition_hits > 0`) is empirically verified on transpositions.
3. **MCTS Selection & Backpropagation Invariant**:
   - Root turn is `self.player_id`; root children represent agent moves (`player_just_moved == self.player_id`).
   - Depth-1 children represent opponent moves (`player_just_moved == self.opp_id`).
   - UCT child selection is symmetric across player turns without sign flipping, and rewards are accumulated strictly from each node's `player_just_moved` perspective.
4. **Telemetry Integrity (PRD §13.3)**:
   - Tree search metrics (`nodes_evaluated`, `pruned_nodes`, `search_depth`, `transposition_hits`) are populated for game-tree agents and strictly `null` for MCTS/random.
   - Simulation metrics (`mcts_iterations`, `mcts_simulations`) are populated for MCTS and strictly `null` for tree-search agents.
5. **Legacy Contract Preservation**:
   - When `agent` is omitted from `POST /api/ai-move`, the response returns `{ "column": col, "row": row }` without extra keys.
   - Legacy `backend/ai_agent.py` remains 100% untouched.
6. **Strict Scope Boundaries**:
   - Tournament runner (`POST /api/benchmark/run`), multi-match execution, CSV/JSON export, and aggregate analytics charts remain strictly deferred to Phase 6 as planned.
