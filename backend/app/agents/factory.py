"""
Agent factory module managing instantiation and validation of Connect Four agents (PRD §6.1).
Supports: 'random', 'greedy', 'minimax', 'alphabeta', 'optimized', 'mcts'.
"""
from typing import Any, Dict, List, Optional, Tuple, Set

from app.agents.base_agent import BaseAgent
from app.agents.random_agent import RandomAgent
from app.agents.greedy_agent import GreedyAgent
from app.agents.minimax_agent import MinimaxAgent
from app.agents.alphabeta_agent import AlphaBetaAgent
from app.agents.optimized_agent import OptimizedAlphaBetaAgent
from app.agents.mcts_agent import MCTSAgent
from app.core.validation import GameRuleException

SUPPORTED_AGENTS: Set[str] = {"random", "greedy", "minimax", "alphabeta", "optimized", "mcts"}


def get_agent(agent_id: str, **kwargs: Any) -> BaseAgent:
    """
    Factory function instantiating agent implementations by ID.

    Args:
        agent_id: Algorithm ID ('random', 'greedy', 'minimax', 'alphabeta', 'optimized', 'mcts').
        **kwargs: Optional parameters (seed, depth, iterations, use_tt, player_id).

    Returns:
        BaseAgent instance.

    Raises:
        GameRuleException with code 'INVALID_AGENT' if agent_id is unsupported.
    """
    if not isinstance(agent_id, str) or agent_id.lower() not in SUPPORTED_AGENTS:
        supported_str = ", ".join(f"'{a}'" for a in sorted(SUPPORTED_AGENTS))
        raise GameRuleException(
            code="INVALID_AGENT",
            message=f"Unknown agent '{agent_id}'. Supported: {supported_str}.",
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
    elif aid == "alphabeta":
        depth = kwargs.get("depth", 4)
        return AlphaBetaAgent(player_id=player_id, depth=depth)
    elif aid == "optimized":
        depth = kwargs.get("depth", 4)
        use_tt = kwargs.get("use_tt", True)
        return OptimizedAlphaBetaAgent(player_id=player_id, depth=depth, use_tt=use_tt)
    elif aid == "mcts":
        iterations = kwargs.get("iterations", 1000)
        seed = kwargs.get("seed")
        return MCTSAgent(player_id=player_id, iterations=iterations, seed=seed)

    raise GameRuleException(
        code="INVALID_AGENT",
        message=f"Unknown agent '{agent_id}'.",
        status_code=400,
    )
