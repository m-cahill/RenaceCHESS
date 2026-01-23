"""Golden file regression test for demo payload generation."""

import json
from datetime import datetime
from pathlib import Path

import pytest

from renacechess.demo.pgn_overlay import generate_demo_payload
from renacechess.determinism import canonical_json_dump


@pytest.fixture
def golden_file_path() -> Path:
    """Path to golden file."""
    return Path(__file__).parent / "golden" / "demo_payload.v1.json"


@pytest.fixture
def sample_pgn_path() -> Path:
    """Path to sample PGN file."""
    return Path(__file__).parent / "data" / "sample.pgn"


def test_demo_payload_golden(sample_pgn_path: Path, golden_file_path: Path) -> None:
    """Test that demo payload matches golden file."""
    # Generate payload with fixed timestamp for determinism
    fixed_time = datetime(2024, 1, 1, 12, 0, 0)
    payload = generate_demo_payload(sample_pgn_path, ply=6, generated_at=fixed_time)

    # Serialize to canonical JSON
    payload_json = canonical_json_dump(payload).decode("utf-8")
    payload_dict = json.loads(payload_json)

    # Load golden file if it exists
    if golden_file_path.exists():
        golden_json = golden_file_path.read_text(encoding="utf-8")
        golden_dict = json.loads(golden_json)

        # Compare (allowing for floating point precision)
        assert payload_dict["meta"]["schemaVersion"] == golden_dict["meta"]["schemaVersion"]
        assert payload_dict["meta"]["inputHash"] == golden_dict["meta"]["inputHash"]
        assert payload_dict["position"]["fen"] == golden_dict["position"]["fen"]
        assert len(payload_dict["policy"]["topMoves"]) == len(golden_dict["policy"]["topMoves"])

        # Compare policy moves (allowing small floating point differences)
        for i, (gen_move, gold_move) in enumerate(
            zip(payload_dict["policy"]["topMoves"], golden_dict["policy"]["topMoves"])
        ):
            assert gen_move["uci"] == gold_move["uci"]
            assert abs(gen_move["p"] - gold_move["p"]) < 1e-6

        # Compare HDI (allowing small differences)
        assert abs(payload_dict["hdi"]["value"] - golden_dict["hdi"]["value"]) < 1e-6

    else:
        # First run: create golden file
        golden_file_path.parent.mkdir(parents=True, exist_ok=True)
        golden_file_path.write_text(payload_json, encoding="utf-8")
        pytest.fail(
            f"Golden file created at {golden_file_path}. "
            "Please review and commit it, then re-run the test."
        )


def test_demo_payload_deterministic(sample_pgn_path: Path) -> None:
    """Test that demo payload is deterministic across runs."""
    fixed_time = datetime(2024, 1, 1, 12, 0, 0)

    payload1 = generate_demo_payload(sample_pgn_path, ply=6, generated_at=fixed_time)
    payload2 = generate_demo_payload(sample_pgn_path, ply=6, generated_at=fixed_time)

    # Serialize both to canonical JSON
    json1 = canonical_json_dump(payload1)
    json2 = canonical_json_dump(payload2)

    # Should be identical
    assert json1 == json2

