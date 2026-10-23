import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

# Ensure backend root is on sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from main import app
from app.schemas.game_schemas import TelemetryMetrics

client = TestClient(app)

def test_canonical_health_endpoint():
    """Verify PRD §12.1 canonical health endpoint."""
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_backward_compatible_health_endpoint():
    """Verify backward-compatible root health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_agent_metadata_catalog():
    """Verify PRD §12.6 agent metadata endpoint returns all 6 specified algorithms."""
    response = client.get("/api/agents")
    assert response.status_code == 200
    data = response.json()
    assert "agents" in data
    agents = data["agents"]
    assert len(agents) == 6

    expected_ids = {"random", "greedy", "minimax", "alphabeta", "optimized", "mcts"}
    actual_ids = {agent["id"] for agent in agents}
    assert actual_ids == expected_ids

    for agent in agents:
        assert isinstance(agent["name"], str) and len(agent["name"]) > 0
        assert isinstance(agent["description"], str) and len(agent["description"]) > 0
        assert isinstance(agent["type"], str) and len(agent["type"]) > 0
        assert isinstance(agent["supported_parameters"], dict)
        assert isinstance(agent["difficulty_levels"], list)

def test_standardized_error_format_on_validation_failure():
    """Verify PRD §12.9 standardized error schema on validation failure without stack traces."""
    response = client.post("/api/ai-move", json={"board": "invalid_board_format", "depth": "not_an_int"})
    assert response.status_code == 422
    data = response.json()
    assert "error" in data
    assert "code" in data["error"]
    assert "message" in data["error"]
    assert data["error"]["code"] == "VALIDATION_ERROR"
    # Ensure raw internal details or tracebacks are suppressed
    assert "Traceback" not in response.text
    assert "pydantic" not in response.text.lower() or "board" in data["error"]["message"].lower()

def test_standardized_error_format_on_not_found():
    """Verify standardized error envelope on 404 Not Found."""
    response = client.get("/api/non-existent-route-for-testing")
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "NOT_FOUND"
    assert "Traceback" not in response.text


def test_domain_exception_handler_returns_standard_envelope():
    """Safeguard 2 verification: Verify domain exceptions map to PRD §12.9 standard error format."""
    from app.core.validation import ColumnFullException
    
    @app.get("/api/test-domain-error-route")
    def _test_route():
        raise ColumnFullException(code="INVALID_MOVE", message="The selected column is full.")

    response = client.get("/api/test-domain-error-route")
    assert response.status_code == 400
    assert response.json() == {
        "error": {
            "code": "INVALID_MOVE",
            "message": "The selected column is full."
        }
    }


def test_unexpected_exception_suppresses_stack_trace():
    """Safeguard 2 verification: Verify unhandled 500 exceptions do not leak stack traces or internals."""
    @app.get("/api/test-unhandled-internal-error")
    def _test_unhandled():
        raise RuntimeError("Secret internal failure with private path details C:\\Sensitive\\Data")

    client_with_500 = TestClient(app, raise_server_exceptions=False)
    response = client_with_500.get("/api/test-unhandled-internal-error")
    assert response.status_code == 500
    data = response.json()
    assert data == {
        "error": {
            "code": "INTERNAL_ERROR",
            "message": "An unexpected internal server error occurred."
        }
    }
    assert "Traceback" not in response.text
    assert "RuntimeError" not in response.text
    assert "Sensitive" not in response.text

def test_backward_compatibility_ai_move():
    """Verify existing prototype endpoint POST /api/ai-move preserves functional compatibility."""
    empty_board = [[0 for _ in range(7)] for _ in range(6)]
    response = client.post("/api/ai-move", json={"board": empty_board, "depth": 2})
    assert response.status_code == 200
    data = response.json()
    assert "column" in data
    assert "row" in data
    assert isinstance(data["column"], int)
    assert 0 <= data["column"] < 7
    assert isinstance(data["row"], int)
    assert 0 <= data["row"] < 6

def test_telemetry_schema_allows_null_for_inapplicable_metrics():
    """Verify TelemetryMetrics supports None for inapplicable metrics and preserves measured 0."""
    metrics_random = TelemetryMetrics(
        decision_time_ms=1.2,
        nodes_evaluated=None,
        pruned_nodes=None,
        search_depth=None,
    )
    assert metrics_random.nodes_evaluated is None
    assert metrics_random.pruned_nodes is None

    metrics_alphabeta = TelemetryMetrics(
        decision_time_ms=25.4,
        nodes_evaluated=520,
        pruned_nodes=0,  # Preserves measured zero!
        search_depth=4,
    )
    assert metrics_alphabeta.pruned_nodes == 0
    assert metrics_alphabeta.nodes_evaluated == 520
