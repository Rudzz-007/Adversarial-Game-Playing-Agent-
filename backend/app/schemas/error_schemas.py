from pydantic import BaseModel, Field

class ErrorDetail(BaseModel):
    code: str = Field(..., description="Standardized error code (e.g., INVALID_MOVE, VALIDATION_ERROR)")
    message: str = Field(..., description="Human-readable error description")

class ErrorResponse(BaseModel):
    error: ErrorDetail
