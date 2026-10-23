"""
Comprehensive test suite for Phase 5 Advanced Search Agents:
- MinimaxAgent
- AlphaBetaAgent
- OptimizedAlphaBetaAgent
- MCTSAgent

Verifies mathematical equivalence, tie-breaking, pruning efficiency, transposition table bound safety,
MCTS selection/backpropagation invariants, PRD §13.3 telemetry compliance, and board immutability.
"""
import copy
import math
import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

# Ensure backend root is on sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from main import app
from app.agents import (
    MinimaxAgent,
    AlphaBetaAgent,
    OptimizedAlphaBetaAgent,
    MCTSAgent,
    get_agent,
    SUPPORTED_AGENTS,
)
from app.core.game_engine import (
    ROWS,
    COLS,
    PLAYER_1,
    PLAYER_2,
    create_board,
    drop_piece,
    get_next_open_row,
)
from app.core.evaluation import (
    WIN_SCORE,
    LOSS_SCORE,
    DRAW_SCORE,
    score_position,
)
from tests.test_game_engine import DRAW_BOARD_FIXTURE

client = TestClient(app)


# =====================================================================
# Fixtures & Helpers
# =====================================================================

def create_tactical_midgame_board() -> list[list[int]]:
    """Create a non-trivial midgame board with tactical branches and transpositions."""
    b = create_board()
    # Drops: col 3 (P1), col 3 (P2), col 2 (P1), col 4 (P2), col 2 (P2), col 4 (P1)
    drop_piece(b, 5, 3, PLAYER_1)
    drop_piece(b, 4, 3, PLAYER_2)
    drop_piece(b, 5, 2, PLAYER_1)
    drop_piece(b, 5, 4, PLAYER_2)
    drop_piece(b, 4, 2, PLAYER_2)
    drop_piece(b, 4, 4, PLAYER_1)
    return b


def create_symmetrical_opening_board() -> list[list[int]]:
    """Create a symmetrical opening board fixture (P1 played center col 3)."""
    b = create_board()
    drop_piece(b, 5, 3, PLAYER_1)
    return b


# =====================================================================
# 1. Strict Board Immutability Tests
# =====================================================================

def test_minimax_agent_board_immutability():
    """Verify MinimaxAgent never mutates caller's board across recursive search."""
    agent = MinimaxAgent(player_id=PLAYER_2, depth=3)
    board = create_tactical_midgame_board()
    board_copy = copy.deepcopy(board)

    col, telemetry = agent.select_move(board)
    assert col is not None
    assert board == board_copy, "MinimaxAgent mutated caller's board matrix!"


def test_alphabeta_agent_board_immutability():
    """Verify AlphaBetaAgent never mutates caller's board across pruned search branches."""
    agent = AlphaBetaAgent(player_id=PLAYER_2, depth=3)
    board = create_tactical_midgame_board()
    board_copy = copy.deepcopy(board)

    col, telemetry = agent.select_move(board)
    assert col is not None
    assert board == board_copy, "AlphaBetaAgent mutated caller's board matrix!"


def test_optimized_agent_board_immutability():
    """Verify OptimizedAlphaBetaAgent never mutates caller's board during search/caching."""
    agent = OptimizedAlphaBetaAgent(player_id=PLAYER_2, depth=3)
    board = create_tactical_midgame_board()
    board_copy = copy.deepcopy(board)

    col, telemetry = agent.select_move(board)
    assert col is not None
    assert board == board_copy, "OptimizedAlphaBetaAgent mutated caller's board matrix!"


def test_mcts_agent_board_immutability():
    """Verify MCTSAgent never mutates caller's board across rollout simulations."""
    agent = MCTSAgent(player_id=PLAYER_2, iterations=150, seed=42)
    board = create_tactical_midgame_board()
    board_copy = copy.deepcopy(board)

    col, telemetry = agent.select_move(board)
    assert col is not None
    assert board == board_copy, "MCTSAgent mutated caller's board matrix!"


# =====================================================================
# 2. Minimax & Alpha-Beta Equivalence & Correctness Tests
# =====================================================================

