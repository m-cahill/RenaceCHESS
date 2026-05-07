"""Developer setup helper for RenaceCHESS.

This script is intentionally conservative: it prints commands by default and
only installs dev dependencies when --install is provided.
"""

from __future__ import annotations

import argparse
import subprocess
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description="RenaceCHESS developer setup helper")
    parser.add_argument(
        "--install",
        action="store_true",
        help='Run python -m pip install -e ".[dev]" in the current environment.',
    )
    args = parser.parse_args()

    print("Recommended setup:")
    print("  python -m venv .venv")
    print("  # Windows: .venv\\Scripts\\activate")
    print("  # macOS/Linux: source .venv/bin/activate")
    print('  python -m pip install -e ".[dev]"')

    if not args.install:
        print("\nNo changes made. Re-run with --install to install dev dependencies.")
        return 0

    return subprocess.call([sys.executable, "-m", "pip", "install", "-e", ".[dev]"])


if __name__ == "__main__":
    raise SystemExit(main())
