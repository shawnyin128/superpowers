---
name: git-convention
description: |
  Enforce structured git commit messages before every commit. MUST be invoked
  before any git commit. Uses [module]: description format so git log serves
  as a reliable context source for new sessions recovering project state.
author: superpowers
version: 1.0.0
---

# git-convention

Enforce structured commit messages. Invoke this skill before every `git commit`.

---

## Commit message format

```
[module]: concise description of what changed and why
```

**module** — the area of code affected. Use the primary directory or component name.
Examples: `auth`, `api`, `skills`, `config`, `tests`, `docs`, `hooks`, `ui`

**description** — what changed and why, in one line. Must be meaningful enough
that `git log --oneline -20` tells the story of recent progress to a new agent.

---

## Examples

Good:
```
[auth]: switch from JWT to session cookies — reduces token refresh complexity
[skills]: add init-project skill for lean CLAUDE.md bootstrap
[api]: fix race condition in batch endpoint — requests were sharing state
[tests]: add integration tests for payment flow
```

Bad:
```
update files                          ← no module, no useful info
[misc]: various changes               ← says nothing
fix bug                               ← which bug? where? why?
[auth]: update auth                   ← redundant, no useful detail
```

---

## Rules

1. Every non-trivial commit MUST use this format
2. Module tag should match the primary directory or component changed
3. When a commit spans multiple modules, use the primary one
4. Description answers "what changed" and ideally "why"
5. Keep the full message under ~72 characters for clean `git log --oneline` output
6. Trivial commits (typo, formatting) can use a simpler format but should still
   have a module tag

---

## Why this matters

New sessions read `git log --oneline -20` as part of the context recovery protocol.
Structured commit messages make this a reliable information source — alongside
memory.md and todo.md — for understanding what happened recently without reading
every file that changed.
