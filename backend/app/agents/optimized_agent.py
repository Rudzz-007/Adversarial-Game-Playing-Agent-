"""
OptimizedAlphaBetaAgent implementing enhanced Alpha-Beta search (PRD §6.5).
Features:
- Center-outward move ordering [3, 2, 4, 1, 5, 0, 6]
- Transposition table caching with typed bound safety (EXACT, LOWER, UPPER)
- 1-ply immediate-win cutoffs
- Accurate nodes_evaluated, pruned_nodes, and transposition_hits telemetry
"""
import math
import time
from dataclasses import dataclass
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

CENTER_ORDER: List[int] = [3, 2, 4, 1, 5, 0, 6]


@dataclass
class TTEntry:
    searched_depth: int
    score: float
    bound_type: str  # "EXACT", "LOWER", "UPPER"
    best_move: Optional[int]


class OptimizedAlphaBetaAgent(BaseAgent):
    """
    Optimized Alpha-Beta adversarial search agent with center-outward ordering,
    typed transposition-table caching, and immediate-win cutoffs.
    """

    def __init__(
        self,
        name: str = "Optimized Alpha-Beta Agent",
        player_id: int = 2,
        depth: int = 4,
        use_tt: bool = True,
    ):
        super().__init__(name=name, player_id=player_id)
        self.depth: int = depth
        self.use_tt: bool = use_tt
        self._nodes_evaluated: int = 0
        self._pruned_nodes: int = 0
        self._transposition_hits: int = 0
        self.last_root_score: Optional[float] = None
        self._tt: Dict[Tuple[Any, ...], TTEntry] = {}

    def clear_cache(self) -> None:
        """Reset the transposition table cache."""
        self._tt.clear()

    def _get_ordered_moves(
        self, valid_locations: List[int], tt_best_move: Optional[int]
    ) -> List[int]:
        """
        Order moves prioritizing transposition-table best move followed by center-outward order.
        """
        valid_set = set(valid_locations)
        ordered: List[int] = []

        if tt_best_move is not None and tt_best_move in valid_set:
            ordered.append(tt_best_move)

        for col in CENTER_ORDER:
            if col in valid_set and col not in ordered:
                ordered.append(col)

        return ordered

    def _alphabeta(
        self,
        board: List[List[int]],
        depth: int,
        alpha: float,
        beta: float,
        maximizing_player: bool,
    ) -> Tuple[Optional[int], float]:
        """
        Recursive alpha-beta search with typed transposition table bounds and move ordering.
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

        active_player = self.player_id if maximizing_player else self.opp_id
        alpha_orig = alpha
        beta_orig = beta
        tt_best_move: Optional[int] = None

        board_key = (tuple(tuple(r) for r in board), active_player)

        # Transposition table probe
        if self.use_tt and board_key in self._tt:
            entry = self._tt[board_key]
            tt_best_move = entry.best_move

            if entry.searched_depth >= depth:
                if entry.bound_type == "EXACT":
                    self._transposition_hits += 1
                    return (entry.best_move, entry.score)
                elif entry.bound_type == "LOWER":
                    alpha = max(alpha, entry.score)
                elif entry.bound_type == "UPPER":
                    beta = min(beta, entry.score)

                if alpha >= beta:
                    self._transposition_hits += 1
                    return (entry.best_move, entry.score)

        candidate_cols = self._get_ordered_moves(valid_locations, tt_best_move)

        # 1-ply immediate-win cutoff check
        for col in candidate_cols:
            row = get_next_open_row(board, col)
            b_copy = [r[:] for r in board]
            drop_piece(b_copy, row, col, active_player)
            if check_win(b_copy, active_player):
                win_val = WIN_SCORE if maximizing_player else LOSS_SCORE
                if self.use_tt:
                    self._tt[board_key] = TTEntry(
                        searched_depth=depth,
                        score=win_val,
                        bound_type="EXACT",
                        best_move=col,
                    )
                return (col, win_val)

        best_col = candidate_cols[0]

        if maximizing_player:
            best_score = -math.inf
            for col in candidate_cols:
                row = get_next_open_row(board, col)
                b_copy = [r[:] for r in board]
                drop_piece(b_copy, row, col, self.player_id)
                _, score = self._alphabeta(b_copy, depth - 1, alpha, beta, False)
                if score > best_score:
                    best_score = score
                    best_col = col
                alpha = max(alpha, best_score)
                if alpha >= beta:
                    self._pruned_nodes += 1
                    break
        else:
            best_score = math.inf
            for col in candidate_cols:
                row = get_next_open_row(board, col)
                b_copy = [r[:] for r in board]
                drop_piece(b_copy, row, col, self.opp_id)
                _, score = self._alphabeta(b_copy, depth - 1, alpha, beta, True)
                if score < best_score:
                    best_score = score
                    best_col = col
                beta = min(beta, best_score)
                if alpha >= beta:
                    self._pruned_nodes += 1
                    break

        # Transposition table record with typed bounds
        if self.use_tt:
            if best_score <= alpha_orig:
                bound = "UPPER"
            elif best_score >= beta_orig:
                bound = "LOWER"
            else:
                bound = "EXACT"

            self._tt[board_key] = TTEntry(
                searched_depth=depth,
                score=best_score,
                bound_type=bound,
                best_move=best_col,
            )

        return (best_col, best_score)

    def select_move(self, board: List[List[int]]) -> Tuple[Optional[int], Dict[str, Any]]:
        """
        Evaluate board and select optimal column using optimized alpha-beta search.
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
                "pruned_nodes": 0,
                "search_depth": self.depth,
                "transposition_hits": 0,
                "mcts_iterations": None,
                "mcts_simulations": None,
                "candidate_scores": None,
            }
            self.last_root_score = None
            return (None, telemetry)

        self._nodes_evaluated = 0
        self._pruned_nodes = 0
        self._transposition_hits = 0
        start_time = time.perf_counter()

        best_col, root_score = self._alphabeta(b_copy, self.depth, -math.inf, math.inf, True)
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        self.last_root_score = root_score

        telemetry = {
            "decision_time_ms": round(elapsed_ms, 3),
            "nodes_evaluated": self._nodes_evaluated,
            "pruned_nodes": self._pruned_nodes,
            "search_depth": self.depth,
            "transposition_hits": self._transposition_hits,
            "mcts_iterations": None,
            "mcts_simulations": None,
            "candidate_scores": None,
        }
        return (best_col, telemetry)
