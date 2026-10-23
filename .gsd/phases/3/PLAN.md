---
phase: 3
plan: 1
wave: 1
gap_closure: false
---

# Plan 3.1 (Revised): Interactive Frontend Interface

## Objective
Build a responsive, modern, and accessible React (Vite) interface for Connect Four conforming strictly to PRD §10, §11, and §12. Construct a modular component architecture (`GameBoard`, `GameCell`, `GameControls`, `GameStatus`, `MetricsPanel`, `ErrorBanner`, `Navbar`) driven by a central `useGame` hook, an API service layer, and an authoritative frontend rules utility (`gameLogic.js`) that mirrors `backend/app/core/game_engine.py`. Integrate strictly with existing Phase 1 & 2 backend contracts (`POST /api/ai-move`, `GET /api/health`, `GET /api/agents`), transparently label deferred controls, display authentic measured telemetry without fabricating numbers, and provide zero-dependency frontend testing via Node's native test runner.

## Context & Existing Contract Audit
Load these files for context:
- [.gsd/SPEC.md](file:///c:/Users/MANAV/Desktop/FAI-project/Adversarial-Game-Playing-Agent-/.gsd/SPEC.md)
- [.gsd/REQUIREMENTS.md](file:///c:/Users/MANAV/Desktop/FAI-project/Adversarial-Game-Playing-Agent-/.gsd/REQUIREMENTS.md)
- [backend/main.py](file:///c:/Users/MANAV/Desktop/FAI-project/Adversarial-Game-Playing-Agent-/backend/main.py#L86-L99)
- [backend/app/api/agent_routes.py](file:///c:/Users/MANAV/Desktop/FAI-project/Adversarial-Game-Playing-Agent-/backend/app/api/agent_routes.py)
- [backend/app/core/game_engine.py](file:///c:/Users/MANAV/Desktop/FAI-project/Adversarial-Game-Playing-Agent-/backend/app/core/game_engine.py)
- [frontend/package.json](file:///c:/Users/MANAV/Desktop/FAI-project/Adversarial-Game-Playing-Agent-/frontend/package.json)

---

## 1. Backend Contract & Integration Audit

### Actual Endpoints Available in Backend:
1. `GET /api/health` and `GET /health`
   - **Contract**: HTTP 200 `{"status": "ok"}`.
   - **Frontend Usage**: Navbar connection status indicator.
2. `GET /api/agents`
   - **Contract**: HTTP 200 `{"agents": [AgentMetadata, ...]}` for all 6 planned agents (`random`, `greedy`, `minimax`, `alphabeta`, `optimized`, `mcts`).
   - **Frontend Usage**: Populates the AI algorithm selector dropdown.
3. `POST /api/ai-move`
   - **Request Schema**: `{"board": list[list[int]], "depth": int = 4}`.
   - **Response Schema**: `{"column": int | null, "row": int}`.
   - **Error Schema**: `{"error": {"code": str, "message": str}}` with HTTP 400, 422, or 500.

### Contract Limitations & Frontend Handling:
| Feature | Backend Contract Status | Phase 3 Frontend Treatment |
|---|---|---|
| **AI Calculation** | Fully supported via `minimax` in `POST /api/ai-move` | Fully functional; sends 6×7 board and depth. |
| **Search Depth** | Supported (`depth`: 2, 4, 6) | Fully functional; mapped to Easy (2), Medium (4), Hard (6). |
| **Algorithm Selection** | NOT supported by `POST /api/ai-move` (hardcoded to Minimax) | Fetches catalog from `GET /api/agents`. `Minimax` is marked as **Active**. Other agents (`Random`, `Greedy`, `Alpha-Beta`, `Optimized`, `MCTS`) are displayed with a clear badge: `(Phase 4/5)`. Selecting another agent displays an informational tooltip explaining backend modular agents activate in Phase 4 & 5. |
| **Starting Player** | Stateless endpoint (no session ID) | Fully supported in frontend state. If AI is set to move first, frontend immediately calls `POST /api/ai-move` on the empty board. |
| **Telemetry (Nodes/Pruned)** | NOT returned by `POST /api/ai-move` | **No fabricated metrics**. Frontend measures actual client-side round-trip `decision_time_ms`. Tree nodes, pruned nodes, and transposition hits are displayed as `N/A`, adhering to PRD §10 & §12. |

---

## 2. Game State Consistency & Rules Architecture

To prevent split-brain or inconsistent state transitions, game logic is strictly structured:

### Authoritative Rule Invariants (`frontend/src/utils/gameLogic.js`)
- Directly mirrors `backend/app/core/game_engine.py`:
  - **Grid**: 6 rows $\times$ 7 columns ($0 \le r \le 5$, $0 \le c \le 6$). Row 0 is top, Row 5 is bottom.
  - **Gravity**: Dropping into column $c$ finds lowest available row $r$ from 5 up to 0.
  - **Win Detection**: Scans horizontal, vertical, positive diagonal ($/$), negative diagonal ($\backslash$) for 4 identical non-zero pieces.
  - **Deterministic 4-Coordinate Sequence**: Extracts sorted `[[r0, c0], [r1, c1], [r2, c2], [r3, c3]]` coordinates. If 5+ pieces are connected, returns the canonical first 4-cell window.
  - **Win-Over-Draw Precedence**: If disc 42 forms a 4-in-a-row, game status is `"won"`, NOT `"draw"`.
  - **Draw Detection**: Full board with no winning line evaluates to `"draw"`.

### UI-Only State (Managed in `useGame.js`)
- `isThinking`: boolean indicating in-flight AI HTTP request.
- `hoveredCol`: column index currently under user cursor for ghost disc guide.
- `errorMessage`: error payload or message from network/validation failure.
- `activeTab`: `'home' | 'game' | 'analytics'` for view switching.
- `clientRoundtripTimeMs`: actual measured request duration in milliseconds.

### Response Reconciliation:
When `POST /api/ai-move` returns `{ column, row }`:
1. Frontend verifies `0 <= column < 7` and `0 <= row < 6`.
2. Frontend verifies `row === getNextOpenRow(board, column)`. If backend returned row does not match physical gravity, frontend uses calculated physical row to guarantee board consistency.
3. If `column === null` or column is full, frontend falls back safely to first open legal column or raises error without crashing.

---

## 3. Human-vs-AI Interaction Lifecycle

```
[User Clicks Column c]
       │
       ▼
[Validate Move] ──(Column full / Game terminal / isThinking)──► Ignore / Shake Feedback
       │
       ▼ (Valid)
[Drop Human Disc (1)] ──► Update Board & History
       │
       ▼
[Check Win/Draw] ──(Human Won or Draw)──► Transition to Terminal State & Stop (No AI Call)
       │
       ▼ (Game Active)
[Switch Turn to AI (2)]
       │
       ├─► Set isThinking = true
       ├─► Lock Board (pointer-events: none, disable controls)
       ├─► Record startTime = performance.now()
       │
       ▼
[Dispatch POST /api/ai-move { board, depth }]
       │
       ├───► [SUCCESS] ──────────────────────────────────────────────┐
       │     ├─► decision_time_ms = Math.round(performance.now() - t0) │
       │     ├─► Validate { column, row }                             │
       │     ├─► Drop AI Disc (2) on Board                            │
       │     ├─► Check Win/Draw for AI                                │
       │     │     ├─► AI Won: status = 'won', winner = 2             │
       │     │     ├─► Draw: status = 'draw'                          │
       │     │     └─► Active: switch turn back to Human (1)          │
       │     └─► Set isThinking = false                               │
       │                                                              │
       └───► [FAILURE / NETWORK ERROR] ───────────────────────────────┤
             ├─► Parse {"error": {"code", "message"}} or timeout err  │
             ├─► Set errorMessage = error.message                     │
             ├─► Board remains preserved in current valid state       │
             ├─► Display ErrorBanner with "Retry AI Move" button      │
             └─► Set isThinking = false                               │
```

### Duplicate-Action Prevention
- All column click targets, keyboard drop inputs, and game setting controls are disabled while `isThinking === true`.
- Clicking during calculation produces no state mutation or API requests.

---

## 4. Component Structure & Responsibilities

```
frontend/src/
├── components/
│   ├── Navbar.jsx          # Header with branding and Home / Game / Analytics navigation
│   ├── GameBoard.jsx       # 7x6 board container with column hover guides
│   ├── GameCell.jsx        # Individual circular cell with disc drop animation & win glow
│   ├── GameControls.jsx    # Mode, Difficulty, AI Algorithm (labeled), Starting Player, Reset
│   ├── GameStatus.jsx      # Turn banner, winner celebration, draw banner, and thinking spinner
│   ├── MetricsPanel.jsx    # Real-time telemetry (measured round-trip ms, N/A for Phase 4/5 metrics)
│   └── ErrorBanner.jsx     # Non-blocking alert conforming to PRD §12.9 with retry button
├── pages/
│   ├── HomePage.jsx        # Project overview, algorithm overview, quick rules
│   ├── GamePage.jsx        # Primary interactive game screen assembling all game components
│   └── AnalyticsPage.jsx   # Analytics dashboard preview/scaffolding for Phase 6
├── hooks/
│   └── useGame.js          # Authoritative game management hook (board state, turns, moves, AI lifecycle)
├── services/
│   └── api.js              # Fetch client communicating with backend API (POST /api/ai-move, GET /api/agents)
├── utils/
│   └── gameLogic.js        # Pure Connect Four rules engine: gravity, win detection, 4-coordinate extraction
├── tests/
│   └── gameLogic.test.js   # Automated unit tests for rules, coordinates, gravity, and win-over-draw
├── App.jsx                 # Top-level view switcher hosting activeTab state
├── App.css
├── index.css
└── main.jsx
```

---

## 5. Testing & Verification Plan

### A. Zero-Dependency Frontend Unit Tests (`frontend/src/tests/gameLogic.test.js`)
Using Node's native test runner (`node:test` and `node:assert`, supported natively in Node v24):
- **Test 1**: Initial empty 6×7 board matrix validation.
- **Test 2**: Gravity row placement ($5 \to 0$) and full-column detection.
- **Test 3**: Horizontal win detection across all rows and column offsets.
- **Test 4**: Vertical win detection across all columns and row offsets.
- **Test 5**: Positive diagonal ($/$) win detection.
- **Test 6**: Negative diagonal ($\backslash$) win detection.
- **Test 7**: Deterministic 4-coordinate sequence extraction for 5-in-a-row connections.
- **Test 8**: Replay of the verified 42-move legal draw sequence terminating in valid draw.
- **Test 9**: Win-over-draw precedence (42nd disc completes 4-in-a-row evaluates to won, not draw).

### B. Build & Lint Verification
1. `npm run lint` (`oxlint`): Must complete with 0 syntax or rule errors.
2. `npm run build` (`vite build`): Must bundle production build to `frontend/dist/` without errors.
3. `npm test` (`node --test src/tests/*.test.js`): All frontend logic tests must pass.

### C. Backend Regression Verification
```powershell
python -m pytest backend/tests/test_game_engine.py backend/tests/test_game_state.py backend/tests/test_foundation.py -v
```
All 31 backend unit, engine, state, and foundation tests must pass with 100% success rate.

---

## 6. Acceptance Criteria
- [ ] **AC-1**: Component architecture implemented under `frontend/src/components/`, `pages/`, `hooks/`, `services/`, and `utils/`.
- [ ] **AC-2**: Responsive 7×6 board renders with smooth drop animation and hover indicator on viewports from 320px to 1920px.
- [ ] **AC-3**: Connect Four gravity, win detection in 4 directions, and 4-cell coordinate highlights strictly mirror the Phase 2 engine.
- [ ] **AC-4**: Full-board draw state is accurately detected with win-over-draw precedence strictly preserved.
- [ ] **AC-5**: Human vs AI mode interacts with `POST /api/ai-move`, sending `{ board, depth }` and receiving `{ column, row }`.
- [ ] **AC-6**: Human vs Human (Pass & Play) mode operates completely locally without network calls.
- [ ] **AC-7**: AI algorithm selector displays catalog from `GET /api/agents` with `Minimax (Active)` and deferred algorithms labeled `(Phase 4/5)`.
- [ ] **AC-8**: Telemetry displays authentic measured round-trip time (`ms`); inapplicable tree metrics display `N/A` without fabricated numbers.
- [ ] **AC-9**: Network failures or validation errors show a standardized `ErrorBanner` with a "Retry Move" button without corrupting state.
- [ ] **AC-10**: React state navigation seamlessly switches between Home, Game, and Analytics views without external router dependencies.
- [ ] **AC-11**: `npm run lint`, `npm run build`, and `npm test` pass with 0 errors.
- [ ] **AC-12**: All 31 backend unit, engine, state, and foundation tests continue to pass with zero regressions.

---

## 7. Files Expected to Change
- `frontend/package.json` (add `"test": "node --test src/tests/*.test.js"`)
- `frontend/src/utils/gameLogic.js` (pure rules and coordinate extraction)
- `frontend/src/tests/gameLogic.test.js` (unit tests for rules and draw replay)
- `frontend/src/services/api.js` (typed API client with error envelope parsing)
- `frontend/src/hooks/useGame.js` (game state and AI coordination hook)
- `frontend/src/components/Navbar.jsx`
- `frontend/src/components/GameBoard.jsx`
- `frontend/src/components/GameCell.jsx`
- `frontend/src/components/GameControls.jsx`
- `frontend/src/components/GameStatus.jsx`
- `frontend/src/components/MetricsPanel.jsx`
- `frontend/src/components/ErrorBanner.jsx`
- `frontend/src/pages/HomePage.jsx`
- `frontend/src/pages/GamePage.jsx`
- `frontend/src/pages/AnalyticsPage.jsx`
- `frontend/src/App.jsx`
- `frontend/src/App.css`
- `frontend/src/index.css`
- `.gsd/STATE.md`
- `.gsd/TODO.md`
