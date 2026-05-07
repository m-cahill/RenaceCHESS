from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_makefile_exists_with_public_targets() -> None:
    makefile = ROOT / "Makefile"
    assert makefile.is_file()

    text = makefile.read_text(encoding="utf-8")
    for target in [
        "help:",
        "install-dev:",
        "install:",
        "lint:",
        "format-check:",
        "type:",
        "test:",
        "test-fast:",
        "docs-check:",
        "boundary-check:",
        "secret-scan:",
        "secret-scan-no-git:",
        "verify:",
        "clean-coverage:",
    ]:
        assert target in text


def test_setup_dev_helper_exists_and_is_conservative() -> None:
    script = ROOT / "scripts" / "setup_dev.py"
    assert script.is_file()

    text = script.read_text(encoding="utf-8")
    assert "--install" in text
    assert 'pip", "install", "-e", ".[dev]"' in text
    assert "No changes made" in text


def test_onboarding_docs_reference_dx_shortcuts() -> None:
    files = [
        ROOT / "CONTRIBUTING.md",
        ROOT / "docs" / "GETTING_STARTED.md",
    ]

    for path in files:
        text = path.read_text(encoding="utf-8")
        assert "make verify" in text or "Makefile" in text
