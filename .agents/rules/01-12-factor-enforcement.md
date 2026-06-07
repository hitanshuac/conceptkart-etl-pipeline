# Rule 01: 12-Factor Enforcement

**Mandate:** API keys, database credentials, and any environmental configurations MUST NEVER be hardcoded within the `src/` directory or any other source files.

1. **Environment Variables:** All configuration must be read from environment variables.
2. **Secrets:** In local development, utilize `.env` or `.secrets/` files. These files are explicitly ignored by version control.
3. **Stateless Processes:** The application must be capable of executing statelessly, deriving its context solely from the provided environment at runtime.

Any pull request or code change attempting to hardcode a secret will be immediately rejected.
