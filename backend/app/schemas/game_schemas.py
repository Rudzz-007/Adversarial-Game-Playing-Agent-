from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator

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
    agent: Optional[str] = Field("minimax", description="Selected AI algorithm ID ('minimax', 'random', 'greedy')")
    seed: Optional[int] = Field(None, description="Optional seed for random agent")

    @field_validator("seed", mode="before")
    @classmethod
    def validate_seed(cls, v):
        if v is not None:
            if isinstance(v, bool) or not isinstance(v, int):
                raise ValueError("Seed must be an integer, not boolean.")
        return v

class GameStateResponse(BaseModel):
    game_id: str = Field(..., description="Unique game session identifier")
    board: List[List[int]] = Field(..., description="6x7 board grid")
    current_player: int = Field(..., description="Active player (1 or 2)")
    status: str = Field(..., description="Game status: 'active', 'won', 'draw'")
    winner: Optional[int] = Field(None, description="Winner player ID if won, else None")
    legal_moves: List[int] = Field(default_factory=list, description="Available legal columns")
    winning_coords: Optional[List[List[int]]] = Field(None, description="Winning 4-cell coordinates")
    move_count: int = Field(0, description="Total moves executed")
    last_move: Optional[Dict[str, Any]] = Field(None, description="Last executed move details")

class MoveResponse(BaseModel):
    board: List[List[int]] = Field(..., description="Updated 6x7 board")
    current_player: int = Field(..., description="Player who moves next")
    status: str = Field(..., description="Game status after move")
    winner: Optional[int] = Field(None, description="Winner player ID if won")
    last_move: Dict[str, Any] = Field(..., description="Details of the applied move")
    winning_coords: Optional[List[List[int]]] = Field(None, description="Winning 4-cell coordinates if won")
