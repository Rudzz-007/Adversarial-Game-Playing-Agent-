---
milestone: v1.0
version: 1.0.0
updated: 2026-10-23
---

# Roadmap — Adversarial Game-Playing Agent (Connect Four AI)

> **Current Phase**: Phase 0 — Specification & Architecture Finalization  
> **Status**: Ready for Planning Lock approval  
> **Reference**: PRD Section 18 (Development Roadmap)

---

## Must-Haves (from PRD & SPEC)
- [ ] Reliable 6×7 Connect Four Game Engine with 100% win/draw detection and unit tests.
- [ ] Shared modular `BaseAgent` interface and all 6 AI agent implementations (Random, Greedy, Minimax, Alpha-Beta, Optimized Alpha-Beta, MCTS/UCT).
- [ ] FastAPI REST API with game management, move submission, AI calculation, and benchmarking endpoints.
- [ ] Polished React (Vite) interface with interactive board, animations, telemetry panels, and game controls.
- [ ] Automated Head-to-Head Benchmarking with telemetry aggregation and CSV/JSON export.
- [ ] Comprehensive test suite and documentation.

---

## Phases

### Phase 1: Foundation & API Contract
**Status**: ⬜ Not Started  
**Objective**: Establish target package structure (`backend/app/`, `frontend/src/`), establish Pydantic schemas, configure CORS, implement `/api/health` and `/api/agents` contract, and ensure clean development environments.  
**Requirements**: REQ-FR-02, REQ-FR-12, REQ-NFR-03, CON-01  
**Deliverable**: Running frontend/backend with synchronized integration contract and health checks.

---

### Phase 2: Core Game Engine & State Validation
**Status**: ⬜ Not Started  
**Objective**: Build and modularize the 6×7 grid engine (`core/game_engine.py`, `core/game_state.py`, `core/validation.py`) with piece dropping, legal column discovery, horizontal/vertical/diagonal win checking, draw detection, and automated `pytest` test suite.  
**Requirements**: REQ-FR-02, REQ-FR-06, REQ-FR-07, REQ-NFR-02, REQ-NFR-05  
**Depends on**: Phase 1  
**Deliverable**: Fully tested, rock-solid game engine with 100% rule coverage.

---

### Phase 3: Interactive Frontend Interface
**Status**: ⬜ Not Started  
**Objective**: Build modern component architecture (`GameBoard`, `GameCell`, `GameControls`, `GameStatus`, `useGame` hook) featuring drop animations, hover columns, win highlight, turn indicators, New Game/Restart, and responsive dark design system.  
**Requirements**: REQ-FR-01, REQ-FR-03, REQ-FR-08, REQ-NFR-04  
**Depends on**: Phase 2  
**Deliverable**: Playable interactive frontend connected to the backend game service.

---

### Phase 4: Baseline AI Agents (Random & Greedy)
**Status**: ⬜ Not Started  
**Objective**: Implement abstract `BaseAgent`, `RandomAgent` (with seed support), and `GreedyAgent` (immediate win prioritization and 1-ply threat blocking), wire to `/api/game/{id}/ai-move`, and display move metrics (decision time ms).  
**Requirements**: REQ-FR-04, REQ-FR-05, REQ-FR-09  
**Depends on**: Phase 3  
**Deliverable**: Functional Human vs AI baseline gameplay with real-time telemetry.

---

### Phase 5: Adversarial Search (Minimax, Alpha-Beta, Optimized, MCTS)
**Status**: ⬜ Not Started  
**Objective**: Implement `MinimaxAgent`, `AlphaBetaAgent` with pruning metrics, `OptimizedAgent` (center-outward move ordering, transposition table caching, immediate cutoff), and `MCTSAgent` (selection, expansion, rollout, backpropagation with UCT).  
**Requirements**: REQ-FR-04, REQ-FR-05, REQ-FR-09, REQ-NFR-01  
**Depends on**: Phase 4  
**Deliverable**: Complete suite of interchangeable AI algorithms with telemetry tracking.

---

### Phase 6: Benchmarking & Analytics Dashboard
**Status**: ⬜ Not Started  
**Objective**: Build automated tournament runner (`/api/benchmark/run`, `/api/benchmark/{id}`) executing alternating matches across agent pairs, and develop the Analytics Page with metric comparisons (W/D/L, win rates, time, node efficiency) and CSV/JSON export.  
**Requirements**: REQ-FR-10, REQ-FR-11  
**Depends on**: Phase 5  
**Deliverable**: Head-to-head comparison dashboard and reproducible evaluation harness.

---

### Phase 7: Integration, Verification & Release Polish
**Status**: ⬜ Not Started  
**Objective**: End-to-end integration tests, edge-case hardening, error-handling validation, performance profiling, final documentation (`README.md`, `API_SPECIFICATION.md`), and production-ready packaging.  
**Requirements**: REQ-FR-12, REQ-NFR-05, All Acceptance Criteria  
**Depends on**: Phase 6  
**Deliverable**: Fully tested, validated, and deployable Connect Four AI application.
