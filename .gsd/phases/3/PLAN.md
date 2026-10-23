---
phase: 3
plan: 1
wave: 1
gap_closure: false
---

# Plan 3.1 (Final): Interactive Frontend Interface

## Objective
Build a responsive, modern, and accessible React (Vite) interface for Connect Four conforming strictly to PRD §10, §11, and §12. Construct a modular component architecture (`GameBoard`, `GameCell`, `GameControls`, `GameStatus`, `MetricsPanel`, `ErrorBanner`, `Navbar`) driven by a central `useGame` hook, an API service layer, and an authoritative frontend rules utility (`gameLogic.js`) that mirrors `backend/app/core/game_engine.py`. Integrate strictly with existing Phase 1 & 2 backend contracts (`POST /api/ai-move`, `GET /api/health`, `GET /api/agents`), enforce strict validation of AI responses without silent substitutions, implement safe AI retries on the unchanged board, define an explicit turn state machine, transparently label deferred controls, display authentic measured telemetry without fabricating numbers, and provide zero-dependency frontend testing via Node's native test runner.

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
   - **Frontend Usage**: Navbar connectivity status indicator.
2. `GET /api/agents`
   - **Contract**: HTTP 200 `{"agents": [AgentMetadata, ...]}` for all 6 planned agents (`random`, `greedy`, `minimax`, `alphabeta`, `optimized`, `mcts`).
   - **Frontend Usage**: Populates the AI algorithm selector dropdown.
3. `POST /api/ai-move`
   - **Request Schema**: `{"board": list[list[int]], "depth": int = 4}`.
   - **Response Schema**: `{"column": int | null, "row": int}`.
   - **Error Schema**: `{"error": {"code": str, "message": str}}` with HTTP 400, 422, or 500.

### Contract Limitations & Phase 3 Scoping:
| Feature | Backend Contract Status | Phase 3 Frontend Treatment |
|---|---|---|
| **AI Calculation** | Fully supported via `minimax` in `POST /api/ai-move` | Fully functional; sends current 6×7 board and depth. |
| **Search Depth** | Supported (`depth`: 2, 4, 6) | Fully functional; mapped to Easy (2), Medium (4), Hard (6). |
| **Algorithm Selection** | NOT supported by `POST /api/ai-move` (hardcoded to Minimax) | Fetches catalog from `GET /api/agents`. `Minimax` is marked as **Active**. Other agents (`Random`, `Greedy`, `Alpha-Beta`, `Optimized`, `MCTS`) are displayed with a clear badge: `(Phase 4/5)`. Selecting another agent displays an informational tooltip explaining that backend modular agents activate in Phase 4 & 5. |
| **Starting Player** | Stateless endpoint (no session ID) | Fully supported in frontend state. If AI is selected to move first, frontend immediately calls `POST /api/ai-move` on the empty board. |
| **Telemetry (Nodes/Pruned)** | NOT returned by `POST /api/ai-move` | **Strictly no fabricated metrics**. Frontend measures actual client-side round-trip `decision_time_ms`. Tree nodes, pruned nodes, and transposition hits are displayed as `N/A`, adhering to PRD §10 & §12. |
| **Benchmarking Engine** | Scheduled for Phase 6 | The Analytics tab renders a static layout/preview of the tournament schema and benchmarking design. |

---

## 2. Strict AI Response Validation (No Silent Substitutions)

When `POST /api/ai-move` returns `{ column, row }`, the frontend validates the move before applying it:

### Validation Rules:
1. `response` must be an object with integer properties `column` and `row`.
2. `column` must be within range: $0 \le \text{column} < 7$.
3. `row` must be within range: $0 \le \text{row} < 6$.
4. Target cell `board[row][column]` must be `EMPTY (0)`.
5. Target column must not be full: `board[0][column] === EMPTY`.
6. **Physical Gravity Match**: `row` MUST strictly equal `getNextOpenRow(board, column)`.

