"""
BaseAgent abstract interface for all Connect Four AI algorithms (PRD §6.1).
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple


class BaseAgent(ABC):
    """
    Abstract base class for all Connect Four adversarial agents.
    Agents are stateless with respect to game sessions; board is supplied to select_move().
    All hypothetical evaluations must guarantee board immutability.
    """

    def __init__(self, name: str, player_id: int = 2):
        self.name: str = name
        self.player_id: int = player_id
        self.opp_id: int = 1 if player_id == 2 else 2

    @abstractmethod
    def select_move(self, board: List[List[int]]) -> Tuple[Optional[int], Dict[str, Any]]:
        """
        Evaluate current board state and select best legal column.

        Args:
            board: 6x7 integer matrix (0: empty, 1: player 1, 2: player 2).

        Returns:
            Tuple of:
            - selected_column: Integer in [0..6], or None if no legal moves exist.
            - telemetry: Dictionary conforming to TelemetryMetrics schema.
        """
        pass
