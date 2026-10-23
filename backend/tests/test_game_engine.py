import sys
from pathlib import Path
import math
import pytest

# Ensure backend root is on sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import game_engine as bridge_engine
from app.core.game_engine import (
    ROWS,
    COLS,
    EMPTY,
    PLAYER_1,
    PLAYER_2,
    create_board,
    is_valid_location,
    get_valid_locations,
    get_next_open_row,
    drop_piece,
    check_win,
    get_winning_coordinates,
    is_board_full,
    is_draw,
)
from ai_agent import minimax

# Concrete, verified 6x7 full-board draw fixture
DRAW_BOARD_FIXTURE = [
    [1, 2, 1, 2, 1, 2, 2],
    [1, 2, 1, 2, 1, 2, 1],
    [2, 1, 2, 1, 2, 1, 2],
    [2, 1, 2, 1, 2, 1, 1],
    [1, 2, 1, 2, 1, 2, 2],
    [1, 2, 1, 2, 1, 2, 1],
]

# Verified legal 42-move sequence reachable under gravity without premature win
DRAW_MOVES_SEQUENCE = [
    6, 6, 6, 6, 6, 5, 4, 5, 5, 6,
    4, 4, 5, 4, 4, 3, 4, 3, 3, 5,
    2, 5, 2, 2, 3, 2, 2, 1, 2, 1,
    1, 3, 0, 3, 0, 0, 1, 0, 0, 1,
    0, 1
]


def test_board_initialization():
    """Verify clean 6x7 board initialization."""
    board = create_board()
    assert len(board) == ROWS
    assert all(len(row) == COLS for row in board)
    assert all(cell == EMPTY for row in board for cell in row)


def test_piece_gravity_and_column_capacity():
    """Verify pieces fall to lowest available row and capacity is respected."""
    board = create_board()
    col = 3
    for expected_row in range(ROWS - 1, -1, -1):
        assert is_valid_location(board, col)
        row = get_next_open_row(board, col)
        assert row == expected_row
        drop_piece(board, row, col, PLAYER_1)

    # Column is now completely full (row 0 occupied)
    assert not is_valid_location(board, col)
    assert get_next_open_row(board, col) == -1


def test_column_bounds_validation():
    """Verify out-of-bounds columns are rejected by engine functions."""
    board = create_board()
    assert not is_valid_location(board, -1)
    assert not is_valid_location(board, 7)
    assert not is_valid_location(board, 100)
    assert get_next_open_row(board, -1) == -1
    assert get_next_open_row(board, 7) == -1


def test_horizontal_win_all_offsets():
    """Verify horizontal 4-in-a-row detection across rows and column offsets."""
    for r in [0, 2, 5]:
        for start_c in range(COLS - 3):
            board = create_board()
            for i in range(4):
                drop_piece(board, r, start_c + i, PLAYER_1)
            assert check_win(board, PLAYER_1)
            assert not check_win(board, PLAYER_2)
            coords = get_winning_coordinates(board, PLAYER_1)
            expected = sorted([(r, start_c + i) for i in range(4)])
            assert coords == expected


def test_vertical_win_all_offsets():
    """Verify vertical 4-in-a-row detection across columns and row offsets."""
    for c in [0, 3, 6]:
        for start_r in range(ROWS - 3):
            board = create_board()
            for i in range(4):
                drop_piece(board, start_r + i, c, PLAYER_2)
            assert check_win(board, PLAYER_2)
            assert not check_win(board, PLAYER_1)
            coords = get_winning_coordinates(board, PLAYER_2)
            expected = sorted([(start_r + i, c) for i in range(4)])
            assert coords == expected


def test_positive_diagonal_win():
    """Verify positive diagonal (/) win detection and coordinate extraction."""
    board = create_board()
    # (3, 0), (2, 1), (1, 2), (0, 3)
    coords_expected = [(3, 0), (2, 1), (1, 2), (0, 3)]
    for r, c in coords_expected:
        drop_piece(board, r, c, PLAYER_1)
    assert check_win(board, PLAYER_1)
    assert not check_win(board, PLAYER_2)
    coords = get_winning_coordinates(board, PLAYER_1)
    assert coords == sorted(coords_expected)


