"""
Evaluation module providing consistent heuristic evaluation and terminal scoring for Connect Four game-tree search agents (PRD §6.4-6.5).
"""
from typing import List
from app.core.game_engine import ROWS, COLS, EMPTY

WIN_SCORE: float = 10_000_000.0
LOSS_SCORE: float = -10_000_000.0
DRAW_SCORE: float = 0.0


def evaluate_window(window: List[int], piece: int, opp_piece: int) -> float:
    """
    Evaluate a 4-cell window heuristic value from the perspective of `piece`.

    Weights conforming to approved GSD specification:
    - 4 of piece: +100.0
    - 3 of piece + 1 empty: +5.0
    - 2 of piece + 2 empty: +2.0
    - 3 of opp_piece + 1 empty: -4.0
    - 2 of opp_piece + 2 empty: -1.0
    """
    score: float = 0.0
    piece_count = window.count(piece)
    opp_count = window.count(opp_piece)
    empty_count = window.count(EMPTY)

    if piece_count == 4:
        score += 100.0
    elif piece_count == 3 and empty_count == 1:
        score += 5.0
    elif piece_count == 2 and empty_count == 2:
        score += 2.0

    if opp_count == 3 and empty_count == 1:
        score -= 4.0
    elif opp_count == 2 and empty_count == 2:
        score -= 1.0

    return score


def score_position(board: List[List[int]], piece: int, opp_piece: int) -> float:
    """
    Score the complete board position from the perspective of `piece`.

    - Center column preference: pieces in column 3 receive +3.0 each.
    - All 4-cell horizontal, vertical, and diagonal windows are evaluated.
    """
    score: float = 0.0

    # 1. Center column preference
    center_col = COLS // 2  # col 3
    center_pieces = sum(1 for r in range(ROWS) if board[r][center_col] == piece)
    score += center_pieces * 3.0

    # 2. Horizontal windows
    for r in range(ROWS):
        row_arr = board[r]
        for c in range(COLS - 3):
            score += evaluate_window(row_arr[c:c + 4], piece, opp_piece)

    # 3. Vertical windows
    for c in range(COLS):
        col_arr = [board[r][c] for r in range(ROWS)]
        for r in range(ROWS - 3):
            score += evaluate_window(col_arr[r:r + 4], piece, opp_piece)

    # 4. Positive diagonals (bottom-left to top-right /)
    for r in range(ROWS - 3):
        for c in range(COLS - 3):
            window = [board[r + i][c + i] for i in range(4)]
            score += evaluate_window(window, piece, opp_piece)

    # 5. Negative diagonals (top-left to bottom-right \)
    for r in range(3, ROWS):
        for c in range(COLS - 3):
            window = [board[r - i][c + i] for i in range(4)]
            score += evaluate_window(window, piece, opp_piece)

    return score
