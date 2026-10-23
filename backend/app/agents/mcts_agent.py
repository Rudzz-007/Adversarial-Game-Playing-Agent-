"""
MCTSAgent implementing Monte Carlo Tree Search with Upper Confidence Bound for Trees (PRD §6.6).
Features:
- 4-step cycle: Selection, Expansion, Rollout Simulation, Backpropagation
- Symmetric node-to-move reward perspective across alternating player plies
- Robust visit-count root move selection
- Isolated pseudo-random seed generator for reproducible simulations
- Strict board immutability and PRD §13.3 compliant telemetry
"""
import math
import random
import time
from typing import Any, Dict, List, Optional, Tuple

from app.agents.base_agent import BaseAgent
from app.core.game_engine import (
    check_win,
    drop_piece,
    get_next_open_row,
    get_valid_locations,
)
from app.core.validation import validate_board_structure


class MCTSNode:
    """
    Node within the Monte Carlo Search Tree.
    Tracks statistics strictly from the perspective of player_just_moved.
    """

    def __init__(
        self,
        board: List[List[int]],
        player_just_moved: int,
        parent: Optional["MCTSNode"] = None,
        move: Optional[int] = None,
    ):
        self.board: List[List[int]] = [r[:] for r in board]
        self.player_just_moved: int = player_just_moved
        self.parent: Optional["MCTSNode"] = parent
        self.move: Optional[int] = move

        self.children: Dict[int, "MCTSNode"] = {}
        self.visits: int = 0
        self.wins: float = 0.0

        valid_locs = get_valid_locations(self.board)
        # Untried moves from this state
        self.untried_moves: List[int] = valid_locs[:]

    @property
    def is_fully_expanded(self) -> bool:
        return len(self.untried_moves) == 0

    @property
    def is_terminal_node(self) -> bool:
        return (
            check_win(self.board, 1)
            or check_win(self.board, 2)
            or len(get_valid_locations(self.board)) == 0
        )

    def select_child(self, exploration_constant: float) -> "MCTSNode":
        """
        Select child node with highest UCT value.
        Each child c represents a move chosen by the player whose turn it was at self.
        c.wins / c.visits is strictly from that player's perspective.
        """
        best_uct = -math.inf
        best_child: Optional["MCTSNode"] = None

        log_parent_visits = math.log(self.visits)

        for child in self.children.values():
            exploitation = child.wins / child.visits
            exploration = exploration_constant * math.sqrt(log_parent_visits / child.visits)
            uct_val = exploitation + exploration

            if uct_val > best_uct:
                best_uct = uct_val
                best_child = child

        assert best_child is not None
        return best_child

    def add_child(self, move: int, player_id: int) -> "MCTSNode":
        """
        Expand an untried move by applying it to a copied board and adding child node.
        """
        row = get_next_open_row(self.board, move)
        child_board = [r[:] for r in self.board]
        drop_piece(child_board, row, move, player_id)

        child = MCTSNode(
            board=child_board,
            player_just_moved=player_id,
            parent=self,
            move=move,
        )
        self.untried_moves.remove(move)
        self.children[move] = child
        return child

    def backpropagate(self, winner: Optional[int]) -> None:
        """
        Propagate simulation outcome up to root.
        Reward is +1.0 for win, +0.5 for draw, 0.0 for loss, relative to player_just_moved.
        """
        curr: Optional["MCTSNode"] = self
        while curr is not None:
            curr.visits += 1
            if winner is None:
                curr.wins += 0.5
            elif winner == curr.player_just_moved:
                curr.wins += 1.0
            # else loss: +0.0
            curr = curr.parent


