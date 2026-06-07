---
name: Local Bootstrapper
description: Workflow to scaffold and verify the local environment before execution.
---

# Bootstrap Workflow

When initiating the workspace or onboarding a new developer/agent, execute these steps sequentially to ensure the 12-Factor App methodology is satisfied locally.

## 1. Verify Factor I (Codebase)
Ensure the repository is fully cloned and the `.agents` folder is intact.

## 2. Verify Factor II (Dependencies)
- Confirm `requirements.txt` exists and all dependencies are pinned.
- Run `pip install -r requirements.txt` inside the virtual environment.
- Confirm `.venv/` is excluded by `.gitignore`.

## 3. Verify Factor III (Config)
- Check if `.secrets` exists. If not, generate it.
- Run a search for leaked API keys inside `src/`. If any are found, immediately purge them and move them to `.secrets`.
- Ensure `.gitignore` is active and blocking `.secrets/`, `.env`, and `data/`.

## 4. Verify Product Design Gate
- Confirm that `.agents/product/templates/` exists and contains all 5 templates (`01_PRD.md`, `02_TAD.md`, `03_SECURITY.md`, `04_FRONTEND.md`, `05_TICKETS.md`).
- If the user is building a new project, execute `.agents/workflows/generate-product-docs.md` to populate them before allowing any code generation.

## 5. Verify Factor VI (Processes)
- Start the ASGI server (e.g., `uvicorn src.server:app`).
- Validate that the router accepts stateless requests and successfully pushes telemetry via lock-free queues.

## 6. Verify Factor XI (Logs)
- Ensure the `data/` directory exists (with `.gitkeep`).
- Confirm `pipeline_metrics.db` is being generated and that Parquet files populate inside `data/quarantine_*` on failure.

## 7. Verify Local Enforcement (Pre-commit)
- Confirm `.pre-commit-config.yaml` exists at the repo root.
- Run `pre-commit install` to ensure hooks are active.
- Run `ruff check .` and `ruff format --check .` to validate the codebase passes linting.

## 8. Verify Testing Infrastructure
- Confirm `src/tests/` exists with at least one test file.
- Run `python -m pytest src/tests/ -v` to ensure all existing tests pass.
- If tests fail, execute `.agents/workflows/error-observability.md` to log and diagnose the failures.
