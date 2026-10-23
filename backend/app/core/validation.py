"""
Validation logic and domain exception definitions for Connect Four rules.
Prevents low-level exceptions (IndexError, TypeError, ValueError) from leaking.
"""
from typing import Any, List
from app.core.game_engine import ROWS, COLS, EMPTY, PLAYER_1, PLAYER_2, is_valid_location


class GameRuleException(Exception):
    """Base exception for all Connect Four domain and rule violations."""

    def __init__(self, code: str, message: str, status_code: int = 400):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


class InvalidMoveException(GameRuleException):
    """Raised when a move specifies an invalid column index or non-integer type."""

    def __init__(self, code: str = "INVALID_MOVE", message: str = "Invalid move."):
        super().__init__(code=code, message=message, status_code=400)


class ColumnFullException(GameRuleException):
    """Raised when an attempt is made to drop a piece into a full column."""

    def __init__(self, code: str = "INVALID_MOVE", message: str = "The selected column is full."):
        super().__init__(code=code, message=message, status_code=400)


class GameTerminalException(GameRuleException):
    """Raised when an action is attempted on a game that has already concluded."""

    def __init__(self, code: str = "GAME_TERMINAL", message: str = "Cannot make a move in a terminal game state."):
        super().__init__(code=code, message=message, status_code=400)


class InvalidBoardException(GameRuleException):
    """Raised when an external board payload is malformed or invalid."""

    def __init__(self, code: str = "VALIDATION_ERROR", message: str = "Malformed board matrix."):
        super().__init__(code=code, message=message, status_code=422)


def validate_column_type_and_range(col: Any) -> int:
    """
    Validate that column input is strictly an integer (rejecting booleans)
    and falls within the legal grid boundaries 0 to 6.
    """
    if isinstance(col, bool) or not isinstance(col, int):
        raise InvalidMoveException(
            code="INVALID_MOVE",
            message="Column must be an integer, not boolean.",
        )
    if col < 0 or col >= COLS:
        raise InvalidMoveException(
            code="INVALID_MOVE",
            message=f"Column index {col} out of bounds (0-{COLS - 1}).",
        )
    return col


def validate_move_legality(board: List[List[int]], col: int, status: str) -> None:
    """
    Validate that the game is active and that the target column has capacity.
    """
    if status != "active":
        raise GameTerminalException(
            code="GAME_TERMINAL",
            message="Cannot make a move in a terminal game state.",
        )
    if not is_valid_location(board, col):
        raise ColumnFullException(
            code="INVALID_MOVE",
            message=f"The selected column {col} is full.",
        )


def validate_board_structure(board: Any) -> None:
    """
    Validate that the provided board is a strictly formatted 6x7 integer matrix
    containing only valid cell values (0: empty, 1: player 1, 2: player 2).
    """
    if not isinstance(board, list) or len(board) != ROWS:
        raise InvalidBoardException(
            code="VALIDATION_ERROR",
            message=f"Board must be a list containing exactly {ROWS} rows.",
        )
    for r_idx, row in enumerate(board):
        if not isinstance(row, list) or len(row) != COLS:
            raise InvalidBoardException(
                code="VALIDATION_ERROR",
                message=f"Row {r_idx} must be a list containing exactly {COLS} columns.",
            )
        for c_idx, cell in enumerate(row):
            if isinstance(cell, bool) or not isinstance(cell, int) or cell not in (EMPTY, PLAYER_1, PLAYER_2):
                raise InvalidBoardException(
                    code="VALIDATION_ERROR",
                    message=f"Cell ({r_idx}, {c_idx}) contains invalid value {cell}. Allowed: 0, 1, 2.",
                )
