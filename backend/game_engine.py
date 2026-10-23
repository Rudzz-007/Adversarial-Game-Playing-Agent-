"""
Compatibility bridge for root game_engine module.
Delegates all Connect Four operations directly to app.core.game_engine
to preserve a single source of truth without code duplication.
"""
from app.core.game_engine import (
    ROWS,
    COLS,
    EMPTY,
    PLAYER_1,
    PLAYER_2,
    PLAYER,
    AI,
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

__all__ = [
    "ROWS",
    "COLS",
    "EMPTY",
    "PLAYER_1",
    "PLAYER_2",
    "PLAYER",
    "AI",
    "create_board",
    "is_valid_location",
    "get_valid_locations",
    "get_next_open_row",
    "drop_piece",
    "check_win",
    "get_winning_coordinates",
    "is_board_full",
    "is_draw",
]