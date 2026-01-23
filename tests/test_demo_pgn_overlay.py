"""Tests for demo PGN overlay module."""

from datetime import datetime
from pathlib import Path

import pytest

from renacechess.demo.pgn_overlay import generate_demo_payload


def test_generate_demo_payload_basic() -> None:
    """Test basic demo payload generation."""
    sample_pgn = Path(__file__).parent / "data" / "sample.pgn"
    fixed_time = datetime(2024, 1, 1, 12, 0, 0)

    payload = generate_demo_payload(sample_pgn, ply=6, generated_at=fixed_time)

    assert "position" in payload
    assert "policy" in payload
    assert "humanWDL" in payload
    assert "hdi" in payload
    assert "meta" in payload
    assert payload["meta"]["schemaVersion"] == "v1"


def test_generate_demo_payload_deterministic() -> None:
    """Test that payload generation is deterministic."""
    sample_pgn = Path(__file__).parent / "data" / "sample.pgn"
    fixed_time = datetime(2024, 1, 1, 12, 0, 0)

    payload1 = generate_demo_payload(sample_pgn, ply=6, generated_at=fixed_time)
    payload2 = generate_demo_payload(sample_pgn, ply=6, generated_at=fixed_time)

    assert payload1["meta"]["inputHash"] == payload2["meta"]["inputHash"]
    assert payload1["position"]["fen"] == payload2["position"]["fen"]


def test_generate_demo_payload_different_ply() -> None:
    """Test that different ply produces different payloads."""
    sample_pgn = Path(__file__).parent / "data" / "sample.pgn"
    fixed_time = datetime(2024, 1, 1, 12, 0, 0)

    payload1 = generate_demo_payload(sample_pgn, ply=6, generated_at=fixed_time)
    payload2 = generate_demo_payload(sample_pgn, ply=10, generated_at=fixed_time)

    # Should have different FENs
    assert payload1["position"]["fen"] != payload2["position"]["fen"]
    # But same schema version
    assert payload1["meta"]["schemaVersion"] == payload2["meta"]["schemaVersion"]


def test_generate_demo_payload_empty_pgn(tmp_path: Path) -> None:
    """Test that empty PGN raises error."""
    empty_pgn = tmp_path / "empty.pgn"
    empty_pgn.write_text("")

    # python-chess returns None for empty files
    with pytest.raises(ValueError, match="Failed to parse PGN"):
        generate_demo_payload(empty_pgn)


def test_generate_demo_payload_nonexistent_file() -> None:
    """Test that nonexistent file raises error."""
    nonexistent = Path("/nonexistent/path.pgn")

    with pytest.raises(FileNotFoundError):
        generate_demo_payload(nonexistent)


def test_generate_demo_payload_wdl_sum_to_one() -> None:
    """Test that WDL probabilities sum to 1."""
    sample_pgn = Path(__file__).parent / "data" / "sample.pgn"
    fixed_time = datetime(2024, 1, 1, 12, 0, 0)

    payload = generate_demo_payload(sample_pgn, ply=6, generated_at=fixed_time)

    pre_wdl = payload["humanWDL"]["pre"]
    assert abs(pre_wdl["w"] + pre_wdl["d"] + pre_wdl["l"] - 1.0) < 1e-6

    # Check postByMove WDLs
    for move_wdl in payload["humanWDL"]["postByMove"].values():
        assert abs(move_wdl["w"] + move_wdl["d"] + move_wdl["l"] - 1.0) < 1e-6


def test_generate_demo_payload_policy_probabilities() -> None:
    """Test that policy probabilities are valid."""
    sample_pgn = Path(__file__).parent / "data" / "sample.pgn"
    fixed_time = datetime(2024, 1, 1, 12, 0, 0)

    payload = generate_demo_payload(sample_pgn, ply=6, generated_at=fixed_time)

    top_moves = payload["policy"]["topMoves"]
    total_prob = sum(move["p"] for move in top_moves)
    assert abs(total_prob - 1.0) < 1e-6

    # All probabilities should be between 0 and 1
    for move in top_moves:
        assert 0.0 <= move["p"] <= 1.0

