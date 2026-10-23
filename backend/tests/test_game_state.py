import sys
from pathlib import Path
import pytest

# Ensure backend root is on sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.core.game_engine import PLAYER_1, PLAYER_2
from app.core.game_state import GameState
from app.core.validation import (
    InvalidMoveException,
    ColumnFullException,
    GameTerminalException,
)
from tests.test_game_engine import DRAW_MOVES_SEQUENCE, DRAW_BOARD_FIXTURE


def test_state_initialization():
    """Verify default initial GameState."""
    game = GameState()
    assert game.status == "active"
    assert game.current_player == PLAYER_1
    assert game.winner is None
    assert game.winning_coords is None
    assert game.move_count == 0
    assert len(game.move_history) == 0
    assert len(game.get_legal_moves()) == 7
    assert not game.is_terminal()


def test_state_turn_transition():
    """Verify turn alternation between Player 1 and Player 2."""
    game = GameState()
    rec1 = game.apply_move(3)
    assert rec1["player"] == PLAYER_1
    assert rec1["row"] == 5
    assert rec1["column"] == 3
    assert game.current_player == PLAYER_2

    rec2 = game.apply_move(3)
    assert rec2["player"] == PLAYER_2
    assert rec2["row"] == 4
    assert rec2["column"] == 3
    assert game.current_player == PLAYER_1


def test_state_boolean_column_rejected():
    """Verify boolean column values (True, False) are strictly rejected as invalid types."""
    game = GameState()
    initial_turn = game.current_player

    with pytest.raises(InvalidMoveException) as exc_info_true:
        game.apply_move(True)
    assert exc_info_true.value.code == "INVALID_MOVE"
    assert "boolean" in exc_info_true.value.message.lower()
    assert game.current_player == initial_turn

    with pytest.raises(InvalidMoveException) as exc_info_false:
        game.apply_move(False)
    assert exc_info_false.value.code == "INVALID_MOVE"
    assert "boolean" in exc_info_false.value.message.lower()
    assert game.current_player == initial_turn


def test_state_immutability_on_any_invalid_move():
    """
    Safeguard 1 verification:
    Confirm that an invalid GameState.apply_move() call leaves the board,
    current player, status, winner, winning_coords, and move history completely unchanged.
    """
    game = GameState()
    # Play 3 legal moves so the game is in a non-initial state
    game.apply_move(3)  # P1
    game.apply_move(3)  # P2
    game.apply_move(2)  # P1

    snapshot_board = [r[:] for r in game.board]
    snapshot_player = game.current_player
    snapshot_status = game.status
    snapshot_winner = game.winner
    snapshot_coords = game.winning_coords
    snapshot_history = [dict(m) for m in game.move_history]
    snapshot_count = game.move_count

    def assert_state_unchanged():
        assert game.board == snapshot_board
        assert game.current_player == snapshot_player
        assert game.status == snapshot_status
        assert game.winner == snapshot_winner
        assert game.winning_coords == snapshot_coords
        assert game.move_history == snapshot_history
        assert game.move_count == snapshot_count

    # 1. Boolean values
    for val in [True, False]:
        with pytest.raises(InvalidMoveException):
            game.apply_move(val)
        assert_state_unchanged()

    # 2. Out of bounds
    for col in [-10, -1, 7, 8, 100]:
        with pytest.raises(InvalidMoveException):
            game.apply_move(col)
        assert_state_unchanged()

    # 3. Invalid types
    for val in ["2", 2.0, None, [1], {"col": 1}]:
        with pytest.raises(InvalidMoveException):
            game.apply_move(val)
        assert_state_unchanged()

    # 4. Full column (fill column 3 to capacity)
    # Column 3 currently has 2 pieces (row 5, row 4). Add 4 more.
    game.apply_move(3)  # P2 (row 3)
    game.apply_move(3)  # P1 (row 2)
    game.apply_move(3)  # P2 (row 1)
    game.apply_move(3)  # P1 (row 0) - full!

    full_snapshot_board = [r[:] for r in game.board]
    full_snapshot_player = game.current_player
    full_snapshot_status = game.status
    full_snapshot_winner = game.winner
    full_snapshot_coords = game.winning_coords
    full_snapshot_history = [dict(m) for m in game.move_history]
    full_snapshot_count = game.move_count

    with pytest.raises(ColumnFullException):
        game.apply_move(3)

    assert game.board == full_snapshot_board
    assert game.current_player == full_snapshot_player
    assert game.status == full_snapshot_status
    assert game.winner == full_snapshot_winner
    assert game.winning_coords == full_snapshot_coords
    assert game.move_history == full_snapshot_history
    assert game.move_count == full_snapshot_count


