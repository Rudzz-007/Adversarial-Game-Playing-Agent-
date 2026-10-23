"""
Canonical Connect Four Game Engine.
Single source of truth for grid dimensions, piece dropping, win detection,
winning coordinate extraction, and draw checking.
"""
from typing import List, Optional, Tuple

ROWS: int = 6
COLS: int = 7
EMPTY: int = 0
PLAYER_1: int = 1
PLAYER_2: int = 2

# Aliases for backward compatibility with existing prototype
PLAYER: int = PLAYER_1
AI: int = PLAYER_2


def create_board() -> List[List[int]]:
    """Initialize and return an empty 6x7 board matrix."""
    return [[EMPTY for _ in range(COLS)] for _ in range(ROWS)]


def is_valid_location(board: List[List[int]], col: int) -> bool:
    """Check if the given column is valid and has open capacity."""
    if not isinstance(col, int) or isinstance(col, bool):
        return False
    if col < 0 or col >= COLS:
        return False
    return board[0][col] == EMPTY


def get_valid_locations(board: List[List[int]]) -> List[int]:
    """Return all column indices that are currently legal for a move."""
    return [c for c in range(COLS) if is_valid_location(board, c)]


def get_next_open_row(board: List[List[int]], col: int) -> int:
    """
    Find the lowest available row index in column `col` (from row 5 up to row 0).
    Returns -1 if column is invalid or full.
    """
    if not isinstance(col, int) or isinstance(col, bool) or col < 0 or col >= COLS:
        return -1
    for r in range(ROWS - 1, -1, -1):
        if board[r][col] == EMPTY:
            return r
    return -1


def drop_piece(board: List[List[int]], row: int, col: int, piece: int) -> None:
    """Place piece into the specified cell."""
    board[row][col] = piece


def check_win(board: List[List[int]], piece: int) -> bool:
    """
    High-performance boolean 4-in-a-row victory detection.
    Evaluates horizontal, vertical, and both diagonal directions.
    """
    # Horizontal check
    for r in range(ROWS):
        for c in range(COLS - 3):
            if (
                board[r][c] == piece
                and board[r][c + 1] == piece
                and board[r][c + 2] == piece
                and board[r][c + 3] == piece
            ):
                return True

    # Vertical check
    for r in range(ROWS - 3):
        for c in range(COLS):
            if (
                board[r][c] == piece
                and board[r + 1][c] == piece
                and board[r + 2][c] == piece
                and board[r + 3][c] == piece
            ):
                return True

    # Diagonal check (\: row increasing, col increasing)
    for r in range(ROWS - 3):
        for c in range(COLS - 3):
            if (
                board[r][c] == piece
                and board[r + 1][c + 1] == piece
                and board[r + 2][c + 2] == piece
                and board[r + 3][c + 3] == piece
            ):
                return True

    # Diagonal check (/: row decreasing, col increasing)
    for r in range(3, ROWS):
        for c in range(COLS - 3):
            if (
                board[r][c] == piece
                and board[r - 1][c + 1] == piece
                and board[r - 2][c + 2] == piece
                and board[r - 3][c + 3] == piece
            ):
                return True

    return False


def get_winning_coordinates(
    board: List[List[int]], piece: int, last_move: Optional[Tuple[int, int]] = None
) -> Optional[List[Tuple[int, int]]]:
    """
    Extract a deterministic sequence of exactly 4 coordinates for a winning line.
    If 5 or more pieces are connected, returns the first 4-cell window detected
    by canonical scan order (or passing through last_move if provided).
    Coordinates are returned as a sorted list of (row, col) tuples.
    Returns None if no 4-in-a-row exists.
    """
    def _is_matching_window(coords: List[Tuple[int, int]]) -> bool:
        return all(board[r][c] == piece for r, c in coords)

    # 1. If last_move provided, prioritize lines passing through that piece
    if last_move is not None:
        lr, lc = last_move
        if 0 <= lr < ROWS and 0 <= lc < COLS and board[lr][lc] == piece:
            # Horizontal windows containing (lr, lc)
            for offset in range(4):
                start_c = lc - offset
                if 0 <= start_c <= COLS - 4:
                    win_coords = [(lr, start_c + i) for i in range(4)]
                    if _is_matching_window(win_coords):
                        return sorted(win_coords)

            # Vertical windows containing (lr, lc)
            for offset in range(4):
                start_r = lr - offset
                if 0 <= start_r <= ROWS - 4:
                    win_coords = [(start_r + i, lc) for i in range(4)]
                    if _is_matching_window(win_coords):
                        return sorted(win_coords)

            # Diagonal \ (increasing row, increasing col)
            for offset in range(4):
                start_r = lr - offset
                start_c = lc - offset
                if 0 <= start_r <= ROWS - 4 and 0 <= start_c <= COLS - 4:
                    win_coords = [(start_r + i, start_c + i) for i in range(4)]
                    if _is_matching_window(win_coords):
                        return sorted(win_coords)

            # Diagonal / (decreasing row, increasing col)
            for offset in range(4):
                start_r = lr + offset
                start_c = lc - offset
                if 3 <= start_r < ROWS and 0 <= start_c <= COLS - 4:
                    win_coords = [(start_r - i, start_c + i) for i in range(4)]
                    if _is_matching_window(win_coords):
                        return sorted(win_coords)

    # 2. Canonical board scan: Horizontal -> Vertical -> Diagonal \ -> Diagonal /
    # Horizontal
    for r in range(ROWS - 1, -1, -1):
        for c in range(COLS - 3):
            win_coords = [(r, c + i) for i in range(4)]
            if _is_matching_window(win_coords):
                return sorted(win_coords)

    # Vertical
    for c in range(COLS):
        for r in range(ROWS - 1, 2, -1):
            win_coords = [(r - i, c) for i in range(4)]
            if _is_matching_window(win_coords):
                return sorted(win_coords)

    # Diagonal \ (row increasing, col increasing)
    for r in range(ROWS - 3):
        for c in range(COLS - 3):
            win_coords = [(r + i, c + i) for i in range(4)]
            if _is_matching_window(win_coords):
                return sorted(win_coords)

    # Diagonal / (row decreasing, col increasing)
    for r in range(3, ROWS):
        for c in range(COLS - 3):
            win_coords = [(r - i, c + i) for i in range(4)]
            if _is_matching_window(win_coords):
                return sorted(win_coords)

    return None


def is_board_full(board: List[List[int]]) -> bool:
    """Return True if all 42 cells are filled (top row has no EMPTY cells)."""
    return all(board[0][c] != EMPTY for c in range(COLS))


def is_draw(board: List[List[int]]) -> bool:
    """
    Return True if the board is completely full and neither player has won.
    Strict win-over-draw precedence: if a 4-in-a-row exists, returns False.
    """
    if check_win(board, PLAYER_1) or check_win(board, PLAYER_2):
        return False
    return is_board_full(board)
