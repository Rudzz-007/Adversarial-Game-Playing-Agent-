---
milestone: v1.0
updated: 2026-10-23
---

# Requirements Traceability Matrix

## Overview
Requirements derived directly from `docs/Adversarial_Game_Playing_Agent_PRD.pdf` v1.0 for systematic coverage and verification tracking across development phases, updated with review clarifications.

---

## Functional Requirements

| ID | Requirement | PRD Source | Phase | Status |
|---|---|---|---|---|
| **REQ-FR-01** | Interactive 7x6 board UI, piece drop animations, column hover indicator, winning 4-in-a-row highlight, post-game lock | FR-01 | Phase 3 | Pending |
| **REQ-FR-02** | Authoritative backend game-state management (board matrix, player turn, legal columns, move history, status, winner) | FR-02 | Phase 1 & 2 | Pending |
| **REQ-FR-03** | Game modes: Human vs AI (core), Human vs Human (local), AI vs AI (automated simulation with pacing delay) | FR-03 | Phase 3 | Pending |
| **REQ-FR-04** | Agent selection interface offering Random, Greedy, Minimax, Alpha-Beta, Optimized Alpha-Beta, MCTS/UCT | FR-04 | Phase 4 & 5 | Pending |
| **REQ-FR-05** | Configurable difficulty / search depth & MCTS simulation budgets | FR-05 | Phase 4 & 5 | Pending |
| **REQ-FR-06** | Strict move legality validation (reject full columns, invalid coordinates, wrong-turn moves, terminal moves) | FR-06 | Phase 2 | Pending |
| **REQ-FR-07** | Exhaustive win detection (horizontal, vertical, positive diagonal, negative diagonal) and full-board draw detection | FR-07 | Phase 2 | Pending |
| **REQ-FR-08** | Control actions: New Game, Restart, Reset metrics, turn toggling, and AI-vs-AI controls | FR-08 | Phase 3 | Pending |
| **REQ-FR-09** | Real-time AI move visualization: return empirical metrics and candidate scores; use `null` for inapplicable metrics (rendered as `N/A`), preserve measured `0`, and do not claim full reasoning traces | FR-09, §13.3 | Phase 3 & 4 | Pending |
| **REQ-FR-10** | Analytics dashboard displaying W/D/L records, win rates, latency percentiles, search depth/node comparisons | FR-10 | Phase 6 | Pending |
| **REQ-FR-11** | Head-to-head benchmarking harness with alternating starting players, reproducible seeds, and CSV/JSON export | FR-11 | Phase 6 | Pending |
| **REQ-FR-12** | Standardized error handling: all errors return `{"error": {"code": "...", "message": "..."}}`. FastAPI exception handlers catch validation & runtime errors, suppressing internal traces | FR-12, §12.9 | Phase 1, 3, 7 | Pending |

---

## Non-Functional Requirements

| ID | Requirement | Category | Phase | Status |
|---|---|---|---|---|
| **REQ-NFR-01** | UI updates under 200ms; AI decision computation bounded by search parameters; non-blocking benchmark runner | Performance | Phase 1-6 | Pending |
| **REQ-NFR-02** | 100% rule correctness; zero corrupt game states; consistent metric calculations | Correctness | Phase 2 | Pending |
| **REQ-NFR-03** | Clear modular separation between core engine, agent algorithms, API layer, and React presentation | Maintainability | Phase 1 | Pending |
| **REQ-NFR-04** | Polished technical dark theme, responsive grid layout, accessible contrast, lightweight state-based navigation for Home/Game/Analytics | Usability / UI | Phase 3 | Pending |
| **REQ-NFR-05** | Automated pytest suite for engine rules and AI algorithms, and frontend test verification | Testability | Phase 2, 5, 7 | Pending |
| **REQ-NFR-06** | Canonical `GET /api/health` with backward-compatible `GET /health`; secure input validation with sanitized error outputs | API / Reliability | Phase 1 | Pending |

---

## Constraints

| ID | Constraint | PRD Source | Impact |
|---|---|---|---|
| **CON-01** | React 19 + Vite (JavaScript) for frontend; Python 3.10+ & FastAPI for backend | PRD Section 1 | Tech stack boundaries |
| **CON-02** | No external database required for initial MVP (in-memory storage with documented session boundaries) | PRD Section 15 | Storage layer simplicity |
| **CON-03** | No deep RL or neural network training | PRD Section 4.3 | Search-based algorithmic focus |
| **CON-04** | No external client routing dependencies for initial MVP (state-based page switching) | PRD Section 13 | Lean bundle size |