def test_state_invalid_move_type_and_range():
    """Verify out-of-range columns and strings are rejected without mutating state."""
    game = GameState()
    initial_board = [r[:] for r in game.board]

    for bad_col in [-1, 7, 10, "3", 2.5, None]:
        with pytest.raises(InvalidMoveException) as exc_info:
            game.apply_move(bad_col)
        assert exc_info.value.code == "INVALID_MOVE"
        assert game.board == initial_board
        assert game.current_player == PLAYER_1
        assert game.move_count == 0


def test_state_full_column_rejected():
    """Verify 7th move in full column raises ColumnFullException without corrupting turn."""
    game = GameState()
    for _ in range(6):
        game.apply_move(0)

    turn_before_error = game.current_player
    with pytest.raises(ColumnFullException) as exc_info:
        game.apply_move(0)

    assert exc_info.value.code == "INVALID_MOVE"
    assert "full" in exc_info.value.message.lower()
    # State and turn must remain frozen on error
    assert game.current_player == turn_before_error
    assert game.move_count == 6


def test_state_terminal_lock_on_win():
    """Verify that after a victory, status is 'won' and subsequent moves are rejected."""
    game = GameState()
    # P1: 0, P2: 0, P1: 1, P2: 1, P1: 2, P2: 2, P1: 3 -> P1 wins horizontally in row 5
    moves = [0, 0, 1, 1, 2, 2, 3]
    for col in moves:
        game.apply_move(col)

    assert game.status == "won"
    assert game.winner == PLAYER_1
    assert game.is_terminal()
    assert len(game.winning_coords) == 4
    assert game.winning_coords == [(5, 0), (5, 1), (5, 2), (5, 3)]
    assert game.get_legal_moves() == []

    # Attempting move after terminal status raises GameTerminalException
    with pytest.raises(GameTerminalException) as exc_info:
        game.apply_move(4)
    assert exc_info.value.code == "GAME_TERMINAL"
    assert game.winner == PLAYER_1


def test_state_terminal_lock_on_draw_replay():
    """
    Verify full 42-move draw replay through GameState.
    Status transitions to 'draw', winner is None, and subsequent moves are locked.
    """
    game = GameState()
    for idx, col in enumerate(DRAW_MOVES_SEQUENCE):
        assert game.status == "active"
        game.apply_move(col)

    assert game.status == "draw"
    assert game.winner is None
    assert game.winning_coords is None
    assert game.is_terminal()
    assert game.get_legal_moves() == []
    assert game.board == DRAW_BOARD_FIXTURE

    # 43rd move must be locked
    with pytest.raises(GameTerminalException) as exc_info:
        game.apply_move(0)
    assert exc_info.value.code == "GAME_TERMINAL"


def test_state_clone_isolation():
    """Verify clone produces an independent copy of GameState."""
    original = GameState()
    original.apply_move(3)

    clone = original.clone()
    assert clone.board == original.board
    assert clone.current_player == original.current_player

    # Move on clone does not affect original
    clone.apply_move(3)
    assert clone.move_count == 2
    assert original.move_count == 1
    assert clone.board != original.board


def test_state_serialization():
    """Verify to_dict returns schema matching PRD requirements."""
    game = GameState()
    game.apply_move(2)
    d = game.to_dict()

    assert "game_id" in d
    assert "board" in d
    assert d["current_player"] == PLAYER_2
    assert d["status"] == "active"
    assert d["winner"] is None
    assert len(d["legal_moves"]) == 7
    assert d["move_count"] == 1
    assert d["last_move"]["column"] == 2
    assert d["last_move"]["row"] == 5
    assert d["last_move"]["player"] == PLAYER_1