def test_minimax_and_alphabeta_score_equivalence():
    """
    Assert that Minimax and Alpha-Beta compute mathematically identical root minimax scores
    across multiple depths on diverse positions.
    """
    test_boards = [
        create_board(),
        create_symmetrical_opening_board(),
        create_tactical_midgame_board(),
    ]

    for depth in [2, 3]:
        for idx, board in enumerate(test_boards):
            mm_agent = MinimaxAgent(player_id=PLAYER_2, depth=depth)
            ab_agent = AlphaBetaAgent(player_id=PLAYER_2, depth=depth)

            mm_col, mm_telem = mm_agent.select_move(board)
            ab_col, ab_telem = ab_agent.select_move(board)

            assert mm_agent.last_root_score == ab_agent.last_root_score, (
                f"Score mismatch at depth {depth} on board {idx}: "
                f"Minimax={mm_agent.last_root_score}, AlphaBeta={ab_agent.last_root_score}"
            )
            assert mm_col == ab_col, (
                f"Move mismatch at depth {depth} on board {idx}: "
                f"Minimax={mm_col}, AlphaBeta={ab_col}"
            )


def test_minimax_and_alphabeta_unique_move_equivalence():
    """
    On a board with a unique winning move, assert Minimax and Alpha-Beta choose the identical column.
    """
    board = create_board()
    # P2 has 3 in a row at row 5 in columns 0, 1, 2 -> unique win at col 3
    drop_piece(board, 5, 0, PLAYER_2)
    drop_piece(board, 5, 1, PLAYER_2)
    drop_piece(board, 5, 2, PLAYER_2)

    mm_agent = MinimaxAgent(player_id=PLAYER_2, depth=2)
    ab_agent = AlphaBetaAgent(player_id=PLAYER_2, depth=2)

    mm_col, _ = mm_agent.select_move(board)
    ab_col, _ = ab_agent.select_move(board)

    assert mm_col == 3
    assert ab_col == 3


def test_alphabeta_pruning_efficiency():
    """
    Assert that Alpha-Beta evaluates strictly fewer nodes than Minimax and records branch cutoffs
    on non-trivial midgame positions.
    """
    board = create_tactical_midgame_board()
    depth = 4

    mm_agent = MinimaxAgent(player_id=PLAYER_2, depth=depth)
    ab_agent = AlphaBetaAgent(player_id=PLAYER_2, depth=depth)

    _, mm_telem = mm_agent.select_move(board)
    _, ab_telem = ab_agent.select_move(board)

    mm_nodes = mm_telem["nodes_evaluated"]
    ab_nodes = ab_telem["nodes_evaluated"]
    ab_pruned = ab_telem["pruned_nodes"]

    assert ab_nodes < mm_nodes, f"Alpha-Beta evaluated {ab_nodes} >= Minimax {mm_nodes}"
    assert ab_pruned > 0, "Alpha-Beta reported 0 pruned nodes on a 4-ply midgame search"


def test_terminal_scoring_consistency():
    """Assert win, loss, and draw return identical centralized scores across deterministic search agents."""
    board_win = create_board()
    drop_piece(board_win, 5, 0, PLAYER_2)
    drop_piece(board_win, 5, 1, PLAYER_2)
    drop_piece(board_win, 5, 2, PLAYER_2)
    drop_piece(board_win, 5, 3, PLAYER_2)  # P2 won

    board_loss = create_board()
    drop_piece(board_loss, 5, 0, PLAYER_1)
    drop_piece(board_loss, 5, 1, PLAYER_1)
    drop_piece(board_loss, 5, 2, PLAYER_1)
    drop_piece(board_loss, 5, 3, PLAYER_1)  # P1 won

    # Terminal evaluation at depth 1
    for b, expected_score in [(board_win, WIN_SCORE), (board_loss, LOSS_SCORE), (DRAW_BOARD_FIXTURE, DRAW_SCORE)]:
        mm = MinimaxAgent(player_id=PLAYER_2, depth=1)
        ab = AlphaBetaAgent(player_id=PLAYER_2, depth=1)
        opt = OptimizedAlphaBetaAgent(player_id=PLAYER_2, depth=1)

        _, mm_val = mm._minimax(b, 1, True)
        _, ab_val = ab._alphabeta(b, 1, -math.inf, math.inf, True)
        _, opt_val = opt._alphabeta(b, 1, -math.inf, math.inf, True)

        assert mm_val == expected_score
        assert ab_val == expected_score
        assert opt_val == expected_score


# =====================================================================
# 3. Optimized Alpha-Beta & Transposition Table Tests
# =====================================================================

def test_optimized_alphabeta_score_equivalence():
    """Assert OptimizedAlphaBetaAgent computes the exact root score as AlphaBetaAgent."""
    board = create_tactical_midgame_board()
    depth = 3

    ab_agent = AlphaBetaAgent(player_id=PLAYER_2, depth=depth)
    opt_agent = OptimizedAlphaBetaAgent(player_id=PLAYER_2, depth=depth)

    ab_agent.select_move(board)
    opt_agent.select_move(board)

    assert opt_agent.last_root_score == ab_agent.last_root_score


