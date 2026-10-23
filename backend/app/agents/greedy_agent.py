"""
Greedy Agent implementation (PRD §6.3).
One-ply tactical lookahead agent with immediate win detection, threat blocking,
full legal opponent reply checking, blunder avoidance, and center-outward tie-breaking.
"""
import time
from typing import Any, Dict, List, Optional, Tuple

from app.agents.base_agent import BaseAgent
from app.core.game_engine import (
    ROWS,
    COLS,
    EMPTY,
    get_valid_locations,
    get_next_open_row,
    drop_piece,
    check_win,
)
from app.core.validation import validate_board_structure

CENTER_OUTWARD_ORDER: List[int] = [3, 2, 4, 1, 5, 0, 6]


def evaluate_window(window: List[int], piece: int, opp_piece: int) -> float:
    """Evaluate a single 4-cell window for positional strength."""
    score = 0.0
    piece_count = window.count(piece)
    empty_count = window.count(EMPTY)
    opp_count = window.count(opp_piece)

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
    """Compute heuristic static board evaluation for given player."""
    score = 0.0

    # Center column bonus
    center_array = [board[r][COLS // 2] for r in range(ROWS)]
    score += center_array.count(piece) * 3.0

    # Horizontal windows
    for r in range(ROWS):
        row_arr = board[r]
        for c in range(COLS - 3):
            score += evaluate_window(row_arr[c : c + 4], piece, opp_piece)

    # Vertical windows
    for c in range(COLS):
        col_arr = [board[r][c] for r in range(ROWS)]
        for r in range(ROWS - 3):
            score += evaluate_window(col_arr[r : r + 4], piece, opp_piece)

    # Diagonal (\: increasing row, increasing col)
    for r in range(ROWS - 3):
        for c in range(COLS - 3):
            win = [board[r + i][c + i] for i in range(4)]
            score += evaluate_window(win, piece, opp_piece)

    # Diagonal (/: decreasing row, increasing col)
    for r in range(3, ROWS):
        for c in range(COLS - 3):
            win = [board[r - i][c + i] for i in range(4)]
            score += evaluate_window(win, piece, opp_piece)

    return score


class GreedyAgent(BaseAgent):
    """
    Greedy heuristic agent evaluating 1-ply candidate moves with tactical reply checking (PRD §6.3).
    
    Decision Hierarchy:
    1. Immediate Winning Move: If any legal move wins the game immediately, select it (win strictly
       precedes blocking, regardless of opponent threats).
    2. Candidate Move Evaluation on Copied Boards:
       - Every legal candidate move is evaluated on a deep-copied board.
       - Evaluates whether candidate moves remove or defuse all opponent threats (leaving 0 winning replies).
       - Does not assume multiple opponent threats make a loss unavoidable: immediate wins and moves
         that defuse/block threats are evaluated first.
       - A move is deemed SAFE if the opponent has 0 winning replies on the subsequent turn.
    3. Selection Tiers:
       - Tier 1 (Safe Block): Blocks an opponent threat AND leaves 0 opponent winning replies.
       - Tier 2 (Safe Heuristic): Leaves 0 opponent winning replies; ranked by heuristic score.
       - Tier 3 (Split-Threat Block): When all moves leave at least one opponent reply, candidate moves
         that directly block an opponent threat are prioritized, minimizing remaining threats and
         tie-breaking via center-outward order [3, 2, 4, 1, 5, 0, 6].
       - Tier 4 (Forced Heuristic): Fallback when no move blocks or is safe.
    
    Guarantees strict board immutability and deterministic center-outward tie-breaking.
    """

    def __init__(self, name: str = "Greedy Agent", player_id: int = 2):
        super().__init__(name=name, player_id=player_id)

    def select_move(self, board: List[List[int]]) -> Tuple[Optional[int], Dict[str, Any]]:
        # Board immutability guarantee: operate strictly on copy
        b_copy = [r[:] for r in board]
        validate_board_structure(b_copy)

        start_time = time.perf_counter()
        valid_locations = get_valid_locations(b_copy)

        if not valid_locations:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return None, {
                "decision_time_ms": round(elapsed_ms, 3),
                "nodes_evaluated": None,
                "pruned_nodes": None,
                "search_depth": 1,
                "transposition_hits": None,
                "mcts_iterations": None,
                "mcts_simulations": None,
                "candidate_scores": [],
            }

        # -------------------------------------------------------------
        # Tactical Priority 1: Immediate Winning Move (Win First!)
        # -------------------------------------------------------------
        winning_candidates = []
        for col in valid_locations:
            b_sim = [r[:] for r in b_copy]
            r = get_next_open_row(b_sim, col)
            drop_piece(b_sim, r, col, self.player_id)
            if check_win(b_sim, self.player_id):
                winning_candidates.append(col)

        if winning_candidates:
            # Tie-break among immediate wins using center-outward preference
            winning_candidates.sort(key=lambda c: CENTER_OUTWARD_ORDER.index(c))
            chosen = winning_candidates[0]
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return chosen, {
                "decision_time_ms": round(elapsed_ms, 3),
                "nodes_evaluated": None,
                "pruned_nodes": None,
                "search_depth": 1,
                "transposition_hits": None,
                "mcts_iterations": None,
                "mcts_simulations": None,
                "candidate_scores": [
                    {"column": c, "score": 10000.0, "is_safe": True, "reason": "immediate_win"}
                    for c in winning_candidates
                ],
            }

        # -------------------------------------------------------------
        # Full Candidate Evaluation with Opponent Reply Checking
        # -------------------------------------------------------------
        candidate_evaluations = []

        for col in valid_locations:
            b_cand = [r[:] for r in b_copy]
            r_cand = get_next_open_row(b_cand, col)
            drop_piece(b_cand, r_cand, col, self.player_id)

            # Did playing in `col` block an immediate opponent threat on `b_copy`?
            b_test_block = [r[:] for r in b_copy]
            r_block = get_next_open_row(b_test_block, col)
            drop_piece(b_test_block, r_block, col, self.opp_id)
            is_direct_block = check_win(b_test_block, self.opp_id)

            # Evaluate all legal opponent replies on `b_cand`
            opp_replies = get_valid_locations(b_cand)
            winning_opp_replies = []

            for c_opp in opp_replies:
                b_opp = [r[:] for r in b_cand]
                r_opp = get_next_open_row(b_opp, c_opp)
                drop_piece(b_opp, r_opp, c_opp, self.opp_id)
                if check_win(b_opp, self.opp_id):
                    winning_opp_replies.append(c_opp)

            # A move is SAFE if it leaves 0 immediate winning replies for opponent
            is_safe = len(winning_opp_replies) == 0

            # Static heuristic position score
            h_score = score_position(b_cand, self.player_id, self.opp_id)

            candidate_evaluations.append({
                "column": col,
                "score": h_score,
                "is_safe": is_safe,
                "is_direct_block": is_direct_block,
                "opp_winning_replies_count": len(winning_opp_replies),
                "center_order": CENTER_OUTWARD_ORDER.index(col),
            })

        # -------------------------------------------------------------
        # Tactical Prioritization & Selection Tiers
        # -------------------------------------------------------------
        # Tier 1: Safe Block (blocks an opponent threat AND leaves 0 winning replies)
        tier_1 = [c for c in candidate_evaluations if c["is_direct_block"] and c["is_safe"]]
        # Tier 2: Safe Move (leaves 0 winning replies for opponent)
        tier_2 = [c for c in candidate_evaluations if c["is_safe"]]
        # Tier 3: Direct Block (blocks an opponent threat in a split-threat fork scenario)
        tier_3 = [c for c in candidate_evaluations if c["is_direct_block"]]
        # Tier 4: All legal candidate moves (fallback when no safe move exists)
        tier_4 = candidate_evaluations

        if tier_1:
            tier_1.sort(key=lambda c: (-c["score"], c["center_order"]))
            selected = tier_1[0]["column"]
            chosen_reason = "safe_block"
        elif tier_2:
            tier_2.sort(key=lambda c: (-c["score"], c["center_order"]))
            selected = tier_2[0]["column"]
            chosen_reason = "safe_heuristic"
        elif tier_3:
            # In unavoidable loss / fork: minimize remaining opponent threats, then center-outward order
            tier_3.sort(key=lambda c: (c["opp_winning_replies_count"], c["center_order"], -c["score"]))
            selected = tier_3[0]["column"]
            chosen_reason = "split_threat_block"
        else:
            # All legal moves allow an opponent win on reply
            tier_4.sort(key=lambda c: (c["opp_winning_replies_count"], -c["score"], c["center_order"]))
            selected = tier_4[0]["column"]
            chosen_reason = "forced_heuristic"

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        telemetry: Dict[str, Any] = {
            "decision_time_ms": round(elapsed_ms, 3),
            "nodes_evaluated": None,
            "pruned_nodes": None,
            "search_depth": 1,
            "transposition_hits": None,
            "mcts_iterations": None,
            "mcts_simulations": None,
            "candidate_scores": [
                {
                    "column": c["column"],
                    "score": round(c["score"], 2),
                    "is_safe": c["is_safe"],
                    "is_direct_block": c["is_direct_block"],
                }
                for c in candidate_evaluations
            ],
            "reason": chosen_reason,
        }

        return selected, telemetry
