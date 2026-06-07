---
description: description: Automatically commit and push the current workspace state to GitHub to prevent data loss.
---

# Secure Checkpoint Workflow

1. Ask the user for a brief commit message describing the current state.
2. Execute the Git Manager to securely stage, commit, and push the codebase, automatically handling errors and branch divergence. // turbo
3. Run `python src/capabilities/git_manager.py checkpoint "[User Message]"`
4. Confirm to the user that their files are permanently secured on GitHub.