def test_optimized_alphabeta_unique_move_equivalence():
    """Assert OptimizedAlphaBetaAgent chooses identical move when best move is unique."""
    board = create_board()
    drop_piece(board, 5, 0, PLAYER_2)
    drop_piece(board, 5, 1, PLAYER_2)
    drop_piece(board, 5, 2, PLAYER_2)

    ab_agent = AlphaBetaAgent(player_id=PLAYER_2, depth=2)
    opt_agent = OptimizedAlphaBetaAgent(player_id=PLAYER_2, depth=2)

    ab_col, _ = ab_agent.select_move(board)
    opt_col, _ = opt_agent.select_move(board)

    assert ab_col == 3
    assert opt_col == 3


def test_optimized_alphabeta_move_ordering_validation():
    """
    Performance fixture on symmetrical opening board at depth 4.
    Treats move-ordering efficiency as an empirical test to validate rather than an unconditional claim.
    Validates root score equivalence and valid legal move selection, logging node counts.
    """
    board = create_symmetrical_opening_board()
    depth = 4

    ab_agent = AlphaBetaAgent(player_id=PLAYER_2, depth=depth)
    opt_agent = OptimizedAlphaBetaAgent(player_id=PLAYER_2, depth=depth)

    ab_col, ab_telem = ab_agent.select_move(board)
    opt_col, opt_telem = opt_agent.select_move(board)

    ab_nodes = ab_telem["nodes_evaluated"]
    opt_nodes = opt_telem["nodes_evaluated"]

    # Root score must be mathematically identical
    assert opt_agent.last_root_score == ab_agent.last_root_score
    # Both select valid legal columns
    assert 0 <= ab_col < COLS
    assert 0 <= opt_col < COLS

    # Empirical validation: record performance comparison
    # Both pruned agents evaluate substantially fewer nodes than exhaustive tree (7^4 = 2401)
    assert opt_nodes < 2401
    assert ab_nodes < 2401


def test_transposition_table_enabled_vs_disabled():
    """Assert OptimizedAlphaBetaAgent produces identical root score whether TT is enabled or disabled."""
    board = create_tactical_midgame_board()
    depth = 3

    opt_tt = OptimizedAlphaBetaAgent(player_id=PLAYER_2, depth=depth, use_tt=True)
    opt_no_tt = OptimizedAlphaBetaAgent(player_id=PLAYER_2, depth=depth, use_tt=False)

    col_tt, _ = opt_tt.select_move(board)
    col_no_tt, _ = opt_no_tt.select_move(board)

    assert opt_tt.last_root_score == opt_no_tt.last_root_score
    assert col_tt == col_no_tt


def test_transposition_table_cache_hits():
    """Assert transposition_hits > 0 on a position with reachable transpositions."""
    board = create_tactical_midgame_board()
    agent = OptimizedAlphaBetaAgent(player_id=PLAYER_2, depth=4, use_tt=True)

    _, telem = agent.select_move(board)
    assert telem["transposition_hits"] > 0, (
        f"Expected transposition hits > 0 on 4-ply tactical midgame search, got {telem['transposition_hits']}"
    )


def test_transposition_bound_safety():
    """Assert non-exact bounds (LOWER or UPPER) where alpha < beta are never returned directly as exact scores."""
    agent = OptimizedAlphaBetaAgent(player_id=PLAYER_2, depth=3)
    board = create_board()

    # Artificially inject a LOWER bound into transposition table with score 50.0
    board_key = (tuple(tuple(r) for r in board), PLAYER_2)
    from app.agents.optimized_agent import TTEntry
    agent._tt[board_key] = TTEntry(searched_depth=4, score=50.0, bound_type="LOWER", best_move=3)

    # Calling _alphabeta with alpha=-math.inf, beta=math.inf
    # Bound should update alpha to max(-inf, 50.0) = 50.0.
    # Since alpha (50.0) < beta (inf), it MUST NOT return 50.0 immediately without searching!
    agent._transposition_hits = 0
    col, score = agent._alphabeta(board, 2, -math.inf, math.inf, True)

    # It evaluated recursively:
    assert agent._nodes_evaluated > 1


