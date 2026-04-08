---
name: framework-check
description: |
  Health check for the superpowers project framework. Verifies CLAUDE.md
  structure, memory system, hooks, features.json, and git conventions.
  Auto-fixes missing components by invoking relevant skills. Run on any
  project to check compliance or migrate from an older setup.
author: superpowers
version: 1.0.0
---

# framework-check

Verify the current project follows the superpowers framework. Auto-fix
anything missing.

---

## Step 1: Run Checks

Check each item independently. Record PASS or FAIL for each.

### CLAUDE.md Structure

- [ ] `CLAUDE.md` exists in project root
- [ ] Contains `## First-Principles Standards` section
- [ ] Contains `## Context Management` section
- [ ] Contains `## Project Map` section
- [ ] Total length is under 80 lines

### Memory System

- [ ] `.claude/mem/` directory exists
- [ ] `.claude/mem/memory.md` exists
- [ ] `memory.md` has `## Current State` section
- [ ] `memory.md` has `## Key Decisions` section
- [ ] `memory.md` has `## Findings` section
- [ ] `.claude/mem/todo.md` exists

### Hooks

- [ ] `.claude/hooks/update-mem-reminder.sh` exists and is executable
- [ ] `.claude/settings.json` has `Stop` hook configured for update-mem
- [ ] `.claude/settings.json` has `UserPromptSubmit` hook configured for update-mem

### Features (only if project is past brainstorming)

- [ ] `docs/features.json` exists (skip if no spec docs exist yet)
- [ ] features.json is valid JSON with `features` array
- [ ] Each feature has: id, category, priority, description, steps, passes

### Git Conventions

- [ ] Last 10 commits follow `[module]: description` format
  (check with `git log --oneline -10` — warn on violations, don't fail
  on pre-existing commits before framework adoption)

---

## Step 2: Report

Present results as a checklist:

```
Framework Health Check
======================

CLAUDE.md Structure
  ✓ CLAUDE.md exists
  ✓ First-Principles Standards
  ✗ Context Management — MISSING
  ✓ Project Map
  ✓ Under 80 lines

Memory System
  ✗ .claude/mem/ — MISSING
  ...

Hooks
  ✗ update-mem-reminder.sh — MISSING
  ...

Features
  ⊘ Skipped (no spec docs found)

Git Conventions
  ⚠ 3/10 commits don't follow [module]: format (pre-existing)

Result: 8/12 checks passed. 4 items need fixing.
```

---

## Step 3: Auto-Fix

For each FAIL, apply the appropriate fix:

### CLAUDE.md missing entirely
→ Invoke `init-project` skill (creates CLAUDE.md + memory + hooks)

### CLAUDE.md exists but missing sections
→ Merge missing sections in place:

**Missing First-Principles Standards:** Insert the standard FPS section
(same content as init-project generates) after the title.

**Missing Context Management:** Insert the standard Context Management
section (with session start protocol) after FPS.

**Missing Project Map:** Scan project and generate map section (same
logic as init-project Step 1 + Step 2).

### Memory system missing
→ Create `.claude/mem/memory.md` with structured template:
```markdown
# Project Memory

## Current State
Project framework initialized. No work started yet.

## Key Decisions

## Findings
```

→ Create `.claude/mem/todo.md`:
```markdown
# Todo
```

### Memory exists but wrong structure
→ Migrate: read existing content, restructure into Current State /
Key Decisions / Findings format. Preserve all existing information.

### Hooks missing
→ Create hook script and configure settings.json (same logic as
init-project Step 4). Merge with existing settings, do not overwrite.

### Features.json invalid
→ Report specific validation errors. Do not auto-create features.json
(that comes from brainstorming).

### Git convention violations
→ Do not rewrite git history. Only warn. Future commits will follow
the convention via git-convention skill.

---

## Step 4: Re-check

After fixes, re-run all checks to confirm everything passes.

Report:
```
Auto-fix complete. Re-check: 12/12 passed.
```

If any checks still fail after fix, report them and stop.

---

## Step 5: Update Memory

Update `.claude/mem/memory.md` Current State to note the framework check.

Commit all fixes:
```
[framework]: auto-fix missing framework components
```

---

## Rules

1. Never delete existing content — only add missing parts
2. When migrating old format memory.md, preserve all entries
3. Do not rewrite git history for convention violations
4. Do not create features.json — that is brainstorming's job
5. If CLAUDE.md exists with custom content beyond the three sections,
   preserve it (only add missing standard sections)
6. This skill is idempotent — running it twice produces no changes
   if everything is already correct
