"""
Comprehensive unit and integration test suite for Connect Four AI Agents (Phase 4).
Tests BaseAgent, RandomAgent, GreedyAgent, tactical priorities, blunder avoidance,
split-threat evaluation, board immutability, API validation, and backward compatibility.
"""
import copy
import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

# Ensure backend root is on sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from main import app
from app.agents import RandomAgent, GreedyAgent, get_agent, SUPPORTED_AGENTS
from app.agents.factory import MinimaxAgent
from app.core.game_engine import (
    ROWS,
    COLS,
    EMPTY,
    PLAYER_1,
    PLAYER_2,
    create_board,
    drop_piece,
    get_next_open_row,
    get_valid_locations,
)
from app.core.validation import GameRuleException
from tests.test_game_engine import DRAW_BOARD_FIXTURE

client = TestClient(app)


# =====================================================================
# 1. Board Immutability Tests
# =====================================================================

def test_random_agent_board_immutability():
    """Verify RandomAgent never mutates caller's board matrix."""
    agent = RandomAgent(seed=42)
    board = create_board()
    drop_piece(board, 5, 3, PLAYER_1)
    drop_piece(board, 4, 3, PLAYER_2)
    board_copy = copy.deepcopy(board)

    col, telemetry = agent.select_move(board)
    assert col is not None
    assert board == board_copy, "RandomAgent mutated the caller board argument!"


def test_greedy_agent_board_immutability():
    """Verify GreedyAgent never mutates caller's board across tactical/heuristic evaluation."""
    agent = GreedyAgent()
    board = create_board()
    drop_piece(board, 5, 2, PLAYER_1)
    drop_piece(board, 5, 3, PLAYER_2)
    drop_piece(board, 5, 4, PLAYER_1)
    board_copy = copy.deepcopy(board)

    col, telemetry = agent.select_move(board)
    assert col is not None
    assert board == board_copy, "GreedyAgent mutated the caller board argument!"


# =====================================================================
# 2. Random Agent Tests
# =====================================================================

def test_random_agent_isolated_seed_reproducibility():
    """Verify isolated seed produces deterministic sequence without global state pollution."""
    board = create_board()
    agent1 = RandomAgent(seed=12345)
    agent2 = RandomAgent(seed=12345)

    seq1 = [agent1.select_move(board)[0] for _ in range(20)]
    seq2 = [agent2.select_move(board)[0] for _ in range(20)]
    assert seq1 == seq2


def test_random_agent_controlled_single_column():
    """Verify RandomAgent returns the only legal column when 6 columns are full."""
    board = create_board()
    # Fill columns 0, 1, 2, 3, 5, 6 completely (leaving only column 4 open)
    for c in [0, 1, 2, 3, 5, 6]:
        for r in range(ROWS):
            board[r][c] = PLAYER_1

    agent = RandomAgent(seed=999)
    for _ in range(10):
        col, _ = agent.select_move(board)
        assert col == 4


def test_random_agent_full_board_returns_none():
    """Verify RandomAgent returns None and telemetry when board is full."""
    agent = RandomAgent(seed=42)
    col, telemetry = agent.select_move(DRAW_BOARD_FIXTURE)
    assert col is None
    assert telemetry["decision_time_ms"] >= 0.0
    assert telemetry["nodes_evaluated"] is None
    assert telemetry["pruned_nodes"] is None


def test_random_agent_rejects_boolean_seed():
    """Verify RandomAgent rejects boolean seed explicitly."""
    with pytest.raises(ValueError, match="Seed must be an integer, not boolean"):
        RandomAgent(seed=True)
    with pytest.raises(ValueError, match="Seed must be an integer, not boolean"):
        RandomAgent(seed=False)


def test_random_agent_telemetry_invariants():
    """Verify RandomAgent telemetry invariants: measured decision time, null tree metrics."""
    agent = RandomAgent(seed=42)
    board = create_board()
    col, telemetry = agent.select_move(board)
    assert telemetry["decision_time_ms"] >= 0.0
    assert telemetry["nodes_evaluated"] is None
    assert telemetry["pruned_nodes"] is None
    assert telemetry["search_depth"] is None
    assert telemetry["transposition_hits"] is None
    assert telemetry["candidate_scores"] is None


