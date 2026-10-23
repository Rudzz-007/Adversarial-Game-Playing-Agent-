from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class TelemetryMetrics(BaseModel):
    decision_time_ms: float = Field(..., description="Decision computation time in milliseconds")
    nodes_evaluated: Optional[int] = Field(None, description="Search-tree nodes evaluated (Minimax/AB); null if not applicable")
    pruned_nodes: Optional[int] = Field(None, description="Branches pruned (Alpha-Beta); null if not applicable")
    search_depth: Optional[int] = Field(None, description="Explored ply horizon; null if not applicable")
    transposition_hits: Optional[int] = Field(None, description="Transposition table cache hits; null if not applicable")
    mcts_iterations: Optional[int] = Field(None, description="MCTS iteration count; null if not applicable")
    mcts_simulations: Optional[int] = Field(None, description="MCTS rollout count; null if not applicable")
    candidate_scores: Optional[List[Dict[str, Any]]] = Field(None, description="Move evaluation candidate breakdown; null if not applicable")

class GameCreateRequest(BaseModel):
    mode: str = Field("human_vs_ai", description="Game mode: 'human_vs_ai', 'human_vs_human', 'ai_vs_ai'")
    ai_agent: str = Field("alphabeta", description="Selected AI algorithm ID")
    difficulty: str = Field("medium", description="Difficulty level: 'easy', 'medium', 'hard', 'expert'")
    starting_player: int = Field(1, description="Player who moves first: 1 or 2")

class MoveRequest(BaseModel):
    column: Optional[int] = Field(None, description="Selected column index (0-6)")
    # Backward compatibility with existing prototype:
    board: Optional[List[List[int]]] = Field(None, description="Existing prototype board state")
    depth: Optional[int] = Field(4, description="Search depth for legacy endpoint")
