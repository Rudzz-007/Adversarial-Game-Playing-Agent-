# Architecture Decision Records (ADRs)

## Decisions Log

### ADR-001: Adoption of PRD v1.0 & Modular Architecture
- **Date**: 2026-10-23
- **Status**: Accepted
- **Context**: The project requires building an adversarial game-playing agent platform for Connect Four with educational and benchmarking capabilities.
- **Decision**: Adopt the architecture defined in `docs/Adversarial_Game_Playing_Agent_PRD.pdf`: React 19 + Vite for frontend, Python + FastAPI for backend, a modular `BaseAgent` abstraction, and in-memory game state for initial MVP.
- **Consequences**: Fast development velocity, strict separation of concerns, zero database overhead for MVP, clear contracts for testing.

### ADR-002: In-Memory Storage for Initial MVP
- **Date**: 2026-10-23
- **Status**: Accepted
- **Context**: PRD Section 14 and 15 state database is optional for initial release.
- **Decision**: Implement games and active benchmarks in memory within the FastAPI application state, designing services with clean repository patterns so PostgreSQL can be added without altering business logic.
- **Consequences**: Immediate local execution without container/DB orchestration requirements; data resets when backend process restarts.

### ADR-003: Standardized API Error Envelopes
- **Date**: 2026-10-23
- **Status**: Accepted
- **Context**: PRD §12.9 requires all error responses to strictly follow `{"error": {"code": "...", "message": "..."}}`.
- **Decision**: Configure custom FastAPI exception handlers for `RequestValidationError`, `HTTPException`, and unhandled server errors to format all responses into the specified error schema, suppressing internal stack traces.
- **Consequences**: Consistent, client-friendly error consumption across all endpoints without leaking internal implementation details.

### ADR-004: Health Check Dual-Endpoint Compatibility
- **Date**: 2026-10-23
- **Status**: Accepted
- **Context**: PRD §12.1 designates `GET /api/health` as the standard endpoint, whereas the initial prototype exposed `GET /health`.
- **Decision**: Establish `GET /api/health` as canonical, while retaining `GET /health` as a backward-compatible alias.
- **Consequences**: Full compliance with the PRD contract without breaking legacy scripts or monitoring endpoints.

### ADR-005: State-Based Frontend Navigation
- **Date**: 2026-10-23
- **Status**: Accepted
- **Context**: PRD §13 defines Home, Game, and Analytics views. `package.json` currently only includes `react` and `react-dom`.
- **Decision**: Use React state-based view switching (`activePage = 'home' | 'game' | 'analytics'`) in the root component for MVP rather than adding an external router library.
- **Consequences**: Lean bundle size, instant page transitions, no router configuration overhead. Can be upgraded to full routing later if deep-linking is required.

### ADR-006: Explicit Distinction of Inapplicable Telemetry Metrics
- **Date**: 2026-10-23
- **Status**: Accepted
- **Context**: PRD §6 FR-10 and §13.3 mandate that algorithm-specific metrics must not report misleading zeroes for inapplicable properties.
- **Decision**: Inapplicable metrics will return `null` and render as `"—"` or `"N/A"`, while measured zero values (e.g. 0 pruned nodes or 0 transposition hits) will be preserved as `0`. Concrete empirical metrics and candidate scores are provided without claiming a complete internal reasoning trace.
- **Consequences**: Honest, transparent metric display for educational and benchmarking comparisons.
