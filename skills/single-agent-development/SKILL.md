---
name: single-agent-development
description: |
  Feature development with a single agent playing all three roles (Planner,
  Generator, Evaluator) sequentially. Same pipeline as three-agent-development
  but without subagent dispatch — all phases run in the main session.
  Use when subagent overhead is unnecessary or for simpler projects.
author: sp-harness
version: 2.1.0
---

# Single-Agent Development

One agent develops a feature by switching between three roles sequentially.
The pipeline is IDENTICAL to three-agent-development — same shared YAML
plan file, same schemas, same terminal output conventions. The only
difference: roles switch in one session instead of dispatching three
subagents.

```
[Planner role]   → writes <feature-id>.plan.yaml (problem, steps, decisions)
                   → terminal: condensed summary + ask low-confidence decisions
[Generator role] → reads plan.yaml, implements, appends execution sections
                   → NO terminal output
[Evaluator role] → reads plan.yaml, runs tests, appends eval.rounds[]
                   → terminal: closure + tests + blockers-or-optimization
                   → iterate (loop back to Generator) or merge
```

---

## File Structure

Single shared YAML per feature: `.claude/agents/state/active/<feature-id>.plan.yaml`.
Schema defined in `${CLAUDE_PLUGIN_ROOT}/docs/plan-file-schema.md`.

```
.claude/agents/state/
├── active/
│   └── <feature-id>.plan.yaml
└── archive/
    └── <feature-id>/
        ├── <feature-id>.plan.yaml
        ├── <feature-id>.iter-<N>.plan.yaml  (if replanned)
        └── supersession.json                 (if feature has supersedes)
```

Permanent tests at `tests/<feature-id>/` — written by Evaluator role,
survive merge as regression guards.

---

## Step 0: Declare session language

**MUST run this before Step 1.** Read `.claude/sp-harness.json` and
extract the `language` field (default `match-input` if missing).
Print `Session language: <code>` as the first line of your reply for
this session. Then follow the rule for the remainder of the session:

- `match-input` (default) — reply in the user's input language each
  turn.
- Any specific code (`en`, `zh`, `ja`, ...) — pin replies to that
  language regardless of input.

In either mode, no code-mixing within a single message. Identifiers
(file paths, command names, field names, product names, IDs) stay in
their original form. Files / commits / docs / plan YAML always
English regardless of chat language.

This rule mirrors the one in feature-tracker Step 1 and the subagent
templates; it lives here because this SKILL is sometimes invoked
directly without going through feature-tracker.

---

## Step 1: Select Feature

Read the feature from `.claude/features.json`. Read context: `CLAUDE.md`,
spec document referenced in CLAUDE.md. Check `active/` for interrupted state.

---

## Step 2: Planner Role

<EXTREMELY-IMPORTANT>
Switch to Planner mindset. You are designing, NOT implementing. Do not
write any code. Produce plans only.
</EXTREMELY-IMPORTANT>

Invoke `Skill(sp-harness:sp-planner-role)` with args `feature_id=<feature-id>`.
The role skill owns Phase 1 (implicit-requirement gap analysis), Phase 2
(plan YAML production), and Phase 3 (terminal summary with the canonical
fence and the 6-item self-check before print). The orchestrator does not
duplicate any of that content.

After the role skill returns, read `<feature-id>.plan.yaml` and confirm
every `decisions[].user_decision` field is populated for any
`ask_user: true` item. Do NOT proceed to Step 3 until those fields are
filled in by the user's choice.

---

## Step 3: Generator Role

<EXTREMELY-IMPORTANT>
Switch to Generator mindset. You are implementing, NOT designing. Follow
the plan. Do not redesign. If the plan seems wrong, mark the step
BLOCKED — do not fix the plan yourself.
</EXTREMELY-IMPORTANT>

Invoke `Skill(sp-harness:sp-generator-role)` with args `feature_id=<feature-id>`.
The role skill owns the per-step TDD cycle, the
`[module]: description` commit-after-each-step discipline, and the
`execution` / `unplanned_changes` / `flags_for_eval` appends to the plan
YAML.

Generator produces no terminal output. Proceed directly to Step 4.

---

## Step 4: Evaluator Role

