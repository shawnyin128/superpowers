"""Regression test for the drop-upstream-fork-residue feature.

If a future commit accidentally re-introduces any of the deleted
upstream-fork artifacts, this test fails. Uses `git ls-files` so the
check matches "what would ship to a user plugin install" rather than
"what happens to be on disk locally".
"""

import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

# Paths that were deleted by the drop-upstream-fork-residue feature.
# Re-introduction of any of these is a regression.
DELETED_PATH_PREFIXES = [
    ".github/",
    "tests/brainstorm-server/",
    "tests/claude-code/",
    "tests/explicit-skill-requests/",
    "tests/skill-triggering/",
    "tests/subagent-driven-dev/",
    "docs/testing.md",
]


def _git_tracked_files() -> list[str]:
    out = subprocess.check_output(
        ["git", "ls-files"], cwd=REPO_ROOT, text=True
    )
    return [line for line in out.splitlines() if line]


def test_no_upstream_fork_residue_tracked() -> None:
    """No tracked file path may start with any of the deleted prefixes."""
    tracked = _git_tracked_files()
    offenders = [
        path
        for path in tracked
        for prefix in DELETED_PATH_PREFIXES
        if path == prefix or path.startswith(prefix)
    ]
    assert offenders == [], (
        "Re-introduced upstream-fork residue detected — these paths "
        "were deleted by the drop-upstream-fork-residue feature and "
        "must not return to git tracking:\n  "
        + "\n  ".join(offenders)
    )


def test_ds_store_not_tracked() -> None:
    """`.DS_Store` files (top-level or nested) must never be tracked.
    They are gitignored, but a git add -f could still introduce them.
    """
    tracked = _git_tracked_files()
    offenders = [path for path in tracked if path.endswith(".DS_Store")]
    assert offenders == [], (
        ".DS_Store files must not be git-tracked. Found:\n  "
        + "\n  ".join(offenders)
    )