### Violation Handling:
- If ANY validation rule fails:
  - **DO NOT mutate the board**.
  - **DO NOT silently substitute a different row or column**.
  - Transition to **AI Error / Retry Pending State**:
    - Set `errorMessage = "AI returned an inconsistent move: column ${column}, row ${row} does not match legal gravity row ${expectedRow}."`
    - Keep `turn = 2` (AI's turn).
    - Keep human board interaction strictly disabled.
    - Display non-blocking `ErrorBanner` with "Retry AI Move" and "Reset Game" options.

---

## 3. Explicit Turn State Transitions & Concurrency Guard

The game state machine explicitly differentiates between all play modes, thinking states, retries, and terminal outcomes:

| State | `turn` | `status` | `isThinking` | `errorMessage` | Human Board Input | Allowed User Actions |
|---|---|---|---|---|---|---|
| **Human 1 Turn** | `1` | `"active"` | `false` | `null` | **Enabled** | Click/keyboard column drop, Reset Game, change mode/depth. |
| **AI Thinking** | `2` | `"active"` | `true` | `null` | **Disabled** (locked) | In-flight AI request mutex locked; duplicate requests blocked. Controls disabled. |
| **AI Move Succeeded** | Transitions to `1` | `"active"` (or `"won"`/`"draw"`) | `false` | `null` | **Enabled** (if active) | Human turn restored. If terminal, transitions to Terminal state. |
| **AI Failure / Retry Pending** | `2` | `"active"` | `false` | `string` | **Disabled** (locked) | "Retry AI Move" (dispatches request for current unchanged board) or "Reset Game". |
| **Human 2 Turn (Pass & Play)** | `2` | `"active"` | `false` | `null` | **Enabled** | Human 2 (Yellow) column drop, Reset Game. Zero network calls. |
| **Terminal Won** | `1` or `2` | `"won"` | `false` | `null` | **Disabled** (locked) | Board locked, winning line glowing. "Play Again" / "Reset Game". |
| **Terminal Draw** | `1` or `2` | `"draw"` | `false` | `null` | **Disabled** (locked) | Board locked, draw banner. "Play Again" / "Reset Game". |
| **AI-First Start** | `2` | `"active"` | `true` | `null` | **Disabled** (locked) | Dispatches `POST /api/ai-move` with empty board $\to$ transitions to Human 1 Turn on success. |

### Concurrency & Duplicate-Action Prevention
- An active request ref (`inFlightRef.current = true`) and `isThinking: true` state form a strict mutex.
- If a click, keyboard trigger, or retry is attempted while `isThinking === true`, it is immediately dropped without effect.
- Board element has CSS `pointer-events: none` while `turn === 2` or `isThinking === true` or `status !== "active"`.

---

## 4. Safe AI Retries

When an AI request fails (network error, timeout, HTTP 4xx/5xx, or invalid response validation):
1. **Board Preservation**: The board remains preserved in its current valid state (including the human move that preceded the AI turn).
2. **Turn Invariant**: The turn remains `turn === 2` (AI's turn).
3. **No Move Replay**: The retry action calls `triggerAIMove()` requesting an AI move for the **current unchanged board**. It NEVER replays, re-drops, or alters the human move.
4. **Strict Human Lock**: Human board input remains strictly disabled until the AI move succeeds or the user explicitly clicks "Reset Game". The human cannot make another move out of turn.
5. **Preconditions for Retry**:
   - `status === "active"`
   - `turn === 2`
   - `!isThinking`
   - `errorMessage !== null`

---

## 5. Authoritative Rules vs. UI-Only State

### Authoritative Rules (`frontend/src/utils/gameLogic.js`)
Directly mirrors `backend/app/core/game_engine.py`:
- **Grid**: 6 rows $\times$ 7 columns ($0 \le r \le 5$, $0 \le c \le 6$). Row 0 is top, Row 5 is bottom.
- **Gravity**: Dropping into column $c$ finds lowest available row $r$ from 5 up to 0 (`getNextOpenRow`).
- **Win Detection**: Scans horizontal, vertical, positive diagonal ($/$), and negative diagonal ($\backslash$) for 4 consecutive matching discs.
- **Deterministic 4-Coordinate Sequence**: Extracts sorted `[[r0, c0], [r1, c1], [r2, c2], [r3, c3]]` coordinates. If 5+ discs are connected, returns the canonical first 4-cell window.
- **Win-Over-Draw Precedence**: If disc 42 forms a 4-in-a-row, game status is `"won"`, NOT `"draw"`.
- **Draw Detection**: Full board with no winning line evaluates to `"draw"`.

### UI-Only State (`frontend/src/hooks/useGame.js`)
- `isThinking`: boolean indicating active backend request.
- `hoveredCol`: column index currently under cursor for ghost disc guide.
- `errorMessage`: error message from network/validation failure.
- `activeTab`: `'home' | 'game' | 'analytics'` for view switching.
- `clientRoundtripTimeMs`: real-time measured roundtrip latency.

---

## 6. Component Architecture & Responsibilities

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

## 7. Testing & Verification Plan

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

## 8. Acceptance Criteria
- [ ] **AC-1**: Component architecture implemented under `frontend/src/components/`, `pages/`, `hooks/`, `services/`, and `utils/`.
- [ ] **AC-2**: Responsive 7×6 board renders with smooth drop animation and hover indicator on viewports from 320px to 1920px.
- [ ] **AC-3**: Connect Four gravity, win detection in 4 directions, and 4-cell coordinate highlights strictly mirror the Phase 2 engine.
- [ ] **AC-4**: Full-board draw state is accurately detected with win-over-draw precedence strictly preserved.
- [ ] **AC-5**: Human vs AI mode interacts with `POST /api/ai-move`, sending `{ board, depth }` and receiving `{ column, row }`.
- [ ] **AC-6**: AI response is strictly validated against gravity and column capacity; inconsistent responses trigger a recoverable error without mutating the board or silently substituting rows.
- [ ] **AC-7**: AI retry action requests an AI move for the current unchanged board, never replays human moves, and keeps human input disabled while the AI move is pending or failed.
- [ ] **AC-8**: Human vs Human (Pass & Play) mode operates completely locally with zero network calls.
- [ ] **AC-9**: AI algorithm selector displays catalog from `GET /api/agents` with `Minimax (Active)` and deferred algorithms labeled `(Phase 4/5)`.
- [ ] **AC-10**: Telemetry displays authentic measured round-trip time (`ms`); inapplicable tree metrics display `N/A` without fabricated numbers.
- [ ] **AC-11**: React state navigation seamlessly switches between Home, Game, and Analytics views without external router dependencies.
- [ ] **AC-12**: `npm run lint`, `npm run build`, and `npm test` pass with 0 errors.
- [ ] **AC-13**: All 31 backend unit, engine, state, and foundation tests continue to pass with zero regressions.

---

## 9. Files Expected to Change
- `frontend/package.json` (add `"test": "node --test src/tests/*.test.js"`)
- `frontend/src/utils/gameLogic.js` (pure rules and coordinate extraction)
- `frontend/src/tests/gameLogic.test.js` (unit tests for rules, gravity, coordinates, draw replay)
- `frontend/src/services/api.js` (typed API client with error envelope parsing)
- `frontend/src/hooks/useGame.js` (game state, strict validation, and safe retry lifecycle hook)
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
