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
