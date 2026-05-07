from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_ci_documents_gitleaks_action_v2_resolution() -> None:
    """Record gitleaks/gitleaks-action@v2 dereferenced SHA for supply-chain audit (see M38 docs)."""
    ci = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    assert "ff98106e4c7b2bc287b24eaf42907196329070c7" in ci


def test_gitleaks_config_exists() -> None:
    assert (ROOT / ".gitleaks.toml").is_file()


def test_credential_scanning_doc_exists() -> None:
    doc = ROOT / "docs" / "security" / "CREDENTIAL_SCANNING.md"
    assert doc.is_file()
    text = doc.read_text(encoding="utf-8")

    for expected in [
        "docs/prompts/",
        "docs/foundationdocs/",
        ".cursorrules",
        "gitleaks",
        "rotate",
        "history rewrite",
    ]:
        assert expected in text


def test_makefile_mentions_secret_scan() -> None:
    text = (ROOT / "Makefile").read_text(encoding="utf-8")
    assert "secret-scan:" in text
    assert "gitleaks" in text


def test_contributing_mentions_credential_scan() -> None:
    text = (ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")
    lowered = text.lower()
    assert "credential" in lowered or "secret" in lowered
    assert "gitleaks" in lowered


def test_full_history_workflow_is_manual_only() -> None:
    path = ROOT / ".github" / "workflows" / "credential-scan-full-history.yml"
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    assert "workflow_dispatch" in text
    assert "fetch-depth: 0" in text
