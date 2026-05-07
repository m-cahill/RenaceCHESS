from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_public_onboarding_docs_exist() -> None:
    required = [
        "CONTRIBUTING.md",
        "docs/GETTING_STARTED.md",
        "docs/DOCS_INDEX.md",
        "docs/release/PUBLIC_REPO_BOUNDARY.md",
    ]

    for path in required:
        assert (ROOT / path).is_file(), path


def test_readme_links_public_onboarding_docs() -> None:
    readme = read("README.md")

    required_links = [
        "docs/GETTING_STARTED.md",
        "CONTRIBUTING.md",
        "docs/DOCS_INDEX.md",
        "docs/release/PUBLIC_REPO_BOUNDARY.md",
    ]

    for link in required_links:
        assert link in readme


def test_contributing_mentions_public_boundary() -> None:
    contributing = read("CONTRIBUTING.md")

    required_terms = [
        "docs/prompts/",
        "docs/foundationdocs/",
        ".cursorrules",
        "scripts/check_public_release_boundary.py",
    ]

    for term in required_terms:
        assert term in contributing
