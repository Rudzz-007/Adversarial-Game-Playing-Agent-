from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class AgentMetadata(BaseModel):
    id: str = Field(..., description="Unique agent identifier (e.g., 'random', 'alphabeta')")
    name: str = Field(..., description="Display name of the agent")
    description: str = Field(..., description="Algorithmic description and characteristics")
    type: str = Field(..., description="Type/category: 'baseline', 'adversarial_search', 'simulation'")
    supported_parameters: Dict[str, Any] = Field(default_factory=dict, description="Configurable hyperparameters")
    difficulty_levels: List[str] = Field(default_factory=list, description="Supported difficulty tiers")

class AgentListResponse(BaseModel):
    agents: List[AgentMetadata]