# =====================================================================
# 3. Greedy Tactical & Reply-Checking Tests
# =====================================================================

def test_greedy_immediate_horizontal_win():
    """Verify GreedyAgent takes immediate horizontal winning move."""
    agent = GreedyAgent(player_id=PLAYER_2)
    board = create_board()
    # Player 2 has 3 pieces at (5, 0), (5, 1), (5, 2)
    drop_piece(board, 5, 0, PLAYER_2)
    drop_piece(board, 5, 1, PLAYER_2)
    drop_piece(board, 5, 2, PLAYER_2)

    col, telemetry = agent.select_move(board)
    assert col == 3
    assert telemetry["search_depth"] == 1


def test_greedy_immediate_vertical_win():
    """Verify GreedyAgent takes immediate vertical winning move."""
    agent = GreedyAgent(player_id=PLAYER_2)
    board = create_board()
    # Player 2 has 3 pieces stacked in column 2
    drop_piece(board, 5, 2, PLAYER_2)
    drop_piece(board, 4, 2, PLAYER_2)
    drop_piece(board, 3, 2, PLAYER_2)

    col, _ = agent.select_move(board)
    assert col == 2


def test_greedy_immediate_positive_diagonal_win():
    """Verify GreedyAgent takes immediate positive diagonal (/) winning move."""
    agent = GreedyAgent(player_id=PLAYER_2)
    board = create_board()
    # Diagonal from (5, 0) up to (2, 3)
    drop_piece(board, 5, 0, PLAYER_2)

    drop_piece(board, 5, 1, PLAYER_1)
    drop_piece(board, 4, 1, PLAYER_2)

    drop_piece(board, 5, 2, PLAYER_1)
    drop_piece(board, 4, 2, PLAYER_1)
    drop_piece(board, 3, 2, PLAYER_2)

    # In col 3: support pieces at row 5, 4, 3 so open row is 2
    drop_piece(board, 5, 3, PLAYER_1)
    drop_piece(board, 4, 3, PLAYER_1)
    drop_piece(board, 3, 3, PLAYER_1)

    col, _ = agent.select_move(board)
    assert col == 3


def test_greedy_immediate_negative_diagonal_win():
    r"""Verify GreedyAgent takes immediate negative diagonal (\) winning move."""
    agent = GreedyAgent(player_id=PLAYER_2)
    board = create_board()
    # Diagonal from (2, 0) down to (5, 3)
    # Target is (2, 0)
    drop_piece(board, 5, 0, PLAYER_1)
    drop_piece(board, 4, 0, PLAYER_1)
    drop_piece(board, 3, 0, PLAYER_1)

    drop_piece(board, 5, 1, PLAYER_1)
    drop_piece(board, 4, 1, PLAYER_1)
    drop_piece(board, 3, 1, PLAYER_2)

    drop_piece(board, 5, 2, PLAYER_1)
    drop_piece(board, 4, 2, PLAYER_2)

    drop_piece(board, 5, 3, PLAYER_2)

    col, _ = agent.select_move(board)
    assert col == 0


def test_greedy_immediate_blocks():
    """Verify GreedyAgent immediately blocks opponent horizontal and vertical winning threats."""
    agent = GreedyAgent(player_id=PLAYER_2)

    # Horizontal block
    board_h = create_board()
    drop_piece(board_h, 5, 0, PLAYER_1)
    drop_piece(board_h, 5, 1, PLAYER_1)
    drop_piece(board_h, 5, 2, PLAYER_1)
    col_h, _ = agent.select_move(board_h)
    assert col_h == 3

    # Vertical block
    board_v = create_board()
    drop_piece(board_v, 5, 4, PLAYER_1)
    drop_piece(board_v, 4, 4, PLAYER_1)
    drop_piece(board_v, 3, 4, PLAYER_1)
    col_v, _ = agent.select_move(board_v)
    assert col_v == 4


