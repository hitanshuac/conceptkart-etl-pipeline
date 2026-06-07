# Testing Standards

This rule governs all testing practices across the Agentic Environment. It enforces industry-standard test structure, naming, and the strict prohibition of shipping untested code.

## 1. Never Ship Untested Code
- Every function, route, and pipeline component that is part of a ticket in `05_TICKETS.md` MUST have at least one corresponding test.
- If a ticket has no acceptance criteria, the agent must ask the user to define them before proceeding.
- Pull Requests with zero test coverage on new code MUST be rejected by CI.

## 2. Test Pyramid Enforcement
- **Unit Tests** must form the majority (~70%) of the test suite. They test pure logic in isolation with mocked dependencies.
- **Integration Tests** (~20%) test boundaries between components (e.g., API → database, validator → DLQ).
- **End-to-End Tests** (~10%) test the full user-facing flow. These are the most expensive and should be used sparingly.

## 3. Naming Conventions
- Test files: `test_<module_name>.py` (e.g., `test_compaction.py`)
- Test functions: `test_<feature>_<behavior>_<expected>` (e.g., `test_compaction_strips_filler_prefix_correctly`)
- Test classes (when grouping): `TestCompaction`, `TestDLQRouting`

## 4. Fixture & Setup Standards
- Shared fixtures must be defined in `src/tests/conftest.py`.
- Database tests must use in-memory DuckDB instances (`:memory:`) unless testing persistence specifically.
- API tests must use FastAPI's `TestClient` — never make real HTTP calls in unit tests.
- External API dependencies must be mocked using `unittest.mock` or `pytest-mock`.

## 5. Test Execution Protocol
- Tests must be run after **every** code change, not just at the end of a feature.
- Use `python -m pytest src/tests/ -v --tb=short` as the standard command.
- The CI/CD pipeline (`.github/workflows/main.yml`) must run the full test suite on every push.

## 6. Failure Handling
- If a test fails, the agent must first check `.agents/workflows/error-observability.md` for historical context.
- The agent must fix the **implementation code**, not weaken the test, unless the test itself contains a genuine error.
- After 3 failed debugging iterations on the same test, the agent must flag it for manual user review and move on.
