"""
Authoritative GameState domain model for Connect Four.
Encapsulates board state, turn rotation, move history, and terminal state invariants.
"""
import copy
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
import uuid

from app.core.game_engine import (
    ROWS,
    COLS,
    EMPTY,
    PLAYER_1,
    PLAYER_2,
    create_board,
    get_valid_locations,
    get_next_open_row,
    drop_piece,
    get_winning_coordinates,
    is_draw,
)
from app.core.validation import (
    validate_column_type_and_range,
    validate_move_legality,
)


class GameState:
    """Encapsulates the complete authoritative state of an active or concluded game."""

    def __init__(
        self,
        game_id: Optional[str] = None,
        board: Optional[List[List[int]]] = None,
        current_player: int = PLAYER_1,
        status: str = "active",
        winner: Optional[int] = None,
        winning_coords: Optional[List[Tuple[int, int]]] = None,
        move_history: Optional[List[Dict[str, Any]]] = None,
    ):
        self.game_id: str = game_id or str(uuid.uuid4())
        self.board: List[List[int]] = [r[:] for r in board] if board is not None else create_board()
        self.current_player: int = current_player
        self.status: str = status  # "active", "won", "draw"
        self.winner: Optional[int] = winner
        self.winning_coords: Optional[List[Tuple[int, int]]] = winning_coords
        self.move_history: List[Dict[str, Any]] = [dict(m) for m in move_history] if move_history is not None else []
        self.move_count: int = len(self.move_history)

    def apply_move(self, col: Any) -> Dict[str, Any]:
        """
        Apply a player move into column `col`.
        Enforces validation, gravity drop, win/draw detection (win takes precedence),
        and turn alternation invariants.

        Raises:
            InvalidMoveException: if col is non-integer or out of bounds.
            ColumnFullException: if col is full.
            GameTerminalException: if game is already concluded.
        """
        # 1. Validate column type and bounds
        valid_col = validate_column_type_and_range(col)

        # 2. Validate move legality (active state, column capacity)
        validate_move_legality(self.board, valid_col, self.status)

        # 3. Drop piece into open row
        row = get_next_open_row(self.board, valid_col)
        drop_piece(self.board, row, valid_col, self.current_player)

        # 4. Record move in history
        self.move_count += 1
        move_record = {
            "move_number": self.move_count,
            "player": self.current_player,
            "column": valid_col,
            "row": row,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self.move_history.append(move_record)

        # 5. Evaluate game termination (win strictly precedes draw)
        win_coords = get_winning_coordinates(self.board, self.current_player, last_move=(row, valid_col))
        if win_coords is not None:
            self.status = "won"
            self.winner = self.current_player
            self.winning_coords = win_coords
        elif is_draw(self.board):
            self.status = "draw"
            self.winner = None
            self.winning_coords = None
        else:
            # Alternate turn only when game remains active
            self.current_player = PLAYER_2 if self.current_player == PLAYER_1 else PLAYER_1

        return move_record

    def get_legal_moves(self) -> List[int]:
        """Return list of legal column indices. Returns empty list if game is terminal."""
        if self.status != "active":
            return []
        return get_valid_locations(self.board)

    def is_terminal(self) -> bool:
        """Return True if game has concluded with a win or draw."""
        return self.status != "active"

    def clone(self) -> "GameState":
        """Produce an isolated deep-copy of this GameState."""
        return GameState(
            game_id=self.game_id,
            board=[r[:] for r in self.board],
            current_player=self.current_player,
            status=self.status,
            winner=self.winner,
            winning_coords=[tuple(c) for c in self.winning_coords] if self.winning_coords else None,
            move_history=[dict(m) for m in self.move_history],
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serialize state matching PRD §12 JSON specifications."""
        return {
            "game_id": self.game_id,
            "board": [r[:] for r in self.board],
            "current_player": self.current_player,
            "status": self.status,
            "winner": self.winner,
            "legal_moves": self.get_legal_moves(),
            "winning_coords": [list(c) for c in self.winning_coords] if self.winning_coords else None,
            "move_count": self.move_count,
            "last_move": self.move_history[-1] if self.move_history else None,
        }