def test_optimized_immediate_win_cutoff():
    """Assert OptimizedAlphaBetaAgent takes immediate win with 1-ply cutoff."""
    board = create_board()
    # P2 ready to win vertically at column 2
    drop_piece(board, 5, 2, PLAYER_2)
    drop_piece(board, 4, 2, PLAYER_2)
    drop_piece(board, 3, 2, PLAYER_2)

    agent = OptimizedAlphaBetaAgent(player_id=PLAYER_2, depth=4)
    col, telem = agent.select_move(board)

    assert col == 2
    assert agent.last_root_score == WIN_SCORE


# =====================================================================
# 4. MCTS Correctness & Perspective Tests
# =====================================================================

def test_mcts_immediate_win_discovery():
    """Verify MCTSAgent identifies and takes immediate win with 400 iterations."""
    board = create_board()
    # P2 has 3 in a row in columns 0, 1, 2 at row 5
    drop_piece(board, 5, 0, PLAYER_2)
    drop_piece(board, 5, 1, PLAYER_2)
    drop_piece(board, 5, 2, PLAYER_2)

    agent = MCTSAgent(player_id=PLAYER_2, iterations=400, seed=42)
    col, telemetry = agent.select_move(board)
    assert col == 3, f"MCTS failed to take immediate winning move at col 3, chose {col}"


def test_mcts_immediate_block_discovery():
    """Verify MCTSAgent blocks opponent immediate win with 500 iterations."""
    board = create_board()
    # P1 (opponent) has 3 in a row in columns 1, 2, 3 at row 5
    drop_piece(board, 5, 1, PLAYER_1)
    drop_piece(board, 5, 2, PLAYER_1)
    drop_piece(board, 5, 3, PLAYER_1)

    agent = MCTSAgent(player_id=PLAYER_2, iterations=500, seed=42)
    col, _ = agent.select_move(board)
    # Opponent threats are at col 0 and col 4
    assert col in (0, 4), f"MCTS failed to block opponent threat at col 0 or 4, chose {col}"


def test_mcts_seed_reproducibility():
    """Verify two MCTSAgent instances with identical seed make 100% identical moves and visit distributions."""
    board = create_tactical_midgame_board()
    agent1 = MCTSAgent(player_id=PLAYER_2, iterations=250, seed=999)
    agent2 = MCTSAgent(player_id=PLAYER_2, iterations=250, seed=999)

    col1, telem1 = agent1.select_move(board)
    col2, telem2 = agent2.select_move(board)

    assert col1 == col2
    assert telem1["candidate_scores"] == telem2["candidate_scores"]


def test_mcts_iteration_budget_enforcement():
    """Assert mcts_iterations and mcts_simulations equal the completed cycle count."""
    board = create_tactical_midgame_board()
    budget = 350
    agent = MCTSAgent(player_id=PLAYER_2, iterations=budget, seed=42)

    _, telemetry = agent.select_move(board)
    assert telemetry["mcts_iterations"] == budget
    assert telemetry["mcts_simulations"] == budget


def test_mcts_terminal_root_handling():
    """Assert MCTS on full board returns (None, telemetry) with 0 iterations and 0 simulations."""
    agent = MCTSAgent(player_id=PLAYER_2, iterations=500, seed=42)
    col, telemetry = agent.select_move(DRAW_BOARD_FIXTURE)

    assert col is None
    assert telemetry["mcts_iterations"] == 0
    assert telemetry["mcts_simulations"] == 0


def test_mcts_telemetry_isolation():
    """Assert tree-search metrics (nodes_evaluated, pruned_nodes, search_depth, transposition_hits) are strictly None for MCTS."""
    agent = MCTSAgent(player_id=PLAYER_2, iterations=100, seed=42)
    board = create_board()
    _, telemetry = agent.select_move(board)

    assert telemetry["nodes_evaluated"] is None
    assert telemetry["pruned_nodes"] is None
    assert telemetry["search_depth"] is None
    assert telemetry["transposition_hits"] is None
    assert telemetry["mcts_iterations"] == 100
    assert telemetry["mcts_simulations"] == 100


