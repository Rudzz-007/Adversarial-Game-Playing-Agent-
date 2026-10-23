import sys
from pathlib import Path
import math
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from pydantic import BaseModel

# Ensure backend root is on sys.path for app.* imports
sys.path.insert(0, str(Path(__file__).resolve().parent))

from ai_agent import minimax
from game_engine import get_next_open_row
from app.api.health_routes import router as health_router
from app.api.agent_routes import router as agent_router
from app.core.validation import GameRuleException

app = FastAPI(
    title="Connect Four AI Agent",
    description="Backend API for the Connect Four adversarial game-playing agent",
    version="1.0.0",
)

# Standardized Error Handlers conforming to PRD §12.9: {"error": {"code": "...", "message": "..."}}
@app.exception_handler(GameRuleException)
async def game_rule_exception_handler(request: Request, exc: GameRuleException):
    """Format domain game rule violations into standardized error envelope."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message}},
    )
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Format schema validation errors into standardized error envelope without stack traces."""
    error_msgs = []
    for err in exc.errors():
        loc = " -> ".join(str(l) for l in err.get("loc", []) if l != "body")
        msg = err.get("msg", "invalid input")
        error_msgs.append(f"{loc}: {msg}" if loc else msg)
    message = "; ".join(error_msgs) if error_msgs else "Invalid request payload."
    return JSONResponse(
        status_code=422,
        content={"error": {"code": "VALIDATION_ERROR", "message": message}},
    )

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Format HTTP errors into standardized error envelope."""
    code_map = {
        400: "BAD_REQUEST",
        404: "NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        422: "UNPROCESSABLE_ENTITY",
        500: "INTERNAL_ERROR",
    }
    code = code_map.get(exc.status_code, "HTTP_ERROR")
    message = exc.detail if isinstance(exc.detail, str) else "HTTP request error."
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": code, "message": message}},
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Catch unhandled errors, returning generic internal error without leaking internal traces."""
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "INTERNAL_ERROR", "message": "An unexpected internal server error occurred."}},
    )

# Enable CORS for frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount modular routers
app.include_router(health_router)
app.include_router(agent_router)

# Preserved existing MoveRequest schema for backward compatibility
class MoveRequest(BaseModel):
    board: list[list[int]]
    depth: int = 4  # 2: Easy, 4: Medium, 6: Hard

# Preserved backward-compatible endpoint for existing React frontend
@app.post("/api/ai-move")
def ai_move(request: MoveRequest):
    col, _ = minimax(request.board, request.depth, -math.inf, math.inf, True)
    row = get_next_open_row(request.board, col) if col is not None else -1
    return {
        "column": col,
        "row": row,
    }