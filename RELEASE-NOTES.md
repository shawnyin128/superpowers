# SP Harness Release Notes

## v1.0.0 (2026-04-08)

Initial release. Forked from [obra/superpowers](https://github.com/obra/superpowers) v5.0.7.

### New Skills

- **init-project** — bootstraps lean CLAUDE.md (~50 lines) with strict template, docs/ directory structure, structured memory, and update-mem hooks
- **update-mem** — maintains memory.md as a state snapshot (Current State / Key Decisions / Findings), not an append-only log
- **feature-tracker** — incremental development orchestrator: picks features from .claude/features.json, loops through three-agent-development, triggers hygiene and feedback
- **three-agent-development** — Planner (Opus) → Generator (Sonnet) → Evaluator (Opus) with JSON file communication (task-plan.json, eval-plan.json, eval-report.json)
- **git-convention** — enforces `[module]: description` commit format
- **code-hygiene** — lightweight periodic cleanup every 3 features
- **feedback (skill) + sp-feedback (project-level agent)** — closes the dev loop. Mode A (auto) runs 6-dimension checklist after all features pass. Mode B (`/feedback`) is user-triggered for observed problems. Routes findings into agent memory updates, new/fix features, or manual review with per-batch confirmation. Replaces the earlier system-feedback skill.
- **framework-check** — health check + auto-migration from old formats

### Modified Skills

- **brainstorming** — reads PROPOSAL.md as input, generates .claude/features.json, updates CLAUDE.md Project Map, divergence risk analysis (risk matrix + divergence trees)
- **writing-plans** — saves to docs/plans/active/, fallback chain design section
- **test-driven-development** — test strategy selection (unit/integration/e2e/browser), coverage awareness mapping feature steps to tests
- **using-sp-harness** — output efficiency rules (drop filler/pleasantries/hedging)

### Architecture

- Structured memory: `.claude/mem/memory.md` (state snapshot) + `todo.md`
- Session start protocol: memory → todo → git log → features.json
- Three-agent file communication: `.claude/agents/state/` with JSON schemas
- Docs hierarchy: `docs/design-docs/`, `docs/plans/active|completed/`, `docs/reports/`
- Feature-driven incremental development with automated hygiene and feedback loops
