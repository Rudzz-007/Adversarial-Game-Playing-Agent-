# STATE.md — Project Memory

## Current Status
- **Current Milestone**: v1.0 — Initial Release
- **Completed Phases**:
  - Phase 1 — Foundation & API Contract (✅ Complete, 7/7 tests passed)
  - Phase 2 — Core Game Engine & State Validation (✅ Complete, 31/31 tests passed including safeguards)
  - Phase 3 — Interactive Frontend Interface (✅ Complete, 10/10 frontend tests, 0 lint errors, clean build, 31/31 backend tests passed)
  - Phase 4 — Baseline AI Agents: Random & Greedy (✅ Complete, 60/60 backend tests passed, 10/10 frontend tests passed, 0 lint errors, clean build)
  - Phase 5 — Advanced Search Agents: Minimax, Alpha-Beta, Optimized Alpha-Beta, MCTS (✅ Complete, 87/87 backend tests passed, 10/10 frontend tests passed, 0 lint errors, clean build)
- **Current Phase**: Phase 6 — Benchmarking & Analytics Dashboard (Pending User Review & Explicit Approval)
- **Specification Status**: `FINALIZED`
- **Planning Lock**: `RELEASED`
- **Next Step**: Await user explicit approval before beginning Phase 6 execution planning

## Last Session Summary
- Implemented and fully verified Phase 5 Advanced Search Agents conforming strictly to PRD §6.4–6.6 and approved plan `.gsd/phases/5/PLAN.md`:
  1. `backend/app/core/evaluation.py`: Centralized heuristic scoring (`evaluate_window`, `score_position`) and terminal values (`WIN_SCORE`, `LOSS_SCORE`, `DRAW_SCORE`).
  2. `MinimaxAgent`: Full depth-limited tree recursion, accurate `nodes_evaluated` counting, deterministic tie-breaking on natural column order `[0..6]`, and board immutability.
  3. `AlphaBetaAgent`: Alpha-beta branch pruning, mathematically guaranteed value equivalence with Minimax, accurate `pruned_nodes` counting, and shared natural column ordering.
  4. `OptimizedAlphaBetaAgent`: Center-outward move ordering `[3, 2, 4, 1, 5, 0, 6]`, transposition table caching with typed bounds (`EXACT`, `LOWER`, `UPPER`), bound safety (never treating lower/upper bounds as exact when $\alpha < \beta$), and 1-ply immediate-win cutoff logic.
  5. `MCTSAgent`: 4-step cycle (UCT Selection, Expansion, Rollout Simulation, Backpropagation), symmetric node-to-move reward perspective (`player_just_moved`), visit-count root selection, isolated pseudo-random seeding, and authentic `mcts_iterations` / `mcts_simulations` telemetry.
  6. Factory registration in `backend/app/agents/factory.py` supporting all 6 agents (`random`, `greedy`, `minimax`, `alphabeta`, `optimized`, `mcts`).
  7. API integration in `backend/main.py` preserving exact legacy Minimax contract (`{"column": col, "row": row}`) when `agent` is omitted.
  8. Frontend activation in `GameControls.jsx`, `MetricsPanel.jsx`, and `useGame.js` activating all 6 agents with dynamic telemetry for tree-search and simulation agents.
  9. Comprehensive verification: 87/87 backend tests passed (27 new advanced search tests + 60 existing tests), 10/10 frontend unit tests passed, 0 oxlint warnings/errors, and production build succeeded cleanly in 159ms.