def test_greedy_priority_win_over_block():
    """Verify GreedyAgent strictly prioritizes an immediate win over an immediate opponent block."""
    agent = GreedyAgent(player_id=PLAYER_2)
    board = create_board()

    # Agent (Player 2) has 3-in-a-row ready to win in col 5 (vertical win at row 2)
    drop_piece(board, 5, 5, PLAYER_2)
    drop_piece(board, 4, 5, PLAYER_2)
    drop_piece(board, 3, 5, PLAYER_2)

    # Opponent (Player 1) has 3-in-a-row ready to win in col 1 (vertical win at row 2)
    drop_piece(board, 5, 1, PLAYER_1)
    drop_piece(board, 4, 1, PLAYER_1)
    drop_piece(board, 3, 1, PLAYER_1)

    col, telemetry = agent.select_move(board)
    assert col == 5, "Agent should choose immediate win (col 5) over opponent block (col 1)"
    assert telemetry["candidate_scores"][0]["reason"] == "immediate_win"


# =====================================================================
# 4. Safeguard 1: Split-Threat Positions & Threat Removal Tests
# =====================================================================

def test_greedy_split_threat_agent_wins_immediately():
    """Safeguard 1: When opponent has multiple winning threats, agent wins immediately if possible."""
    agent = GreedyAgent(player_id=PLAYER_2)
    board = create_board()

    # Opponent (Player 1) has split threats:
    # Threat 1: Col 1 has 3 pieces stacked (5, 1), (4, 1), (3, 1) -> win at (2, 1)
    drop_piece(board, 5, 1, PLAYER_1)
    drop_piece(board, 4, 1, PLAYER_1)
    drop_piece(board, 3, 1, PLAYER_1)

    # Threat 2: Col 6 has 3 pieces stacked (5, 6), (4, 6), (3, 6) -> win at (2, 6)
    drop_piece(board, 5, 6, PLAYER_1)
    drop_piece(board, 4, 6, PLAYER_1)
    drop_piece(board, 3, 6, PLAYER_1)

    # But Agent (Player 2) has an immediate win in col 3!
    drop_piece(board, 5, 3, PLAYER_2)
    drop_piece(board, 4, 3, PLAYER_2)
    drop_piece(board, 3, 3, PLAYER_2)

    col, telemetry = agent.select_move(board)
    assert col == 3, "Agent must win immediately rather than assume loss is unavoidable"
    assert telemetry["candidate_scores"][0]["reason"] == "immediate_win"


def test_greedy_split_threat_single_move_defuses_both():
    """Safeguard 1: When multiple threats share an intersection, single move defuses both threats."""
    agent = GreedyAgent(player_id=PLAYER_2)
    board = create_board()

    # Opponent has 3 vertical pieces in col 3 at (5, 3), (4, 3), (3, 3) -> threat at (2, 3)
    drop_piece(board, 5, 3, PLAYER_1)
    drop_piece(board, 4, 3, PLAYER_1)
    drop_piece(board, 3, 3, PLAYER_1)

    # Opponent ALSO has horizontal pieces at (2, 1), (2, 2) needing (2, 3) to make 4
    # Set up supports for (2, 1) and (2, 2)
    drop_piece(board, 5, 1, PLAYER_2)
    drop_piece(board, 4, 1, PLAYER_2)
    drop_piece(board, 3, 1, PLAYER_2)
    drop_piece(board, 2, 1, PLAYER_1)

    drop_piece(board, 5, 2, PLAYER_2)
    drop_piece(board, 4, 2, PLAYER_2)
    drop_piece(board, 3, 2, PLAYER_2)
    drop_piece(board, 2, 2, PLAYER_1)

    # Now (2, 3) is the open cell in col 3, which blocks BOTH the vertical and horizontal threats!
    col, telemetry = agent.select_move(board)
    assert col == 3, "Move in col 3 defuses both opponent threats simultaneously"
    assert telemetry["reason"] == "safe_block"


