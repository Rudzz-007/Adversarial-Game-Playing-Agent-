"""
Agent factory module managing instantiation and validation of Connect Four agents (PRD §6.1).
"""
import math
import time
from typing import Any, Dict, List, Optional, Tuple

from app.agents.base_agent import BaseAgent
from app.agents.random_agent import RandomAgent
from app.agents.greedy_agent import GreedyAgent
from app.core.validation import GameRuleException, validate_board_structure
from ai_agent import minimax

SUPPORTED_AGENTS = {"random", "greedy", "minimax"}


class MinimaxAgent(BaseAgent):
    """
    Minimax adapter wrapping legacy minimax for unified BaseAgent interface.
    """

    def __init__(self, name: str = "Minimax Agent", player_id: int = 2, depth: int = 4):
        super().__init__(name=name, player_id=player_id)
        self.depth = depth

    def select_move(self, board: List[List[int]]) -> Tuple[Optional[int], Dict[str, Any]]:
        b_copy = [r[:] for r in board]
        validate_board_structure(b_copy)

        start_time = time.perf_counter()
        col, _ = minimax(b_copy, self.depth, -math.inf, math.inf, True)
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        telemetry: Dict[str, Any] = {
            "decision_time_ms": round(elapsed_ms, 3),
            "nodes_evaluated": None,
            "pruned_nodes": None,
            "search_depth": self.depth,
            "transposition_hits": None,
            "mcts_iterations": None,
            "mcts_simulations": None,
            "candidate_scores": None,
        }
        return col, telemetry


def get_agent(agent_id: str, **kwargs: Any) -> BaseAgent:
    """
    Factory function instantiating agent implementations by ID.

    Args:
        agent_id: Algorithm ID ('random', 'greedy', 'minimax').
        **kwargs: Optional parameters (seed, depth, player_id).

    Returns:
        BaseAgent instance.

    Raises:
        GameRuleException with code 'INVALID_AGENT' if agent_id is unsupported.
    """
    if not isinstance(agent_id, str) or agent_id.lower() not in SUPPORTED_AGENTS:
        raise GameRuleException(
            code="INVALID_AGENT",
            message=f"Unknown agent '{agent_id}'. Supported: 'random', 'greedy', 'minimax'.",
            status_code=400,
        )

    aid = agent_id.lower()
    player_id = kwargs.get("player_id", 2)

    if aid == "random":
        seed = kwargs.get("seed")
        return RandomAgent(player_id=player_id, seed=seed)
    elif aid == "greedy":
        return GreedyAgent(player_id=player_id)
    elif aid == "minimax":
        depth = kwargs.get("depth", 4)
        return MinimaxAgent(player_id=player_id, depth=depth)

    raise GameRuleException(
        code="INVALID_AGENT",
        message=f"Unknown agent '{agent_id}'. Supported: 'random', 'greedy', 'minimax'.",
        status_code=400,
    )