<EXTREMELY-IMPORTANT>
Switch to Evaluator mindset. You are a RED TEAM. Your job is to FIND
PROBLEMS in code YOU JUST WROTE. This is the hardest part — you must
actively fight the urge to approve your own work.

**Self-persuasion is your enemy.** RESIST.
</EXTREMELY-IMPORTANT>

Invoke `Skill(sp-harness:sp-evaluator-role)` with args `feature_id=<feature-id>`.
The role skill owns the mandatory adversarial protocol (Self-Persuasion
Traps re-read, Cool-down, Zero-issue rule), Round determination, Round 1
closure + test design + execution, Round 2+ replay and regression
detection, the optional Optimization pass, and the per-verdict terminal
summary (ITERATE / PASS+optimization fences). Both terminal fences are
decision touch-points per
`${CLAUDE_PLUGIN_ROOT}/docs/decision-touchpoint-protocol.md`.

After the role skill returns, read the latest `eval.rounds[N]` entry
from `<feature-id>.plan.yaml`. Use its `verdict` field — `PASS` or
`ITERATE` — and the user's response captured by the role skill's
terminal prompt to dispatch Step 5.

---

## Step 5: Handle Verdict

### (a) on ITERATE — fix and re-eval
Switch back to Generator role (Step 3). Address blockers. After Generator
re-runs, switch to Evaluator role (Step 4, Round N+1).

### (b) on ITERATE — force-merge
Skip remaining rounds, go to MERGE path below.

### (c) on ITERATE — replan
Archive current plan file to `archive/<feature-id>/<feature-id>.iter-<N>.plan.yaml`.
Return to Step 2 with `iteration: N+1`.

### (a) on PASS — merge
1. Mark feature passing:
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/skills/manage-features/scripts/mutate.py" \
     mark-passing <feature-id>
   ```
2. Move `active/<feature-id>.plan.yaml` → `archive/<feature-id>/<feature-id>.plan.yaml`
3. If `supersedes` non-empty: extract spec's Supersession Plan, save to
   `archive/<feature-id>/supersession.json`
4. Commit using the humanized template. Fetch display_name first:
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/skills/manage-features/scripts/query.py" \
     get <feature-id> --format=json
   ```
   Parse `display_name` (fall back to `<feature-id>` if missing). Then:
   `[features]: complete "<display_name>" (<feature-id>)`
5. Return to feature-tracker

### (b) on PASS — optimize
Switch back to Generator role, apply optimization suggestions. Then back
to Evaluator (Round N+1 for verification).

### Max Rounds Escalation

If Round 6 would trigger, write blocker "Max rounds exceeded", ITERATE
verdict, and print:

**Self-check before print:** even on this rare escalation path, apply
the runtime self-check from `using-sp-harness/SKILL.md` "Output prose
self-check" — every first-occurrence short code is glossed inline,
language pin honored, no fancy quotes. Option lines are full sentences
of consequence, never bare labels.

```output-template
⚠️ 5 rounds completed and blockers still present. The plan may be
   fundamentally wrong — five attempts have not converged.

→ Your call:
  (a) Try one more iteration — Generator role addresses current
      blockers; we may converge or hit the same wall again.
  (b) Replan from scratch — current plan is archived, Planner role
      re-runs with full knowledge of the round history (best when
      blockers look like the wrong design, not buggy execution).
  (c) Force-merge as-is — ship with the listed blockers open, you
      own the risk; pick this only if blockers turn out to be
      cosmetic or out-of-scope.
```

---

## When to Use Single-Agent vs Three-Agent

| Factor | Single-Agent | Three-Agent |
|--------|-------------|-------------|
| Project complexity | Simple to moderate | Complex |
| Context sharing | Roles share context (pro: continuity; con: self-persuasion) | Isolated (pro: independence; con: context loss) |
| Token cost | Lower (one session) | Higher (3 subagents) |
| Evaluation rigor | Weaker (self-assessment bias) | Stronger (independent evaluator) |
| Speed | Faster (no dispatch overhead) | Slower (subagent startup) |

**Default recommendation:** single-agent for most projects (faster, lower
token cost, simpler dispatch). Switch to three-agent when correctness
matters enough to pay for adversarial review by an isolated evaluator —
e.g. complex refactors, security-sensitive code, or projects where
subtle regressions are costly.

To switch: use `sp-harness:switch-dev-mode`.
