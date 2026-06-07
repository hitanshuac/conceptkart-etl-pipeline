# Agent Integrations & AI Boundaries

## The Agentic Extractor (Tier 3)

The ConceptKart ETL pipeline leverages LLMs not as the primary engine, but as a robust fallback (Tier 3) when traditional parsing heuristics fail.

### Trigger Conditions
- Tier 1 (HTTP) returns `None` or fails to locate the price.
- Tier 2 (Browser) fails to locate the price in the DOM.
- The pipeline delegates the raw HTML payload to the AI Agent.

### Agent Behavior
- The Agent operates strictly in **JSON Mode**.
- It is instructed to locate the Product Name and the Current Price.
- It must respond with a strict JSON format matching the `ScrapedProduct` schema.
- **Provider Agnostic:** The agent defaults to free providers. It checks for `GROQ_API_KEY`, `OPENROUTER_API_KEY`, or `HF_API_KEY` and routes the request to whichever is available.

## Agentic Governance Rules

When AI agents (e.g., Antigravity, Cursor) operate inside this repository, they are bound by the `.agents/rules/` Control Plane.

1. **Rule 00: No Unauthorized Deletions.** Agents must never perform destructive actions on existing legacy code unless explicitly ordered.
2. **12-Factor Compliance:** Agents must ensure all new features utilize environment variables. Hardcoded credentials are automatically rejected by the pre-commit standards.
3. **Idempotency Standard:** Agents writing SQL must use `INSERT OR REPLACE` or `UPSERT`.
4. **Context Compaction:** Agents analyzing errors must use AST compression (e.g., `jCodeMunch`) to minimize token consumption and maintain context hygiene.
