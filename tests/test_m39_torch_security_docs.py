from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_torch_security_review_exists() -> None:
    path = ROOT / "docs" / "security" / "TORCH_SECURITY_REVIEW.md"
    assert path.is_file()

    text = path.read_text(encoding="utf-8")
    for term in [
        "Torch Security Review",
        "M39",
        "pip-audit",
        "Decision",
        "Evidence",
    ]:
        assert term in text


def test_m39_milestone_docs_exist() -> None:
    base = ROOT / "docs" / "milestones" / "PhaseG" / "M39"
    for name in ["M39_plan.md", "M39_summary.md", "M39_audit.md"]:
        assert (base / name).is_file()
