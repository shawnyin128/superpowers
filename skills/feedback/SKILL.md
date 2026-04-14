---
name: feedback
description: |
  User-triggered feedback mode. When you observe a problem while using the
  system (bug, missing feature, agent misbehavior, performance issue, etc.),
  invoke this to have sp-feedback diagnose and route the fix back into the
  pipeline. Asks clarifying questions before analysis.
author: sp-harness
version: 2.0.0
---

# feedback

Entry point for **Mode B** of sp-feedback (the feedback agent).

Use when you are using a project built with sp-harness and you notice something
is wrong — a bug, a missing feature, an agent that behaves poorly, a
performance issue. Instead of describing it informally, invoke this skill to
get structured diagnosis and routed fixes.

## Step 1: Verify sp-feedback exists

Check `.claude/agents/sp-feedback.md` exists. If not, tell the user to run
`init-project` first to generate the feedback agent.

## Step 2: Capture user observation

Ask the user (if not already stated in the invocation):

> "What did you observe? Describe the problem briefly."

## Step 3: Dispatch sp-feedback in Mode B

Invoke `@agent sp-feedback` with:
- The user's observation
- Mode flag: `"mode": "B"`
- The orchestrator is YOU (the main session)

sp-feedback will:
1. Ask clarifying questions one at a time (what/when/expected/reproducible)
2. Run scoped checklist review based on the user's complaint
3. Auto-execute memory operations (no user gate)
4. Write `.claude/agents/state/active/feedback-actions.json`
5. Present findings grouped by action type

## Step 4: Review auto-executed memory ops

sp-feedback has already executed `memory_update` and `memory_compact` actions
before returning. Read the results from `.claude/agents/state/active/memory-ops-log.json`
and print a brief summary:

```
Auto-executed memory operations:
  memory_update: X applied, Y rejected by target agent
  memory_compact: Z agents compacted (before/after line counts)
```

This is FYI only — no confirmation needed. Agents decide via structured
checklists. Details auditable in memory-ops-log.json.

## Step 5: Per-batch confirmation (HARD-GATE for remaining actions)

For actions that DO require user input (new_feature, fix_feature, manual):

- "Append N new features / M fix features to features.json?"
- "Manual items: {list} — review yourself later"

Wait for confirmation before applying.

## Step 6: Execute approved actions

For confirmed batches:
- **new_feature**: append to `.claude/features.json` with `passes: false`.
  Suggest user run `/brainstorming` to flesh out design.
- **fix_feature**: append to `.claude/features.json`. Will be picked up by
  feature-tracker on next loop.
- **manual**: print to user, no automated action.

## Rules

1. Never skip the clarifying questions phase — user complaints are often vague.
2. Memory operations auto-execute before user gates. No confirmation needed.
3. new_feature / fix_feature / manual require per-batch confirmation.
4. Never write directly to another agent's MEMORY.md — always dispatch with
   the Append/Compact Checklist context.
5. After execution, summarize what was auto-executed, what was confirmed,
   and what was deferred.
