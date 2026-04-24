---
name: three-agent-development
description: |
  Feature-level orchestration with three independent agents: Planner (design),
  Generator (execution), and Evaluator (quality assessment). Agents communicate
  through a single shared YAML plan file per feature. User reviews condensed
  terminal output at three touch points: Plan review, per-round Eval review,
  and Optimization review. Explicitly triggered by feature-tracker or user.
author: sp-harness
version: 3.0.0
---

# Three-Agent Development

Three independent agents develop a feature through a shared YAML plan file.
Each agent reads and appends to the same file; the orchestrator drives the
flow and manages user interaction at three touch points.

```
Planner   → writes plan.yaml (problem, steps, decisions)
            → terminal: condensed summary + ask for low-confidence decisions
            → user decides → orchestrator fills user_decision
Generator → reads plan.yaml, implements, appends execution/unplanned/flags
            → NO terminal output (invisible to user)
Evaluator → reads plan.yaml, runs tests, appends eval.rounds[]
            → terminal: closure + tests + blockers-or-optimization
            → user decides → iterate (back to Generator) or merge
```

---

## File Structure

Single shared YAML per feature: `.claude/agents/state/active/<feature-id>.plan.yaml`.
Schema defined in `docs/plan-file-schema.md`.

Active work lives in `active/`. Completed features archive to `archive/<feature-id>/`.

```
.claude/agents/state/
├── active/
│   └── <feature-id>.plan.yaml        ← the shared file
└── archive/
    └── <feature-id>/
        ├── <feature-id>.plan.yaml    ← final plan file
        ├── <feature-id>.iter-<N>.plan.yaml  (if replanned)
        └── supersession.json          (if feature has supersedes)
```

Permanent tests (written by Evaluator) live at `tests/<feature-id>/` and
survive as regression guards after merge.

---

## Step 1: Select Feature

Read the feature from `.claude/features.json` (passed by feature-tracker, or
specified by user). Read context: `CLAUDE.md`, spec document referenced in
CLAUDE.md's Design Docs section (if any). Check `active/` for in-progress
state from a prior interrupted session.

---

## Step 2: Dispatch Planner

Dispatch `@agent sp-planner`. It runs as Opus with writing-plans pre-loaded
and project memory enabled.

Planner will:
1. Discover implicit requirements (gap analysis, root-cause check for bugfixes)
2. Write `<feature-id>.plan.yaml` with `problem`, `steps`, `decisions`
3. Print a condensed terminal summary (≤ 30 lines)

### Touch Point 1: User reviews Plan

Planner's terminal output ends with one of:

- **Multi-choice ask** (if any decision has `ask_user: true`): user picks
  option for each high-gravity decision.
- **Confirmation** (if all decisions are high-confidence): user says
  yes/no/adjust.

<HARD-GATE>
The orchestrator (YOU — not the Planner subagent) MUST:

1. Wait for user response to Planner's ask.
2. For each `ask_user: true` decision, capture the user's choice.
3. Write the user's choice into `decisions[].user_decision` in the plan
   YAML file. Use `yq` or direct edit (preserve schema).