def test_greedy_multiple_opponent_threats_fork():
    """Safeguard 1: When an opponent fork has distinct threats, block using center-outward tie-break."""
    agent = GreedyAgent(player_id=PLAYER_2)
    board = create_board()

    # Opponent has horizontal 3-in-a-row at row 5 in columns 2, 3, 4:
    # Threats exist in column 1 and column 5!
    drop_piece(board, 5, 2, PLAYER_1)
    drop_piece(board, 5, 3, PLAYER_1)
    drop_piece(board, 5, 4, PLAYER_1)

    # Center-outward order: [3, 2, 4, 1, 5, 0, 6]
    # Column 1 appears at index 3, column 5 appears at index 4.
    col, telemetry = agent.select_move(board)
    assert col == 1, f"Expected column 1 based on center-outward order, got {col}"
    assert telemetry["reason"] == "split_threat_block"


def test_greedy_all_reply_blunder_avoidance():
    """Verify GreedyAgent avoids playing in a column that allows opponent to win on immediate reply."""
    agent = GreedyAgent(player_id=PLAYER_2)
    board = create_board()

    # Row 5 setup: neither player can win at row 5
    drop_piece(board, 5, 0, PLAYER_2)
    drop_piece(board, 5, 2, PLAYER_1)
    drop_piece(board, 5, 3, PLAYER_2)

    # Row 4 setup: Opponent has 3 discs at (4, 0), (4, 2), (4, 3)
    drop_piece(board, 4, 0, PLAYER_1)
    drop_piece(board, 4, 2, PLAYER_1)
    drop_piece(board, 4, 3, PLAYER_1)

    # Column 1 is completely empty (open at row 5).
    # If agent drops in col 1, agent lands at (5, 1).
    # That creates support for (4, 1)!
    # On opponent's reply: opponent drops in col 1 at (4, 1) and completes 4-in-a-row!
    # Col 1 is an UNSAFE move.
    col, telemetry = agent.select_move(board)
    assert col != 1, "Agent blundered into setting up opponent's winning reply in col 1!"
    # Ensure column 1 is identified as unsafe in telemetry
    cand_1 = [c for c in telemetry["candidate_scores"] if c["column"] == 1][0]
    assert cand_1["is_safe"] is False
    # Ensure the chosen move is SAFE
    chosen_cand = [c for c in telemetry["candidate_scores"] if c["column"] == col][0]
    assert chosen_cand["is_safe"] is True



def test_greedy_no_safe_moves_fallback():
    """Verify GreedyAgent falls back gracefully when every candidate move is unsafe."""
    agent = GreedyAgent(player_id=PLAYER_2)
    board = create_board()

    # Create a situation where opponent has multiple immediate threats in all open columns
    # Fill columns 2..6, leave col 0 and 1 open
    for c in range(2, COLS):
        for r in range(ROWS):
            board[r][c] = PLAYER_1

    # In col 0 and 1: row 5 is open. Opponent has 3 vertical pieces in BOTH col 0 and col 1.
    for r in range(3, ROWS):
        board[r][0] = PLAYER_1
        board[r][1] = PLAYER_1

    col, telemetry = agent.select_move(board)
    assert col in (0, 1)
    assert telemetry["reason"] == "split_threat_block"


def test_greedy_center_outward_tie_breaking():
    """Verify GreedyAgent selects center column 3 on an empty board."""
    agent = GreedyAgent(player_id=PLAYER_2)
    board = create_board()
    col, _ = agent.select_move(board)
    assert col == 3, f"Expected center column 3 on empty board, got {col}"


def test_greedy_telemetry_contract():
    """Verify GreedyAgent telemetry adheres to PRD §12.2 and approved plan."""
    agent = GreedyAgent(player_id=PLAYER_2)
    board = create_board()
    _, telemetry = agent.select_move(board)

    assert telemetry["decision_time_ms"] >= 0.0
    assert telemetry["search_depth"] == 1
    assert telemetry["nodes_evaluated"] is None
    assert telemetry["pruned_nodes"] is None
    assert telemetry["transposition_hits"] is None
    assert isinstance(telemetry["candidate_scores"], list)
    assert len(telemetry["candidate_scores"]) == 7


# =====================================================================
# 5. Factory Module Tests
# =====================================================================

def test_factory_instantiates_supported_agents():
    """Verify get_agent instantiates RandomAgent, GreedyAgent, MinimaxAgent."""
    agent_r = get_agent("random", seed=42)
    assert isinstance(agent_r, RandomAgent)
    assert agent_r.seed == 42

    agent_g = get_agent("greedy")
    assert isinstance(agent_g, GreedyAgent)

    agent_m = get_agent("minimax", depth=3)
    assert isinstance(agent_m, MinimaxAgent)
    assert agent_m.depth == 3


