---
phase: 1
plan: 1
wave: 1
gap_closure: false
---

# Plan 1.1: Foundation, API Contracts & Standardized Error Handling

## Objective
Establish the modular package architecture (`backend/app/`), formalize Pydantic data schemas, configure CORS and centralized exception handlers for the PRD's standardized error envelope (`{"error": {"code": "...", "message": "..."}}`), implement the canonical `GET /api/health` and `GET /api/agents` endpoints, and verify environment integration with automated tests while preserving existing functionality.

## Context
Load these files for context:
- [.gsd/SPEC.md](file:///c:/Users/MANAV/Desktop/FAI-project/Adversarial-Game-Playing-Agent-/.gsd/SPEC.md)
- [.gsd/REQUIREMENTS.md](file:///c:/Users/MANAV/Desktop/FAI-project/Adversarial-Game-Playing-Agent-/.gsd/REQUIREMENTS.md)
- [.gsd/ARCHITECTURE.md](file:///c:/Users/MANAV/Desktop/FAI-project/Adversarial-Game-Playing-Agent-/.gsd/ARCHITECTURE.md)
- [backend/main.py](file:///c:/Users/MANAV/Desktop/FAI-project/Adversarial-Game-Playing-Agent-/backend/main.py)
- [backend/requirements.txt](file:///c:/Users/MANAV/Desktop/FAI-project/Adversarial-Game-Playing-Agent-/backend/requirements.txt)
- [frontend/src/services/api.js](file:///c:/Users/MANAV/Desktop/FAI-project/Adversarial-Game-Playing-Agent-/frontend/src/services/api.js)

---

## Tasks

<task type="auto">
  <name>Task 1: Package Structure, Schemas & Standardized Exception Handlers</name>
  <files>
    backend/app/__init__.py
    backend/app/schemas/__init__.py
    backend/app/schemas/error_schemas.py
    backend/app/schemas/game_schemas.py
    backend/app/schemas/agent_schemas.py
  </files>
  <action>
    1. Initialize the `backend/app/` module and `backend/app/schemas/` directory.
    2. In `error_schemas.py`, define Pydantic models for:
       - `ErrorDetail`: `code: str`, `message: str`
       - `ErrorResponse`: `error: ErrorDetail`
    3. In `game_schemas.py`, define initial request/response models for:
       - `GameCreateRequest`: `mode: str = "human_vs_ai"`, `ai_agent: str = "alphabeta"`, `difficulty: str = "medium"`, `starting_player: int = 1`
       - `MoveRequest`: `column: int`
       - `TelemetryMetrics`: `decision_time_ms: float`, `nodes_evaluated: Optional[int] = None`, `pruned_nodes: Optional[int] = None`, `search_depth: Optional[int] = None`, `transposition_hits: Optional[int] = None`, `mcts_iterations: Optional[int] = None`, `mcts_simulations: Optional[int] = None`, `candidate_scores: Optional[List[Dict[str, Any]]] = None`
    4. In `agent_schemas.py`, define models for:
       - `AgentMetadata`: `id: str`, `name: str`, `description: str`, `type: str`, `supported_parameters: Dict[str, Any]`, `difficulty_levels: List[str]`
       - `AgentListResponse`: `agents: List[AgentMetadata]`

    AVOID: Exposing Python tracebacks or default FastAPI validation errors in raw format.
    USE: Explicit Pydantic models with field validations and default values matching PRD §12.
  </action>
  <verify>
    python -c "from app.schemas.error_schemas import ErrorResponse; from app.schemas.game_schemas import TelemetryMetrics; print('Schemas valid')"
  </verify>
  <done>
    All schemas load cleanly without circular dependencies, and `TelemetryMetrics` correctly supports `None` for inapplicable metrics.
  </done>
</task>

<task type="auto">
  <name>Task 2: API Router Integration, Exception Handlers & Dual Health Endpoints</name>
  <files>
    backend/app/api/__init__.py
    backend/app/api/health_routes.py
    backend/app/api/agent_routes.py
    backend/main.py
  </files>
  <action>
    1. In `health_routes.py`:
       - Implement canonical `GET /api/health` returning `{"status": "ok"}`.
       - Implement backward-compatible alias `GET /health` returning `{"status": "ok"}`.
    2. In `agent_routes.py`:
       - Implement `GET /api/agents` returning metadata for all 6 PRD-specified agents:
         - `random`: Random baseline (supported parameters: `seed`)
         - `greedy`: 1-ply immediate win/threat heuristic
         - `minimax`: Depth-limited minimax (parameters: `depth`)
         - `alphabeta`: Minimax with alpha-beta pruning (parameters: `depth`)
         - `optimized`: Optimized alpha-beta with move ordering and transposition table (parameters: `depth`)
         - `mcts`: Monte Carlo Tree Search with UCT (parameters: `iterations`, `exploration_constant`)
    3. In `backend/main.py`:
       - Mount the health and agent routers.
       - Add custom exception handlers for:
         - `RequestValidationError`: formats request validation errors to `ErrorResponse(error={"code": "VALIDATION_ERROR", "message": "..."})`
         - `HTTPException`: formats status codes to `ErrorResponse(error={"code": "...", "message": "..."})`
         - Generic unhandled `Exception`: returns 500 with `ErrorResponse(error={"code": "INTERNAL_ERROR", "message": "An unexpected error occurred."})` without leaking internal tracebacks.
       - Preserve the existing `POST /api/ai-move` endpoint unchanged so current frontend remains functional during transition.
  </action>
  <verify>
    uvicorn backend.main:app --port 8000 (verify GET /api/health, GET /health, GET /api/agents, and verify error payload on malformed request)
  </verify>
  <done>
    `GET /api/health` and `GET /health` return 200 `{"status": "ok"}`; `GET /api/agents` returns 6 agents; malformed input returns `{"error": {"code": "...", "message": "..."}}`.
  </done>
</task>

<task type="auto">
  <name>Task 3: Automated Foundation & Contract Tests</name>
  <files>
    backend/tests/__init__.py
    backend/tests/test_foundation.py
  </files>
  <action>
    1. Create `backend/tests/test_foundation.py` using `fastapi.testclient.TestClient`.
    2. Test cases:
       - `test_canonical_health`: asserts `GET /api/health` returns status 200 and `{"status": "ok"}`.
       - `test_compat_health`: asserts `GET /health` returns status 200 and `{"status": "ok"}`.
       - `test_agent_metadata_catalog`: asserts `GET /api/agents` lists 6 agents with required keys (`id`, `name`, `description`).
       - `test_standardized_error_format_validation`: asserts invalid payload to a route produces HTTP 422 with `{"error": {"code": "VALIDATION_ERROR", ...}}` and no stack trace.
       - `test_standardized_error_format_404`: asserts missing route returns HTTP 404 with standardized error schema.
       - `test_backward_compat_ai_move`: asserts existing `POST /api/ai-move` continues to respond correctly with column and row.
    3. Execute pytest suite and ensure 100% pass rate.
  </action>
  <verify>
    pytest backend/tests/test_foundation.py -v
  </verify>
  <done>
    All foundation tests pass cleanly; error envelope format validated; existing prototype functionality verified.
  </done>
</task>

---

## Must-Haves
After all tasks complete, verify:
- [x] `GET /api/health` and `GET /health` both respond with `{"status": "ok"}`.
- [x] `GET /api/agents` returns the catalog of 6 AI agents.
- [x] Error responses strictly conform to `{"error": {"code": "...", "message": "..."}}`.
- [x] Existing `POST /api/ai-move` endpoint remains backward-compatible and functional.
- [x] All automated tests in `backend/tests/test_foundation.py` pass.

## Success Criteria
- [x] All 3 tasks verified passing.
- [x] Must-haves confirmed.
- [x] No regressions in existing code.
