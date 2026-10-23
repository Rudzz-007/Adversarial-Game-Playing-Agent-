---
phase: 2
plan: 1
wave: 1
gap_closure: false
---

# Plan 2.1 (Revised): Core Game Engine, State Validation & Comprehensive Rules Testing

## Objective
Establish the authoritative single source of truth for Connect Four game state and rules in `backend/app/core/` (`game_engine.py`, `game_state.py`, `validation.py`). Implement exhaustive 4-in-a-row win detection across all directions with deterministic 4-coordinate extraction, strict win-over-draw precedence, full-board draw validation, turn-transition invariants, and domain-to-error-envelope mapping, backed by an exhaustive `pytest` suite while maintaining 100% backward compatibility for `backend/game_engine.py`, `backend/ai_agent.py`, and `POST /api/ai-move`.

## Context
Load these files for context:
- [.gsd/SPEC.md](file:///c:/Users/MANAV/Desktop/FAI-project/Adversarial-Game-Playing-Agent-/.gsd/SPEC.md)
- [.gsd/REQUIREMENTS.md](file:///c:/Users/MANAV/Desktop/FAI-project/Adversarial-Game-Playing-Agent-/.gsd/REQUIREMENTS.md)
- [.gsd/ARCHITECTURE.md](file:///c:/Users/MANAV/Desktop/FAI-project/Adversarial-Game-Playing-Agent-/.gsd/ARCHITECTURE.md)
- [backend/game_engine.py](file:///c:/Users/MANAV/Desktop/FAI-project/Adversarial-Game-Playing-Agent-/backend/game_engine.py)
- [backend/ai_agent.py](file:///c:/Users/MANAV/Desktop/FAI-project/Adversarial-Game-Playing-Agent-/backend/ai_agent.py)
- [backend/main.py](file:///c:/Users/MANAV/Desktop/FAI-project/Adversarial-Game-Playing-Agent-/backend/main.py)
- [backend/tests/test_foundation.py](file:///c:/Users/MANAV/Desktop/FAI-project/Adversarial-Game-Playing-Agent-/backend/tests/test_foundation.py)

---

## Detailed Rules & Engine Specification

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

### 2. Move Legality & Robust Input Validation
- Prevent low-level exceptions (`IndexError`, `TypeError`, `ValueError`) by strictly validating moves before board access:
  - **Type Validation**: `col` must be an integer (`isinstance(col, int) and not isinstance(col, bool)`). Otherwise raise `InvalidMoveException(code="INVALID_MOVE", message="Column must be an integer.")`.
  - **Range Validation**: `col` must satisfy $0 \le c \le 6$. Otherwise raise `InvalidMoveException(code="INVALID_MOVE", message=f"Column index {col} out of bounds (0-6).")`.
  - **Capacity Validation**: `board[0][col] == EMPTY`. If full, raise `ColumnFullException(code="INVALID_MOVE", message=f"The selected column {col} is full.")`.
  - **Board Structure Validation**: When validating an external board, verify it is a list of exactly 6 lists, each containing exactly 7 integers in $\{0, 1, 2\}$. Otherwise raise `InvalidBoardException(code="VALIDATION_ERROR", message="Board must be a 6x7 integer matrix containing only 0, 1, or 2.")`.

### 3. Directional Win Detection & Deterministic Winning Coordinates
- High-speed boolean check: `check_win(board, piece: int) -> bool` for fast evaluation loops.
- Coordinate extraction: `get_winning_coordinates(board, piece: int, last_move: Optional[Tuple[int, int]] = None) -> Optional[List[Tuple[int, int]]]`
- **Deterministic 4-Coordinate Behavior**:
  - If a move creates 5 or more connected pieces (or multiple winning lines), the engine deterministically extracts exactly **four** coordinate pairs for UI highlighting.
  - When `last_move=(r, c)` is provided (as in `apply_move`), lines passing through `(r, c)` are evaluated in canonical order (Horizontal $\to$ Vertical $\to$ Positive Diagonal $\to$ Negative Diagonal), taking the first 4-cell window containing `(r, c)`.
  - When scanning an arbitrary board, canonical scan order is used:
    1. Horizontal: bottom-to-top ($r = 5 \to 0$), left-to-right ($c = 0 \to 3$).
    2. Vertical: left-to-right ($c = 0 \to 6$), bottom-to-top ($r = 5 \to 3$).
    3. Positive Diagonal ($\nearrow$): bottom-to-top ($r = 5 \to 3$), left-to-right ($c = 0 \to 3$).
    4. Negative Diagonal ($\searrow$): top-to-bottom ($r = 0 \to 2$), left-to-right ($c = 0 \to 3$).
  - Coordinates are returned as a sorted list of four coordinate pairs: `[(r0, c0), (r1, c1), (r2, c2), (r3, c3)]`.

### 4. Win vs. Draw Precedence & Full-Board Draw Fixtures
- **Win strictly precedes Draw**: If the 42nd piece (filling the board) completes a 4-in-a-row, status is `"won"` with `winner = current_player` and valid `winning_coords`. It is **never** classified as a draw.
- **Draw Definition**: `is_draw(board) == True` if and only if:
  1. No winning 4-in-a-row exists for either player (`check_win(board, 1) == False` and `check_win(board, 2) == False`), AND
  2. The board is full (`is_board_full(board) == True`).
- **Fixtures in Tests**:
  - Real, valid full-board draw fixture (no 4-in-a-row anywhere on board).
  - Full-board win fixture (42nd piece creates horizontal or vertical win).

### 5. GameState Mutation & Turn-Transition Invariants
- `GameState` encapsulates the authoritative state: `game_id`, `board`, `current_player`, `status`, `winner`, `winning_coords`, `move_count`, `move_history`.
- Invariants enforced by `apply_move(col: int)`:
  1. **Terminal-State Lock**: If `status != "active"`, raise `GameTerminalException(code="GAME_TERMINAL", message="Cannot make a move in a terminal game state.")`. State is completely unmodified.
  2. **Atomic Move Application**: Validates legality $\to$ finds open row $\to$ places piece $\to$ checks win $\to$ checks draw.
  3. **Turn Progression**: If move does not end game, `current_player = 2 if current_player == 1 else 1`. If game ends, `current_player` remains the winning player (or last mover) and does not toggle.
  4. **Illegal Move Isolation**: Any invalid move raises an exception and leaves `board`, `current_player`, `status`, and `move_history` strictly unchanged.
  5. **History Tracking**: Appends `{"move_number": n, "player": p, "column": col, "row": row, "timestamp": iso_str}`.

### 6. Domain Exceptions & Standardized Error Envelope
- Define base `GameRuleException(Exception)` with `status_code`, `code`, and `message`.
- Derived exceptions:
  - `InvalidMoveException(GameRuleException)`: status 400, code `"INVALID_MOVE"`
  - `ColumnFullException(GameRuleException)`: status 400, code `"INVALID_MOVE"`
  - `GameTerminalException(GameRuleException)`: status 400, code `"GAME_TERMINAL"`
  - `InvalidBoardException(GameRuleException)`: status 422, code `"VALIDATION_ERROR"`
- Connected to FastAPI via exception handler in `backend/main.py` producing:
  ```json
  {"error": {"code": "...", "message": "..."}}
  ```
  without leaking stack traces, while preserving existing `POST /api/ai-move` response contract.

---

## Tasks

<task type="auto">
  <name>Task 1: Canonical Core Engine, Coordinate Extraction & Domain Validation</name>
  <files>
    backend/app/core/__init__.py
    backend/app/core/game_engine.py
    backend/app/core/validation.py
    backend/game_engine.py
    backend/main.py
  </files>
  <action>
    1. In `backend/app/core/game_engine.py`:
       - Define canonical constants: `ROWS = 6`, `COLS = 7`, `EMPTY = 0`, `PLAYER_1 = 1`, `PLAYER_2 = 2`, `PLAYER = 1`, `AI = 2`.
       - Implement pure board functions:
         - `create_board() -> List[List[int]]`
         - `is_valid_location(board, col: int) -> bool`
         - `get_valid_locations(board) -> List[int]`
         - `get_next_open_row(board, col: int) -> int`
         - `drop_piece(board, row: int, col: int, piece: int) -> None`
         - `check_win(board, piece: int) -> bool` (fast boolean check for AI loops)
         - `get_winning_coordinates(board, piece: int, last_move: Optional[Tuple[int, int]] = None) -> Optional[List[Tuple[int, int]]]` (deterministic 4-coordinate sequence)
         - `is_board_full(board) -> bool`
         - `is_draw(board) -> bool` (strict win precedence: checks not check_win for either player before returning True)
    2. In `backend/app/core/validation.py`:
       - Define `GameRuleException`, `InvalidMoveException`, `ColumnFullException`, `GameTerminalException`, `InvalidBoardException`.
       - Implement `validate_column_type_and_range(col: Any) -> int`
       - Implement `validate_move_legality(board, col: int, status: str) -> None`
       - Implement `validate_board_structure(board: Any) -> None`
    3. In `backend/game_engine.py`:
       - Refactor root module to delegate to `app.core.game_engine`:
         ```python
         from app.core.game_engine import (
             ROWS, COLS, EMPTY, PLAYER, AI,
             create_board, is_valid_location, get_next_open_row,
             drop_piece, check_win, get_valid_locations,
             get_winning_coordinates, is_board_full, is_draw
         )
         ```
       - Guarantees 100% backward compatibility for `backend/ai_agent.py` and `backend/main.py`.
    4. In `backend/main.py`:
       - Register exception handler for `GameRuleException` returning standardized `{"error": {"code": exc.code, "message": exc.message}}`.
  </action>
  <verify>
    python -c "from app.core.game_engine import create_board, get_winning_coordinates, is_draw; from game_engine import ROWS, check_win; print('Core engine and compatibility bridge verified')"
  </verify>
  <done>
    `app.core.game_engine` functions return correct coordinates, deterministic 4-cell lines, and win-precedence draw checks. Root `game_engine.py` re-exports all symbols with zero code duplication.
  </done>
</task>

<task type="auto">
  <name>Task 2: Authoritative GameState Domain Model & Serialization</name>
  <files>
    backend/app/core/game_state.py
    backend/app/schemas/game_schemas.py
  </files>
  <action>
    1. In `backend/app/core/game_state.py`, implement `GameState`:
       - Attributes: `game_id: str`, `board: List[List[int]]`, `current_player: int`, `status: str`, `winner: Optional[int]`, `winning_coords: Optional[List[Tuple[int, int]]]`, `move_count: int`, `move_history: List[Dict[str, Any]]`.
       - Methods:
         - `apply_move(col: Any) -> Dict[str, Any]`: validates type/bounds/status via `validation.py`, drops piece, evaluates win/draw with win precedence, updates turn if non-terminal, appends history, returns move details.
         - `get_legal_moves() -> List[int]`
         - `is_terminal() -> bool`
         - `to_dict() -> Dict[str, Any]` matching PRD §12 schema.
         - `clone() -> GameState` deep-copying board and state for lookahead simulations.
    2. In `backend/app/schemas/game_schemas.py`:
       - Add `GameStateResponse` and `MoveResponse` models with optional `winning_coords: Optional[List[List[int]]]`.
  </action>
  <verify>
    python -c "from app.core.game_state import GameState; g = GameState(); res = g.apply_move(3); assert res['row'] == 5; assert g.current_player == 2; print('GameState verified')"
  </verify>
  <done>
    `GameState` enforces turn-transition invariants, terminal locks, atomic state mutation, and serializes matching the PRD schema.
  </done>
</task>

<task type="auto">
  <name>Task 3: Comprehensive Pytest Engine, Rules & Minimax Regression Suite</name>
  <files>
    backend/tests/test_game_engine.py
    backend/tests/test_game_state.py
  </files>
  <action>
    1. Create `backend/tests/test_game_engine.py`:
       - `test_board_initialization`: 6 rows, 7 columns, all 0s.
       - `test_piece_gravity`: drops fill bottom row 5 first, then row 4, row 3, etc.
       - `test_column_bounds_and_capacity`: column < 0, column >= 7, column full.
       - `test_horizontal_win_all_offsets`: test horizontal wins across different rows and column offsets (0-3, 1-4, 2-5, 3-6); verify exact 4 coordinates.
       - `test_vertical_win_all_offsets`: test vertical wins across columns and row offsets (5-2, 4-1, 3-0); verify exact 4 coordinates.
       - `test_positive_diagonal_win`: verify win from bottom-left to top-right ($\nearrow$); verify exact 4 coordinates.
       - `test_negative_diagonal_win`: verify win from top-left to bottom-right ($\searrow$); verify exact 4 coordinates.
       - `test_deterministic_winning_coords_5_in_a_row`: construct 5-in-a-row and verify engine deterministically returns documented 4-coordinate sequence.
       - `test_valid_full_board_draw_fixture`: test a known full-board draw fixture with 42 discs; verify `is_board_full == True`, `is_draw == True`, `check_win == False`.
       - `test_full_board_win_takes_precedence_over_draw`: 42nd piece creates a win; verify `check_win == True`, `is_draw == False`, status is `"won"`.
       - `test_legacy_minimax_regression_execution`: call `ai_agent.minimax(board, depth=2, alpha=-math.inf, beta=math.inf, maximizing_player=True)` through the compatibility bridge; verify it returns a valid legal column `0 <= col < 7` and integer/float evaluation score.
    2. Create `backend/tests/test_game_state.py`:
       - `test_state_initialization`: player 1 first, 7 legal moves, status active.
       - `test_state_turn_transition`: player 1 $\to$ player 2 $\to$ player 1.
       - `test_state_invalid_move_type_and_range`: non-integer col, negative col, col >= 7 raise `InvalidMoveException`.
       - `test_state_full_column_rejected`: 7th move in full column raises `ColumnFullException` without mutating state or changing player turn.
       - `test_state_terminal_lock`: attempting move after win or draw raises `GameTerminalException`; board and player turn remain frozen.
       - `test_state_move_history`: verify move records contain move_number, player, col, row, and timestamp.
    3. Run full test suite across all foundation and game engine tests.
  </action>
  <verify>
    python -m pytest backend/tests/test_game_engine.py backend/tests/test_game_state.py backend/tests/test_foundation.py -v
  </verify>
  <done>
    All engine, state, validation, and legacy regression tests pass with 100% success rate.
  </done>
</task>

---

## Must-Haves
After all tasks complete, verify:
- [ ] Connect Four rules have a single source of truth in `backend/app/core/game_engine.py`.
- [ ] `backend/game_engine.py` delegates to `app.core.game_engine` exporting all legacy symbols (`ROWS, COLS, EMPTY, PLAYER, AI, create_board, is_valid_location, get_next_open_row, drop_piece, check_win, get_valid_locations`).
- [ ] Existing `minimax` function in `backend/ai_agent.py` executes successfully through the bridge in regression testing.
- [ ] Deterministic 4-coordinate sequence is returned when 4 or more connected pieces exist.
- [ ] Win strictly takes precedence over draw; verified with full-board draw and full-board win fixtures.
- [ ] Input validation rejects out-of-range, non-integer, and full columns without leaking low-level exceptions.
- [ ] Domain exceptions format into standardized error envelope `{"error": {"code": "...", "message": "..."}}`.
- [ ] Moves after game win or draw are strictly locked and rejected.
- [ ] `POST /api/ai-move` continues to pass regression tests without modification.
- [ ] Full pytest suite passes with 0 failures.

## Success Criteria
- [ ] All 3 tasks verified passing.
- [ ] Must-haves confirmed.
- [ ] No regressions in foundation tests or existing AI agent.
