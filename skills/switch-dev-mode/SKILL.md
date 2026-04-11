---
name: switch-dev-mode
description: |
  Switch between single-agent and three-agent development modes.
  Reads and updates .claude/sp-harness.json. Use when the user wants
  to change how features are developed.
author: sp-harness
version: 1.0.0
---

# switch-dev-mode

Switch the project's development mode between `single-agent` and `three-agent`.

## Steps

1. Read `.claude/sp-harness.json`. If missing, create with default `"three-agent"`.

2. Print current mode:
   ```
   Current dev mode: {dev_mode}
   ```

3. Ask: "Switch to {other_mode}? (yes/no)"
   - `three-agent` → "Switch to single-agent?"
   - `single-agent` → "Switch to three-agent?"

4. If yes:
   - Update `dev_mode` in `.claude/sp-harness.json`
   - Write to disk
   - Print: "Dev mode switched to {new_mode}."

5. If switching TO `three-agent`:
   - Check if `agents/sp-planner.md`, `agents/sp-generator.md`, `agents/sp-evaluator.md`
     exist (plugin-level or project-level)
   - If project-level overrides exist in `.claude/agents/`, print their config
   - Ask: "Use current subagent configuration, or reconfigure?"
   - If reconfigure: for each agent, ask model / tools / memory / isolation
     and update `.claude/agents/sp-{role}.md`

6. If switching TO `single-agent`:
   - No subagent configuration needed
   - Print: "Single-agent mode uses main session for all roles. No subagent config required."
