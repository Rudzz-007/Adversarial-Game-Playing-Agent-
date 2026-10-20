from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import math
from ai_agent import minimax
from game_engine import get_next_open_row

app = FastAPI(
    title="Connect Four AI Agent",
    description="Backend API for the Connect Four adversarial game-playing agent",
    version="1.0.0",
)

# Enable CORS for frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class MoveRequest(BaseModel):
    board: list[list[int]]
    depth: int = 4  # 2: Easy, 4: Medium, 6: Hard

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/api/ai-move")
def ai_move(request: MoveRequest):
    col, _ = minimax(request.board, request.depth, -math.inf, math.inf, True)
    row = get_next_open_row(request.board, col) if col is not None else -1
    return {
        "column": col,
        "row": row,
    }