# Antigravity Master OS Bootstrap Directive

**Role:** Principal Platform Engineer & SRE
**Objective:** Scaffold a Universal Agentic Monorepo utilizing a Split-Plane Architecture. Integrate external routing/QA engines and establish a GitHub Actions CI/CD pipeline.

## Phase 0: Pre-flight Conflict Resolution
Before scaffolding or modifying any files, you MUST execute the `.agents/workflows/merge-conflict-resolution.md` workflow. This ensures that the incoming environment acts strictly as a non-destructive enhancer and does not overwrite or delete existing project files.

## Phase 1: Directory Scaffolding
Create the following strict directory structure. Do not deviate.
- `.agents/rules/`
- `.agents/workflows/`
- `.agents/skills/data_engineering/`
- `.agents/skills/backend_routing/`
- `.config/antigravity/`
- `src/`
- `data/`
- `.github/workflows/`

Create a `.gitignore` that explicitly ignores `data/`, `.secrets/`, `.env`, and `*.parquet`.

## Phase 2: Global SRE Rules
Create the following files in `.agents/rules/` using pure Markdown (no XML tags):
1. `01-12-factor-enforcement.md`: Enforce that API keys are never hardcoded in `src/` and must be read from the environment or `.secrets/`.
2. `02-idempotency-standards.md`: Enforce that all database operations (specifically DuckDB) must use `INSERT OR REPLACE` logic to prevent duplicate records on retry.
3. `03-quarantine-dlq.md`: Enforce that any Pydantic validation failures must be routed to `data/quarantine_log.parquet` without crashing the main event loop.

## Phase 3: Workflow Generation
Create the following files in `.agents/workflows/`:
1. `git-discovery-preflight.md`: Instruct the agent to use the GitHub CLI (`gh search repos <keywords>`) to find existing open-source solutions before writing custom code. The agent must halt and ask for human approval before proceeding.
2. `build-etl.md`: Instruct the agent to only load skills from `.agents/skills/data_engineering/` when executed.
3. `build-api-router.md`: Instruct the agent to only load skills from `.agents/skills/backend_routing/` when executed.

## Phase 4: External Integrations (Git & MCP)
Execute the following commands to pull in our required context engines:
1. Run `git init`.
2. Add the multi-agent QA engine as a submodule: `git submodule add https://github.com/study8677/antigravity-workspace-template .external_engines/study8677`
3. Create `.config/antigravity/mcp.json` and add a configuration block for the `jCodeMunch` MCP server to enable O(1) AST code symbol retrieval.

## Phase 5: CI/CD Pipeline (GitHub Actions)
Create a file at `.github/workflows/main.yml`.
Write a standard GitHub Actions pipeline that triggers on `push` to the `main` branch. The pipeline must:
1. Set up Python 3.11.
2. Install standard dependencies (FastAPI, DuckDB, Pydantic).
3. Run a placeholder step: `python -m pytest src/tests/` to validate the Agentic Application cascade and Dead-Letter Queue routing.

## Phase 6: Finalization
Once all files are generated, run the Antigravity synchronization command: `ag refresh --workspace .`