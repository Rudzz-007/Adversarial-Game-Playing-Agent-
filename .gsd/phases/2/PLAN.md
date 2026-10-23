---
phase: 2
plan: 1
wave: 1
gap_closure: false
---

# Plan 2.1: Core Game Engine, State Validation & Comprehensive Rules Testing

## Objective
Establish the authoritative single source of truth for Connect Four game state and rules in `backend/app/core/` (`game_engine.py`, `game_state.py`, `validation.py`). Implement exhaustive 4-in-a-row win detection across all directions with winning coordinate reporting, draw detection, turn rotation, and terminal-state locking, backed by an exhaustive `pytest` suite while maintaining 100% backward compatibility for `backend/game_engine.py` and `POST /api/ai-move`.

## Context
Load these files for context:
- [.gsd/SPEC.md](file:///c:/Users/MANAV/Desktop/FAI-project/Adversarial-Game-Playing-Agent-/.gsd/SPEC.md)
- [.gsd/REQUIREMENTS.md](file:///c:/Users/MANAV/Desktop/FAI-project/Adversarial-Game-Playing-Agent-/.gsd/REQUIREMENTS.md)
- [.gsd/ARCHITECTURE.md](file:///c:/Users/MANAV/Desktop/FAI-project/Adversarial-Game-Playing-Agent-/.gsd/ARCHITECTURE.md)
- [backend/game_engine.py](file:///c:/Users/MANAV/Desktop/FAI-project/Adversarial-Game-Playing-Agent-/backend/game_engine.py)
- [backend/ai_agent.py](file:///c:/Users/MANAV/Desktop/FAI-project/Adversarial-Game-Playing-Agent-/backend/ai_agent.py)
- [backend/tests/test_foundation.py](file:///c:/Users/MANAV/Desktop/FAI-project/Adversarial-Game-Playing-Agent-/backend/tests/test_foundation.py)

---

## Game State & Rules Specification

### 1. Board Representation & Coordinate Conventions
- **Grid Dimensions**: Exactly 6 rows by 7 columns ($6 \times 7$ matrix).
- **Coordinate Indexing**:
  - `row`: $0 \le r \le 5$, where row `0` is the **top row** and row `5` is the **bottom row**.
  - `col`: $0 \le c \le 6$, where column `0` is the **leftmost column** and column `6` is the **rightmost column**.
- **Cell Values**:
  - `0`: Empty cell (`EMPTY`)
  - `1`: Player 1 / Human (`PLAYER_1` / `PLAYER`)
  - `2`: Player 2 / AI Agent (`PLAYER_2` / `AI`)
- **Piece Gravity**: Dropping into column $c$ occupies the highest available row index $r$ (from bottom row 5 up to top row 0).

### 2. Valid-Move & Column Full Behavior
- A move into column $c$ is legal if and only if $0 \le c \le 6$ and `board[0][c] == 0`.
- If $c < 0$ or $c > 6$, reject with `INVALID_MOVE` ("Column index out of bounds (0-6).").
- If `board[0][c] != 0`, column is full: reject with `INVALID_MOVE` ("The selected column is full.").

### 3. Turn Rules & Terminal-State Handling
- Players alternate turns strictly: Player 1 $\to$ Player 2 $\to$ Player 1.
- Initial game status: `"active"`.
- If a move creates 4 consecutive matching pieces: status transitions to `"won"`, `winner = current_player`, and `winning_coords` records the 4 coordinates.
- If all 42 cells are filled and no win exists: status transitions to `"draw"`, `winner = null`, `winning_coords = null`.
- Once status is `"won"` or `"draw"`, game is **terminal**: any subsequent move attempts are rejected with `GAME_TERMINAL` ("Cannot make a move in a terminal game state.").

### 4. Directional Win Detection & Coordinate Extraction
Win checking evaluates four distinct vectors from every eligible origin $(r, c)$:
- **Horizontal**: $(r, c), (r, c+1), (r, c+2), (r, c+3)$ for $0 \le r < 6$, $0 \le c \le 3$.
- **Vertical**: $(r, c), (r+1, c), (r+2, c), (r+3, c)$ for $0 \le r \le 2$, $0 \le c < 7$.
- **Positive Diagonal ($\nearrow$ / row index decreasing)**: $(r, c), (r-1, c+1), (r-2, c+2), (r-3, c+3)$ for $3 \le r < 6$, $0 \le c \le 3$.
- **Negative Diagonal ($\searrow$ / row index increasing)**: $(r, c), (r+1, c+1), (r+2, c+2), (r+3, c+3)$ for $0 \le r \le 2$, $0 \le c \le 3$.
- **Winning Coordinate Format**: Sorted list of coordinate pairs: `[[r0, c0], [r1, c1], [r2, c2], [r3, c3]]`.

---

## Tasks

<task type="auto">
  <name>Task 1: Authoritative Core Game Engine & Validation</name>
  <files>
    backend/app/core/__init__.py
    backend/app/core/game_engine.py
    backend/app/core/validation.py
    backend/game_engine.py
  </files>
  <action>
    1. Create `backend/app/core/__init__.py` exporting core functions.
    2. In `backend/app/core/game_engine.py`:
       - Define canonical constants: `ROWS = 6`, `COLS = 7`, `EMPTY = 0`, `PLAYER_1 = 1`, `PLAYER_2 = 2`, `PLAYER = 1`, `AI = 2`.
       - Implement pure board functions:
         - `create_board() -> List[List[int]]`
         - `is_valid_location(board, col: int) -> bool`
         - `get_valid_locations(board) -> List[int]`
         - `get_next_open_row(board, col: int) -> int`
         - `drop_piece(board, row: int, col: int, piece: int) -> None`
         - `check_win(board, piece: int) -> bool` (high-speed boolean check for AI search loops)
         - `get_winning_coordinates(board, piece: int) -> Optional[List[Tuple[int, int]]]`
         - `is_board_full(board) -> bool`
         - `is_draw(board) -> bool`
    3. In `backend/app/core/validation.py`:
       - Define custom domain exceptions: `GameRuleException`, `InvalidMoveException`, `ColumnFullException`, `GameTerminalException`.
       - Implement `validate_column(col: int) -> None`
       - Implement `validate_move_legality(board, col: int, status: str) -> None`
    4. Refactor root `backend/game_engine.py`:
       - Delegate directly to `app.core.game_engine` via `from app.core.game_engine import *`.
       - This eliminates duplicate code while preserving exact import compatibility for existing `backend/ai_agent.py` and `backend/main.py`.
  </action>
  <verify>
    python -c "from app.core.game_engine import create_board, get_winning_coordinates, is_draw; from game_engine import ROWS, check_win; print('Core engine and delegation verified')"
  </verify>
  <done>
    `app.core.game_engine` functions return correct coordinates and booleans; root `game_engine.py` delegates seamlessly with zero regressions.
  </done>
</task>

<task type="auto">
  <name>Task 2: Authoritative GameState Domain Model</name>
  <files>
    backend/app/core/game_state.py
    backend/app/schemas/game_schemas.py
  </files>
  <action>
    1. In `backend/app/core/game_state.py`, implement `GameState`:
       - Attributes:
         - `game_id: str` (UUID string)
         - `board: List[List[int]]` (6x7 grid)
         - `current_player: int` (1 or 2)
         - `status: str` (`"active"`, `"won"`, `"draw"`)
         - `winner: Optional[int]` (1, 2, or None)
         - `winning_coords: Optional[List[Tuple[int, int]]]`
         - `move_count: int`
         - `move_history: List[Dict[str, Any]]` (records `player`, `column`, `row`, `move_number`)
       - Methods:
         - `apply_move(col: int) -> Dict[str, Any]`: validates move legality, places piece at lowest open row, checks for victory or draw, updates turn if active, appends to history, and returns move result.
         - `get_legal_moves() -> List[int]`
         - `is_terminal() -> bool`
         - `to_dict() -> Dict[str, Any]`: serializes state matching PRD §12.2 and §12.5.
         - `clone() -> GameState`: produces an isolated deep-copy for hypothetical rollouts.
    2. In `backend/app/schemas/game_schemas.py`:
       - Add `GameStateResponse`: `game_id: str`, `board: List[List[int]]`, `current_player: int`, `status: str`, `winner: Optional[int]`, `legal_moves: List[int]`, `winning_coords: Optional[List[List[int]]] = None`.
       - Add `MoveResponse`: `board: List[List[int]]`, `current_player: int`, `status: str`, `winner: Optional[int]`, `last_move: Dict[str, Any]`, `winning_coords: Optional[List[List[int]]] = None`.
  </action>
  <verify>
    python -c "from app.core.game_state import GameState; g = GameState(); res = g.apply_move(3); assert res['row'] == 5; assert g.current_player == 2; print('GameState verified')"
  </verify>
  <done>
    `GameState` encapsulates full game lifecycle, enforces rule validation, updates history, and serializes to the PRD §12 schema.
  </done>
</task>

<task type="auto">
  <name>Task 3: Comprehensive Pytest Engine Test Suite</name>
  <files>
    backend/tests/test_game_engine.py
    backend/tests/test_game_state.py
  </files>
  <action>
    1. Create `backend/tests/test_game_engine.py`:
       - `test_board_initialization`: 6x7, all 0s.
       - `test_piece_gravity`: drops fill row 5, then row 4, etc.
       - `test_column_full_detection`: 6 pieces fill column; `is_valid_location` becomes False.
       - `test_horizontal_win`: test all rows, multiple column spans (0-3, 1-4, 2-5, 3-6); verify exact 4 coordinates.
       - `test_vertical_win`: test all columns, multiple row spans (5-2, 4-1, 3-0); verify exact 4 coordinates.
       - `test_positive_diagonal_win`: verify win from bottom-left to top-right ($\nearrow$); verify coordinates.
       - `test_negative_diagonal_win`: verify win from top-left to bottom-right ($\searrow$); verify coordinates.
       - `test_full_board_draw`: fill board without 4-in-a-row; verify `is_board_full` is True, `is_draw` is True, `check_win` is False.
       - `test_legacy_engine_compatibility`: verify existing `ai_agent.minimax` runs using the refactored `game_engine.py` without error.
    2. Create `backend/tests/test_game_state.py`:
       - `test_state_initial_values`: player 1 first, 7 legal moves, status active.
       - `test_state_turn_alternation`: move switches player 1 $\to$ 2 $\to$ 1.
       - `test_state_invalid_column_rejected`: column < 0 or >= 7 raises `InvalidMoveException`.
       - `test_state_full_column_rejected`: 7th move in full column raises `ColumnFullException`.
       - `test_state_terminal_lock`: moves after win or draw raise `GameTerminalException`.
       - `test_state_history_tracking`: each move appends player, col, row, and move_number.
    3. Run full pytest suite across both foundation and engine tests.
  </action>
  <verify>
    python -m pytest backend/tests/test_game_engine.py backend/tests/test_game_state.py backend/tests/test_foundation.py -v
  </verify>
  <done>
    All engine and state tests pass with 100% rule coverage; foundation tests continue to pass with 0 regressions.
  </done>
</task>

---

## Must-Haves
After all tasks complete, verify:
- [ ] Connect Four rules have a single source of truth in `backend/app/core/game_engine.py`.
- [ ] `backend/game_engine.py` delegates to `app.core.game_engine` with zero logic duplication.
- [ ] Horizontal, vertical, positive diagonal, and negative diagonal wins are verified with exact coordinate reporting.
- [ ] Draw condition is explicitly detected and verified.
- [ ] Moves after game win/draw are strictly rejected.
- [ ] `POST /api/ai-move` continues to pass regression tests without modification.
- [ ] Full pytest suite passes with 0 failures.

## Success Criteria
- [ ] All 3 tasks verified passing.
- [ ] Must-haves confirmed.
- [ ] No regressions in foundation tests or existing AI agent.
