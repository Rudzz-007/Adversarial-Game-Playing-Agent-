from fastapi import APIRouter
from app.schemas.agent_schemas import AgentListResponse, AgentMetadata

router = APIRouter(prefix="/api", tags=["Agents"])

AGENTS_CATALOG = [
    AgentMetadata(
        id="random",
        name="Random Agent",
        description="Chooses uniformly at random from all legal moves. Supports seeded pseudo-randomness for reproducibility.",
        type="baseline",
        supported_parameters={"seed": "optional int"},
        difficulty_levels=["easy"]
    ),
    AgentMetadata(
        id="greedy",
        name="Greedy Agent",
        description="One-ply heuristic agent that prioritizes immediate winning moves and blocks immediate opponent threats.",
        type="baseline",
        supported_parameters={},
        difficulty_levels=["medium"]
    ),
    AgentMetadata(
        id="minimax",
        name="Minimax Agent",
        description="Classical depth-limited adversarial game-tree search exploring all alternating maximizing and minimizing turns.",
        type="adversarial_search",
        supported_parameters={"depth": "int (1-6)"},
        difficulty_levels=["easy", "medium", "hard"]
    ),
    AgentMetadata(
        id="alphabeta",
        name="Alpha-Beta Pruning Agent",
        description="Depth-limited minimax with alpha-beta branch pruning, guaranteeing identical value to Minimax while exploring fewer nodes.",
        type="adversarial_search",
        supported_parameters={"depth": "int (1-7)"},
        difficulty_levels=["medium", "hard"]
    ),
    AgentMetadata(
        id="optimized",
        name="Optimized Alpha-Beta Agent",
        description="Enhanced Alpha-Beta search incorporating center-outward move ordering, transposition table caching, and immediate win cutoffs.",
        type="adversarial_search",
        supported_parameters={"depth": "int (1-8)"},
        difficulty_levels=["hard", "expert"]
    ),
    AgentMetadata(
        id="mcts",
        name="Monte Carlo Tree Search (UCT)",
        description="Simulation-based search algorithm with selection, expansion, random rollout simulation, and backpropagation using Upper Confidence Bound for Trees.",
        type="simulation",
        supported_parameters={"iterations": "int (100-5000)", "exploration_constant": "float (default ~1.414)"},
        difficulty_levels=["medium", "hard", "expert"]
    )
]

@router.get("/agents", response_model=AgentListResponse)
def get_agents():
    """Retrieve metadata for all supported AI agents as specified in PRD §12.6."""
    return AgentListResponse(agents=AGENTS_CATALOG)
