---
name: feedback
description: |
  User-triggered feedback mode. When you observe a problem while using the
  system (bug, missing feature, agent misbehavior, performance issue, etc.),
  invoke this to have sp-feedback diagnose and route the fix back into the
  pipeline. Asks clarifying questions before analysis.
author: sp-harness
version: 1.0.0
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
3. Write `.claude/agents/state/feedback-actions.json`
4. Present findings grouped by action type

## Step 4: Confirmation gate (orchestrator role)

After sp-feedback returns, read `feedback-actions.json` and print the
findings to the user. For each action batch:

- "Apply N agent memory updates? (target: {agents})"
- "Append N new features / N fix features to features.json?"
- "Manual items: {list} — review yourself later"

Wait for per-batch user confirmation.

## Step 5: Execute approved actions

For confirmed batches:
- **memory_update**: dispatch the target agent (`@agent sp-planner` or
  `@agent sp-evaluator`) with the structured insight from the finding.
  The target agent decides whether/how to write to its own MEMORY.md.
- **new_feature / fix_feature**: append to `.claude/features.json`.
  For new_feature, suggest user run `/brainstorming` to design it.
  For fix_feature, it will be picked up by feature-tracker next loop.
- **manual**: print to user, no automated action.

## Rules

1. Never skip the clarifying questions phase — user complaints are often vague.
2. Never apply actions without per-batch confirmation.
3. Never write directly to another agent's MEMORY.md — always dispatch.
4. After execution, summarize what was applied vs. deferred.
