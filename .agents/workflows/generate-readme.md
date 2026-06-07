---
name: Generate README Workflow
description: Workflow to dynamically generate a GitHub-ready README.md showcasing the Base Agentic Environment and its active skills/rules.
---

# Generate README Workflow

When this workflow is invoked, the agent must generate or update the `README.md` in the root directory following these exact steps:

<workflow_steps>
1. **Analyze the Environment State**
   - Scan `.agents/rules/` to identify the active governance constraints (e.g., 12-factor, idempotency, data-validation).
   - Scan `.agents/skills/` to catalog the currently loaded skills.
   - Scan `.agents/workflows/` to list the automated operational capabilities.

2. **Structure the README**
   The generated `README.md` must contain the following sections:
   - **Header & Badges**: Title ("Antigravity Base Agentic Environment") and relevant tech badges.
   - **Overview**: A brief summary explaining that this is a powerful, extensible "Base Environment" leveraging a Split-Plane Architecture (Control Plane vs. Data Plane).
   - **Dynamic Skill Integration**: A section explicitly mentioning that as new skills are developed in other projects, they are imported here to continually enhance the environment's capabilities.
   - **Current Capabilities**: A dynamic bulleted list of the current Rules, Workflows, and Skills discovered in Step 1.
   - **Directory Structure**: A brief overview of the `src/`, `data/`, `.agents/`, and `.antigravity/` hierarchy.

3. **Generate & Save**
   - Synthesize the findings into a clean, professional markdown format.
   - Write the output to `README.md` in the root directory.

</workflow_steps>
