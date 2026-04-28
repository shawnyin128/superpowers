---
name: switch-dev-mode
description: |
  Switch between single-agent and three-agent development modes.
  Reads and updates .claude/sp-harness.json. Generates project-level
  agent files from templates if needed. Use when the user wants to
  change how features are developed.
author: sp-harness
version: 2.0.0
---

# switch-dev-mode

Switch the project's development mode between `single-agent` and `three-agent`.
Handles agent file generation when switching to three-agent if they don't
already exist.

## Steps

1. Read `.claude/sp-harness.json`. If missing, create with default `"single-agent"`.

2. Print current mode:
   ```
   Current dev mode: {dev_mode}
   ```

3. Ask: "Switch to {other_mode}? (yes/no)"
   - `three-agent` → "Switch to single-agent?"
   - `single-agent` → "Switch to three-agent?"

4. If no: stop.

5. If yes: update `dev_mode` in `.claude/sp-harness.json` and write to disk.

## When switching TO `three-agent`:

Check if `.claude/agents/sp-planner.md`, `sp-generator.md`, `sp-evaluator.md` exist:

- **All three exist:** check for **template drift** first (see below).
  If drift detected, warn and offer regenerate before asking about
  configuration. Otherwise print their current configs (model, tools,
  memory, isolation). Ask: "Use existing configuration, or reconfigure?"
  - If reconfigure: for each agent, ask model / tools / memory / isolation
    and rewrite the file using the template + user answers.

- **Missing any:** read template from `${CLAUDE_PLUGIN_ROOT}/agent-templates/{name}.md`,
  replace `{PROJECT_NAME}` and `{PROJECT_CONTEXT}` from CLAUDE.md, write to
  `.claude/agents/{name}.md`. Ask if user wants to customize; if yes, run
  the 4-question flow.

### Template drift detection (v0.7.0+)

For each existing agent file, check these markers to detect stale copies:

| Agent file | Old-format marker (BAD) | New-format marker (EXPECTED) |
|---|---|---|
| `sp-planner.md` | `task-plan.json` or `eval-plan.json` | `<feature-id>.plan.yaml` |
| `sp-generator.md` | `implementation.md` | `<feature-id>.plan.yaml` |
| `sp-evaluator.md` | `eval-report.json` | `eval.rounds[]` or `<feature-id>.plan.yaml` |
| `sp-feedback.md` | `final-eval-report.json` or `iter-N-eval-report.json` | `<feature-id>.plan.yaml` |

If ANY agent has an old marker OR lacks its new marker → **stale**.

Report which agents are stale. The two example bullets reference real
file names (`task-plan.json`, `plan.yaml`, `eval-report.json`) — these
are legitimate domain identifiers being flagged as stale markers, so the
inline R3 disables below intentionally allow them inside glosses.

```output-template
⚠️ Stale agent templates detected:
<!-- lint:disable=R3 -->
  - sp-planner.md (contains task-plan.json, missing plan.yaml)
<!-- lint:disable=R3 -->
  - sp-evaluator.md (contains eval-report.json)

The current plugin expects new-format agents. Running three-agent mode
with stale files will fail.
```

Then ask — decision touch-point per `${CLAUDE_PLUGIN_ROOT}/docs/decision-touchpoint-protocol.md`
(structured menu, plain-language consequences). Re-read each option
line aloud first as if to a colleague unfamiliar with the project; if a
phrase reads like jargon, rewrite it before printing. Also apply the
specific-pattern self-check from `using-sp-harness/SKILL.md` "Output
prose self-check" (project-internal short codes each glossed inline).

```output-template
→ Regenerate the stale agents from current templates?
  · yes  — overwrite each stale `.claude/agents/*.md` with a fresh copy
           from the plugin template; any hand-customization in those
           files is lost (you confirm again before the actual write).
  · no   — keep the stale files; three-agent runs will likely fail
           until you run framework-check or reconcile by hand.
  · diff — print the diff between deployed and template for each stale
           agent, then re-ask yes/no.
```

**Note:** `.claude/agents/sp-feedback.md` should already exist from init-project.
If it's missing, generate it from the template regardless of dev mode.

Also run the drift check for `sp-feedback.md` even when switching TO
single-agent (it's active in both modes). If stale, offer regenerate
using the same yes/no/diff flow.

## When switching TO `single-agent`:

No Planner/Generator/Evaluator subagent configuration needed — main session
plays those roles. The existing `.claude/agents/sp-*.md` files (if any) are
left in place but unused.

`.claude/agents/sp-feedback.md` is still used (feedback agent is independent
of dev mode). Run drift check on it; offer regenerate if stale.

Print: "Single-agent mode. Planner/Generator/Evaluator roles run in main
session. sp-feedback remains active for system-level review."
