"""Verify private release-boundary paths are not tracked by git.

M35 public release boundary:
- docs/prompts/
- docs/foundationdocs/
- .cursorrules

These paths may exist locally, but must not be committed.
"""

from __future__ import annotations

import subprocess
import sys

PRIVATE_PATHS = (
    "docs/prompts",
    "docs/foundationdocs",
    ".cursorrules",
)


def main() -> int:
    """Return non-zero if private boundary paths are tracked."""
    result = subprocess.run(
        ["git", "ls-files", *PRIVATE_PATHS],
        check=False,
        capture_output=True,
        text=True,
    )

    tracked = result.stdout.strip()

    if tracked:
        print("Private release-boundary files are tracked:")
        print(tracked)
        print()
        print("These paths must remain local/private only:")
        for path in PRIVATE_PATHS:
            print(f"- {path}")
        return 1

    print("Public release boundary check passed: no private paths are tracked.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