def test_factory_rejects_unsupported_agent():
    """Verify get_agent raises GameRuleException with INVALID_AGENT code."""
    with pytest.raises(GameRuleException) as exc_info:
        get_agent("alphabeta")  # Not in Phase 4 scope
    assert exc_info.value.code == "INVALID_AGENT"
    assert exc_info.value.status_code == 400


# =====================================================================
# 6. Safeguard 2: API Validation & Legacy Compatibility Tests
# =====================================================================

def test_api_unknown_agent_error_envelope():
    """Safeguard 2: Verify POST /api/ai-move returns 400 INVALID_AGENT for unknown agents."""
    empty_board = create_board()
    response = client.post("/api/ai-move", json={"board": empty_board, "agent": "unknown_ai"})
    assert response.status_code == 400
    data = response.json()
    assert data["error"]["code"] == "INVALID_AGENT"
    assert "unknown_ai" in data["error"]["message"].lower()


def test_api_invalid_seed_error_envelope():
    """Safeguard 2: Verify POST /api/ai-move rejects boolean seed with 422 VALIDATION_ERROR."""
    empty_board = create_board()
    response = client.post("/api/ai-move", json={"board": empty_board, "agent": "random", "seed": True})
    assert response.status_code == 422
    data = response.json()
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert "seed" in data["error"]["message"].lower()


def test_api_random_agent_execution():
    """Verify POST /api/ai-move executes RandomAgent with seed and returns telemetry."""
    empty_board = create_board()
    response = client.post("/api/ai-move", json={"board": empty_board, "agent": "random", "seed": 42})
    assert response.status_code == 200
    data = response.json()
    assert "column" in data and isinstance(data["column"], int)
    assert "row" in data and isinstance(data["row"], int)
    assert "telemetry" in data
    assert data["telemetry"]["decision_time_ms"] >= 0.0
    assert data["telemetry"]["search_depth"] is None


def test_api_greedy_agent_execution():
    """Verify POST /api/ai-move executes GreedyAgent and selects winning move with telemetry."""
    board = create_board()
    drop_piece(board, 5, 0, PLAYER_2)
    drop_piece(board, 5, 1, PLAYER_2)
    drop_piece(board, 5, 2, PLAYER_2)

    response = client.post("/api/ai-move", json={"board": board, "agent": "greedy"})
    assert response.status_code == 200
    data = response.json()
    assert data["column"] == 3
    assert data["row"] == 5
    assert "telemetry" in data
    assert data["telemetry"]["search_depth"] == 1


def test_api_legacy_minimax_contract_unbroken():
    """Safeguard 2: Verify existing Minimax request/response contract is preserved exactly when agent is omitted."""
    empty_board = create_board()
    # Call without "agent" parameter
    response = client.post("/api/ai-move", json={"board": empty_board, "depth": 2})
    assert response.status_code == 200
    data = response.json()
    # Exact legacy response contract
    assert set(data.keys()) == {"column", "row"}
    assert isinstance(data["column"], int)
    assert 0 <= data["column"] < COLS
    assert isinstance(data["row"], int)
    assert 0 <= data["row"] < ROWS


def test_api_full_board_returns_none_column():
    """Safeguard 2: Verify full board returns column: None, row: -1 gracefully."""
    response = client.post("/api/ai-move", json={"board": DRAW_BOARD_FIXTURE, "agent": "greedy"})
    assert response.status_code == 200
    data = response.json()
    assert data["column"] is None
    assert data["row"] == -1
    assert "telemetry" in data


def test_api_full_board_legacy_contract():
    """Safeguard 2: Verify legacy Minimax call on full board returns column: None, row: -1."""
    response = client.post("/api/ai-move", json={"board": DRAW_BOARD_FIXTURE})
    assert response.status_code == 200
    data = response.json()
    assert data["column"] is None
    assert data["row"] == -1
    assert set(data.keys()) == {"column", "row"}
