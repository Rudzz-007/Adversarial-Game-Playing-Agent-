"""
Pydantic schemas for requests, responses, telemetry, and standardized errors.
"""
from app.schemas.error_schemas import ErrorDetail, ErrorResponse
from app.schemas.agent_schemas import AgentMetadata, AgentListResponse
from app.schemas.game_schemas import (
    TelemetryMetrics,
    GameCreateRequest,
    MoveRequest,
    GameStateResponse,
    MoveResponse,
)

__all__ = [
    "ErrorDetail",
    "ErrorResponse",
    "AgentMetadata",
    "AgentListResponse",
    "TelemetryMetrics",
    "GameCreateRequest",
    "MoveRequest",
    "GameStateResponse",
    "MoveResponse",
]
