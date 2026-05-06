from __future__ import annotations

import subprocess


def test_private_release_boundary_paths_are_not_tracked() -> None:
    result = subprocess.run(
        ["git", "ls-files", "docs/prompts", "docs/foundationdocs", ".cursorrules"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.stdout.strip() == ""