class MCTSAgent(BaseAgent):
    """
    Monte Carlo Tree Search agent using Upper Confidence Bound for Trees (UCT).
    """

    def __init__(
        self,
        name: str = "Monte Carlo Tree Search (UCT)",
        player_id: int = 2,
        iterations: int = 1000,
        exploration_constant: float = math.sqrt(2.0),
        seed: Optional[int] = None,
    ):
        super().__init__(name=name, player_id=player_id)
        if isinstance(seed, bool):
            raise ValueError("Seed must be an integer, not boolean.")

        self.iterations: int = iterations
        self.exploration_constant: float = exploration_constant
        self.seed: Optional[int] = seed
        self.rng: random.Random = random.Random(seed)

    def _rollout(self, board: List[List[int]], current_turn: int) -> Optional[int]:
        """
        Simulate a random rollout to a terminal state on a copied board.
        Returns winning player ID (1 or 2) or None for draw.
        """
        sim_board = [r[:] for r in board]
        turn = current_turn

        while True:
            valid_locs = get_valid_locations(sim_board)
            if not valid_locs:
                return None  # Draw

            col = self.rng.choice(valid_locs)
            row = get_next_open_row(sim_board, col)
            drop_piece(sim_board, row, col, turn)

            if check_win(sim_board, turn):
                return turn

            turn = 1 if turn == 2 else 2

    def select_move(self, board: List[List[int]]) -> Tuple[Optional[int], Dict[str, Any]]:
        """
        Execute MCTS iterations from current board state and select move with max visits.
        Guarantees input board immutability.
        """
        b_copy = [r[:] for r in board]
        validate_board_structure(b_copy)

        valid_locations = get_valid_locations(b_copy)
        is_win = check_win(b_copy, self.player_id)
        is_loss = check_win(b_copy, self.opp_id)

        # Terminal root or full board: 0 iterations, 0 simulations
        if len(valid_locations) == 0 or is_win or is_loss:
            telemetry: Dict[str, Any] = {
                "decision_time_ms": 0.0,
                "nodes_evaluated": None,
                "pruned_nodes": None,
                "search_depth": None,
                "transposition_hits": None,
                "mcts_iterations": 0,
                "mcts_simulations": 0,
                "candidate_scores": None,
            }
            return (None, telemetry)

        # Single legal move: early return with valid move
        if len(valid_locations) == 1:
            telemetry = {
                "decision_time_ms": 0.0,
                "nodes_evaluated": None,
                "pruned_nodes": None,
                "search_depth": None,
                "transposition_hits": None,
                "mcts_iterations": 0,
                "mcts_simulations": 0,
                "candidate_scores": [
                    {"column": valid_locations[0], "visits": 0, "win_rate": 0.0}
                ],
            }
            return (valid_locations[0], telemetry)

        start_time = time.perf_counter()

        # Root node: player_just_moved was opponent, next mover is self.player_id
        root = MCTSNode(board=b_copy, player_just_moved=self.opp_id)

        completed_iterations = 0
        completed_simulations = 0

        for _ in range(self.iterations):
            node = root

            # 1. Selection
            while node.is_fully_expanded and not node.is_terminal_node:
                node = node.select_child(self.exploration_constant)

            # 2. Expansion
            if not node.is_terminal_node and not node.is_fully_expanded:
                next_player = 1 if node.player_just_moved == 2 else 2
                move = self.rng.choice(node.untried_moves)
                node = node.add_child(move, next_player)

            # 3. Simulation
            if node.is_terminal_node:
                # Immediate terminal expansion
                if check_win(node.board, 1):
                    winner: Optional[int] = 1
                elif check_win(node.board, 2):
                    winner = 2
                else:
                    winner = None
            else:
                next_sim_player = 1 if node.player_just_moved == 2 else 2
                winner = self._rollout(node.board, next_sim_player)

            completed_simulations += 1

            # 4. Backpropagation
            node.backpropagate(winner)
            completed_iterations += 1

        # Move selection at root: highest visit count
        best_col = None
        max_visits = -1
        candidate_scores: List[Dict[str, Any]] = []

        # Sort candidate moves deterministically by column index
        for col in sorted(root.children.keys()):
            child = root.children[col]
            win_rate = child.wins / child.visits if child.visits > 0 else 0.0
            candidate_scores.append(
                {
                    "column": col,
                    "visits": child.visits,
                    "win_rate": round(win_rate, 4),
                }
            )
            if child.visits > max_visits:
                max_visits = child.visits
                best_col = col

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        telemetry = {
            "decision_time_ms": round(elapsed_ms, 3),
            "nodes_evaluated": None,
            "pruned_nodes": None,
            "search_depth": None,
            "transposition_hits": None,
            "mcts_iterations": completed_iterations,
            "mcts_simulations": completed_simulations,
            "candidate_scores": candidate_scores,
        }

        return (best_col, telemetry)
