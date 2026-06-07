# Workflow: Test Automation & Test Plan Generation

**Trigger:** Mandatory after every code change. Also invocable via `/ask run @[.agents/workflows/test-automation.md]`

## Objective
Eliminate the token-burn cycle of "write code → manually write tests → debug → refactor → retest" by automating test plan generation from ticket acceptance criteria. This workflow enforces the industry-standard **Red-Green-Refactor** loop and the **Test Pyramid**.

## Industry Standard: The Testing Protocol

### The Test Pyramid (Mandatory Structure)
```
        /  E2E  \          ← Fewest: Browser/API integration tests
       / Integ.  \         ← Middle: Cross-component contract tests
      /   Unit    \        ← Most: Pure function/method tests
```
- **Unit Tests (70%):** Test individual functions in isolation. Mock all external dependencies.
- **Integration Tests (20%):** Test component boundaries (e.g., FastAPI route → DuckDB, Pydantic model → quarantine DLQ).
- **E2E Tests (10%):** Test the full user-facing flow. Use sparingly — they are slow and expensive.

### Red-Green-Refactor Loop
1. **Red:** Write a failing test *before* writing the implementation code.
2. **Green:** Write the minimum code to make the test pass.
3. **Refactor:** Clean up the code while keeping all tests green.

## Execution Steps

### Phase 1: Test Plan Generation
1. Read `05_TICKETS.md` and extract the **Acceptance Criteria** for the current ticket.
2. For each acceptance criterion, generate one or more test case descriptions.
3. Output a `test_plan.md` in the project's `docs/` directory listing every test case with:
   - **Test Name** (descriptive, using `test_<feature>_<behavior>_<expected>` naming convention)
   - **Test Type** (Unit / Integration / E2E)
   - **Setup** (what fixtures or mocks are needed)
   - **Action** (what operation is performed)
   - **Assertion** (what the expected outcome is)
4. Present the test plan to the user for review before generating code.

### Phase 2: Test Scaffold Generation
1. Generate pytest files in `src/tests/` following the naming convention `test_<module_name>.py`.
2. Each test function must have a docstring explaining what it validates.
3. Use `pytest` fixtures for setup/teardown. Do not duplicate setup code across tests.
4. For DuckDB tests, use an in-memory database (`:memory:`) to avoid file system side effects.
5. For API tests, use FastAPI's `TestClient` for synchronous endpoint testing.

### Phase 3: Execution & Observability
1. Run `python -m pytest src/tests/ -v --tb=short` after every code change.
2. If tests fail:
   - Execute `.agents/workflows/error-observability.md` to log the failure.
   - Read the error log to understand if this failure has occurred before and what strategy was used.
   - Fix the code (not the test, unless the test itself is wrong).
   - Re-run. Do not proceed to the next ticket until all tests pass.
3. If tests pass, mark the ticket's acceptance criteria as completed in `05_TICKETS.md`.

### Phase 4: Coverage Gate (Optional)
1. Run `python -m pytest --cov=src --cov-report=term-missing` to check code coverage.
2. Target: **80% minimum line coverage** for new code.
3. If coverage drops below threshold, add missing test cases before proceeding.

## Token Conservation Rules
To avoid burning tokens on test debugging loops:
1. **Never generate more than 5 test files in a single pass.** Run tests after each file.
2. **Never debug a failing test for more than 3 iterations.** If a test fails 3 times, flag it for user review and move on.
3. **Reuse fixtures aggressively.** Define shared fixtures in `src/tests/conftest.py`.
4. **Keep test output concise.** Use `--tb=short` to minimize traceback noise in the context window.
