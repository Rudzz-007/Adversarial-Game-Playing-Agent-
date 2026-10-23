"""
MinimaxAgent implementing full depth-limited adversarial game-tree search (PRD §6.4).
Features accurate nodes_evaluated counting, deterministic tie-breaking, and strict board immutability.
"""
import math
import time
from typing import Any, Dict, List, Optional, Tuple

from app.agents.base_agent import BaseAgent
from app.core.game_engine import (
    COLS,
    check_win,
    drop_piece,
    get_next_open_row,
    get_valid_locations,
)
from app.core.evaluation import (
    WIN_SCORE,
    LOSS_SCORE,
    DRAW_SCORE,
    score_position,
)
from app.core.validation import validate_board_structure


class MinimaxAgent(BaseAgent):
    """
    Minimax adversarial search agent with depth-bounded exhaustive tree exploration.
    """

    def __init__(self, name: str = "Minimax Agent", player_id: int = 2, depth: int = 4):
        super().__init__(name=name, player_id=player_id)
        self.depth: int = depth
        self._nodes_evaluated: int = 0
        self.last_root_score: Optional[float] = None

    def _minimax(
        self, board: List[List[int]], depth: int, maximizing_player: bool
    ) -> Tuple[Optional[int], float]:
        """
        Recursive depth-limited minimax traversal without pruning.
        """
        self._nodes_evaluated += 1

        is_win = check_win(board, self.player_id)
        is_loss = check_win(board, self.opp_id)
        valid_locations = get_valid_locations(board)
        is_terminal = is_win or is_loss or (len(valid_locations) == 0)

        if depth == 0 or is_terminal:
            if is_win:
                return (None, WIN_SCORE)
            if is_loss:
                return (None, LOSS_SCORE)
            if is_terminal:
                return (None, DRAW_SCORE)
            return (None, score_position(board, self.player_id, self.opp_id))

        # Shared natural column order [0..6] filtered for legal columns
        candidate_cols = [c for c in range(COLS) if c in valid_locations]

        if maximizing_player:
            best_score = -math.inf
            best_col = candidate_cols[0]
            for col in candidate_cols:
                row = get_next_open_row(board, col)
                b_copy = [r[:] for r in board]
                drop_piece(b_copy, row, col, self.player_id)
                _, score = self._minimax(b_copy, depth - 1, False)
                if score > best_score:
                    best_score = score
                    best_col = col
            return (best_col, best_score)
        else:
            best_score = math.inf
            best_col = candidate_cols[0]
            for col in candidate_cols:
                row = get_next_open_row(board, col)
                b_copy = [r[:] for r in board]
                drop_piece(b_copy, row, col, self.opp_id)
                _, score = self._minimax(b_copy, depth - 1, True)
                if score < best_score:
                    best_score = score
                    best_col = col
            return (best_col, best_score)

    def select_move(self, board: List[List[int]]) -> Tuple[Optional[int], Dict[str, Any]]:
        """
        Evaluate board and select optimal column according to minimax value.
        Guarantees input board immutability.
        """
        b_copy = [r[:] for r in board]
        validate_board_structure(b_copy)

        valid_locations = get_valid_locations(b_copy)
        is_win = check_win(b_copy, self.player_id)
        is_loss = check_win(b_copy, self.opp_id)

        # Terminal or full root board
        if len(valid_locations) == 0 or is_win or is_loss:
            telemetry: Dict[str, Any] = {
                "decision_time_ms": 0.0,
                "nodes_evaluated": 0,
                "pruned_nodes": None,
                "search_depth": self.depth,
                "transposition_hits": None,
                "mcts_iterations": None,
                "mcts_simulations": None,
                "candidate_scores": None,
            }
            self.last_root_score = None
            return (None, telemetry)

        self._nodes_evaluated = 0
        start_time = time.perf_counter()

        best_col, root_score = self._minimax(b_copy, self.depth, True)
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        self.last_root_score = root_score

        telemetry = {
            "decision_time_ms": round(elapsed_ms, 3),
            "nodes_evaluated": self._nodes_evaluated,
            "pruned_nodes": None,
            "search_depth": self.depth,
            "transposition_hits": None,
            "mcts_iterations": None,
            "mcts_simulations": None,
            "candidate_scores": None,
        }
        return (best_col, telemetry)
