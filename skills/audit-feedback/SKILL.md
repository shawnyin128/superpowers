---
name: audit-feedback
description: |
  Read `.claude/sp-feedback-calibration.json` and print precision/recall
  statistics for sp-feedback's health. Invoked periodically to check if
  sp-feedback is over-predicting, under-detecting, or drifting. Does NOT
  modify the calibration file — read-only.
user-invocable: false
---

# audit-feedback

Analyze sp-feedback's self-health via `.claude/sp-feedback-calibration.json`.
Print precision (how often findings were real) and recall (how many real
problems sp-feedback caught).

## Steps

1. Read `.claude/sp-feedback-calibration.json`. If absent, report "No
   calibration data yet — sp-feedback hasn't run Mode A or Mode B."

2. Count entries in `findings_history` by status:
   - `confirmed`: `runtime_validation == "confirmed"`
   - `refuted`: `runtime_validation == "refuted"` OR `user_action == "rejected"`
   - `stale`: `runtime_validation == "stale"`
   - `pending`: `runtime_validation == "pending"`
   - `accepted_pending`: `user_action == "accepted"` AND `runtime_validation == "pending"`

3. Count `missed_detections` entries.

4. Compute metrics:
   - **Precision** = `confirmed / (confirmed + refuted + stale)` (of findings
     with a final verdict, how many were real). `None` if denominator is 0.
   - **Recall (estimate)** = `confirmed / (confirmed + missed)` (of real
     problems, how many sp-feedback caught). `None` if denominator is 0.

5. Before printing, re-read each gloss aloud as if to a colleague
   unfamiliar with the project. If a phrase reads like jargon, rewrite
   it in plain language before emitting. Also apply the specific-pattern
   self-check from `using-sp-harness/SKILL.md` "Output prose self-check"
   (project-internal short codes each glossed inline).

   Print summary:

```output-template
sp-feedback calibration (last N total findings):

Findings: N
  Confirmed: X (runtime or user accepted + later confirmed)
  Refuted: Y (user rejected or runtime contradicted)
  Stale: Z (pending too long, downgraded)
  Pending: W (awaiting validation)
  Accepted (user) but pending runtime: V

<!-- lint:disable=R3 -->
Missed detections: M (real issues sp-feedback did not flag)

Precision: {X}/{X+Y+Z} = P%
Recall (estimate): {X}/{X+M} = R%

Recent trends (last 10 findings): <brief>
<!-- lint:disable=R3 -->
Common missed categories (from the missed-detections list): <grouped>
```

6. Do NOT modify calibration file. Do NOT propose fixes to sp-feedback
   itself — that's out of scope. User reviews stats and decides if
   sp-feedback needs manual tuning (or flags via harness-feedback
   mechanism once that exists).

## When to invoke

This skill is internal and not auto-triggered. Main session may invoke
when:
- User asks "how is sp-feedback doing?"
- After a large batch of features (every 10+ features passed)
- Before major refactors of sp-feedback prompts
- As part of framework-check (optional — can be deferred if stats are noisy)

## Rules

1. Read-only. Never modify calibration.
2. Report `None` or `insufficient data` rather than dividing by zero.
3. Do not count `accepted_pending` as confirmed (user agreement ≠ runtime
   validation).
4. Do not grade sp-feedback subjectively — just report numbers.
