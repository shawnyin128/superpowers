"""Regression test for consolidate-changelog feature.

CHANGELOG.md must be the single source of release history. RELEASE-
NOTES.md must not return. Both the post-fork v0.5.0+ history and the
fork-creation 1.0.0 marker must remain in CHANGELOG.md.
"""

import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CHANGELOG = REPO_ROOT / "CHANGELOG.md"


def test_changelog_exists() -> None:
    assert CHANGELOG.exists(), "CHANGELOG.md must exist at repo root"


def test_release_notes_md_not_tracked() -> None:
    """RELEASE-NOTES.md must not be git-tracked. If it returns, it
    means the consolidation got reverted."""
    out = subprocess.check_output(
        ["git", "ls-files"], cwd=REPO_ROOT, text=True
    )
    tracked = [line for line in out.splitlines() if line]
    assert "RELEASE-NOTES.md" not in tracked, (
        "RELEASE-NOTES.md returned to git tracking — consolidation reverted"
    )


def test_changelog_has_post_fork_history() -> None:
    """The consolidated CHANGELOG must include the v0.5.0 entry that
    came from RELEASE-NOTES.md."""
    text = CHANGELOG.read_text()
    assert "## v0.5.0" in text, (
        "CHANGELOG.md must include the v0.5.0 (Supersession tracking) "
        "section migrated from RELEASE-NOTES.md."
    )


def test_changelog_preserves_fork_marker() -> None:
    """The fork-creation 1.0.0 entry must remain so the version
    sequence reset (1.0.0 → v0.5.0) is documented."""
    text = CHANGELOG.read_text()
    assert "## [1.0.0]" in text, (
        "CHANGELOG.md must preserve the [1.0.0] fork-creation marker."
    )
