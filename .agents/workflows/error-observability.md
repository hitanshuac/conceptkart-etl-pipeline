---
description: Mandatory error logging, monitoring, and context compression workflow.
---

# Error Observability & Remediation Workflow

This workflow forces strict error logging, historical context checking, and resolution documentation to ensure the AI agent never repeats past mistakes, while maintaining strict context window compression constraints.

## Step 1: Pre-Execution Log Verification (Mandatory)
Before generating or modifying any code, the agent MUST:
1. Check for the existence of `data/error_logs.json`. If it does not exist, initialize it.
2. **Database Scaling:** If `data/error_logs.json` becomes too large or inefficient to query, the agent MUST autonomously initialize a local database (e.g., `data/error_metrics.db` via SQLite or DuckDB) to migrate and store all future error context.
3. Read the recent error history (from JSON or DB) to understand past failures and attempted fixes.
4. **DO NOT** repeat strategies that have already been documented as "failed" in the logs.

## Step 2: Context Window Compression (jCodeMunch)
To avoid overloading the LLM context window with raw stack traces and massive log files:
1. Use the **jCodeMunch** MCP Server (configured in `.config/antigravity/mcp.json`) to retrieve only the relevant structural symbols or AST nodes related to the error.
2. Instead of dumping raw file contents, extract and summarize the specific function/class where the failure occurred.
3. Keep log entries concise. Extract the core exception message and the exact line of failure.

## Step 3: Monitor & Log Failures
When an error, test failure, or pipeline crash occurs:
1. Append a new entry to the error log.
2. Format:
   - `timestamp`: Current UTC time.
   - `error_type`: Type of exception.
   - `component`: The function or module that broke (retrieved via jCodeMunch).
   - `stack_trace_summary`: A highly compressed summary of the stack trace.
   - `status`: "UNRESOLVED".

## Step 4: Document the Fix
After successfully resolving an error and passing tests:
1. Return to the error log and update the specific entry.
2. Change `status` to "RESOLVED".
3. Add a `resolution_strategy` field detailing *exactly* what was changed to fix the issue.
4. Keep this resolution brief to conserve future context windows.
