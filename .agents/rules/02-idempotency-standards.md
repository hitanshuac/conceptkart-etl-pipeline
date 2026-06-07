# Rule 02: Idempotency Standards

**Mandate:** All database operations (specifically DuckDB) MUST be idempotent. 

1. **INSERT OR REPLACE:** When ingesting data, never use standard `INSERT` statements which could crash or create duplicates upon a network retry. Always utilize `INSERT OR REPLACE` logic.
2. **Crash Resilience:** The data pipelines must be able to fail and restart at any point without duplicating records or corrupting the database state.
3. **Write-Ahead Logging:** Ensure DuckDB is configured with Write-Ahead Logging (WAL) to prevent data loss during sudden process termination.