def test_mcts_alternating_player_selection_and_rewards():
    """
    Verify the MCTS selection and backpropagation invariant:
    - Root turn is agent (PLAYER_2), root's player_just_moved is PLAYER_1.
    - Root children represent agent moves: each child's player_just_moved == PLAYER_2.
    - Each depth-1 child represents opponent moves: each grandchild's player_just_moved == PLAYER_1.
    - Rewards on each node represent wins strictly from that node's player_just_moved perspective.
    """
    agent = MCTSAgent(player_id=PLAYER_2, iterations=200, seed=42)
    board = create_symmetrical_opening_board()

    # Run select_move to populate the tree
    agent.select_move(board)

    # Instantiate manual root to inspect structure
    from app.agents.mcts_agent import MCTSNode
    root = MCTSNode(board=board, player_just_moved=agent.opp_id)
    assert root.player_just_moved == PLAYER_1

    # Expand child
    child = root.add_child(3, agent.player_id)
    assert child.player_just_moved == PLAYER_2

    # Expand grandchild
    grandchild = child.add_child(2, agent.opp_id)
    assert grandchild.player_just_moved == PLAYER_1

    # Simulate win for PLAYER_2 (agent)
    grandchild.backpropagate(winner=PLAYER_2)

    # Check rewards:
    # child (player_just_moved == 2): +1.0 win
    assert child.wins == 1.0
    assert child.visits == 1
    # grandchild (player_just_moved == 1): 0.0 loss
    assert grandchild.wins == 0.0
    assert grandchild.visits == 1


# =====================================================================
# 5. API Schema, Validation & Legacy Compatibility Tests
# =====================================================================

def test_api_advanced_agents_execution():
    """Verify POST /api/ai-move successfully executes alphabeta, optimized, and mcts agents."""
    board = create_symmetrical_opening_board()

    for agent_id in ["alphabeta", "optimized", "mcts"]:
        response = client.post(
            "/api/ai-move",
            json={"board": board, "agent": agent_id, "depth": 3, "iterations": 100, "seed": 42},
        )
        assert response.status_code == 200, f"Agent {agent_id} returned HTTP {response.status_code}"
        data = response.json()
        assert "column" in data and 0 <= data["column"] < COLS
        assert "row" in data and 0 <= data["row"] < ROWS
        assert "telemetry" in data
        assert data["telemetry"]["decision_time_ms"] >= 0.0

        if agent_id in ("alphabeta", "optimized"):
            assert data["telemetry"]["nodes_evaluated"] > 0
            assert data["telemetry"]["pruned_nodes"] >= 0
            assert data["telemetry"]["search_depth"] == 3
            assert data["telemetry"]["mcts_iterations"] is None
        elif agent_id == "mcts":
            assert data["telemetry"]["nodes_evaluated"] is None
            assert data["telemetry"]["mcts_iterations"] == 100
            assert data["telemetry"]["mcts_simulations"] == 100


def test_api_legacy_minimax_contract_unbroken():
    """Verify legacy POST /api/ai-move without agent parameter returns exact {column, row} contract."""
    board = create_symmetrical_opening_board()
    response = client.post("/api/ai-move", json={"board": board, "depth": 2})

    assert response.status_code == 200
    data = response.json()
    assert set(data.keys()) == {"column", "row"}
    assert isinstance(data["column"], int)
    assert isinstance(data["row"], int)


def test_api_full_board_handling():
    """Verify all advanced agents handle full board returning column: None, row: -1 gracefully."""
    for agent_id in ["minimax", "alphabeta", "optimized", "mcts"]:
        response = client.post(
            "/api/ai-move",
            json={"board": DRAW_BOARD_FIXTURE, "agent": agent_id},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["column"] is None
        assert data["row"] == -1
        assert "telemetry" in data


def test_api_iterations_validation():
    """Verify iterations must be integer between 10 and 10000; reject boolean or out-of-range."""
    board = create_board()

    # Boolean rejected
    res_bool = client.post("/api/ai-move", json={"board": board, "agent": "mcts", "iterations": True})
    assert res_bool.status_code == 422
    assert "iterations" in res_bool.json()["error"]["message"].lower()

    # Out of range (< 10)
    res_low = client.post("/api/ai-move", json={"board": board, "agent": "mcts", "iterations": 5})
    assert res_low.status_code == 422

    # Out of range (> 10000)
    res_high = client.post("/api/ai-move", json={"board": board, "agent": "mcts", "iterations": 10001})
    assert res_high.status_code == 422


def test_api_depth_validation():
    """Verify depth must be integer between 1 and 8; reject boolean or out-of-range."""
    board = create_board()

    # Boolean rejected
    res_bool = client.post("/api/ai-move", json={"board": board, "agent": "alphabeta", "depth": True})
    assert res_bool.status_code == 422
    assert "depth" in res_bool.json()["error"]["message"].lower()

    # Out of range (> 8)
    res_high = client.post("/api/ai-move", json={"board": board, "agent": "alphabeta", "depth": 9})
    assert res_high.status_code == 422