4. Do NOT dispatch Generator until all `ask_user: true` decisions are
   filled. If user chose "adjust", go back to Step 2 (re-dispatch Planner
   with the user's feedback).
</HARD-GATE>

---

## Step 3: Dispatch Generator

Dispatch `@agent sp-generator`. It runs as Sonnet in an isolated worktree.

Generator will:
1. Read `<feature-id>.plan.yaml` (Planner section + user_decision values)
2. Execute `steps[]` via `sp-harness:subagent-driven-development`
3. Append `execution`, `unplanned_changes`, `flags_for_eval` sections
4. **No terminal output** — user does not see Generator

After Generator completes, proceed immediately to Evaluator. Do NOT pause
for user confirmation between Generator and Evaluator — there is no
user-facing Generator review.

---

## Step 4: Dispatch Evaluator

Dispatch `@agent sp-evaluator`. It runs as Opus with project memory.

Evaluator determines Round N (Round 1 if no prior eval; Round N+1 if
previous rounds exist in the file).

Evaluator will:
1. Read plan YAML (all sections so far)
2. Closure check: verify user_decisions honored, no missing plan items,
   confidence mismatches, unplanned changes reviewed
3. Test design + execution: per step, design unit tests from `test_plan`,
   write to `tests/<feature-id>/`, run, record coverage
4. Append new `eval.rounds[]` entry with verdict (PASS or ITERATE)
5. If PASS: also append `eval.optimization` with non-blocking suggestions
6. Print condensed terminal output (≤ 30 lines)

### Touch Point 2: User reviews Eval

Evaluator's terminal output ends with one of:

**If verdict == ITERATE:**
```
→ Your call:
  (a) Send back to Generator to fix (<N> blockers)
  (b) Force-merge (you own the risk)
  (c) Replan
```

**If verdict == PASS (optimization):**
```
→ Your call:
  (a) Accept, merge
  (b) Apply optimizations first, then merge
```

Orchestrator waits for user choice, then routes:

- `(a)` on ITERATE → back to Step 3 (Generator fixes, Round N+1 follows)
- `(b)` on ITERATE → force-merge path (see Step 5 PASS)
- `(c)` on ITERATE → replan: archive current plan file to
  `archive/<feature-id>/<feature-id>.iter-<N>.plan.yaml`, go to Step 2
  with `iteration: N+1`
- `(a)` on PASS → merge (Step 5 PASS)
- `(b)` on PASS → Generator iterates on optimization suggestions, then
  back to Step 4 for re-verification

### Max Rounds Safeguard

If Round 6 would be triggered (5 rounds completed without PASS), the
Evaluator writes a blocker "Max rounds exceeded" and forces ITERATE.
Orchestrator escalates to user explicitly:

```
⚠️ 5 rounds and blockers still present. Plan may be fundamentally wrong.
→ Your call:
  (a) Keep iterating (Round 6)
  (b) Replan
  (c) Force-merge
```

---

## Step 5: Handle Final Verdict

### MERGE (user accepted PASS or force-merged)

1. Mark feature passing:
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/skills/manage-features/scripts/mutate.py" \
     mark-passing <feature-id>
   ```
2. Archive state files:
   - Create `.claude/agents/state/archive/<feature-id>/` if missing
   - Move `active/<feature-id>.plan.yaml` → `archive/<feature-id>/<feature-id>.plan.yaml`
   - Any prior iteration files already in archive stay put
3. If feature has `supersedes` non-empty: extract the spec's
   `## Supersession Plan` section, save to
   `archive/<feature-id>/supersession.json` (schema below). This is what
   sp-feedback Mode A reads to audit stale artifacts later.

```json
{
  "superseded_features": ["..."],
  "source_paths_removed": ["..."],
  "artifacts_handled": [
    {"path": "...", "action": "DELETE|MIGRATE", "destination": "..."}
  ],
  "verification_patterns": ["grep pattern", "..."]
}
```

4. Commit using the humanized template. Fetch display_name first:
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/skills/manage-features/scripts/query.py" \
     get <feature-id> --format=json
   ```
   Parse `display_name` (fall back to `<feature-id>` if missing). Then:
   `[features]: complete "<display_name>" (<feature-id>)`
   (include features.json + archive/)
5. Return to feature-tracker

### REPLAN (user picked (c) on ITERATE)

1. Move current active plan to
   `archive/<feature-id>/<feature-id>.iter-<N>.plan.yaml`
2. Return to Step 2 with `iteration: N+1`

### REJECT (Evaluator hits diverging pattern or user abandons)

1. Stop. Preserve all files in `.claude/agents/state/active/`.
2. Report to user: what was attempted, why it failed, full Evaluator
   assessment.

---

## Agent Independence

1. Planner never reads `execution` or `eval` sections (except on replan,
   reads prior `eval.rounds[].blockers` to inform redesign).
2. Generator never reads `eval` section.
3. Evaluator reads everything but writes only to `eval`.
4. All communication through the single shared YAML file.
5. Each agent refuses to write outside its owned section (per schema's
   Write Permissions table).

---

## User Touch Points Summary

| Touch | When | Decision |
|---|---|---|
| 1 (Plan) | After Planner writes plan.yaml | Pick options for ask_user decisions, or confirm |
| 2 (Eval Round N) | After each Eval round | Fix / force-merge / replan (on ITERATE); Accept / optimize (on PASS) |
| 2' (Max rounds) | After 5 rounds without PASS | Keep iterating / replan / force-merge |

All touch points are multi-choice questions in terminal, ≤ 3 options.
Typical feature has 2-3 touch points. Each touch costs <1 min of user time.

---

## Subagent Definitions

All agents are project-level, generated by init-project from templates at
`${CLAUDE_PLUGIN_ROOT}/agent-templates/`:

- `.claude/agents/sp-planner.md` — Opus, writing-plans preloaded, project memory
- `.claude/agents/sp-generator.md` — Sonnet, TDD + subagent-driven-dev + git-convention, worktree isolation
- `.claude/agents/sp-evaluator.md` — Opus, read-only + Bash + write to plan YAML, project memory

Templates include `{PROJECT_CONTEXT}` slots filled during init-project.

To regenerate or reconfigure after init: use `sp-harness:switch-dev-mode`.
