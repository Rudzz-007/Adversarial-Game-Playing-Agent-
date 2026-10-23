---
phase: 3
plan: 1
wave: 1
gap_closure: false
---

# Plan 3.1: Interactive Frontend Interface

## Objective
Build a responsive, modern, and accessible React (Vite) interface for Connect Four conforming strictly to PRD §10, §11, and §12. Construct a modular component architecture (`GameBoard`, `GameCell`, `GameControls`, `GameStatus`, `MetricsPanel`, `ErrorBanner`, `Navbar`) driven by a central `useGame` hook and an API service layer. Support Human vs AI and Human vs Human modes, difficulty selection, smooth gravity drop animations, hover column guides, 4-cell win highlights, clear draw states, telemetry display, and robust error handling without external routing dependencies.

## Context
Load these files for context:
- [.gsd/SPEC.md](file:///c:/Users/MANAV/Desktop/FAI-project/Adversarial-Game-Playing-Agent-/.gsd/SPEC.md)
- [.gsd/REQUIREMENTS.md](file:///c:/Users/MANAV/Desktop/FAI-project/Adversarial-Game-Playing-Agent-/.gsd/REQUIREMENTS.md)
- [.gsd/ARCHITECTURE.md](file:///c:/Users/MANAV/Desktop/FAI-project/Adversarial-Game-Playing-Agent-/.gsd/ARCHITECTURE.md)
- [backend/main.py](file:///c:/Users/MANAV/Desktop/FAI-project/Adversarial-Game-Playing-Agent-/backend/main.py)
- [frontend/package.json](file:///c:/Users/MANAV/Desktop/FAI-project/Adversarial-Game-Playing-Agent-/frontend/package.json)
- [frontend/src/App.jsx](file:///c:/Users/MANAV/Desktop/FAI-project/Adversarial-Game-Playing-Agent-/frontend/src/App.jsx)
- [frontend/src/services/api.js](file:///c:/Users/MANAV/Desktop/FAI-project/Adversarial-Game-Playing-Agent-/frontend/src/services/api.js)

---

## Architecture & Component Design

### 1. Directory Structure
```
frontend/src/
├── components/
│   ├── Navbar.jsx          # Header with branding and Home / Game / Analytics navigation
│   ├── GameBoard.jsx       # 7x6 board container with column hover guides
│   ├── GameCell.jsx        # Individual circular cell with disc drop animation & win glow
│   ├── GameControls.jsx    # Mode, Difficulty, AI Algorithm, Starting Player, and Reset controls
│   ├── GameStatus.jsx      # Turn banner, winner celebration, draw banner, and thinking spinner
│   ├── MetricsPanel.jsx    # Telemetry display (decision time ms, depth, nodes evaluated, pruned)
│   └── ErrorBanner.jsx     # Non-blocking alert conforming to PRD §12.9 error format with retry
├── pages/
│   ├── HomePage.jsx        # Project overview, algorithm overview, quick rules
│   ├── GamePage.jsx        # Primary interactive game screen assembling all game components
│   └── AnalyticsPage.jsx   # Analytics dashboard placeholder/scaffolding for Phase 6
├── hooks/
│   └── useGame.js          # Authoritative game management hook (board state, turns, moves, AI calls)
├── services/
│   └── api.js              # Fetch client communicating with backend API (POST /api/ai-move, GET /api/agents)
├── styles/
│   └── main.css            # Dark design system tokens, typography, grid, and animations
├── App.jsx                 # Top-level view switcher hosting activeTab state
├── App.css
├── index.css
└── main.jsx
```

### 2. Component Responsibilities

#### `Navbar.jsx`
- Displays project branding: "Connect Four AI — Adversarial Agent".
- Renders 3 view tabs: **Home**, **Game**, **Analytics**.
- Handles tab selection via parent state callback (`activeTab`, `setActiveTab`).
- Displays backend connectivity status badge (online / offline) via periodic health check.

#### `GameBoard.jsx`
- Renders the 7-column × 6-row grid container using responsive CSS Grid.
- Displays interactive column drop zones above each column.
- Shows a ghost hover disc indicating which column is targeted and where the piece will land.
- Disables full columns with `cursor: not-allowed` and dims hover preview.
- Emits column index `col` to `onColumnClick` handler.

#### `GameCell.jsx`
- Renders a single cell at coordinate `(r, c)`.
- Renders empty slot (`0`), Player 1 disc (`1`, Red `#ef4444`), or Player 2/AI disc (`2`, Yellow `#eab308`).
- Applies CSS gravity-drop animation (`@keyframes dropDisc`) when newly populated.
- Applies prominent pulsing glow border (`animation: winGlow 1.2s infinite alternate`) when `isWinningCell` is `true`.
- Supports accessibility attributes: `role="gridcell"`, `aria-label="Row {r}, Column {c}"`.

#### `GameControls.jsx`
- **Game Mode Selection**: "Human vs AI" (default) or "Pass & Play (2 Players)".
- **AI Algorithm Selection**: Dropdown dynamically populated from `GET /api/agents` (`Random`, `Greedy`, `Minimax`, `Alpha-Beta`, `Optimized Alpha-Beta`, `MCTS`).
- **Difficulty / Depth Selector**: Easy (Depth 2), Medium (Depth 4), Hard (Depth 6).
- **First Player Selector**: Player 1 (Human) starts vs Player 2 (AI) starts.
- **Action Buttons**: "New Game" (resets board, restores initial turn) and "Reset".
- Locks controls during AI thinking (`isThinking === true`) to prevent inconsistent state transitions.

#### `GameStatus.jsx`
- **Active Turn**:
  - Human Turn: Red disc badge with "Your Turn (Player 1)".
  - AI Turn: Yellow disc badge with animated pulsing dots "AI is calculating move...".
- **Won Game**:
  - Celebratory banner: "🎉 Player 1 (Red) Wins!" or "🤖 AI Agent (Yellow) Wins!".
  - Displays "Play Again" button.
- **Drawn Game**:
  - Neutral banner: "🤝 Game Drawn — Board Full (No Winner)".
- **Move Counter**: Displays current move number and last placed position.

#### `MetricsPanel.jsx`
- Renders real-time AI decision telemetry adhering to PRD §10:
  - **Decision Time**: Formatted in milliseconds (e.g. `142 ms`).
  - **Search Depth**: e.g. `Depth 4`.
  - **Nodes Evaluated**: Tree nodes evaluated (or `N/A` if inapplicable).
  - **Pruned Branches**: Pruned nodes (or `N/A` if inapplicable; preserves genuine `0`).
- Displays algorithm badge (e.g. `Minimax with Alpha-Beta Pruning`).

#### `ErrorBanner.jsx`
- Displays user-friendly error banners when API calls or validation errors occur.
- Formats standard error payload: `code` and `message` (e.g. `INVALID_MOVE: The selected column is full.`).
- Provides a "Dismiss" and a "Retry Move" button.

#### `useGame.js` Hook
- Authoritative local state manager:
  - `board`: 6×7 2D array of integers (`0`, `1`, `2`).
  - `turn`: `1` (Player 1) or `2` (Player 2 / AI).
  - `status`: `"active"`, `"won"`, `"draw"`.
  - `winner`: `null`, `1`, or `2`.
  - `winningCoords`: array of `[row, col]` pairs.
  - `moveHistory`: array of move records `{ move_number, player, column, row, timestamp }`.
  - `telemetry`: AI metrics object `{ decision_time_ms, nodes_evaluated, pruned_nodes, search_depth }`.
  - `isThinking`: boolean indicating active AI computation.
  - `errorMessage`: error message string or `null`.
- Functions:
  - `handleMove(col)`: validates column capacity, drops piece into lowest open row, checks win/draw, triggers AI move if mode is Human vs AI.
  - `triggerAIMove()`: calls `services/api.js`, handles response, applies AI move, updates telemetry.
  - `resetGame(newSettings)`: resets board and initializes starting player according to settings.

---

## Detailed Task Breakdown

### Task 1: Environment Setup & CSS Design System
- Run `npm install` in `frontend/` to install React 19, Vite, and Oxlint dependencies.
- Build design system in `frontend/src/index.css` and `frontend/src/App.css`:
  - Color palette: Slate dark background (`#0b1120`), card surface (`#1e293b`), borders (`#334155`), cyan primary (`#0ea5e9`), sky accent (`#38bdf8`), player red (`#ef4444`), AI yellow (`#eab308`), win green (`#22c55e`).
  - CSS Grid rules for responsive 7-column layout with `max-width: 600px`, `aspect-ratio: 7 / 6`.
  - Keyframes for `@keyframes dropDisc` (smooth translateY with bounce) and `@keyframes winPulse` (glow pulsation).
  - Media queries ensuring responsive scaling from 320px mobile screens to desktop.

### Task 2: API Client Service (`frontend/src/services/api.js`)
- Implement `fetchHealth()` querying `GET /api/health`.
- Implement `fetchAgentCatalog()` querying `GET /api/agents`.
- Implement `fetchAIMove(board, depth, algorithm)` calling `POST /api/ai-move`:
  - Preserves exact contract: `{ board, depth }` sending to backend.
  - Measures request round-trip time in milliseconds as client-side telemetry fallback.
  - Gracefully handles HTTP error responses parsing `{ "error": { "code": "...", "message": "..." } }`.
  - Throws typed error with descriptive message on network disconnect or 500 error.

### Task 3: Game State Hook (`frontend/src/hooks/useGame.js`)
- Initialize clean 6×7 board matrix with 0s.
- Enforce Connect Four gravity: find lowest available row in column ($5 \to 0$).
- Enforce win detection on client side for instant feedback using directional scan matching `app.core.game_engine`.
- Enforce full-board draw detection with win-over-draw precedence.
- Manage AI turn lifecycle: set `isThinking = true`, disable board clicks, invoke `fetchAIMove`, apply returned row and column, record move telemetry, and return turn to player.
- Capture and format API or network errors in `errorMessage`.

### Task 4: UI Components Assembly
- Implement `GameCell.jsx` with disc rendering, drop animation, and win glow.
- Implement `GameBoard.jsx` with responsive grid, column drop hover triggers, and disabled indicators for full columns.
- Implement `GameStatus.jsx` with active player badge, AI thinking spinner, victory banner, and draw banner.
- Implement `GameControls.jsx` with mode toggle, AI algorithm selector, depth selector (2, 4, 6), starting player selector, and Reset button.
- Implement `MetricsPanel.jsx` with decision time, search depth, node evaluations, and pruned count.
- Implement `ErrorBanner.jsx` with error code, message, and retry action.
- Implement `Navbar.jsx` with tab switcher and backend connection indicator.

### Task 5: Pages & Main Routing (`App.jsx`)
- Implement `HomePage.jsx` explaining Connect Four rules, AI algorithm characteristics, and quick start guide.
- Implement `GamePage.jsx` assembling `GameStatus`, `GameBoard`, `GameControls`, and `MetricsPanel`.
- Implement `AnalyticsPage.jsx` displaying an analytics preview and metrics overview (scaffolding for Phase 6).
- Update `App.jsx` with state-based navigation (`activeTab === 'home' | 'game' | 'analytics'`).

### Task 6: Accessibility & Mobile Optimization
- Ensure keyboard navigability: columns can be focused using Tab and selected using Enter or Space.
- Add ARIA labels (`aria-label="Drop disc in column 3 of 7"`).
- Verify mobile responsiveness (minimum 44×44px touch targets on mobile viewports).

---

## Verification & Acceptance Criteria

### Verification Commands
1. **Frontend Dependencies**:
   ```powershell
   cd frontend; npm install
   ```
2. **Frontend Linter**:
   ```powershell
   cd frontend; npm run lint
   ```
   *(Must exit with 0 errors)*
3. **Frontend Production Build**:
   ```powershell
   cd frontend; npm run build
   ```
   *(Must generate valid bundle in `frontend/dist/` without build warnings or errors)*
4. **Backend Regression Verification**:
   ```powershell
   python -m pytest backend/tests/test_game_engine.py backend/tests/test_game_state.py backend/tests/test_foundation.py -v
   ```
   *(All 31 unit, engine, state, and foundation tests must pass)*

### Acceptance Criteria
- [ ] **AC-1**: Full component hierarchy implemented: `Navbar`, `GameBoard`, `GameCell`, `GameControls`, `GameStatus`, `MetricsPanel`, `ErrorBanner`.
- [ ] **AC-2**: 7×6 Connect Four board renders responsively on screen sizes from 320px up to 1920px.
- [ ] **AC-3**: Gravity drop animation smoothly animates disc fall to the lowest unoccupied row.
- [ ] **AC-4**: Column hover guide indicates target column and prevents clicks on full columns.
- [ ] **AC-5**: Winning 4-in-a-row triggers celebratory banner and pulsing highlight on the 4 winning cells.
- [ ] **AC-6**: Full-board game without a winner triggers a clear Draw banner with moves locked.
- [ ] **AC-7**: Human vs AI mode correctly interacts with `POST /api/ai-move`, displaying decision time telemetry.
- [ ] **AC-8**: Human vs Human (Pass & Play) mode allows local two-player turns without calling the backend.
- [ ] **AC-9**: Controls allow selecting difficulty (Depth 2, 4, 6), starting player, and Resetting the game.
- [ ] **AC-10**: Navigation bar switches smoothly between Home, Game, and Analytics views via React state.
- [ ] **AC-11**: Network errors or invalid inputs display a standardized error banner without crashing the application.
- [ ] **AC-12**: `npm run build` succeeds cleanly; all 31 backend tests pass with zero regressions.

---

## Files Expected to Change
- `frontend/package.json`
- `frontend/src/services/api.js`
- `frontend/src/hooks/useGame.js`
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