def test_negative_diagonal_win():
    """Verify negative diagonal (\\) win detection and coordinate extraction."""
    board = create_board()
    # (0, 0), (1, 1), (2, 2), (3, 3)
    coords_expected = [(0, 0), (1, 1), (2, 2), (3, 3)]
    for r, c in coords_expected:
        drop_piece(board, r, c, PLAYER_2)
    assert check_win(board, PLAYER_2)
    assert not check_win(board, PLAYER_1)
    coords = get_winning_coordinates(board, PLAYER_2)
    assert coords == sorted(coords_expected)


def test_deterministic_winning_coords_5_in_a_row():
    """Verify deterministic 4-coordinate extraction when 5 connected pieces exist."""
    board = create_board()
    # Place 5 pieces horizontally in bottom row (col 1 to 5)
    for c in range(1, 6):
        drop_piece(board, 5, c, PLAYER_1)
    assert check_win(board, PLAYER_1)
    coords = get_winning_coordinates(board, PLAYER_1)
    assert coords is not None
    assert len(coords) == 4
    # Canonical scan returns the first valid 4-cell window [(5, 1), (5, 2), (5, 3), (5, 4)]
    assert coords == [(5, 1), (5, 2), (5, 3), (5, 4)]


def test_draw_game_replay_sequence_and_fixture():
    """
    Verify that DRAW_BOARD_FIXTURE is reachable via legal alternating moves
    under gravity without premature win, and terminates in a valid draw.
    """
    board = create_board()
    current_player = PLAYER_1

    for idx, col in enumerate(DRAW_MOVES_SEQUENCE):
        row = get_next_open_row(board, col)
        assert row != -1, f"Column {col} full prematurely at move {idx + 1}"
        drop_piece(board, row, col, current_player)

        # Neither player has won during any intermediate step
        if idx < 41:
            assert not check_win(board, PLAYER_1), f"Player 1 prematurely won at move {idx + 1}"
            assert not check_win(board, PLAYER_2), f"Player 2 prematurely won at move {idx + 1}"

        current_player = PLAYER_2 if current_player == PLAYER_1 else PLAYER_1

    # Final move checks
    assert board == DRAW_BOARD_FIXTURE
    assert is_board_full(board)
    assert not check_win(board, PLAYER_1)
    assert not check_win(board, PLAYER_2)
    assert is_draw(board)


def test_full_board_win_takes_precedence_over_draw():
    """
    Verify that when the 42nd piece completes 4-in-a-row,
    win strictly precedes draw (is_draw returns False).
    """
    board = [r[:] for r in DRAW_BOARD_FIXTURE]
    # Modify top row so that player 2 has 4-in-a-row in row 0
    # Originally row 0 is: [1, 2, 1, 2, 1, 2, 2]
    # Change to: [2, 2, 2, 2, 1, 2, 2]
    board[0][0] = 2
    board[0][2] = 2

    assert is_board_full(board)
    assert check_win(board, PLAYER_2)
    # Win strictly precludes draw!
    assert not is_draw(board)


def test_legacy_minimax_regression_execution():
    """
    Regression test exercising existing minimax through the compatibility bridge.
    Asserts returned column is strictly legal for the test board and matches signature.
    """
    board = create_board()
    # Populate a realistic 4-ply opening board
    drop_piece(board, 5, 3, PLAYER_1)
    drop_piece(board, 4, 3, PLAYER_2)
    drop_piece(board, 5, 2, PLAYER_1)
    drop_piece(board, 5, 4, PLAYER_2)

    valid_cols = get_valid_locations(board)
    assert len(valid_cols) == 7

    # Call minimax with its exact original signature
    col, score = minimax(board, depth=2, alpha=-math.inf, beta=math.inf, maximizing_player=True)

    assert isinstance(col, int)
    assert col in valid_cols
    assert math.isfinite(score)
    row = get_next_open_row(board, col)
    assert 0 <= row < ROWS


def test_compatibility_bridge_delegation():
    """Verify that root game_engine module re-exports all canonical symbols."""
    assert bridge_engine.ROWS == ROWS
    assert bridge_engine.COLS == COLS
    assert bridge_engine.EMPTY == EMPTY
    assert bridge_engine.PLAYER == PLAYER_1
    assert bridge_engine.AI == PLAYER_2
    assert bridge_engine.create_board is create_board
    assert bridge_engine.check_win is check_win
    assert bridge_engine.get_next_open_row is get_next_open_row
