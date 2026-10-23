"""
Random Agent baseline implementation (PRD §6.2).
Selects uniformly at random from legal columns with optional isolated pseudo-random seeding.
"""
import random
import time
from typing import Any, Dict, List, Optional, Tuple

from app.agents.base_agent import BaseAgent
from app.core.game_engine import get_valid_locations
from app.core.validation import validate_board_structure


class RandomAgent(BaseAgent):
    """
    Uniform random baseline agent.
    Guarantees board immutability and isolated RNG state for reproducible benchmarking.
    """

    def __init__(
        self,
        name: str = "Random Agent",
        player_id: int = 2,
        seed: Optional[int] = None,
    ):
        super().__init__(name=name, player_id=player_id)
        if isinstance(seed, bool) or (seed is not None and not isinstance(seed, int)):
            raise ValueError("Seed must be an integer, not boolean.")
        self.seed = seed
        self.rng = random.Random(seed)

    def select_move(self, board: List[List[int]]) -> Tuple[Optional[int], Dict[str, Any]]:
        # Board immutability guarantee: operate on deep copy
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
                "search_depth": None,
                "transposition_hits": None,
                "mcts_iterations": None,
                "mcts_simulations": None,
                "candidate_scores": None,
            }

        selected_column = self.rng.choice(valid_locations)
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        telemetry: Dict[str, Any] = {
            "decision_time_ms": round(elapsed_ms, 3),
            "nodes_evaluated": None,
            "pruned_nodes": None,
            "search_depth": None,
            "transposition_hits": None,
            "mcts_iterations": None,
            "mcts_simulations": None,
            "candidate_scores": None,
        }

        return selected_column, telemetry
