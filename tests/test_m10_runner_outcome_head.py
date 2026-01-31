"""Tests for eval runner outcome head integration (M10)."""

import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from renacechess.dataset.builder import build_dataset
from renacechess.dataset.config import DatasetBuildConfig
from renacechess.eval.runner import run_conditioned_evaluation


def test_runner_outcome_head_integration(tmp_path: Path, monkeypatch) -> None:
    """Test eval runner outcome head integration path (M10).

    This test exercises the outcome head loading and metrics computation
    paths in run_conditioned_evaluation.
    """
    # Build a small dataset
    pgn_path = Path(__file__).parent / "data" / "sample.pgn"
    dataset_dir = tmp_path / "dataset"
    config = DatasetBuildConfig(
        pgn_paths=[pgn_path],
        output_dir=dataset_dir,
        max_positions=10,
    )
    build_dataset(config)

    manifest_path = dataset_dir / "manifest.json"

    # Create fake outcome head directory with sentinel files
    outcome_head_dir = tmp_path / "outcome_head"
    outcome_head_dir.mkdir()
    (outcome_head_dir / "outcome_head_v1.pt").write_bytes(b"fake_model_data")
    (outcome_head_dir / "outcome_head_v1_metadata.json").write_text(
        json.dumps({"model_type": "OutcomeHeadV1", "move_vocab_size": 100}),
        encoding="utf-8",
    )

    # Create a deterministic stub outcome head provider
    # Outcome head returns 'w', 'd', 'l' keys (not 'win', 'draw', 'loss')
    stub_predictions = {
        "w": 0.5,
        "d": 0.3,
        "l": 0.2,
    }

    def stub_predict(record: dict[str, Any]) -> dict[str, float]:
        """Stub predict function that returns deterministic W/D/L."""
        return stub_predictions.copy()

    # Mock the LearnedOutcomeHeadV1 class to return a stub
    mock_outcome_head = MagicMock()
    mock_outcome_head.predict = stub_predict

    # Create a mock class that returns our mock instance when instantiated
    def mock_class_init(model_file: Path, metadata_file: Path) -> MagicMock:
        """Mock class that returns our stub instance."""
        return mock_outcome_head

    # Patch at the source module where it's imported from
    with patch(
        "renacechess.eval.outcome_head.LearnedOutcomeHeadV1",
        side_effect=mock_class_init,
    ):
        # Run conditioned evaluation with outcome head
        eval_config = {"max_records": None}
        result = run_conditioned_evaluation(
            manifest_path=manifest_path,
            policy_id="baseline.first_legal",
            eval_config=eval_config,
            max_records=10,
            outcome_head_path=outcome_head_dir,
        )

    # Verify outcome metrics are present in result
    assert "outcome_metrics" in result
    outcome_metrics = result["outcome_metrics"]

    # Outcome metrics structure: direct fields, not nested "overall"
    assert "total_predictions" in outcome_metrics
    assert "cross_entropy" in outcome_metrics
    assert "brier_score" in outcome_metrics
    assert "ece" in outcome_metrics

    # If we have predictions, metrics should be numeric
    if outcome_metrics["total_predictions"] > 0:
        assert outcome_metrics["cross_entropy"] is not None
        assert outcome_metrics["brier_score"] is not None
        assert isinstance(outcome_metrics["cross_entropy"], int | float)
        assert isinstance(outcome_metrics["brier_score"], int | float)

    # Verify stratified outcome metrics are present
    assert "outcome_metrics_by_skill" in result
    assert "outcome_metrics_by_time_control" in result
    assert "outcome_metrics_by_time_pressure" in result


def test_runner_outcome_head_file_not_found(tmp_path: Path) -> None:
    """Test eval runner outcome head error handling when files are missing (M10)."""
    # Build a small dataset
    pgn_path = Path(__file__).parent / "data" / "sample.pgn"
    dataset_dir = tmp_path / "dataset"
    config = DatasetBuildConfig(
        pgn_paths=[pgn_path],
        output_dir=dataset_dir,
        max_positions=10,
    )
    build_dataset(config)

    manifest_path = dataset_dir / "manifest.json"

    # Create outcome head directory but missing model file
    outcome_head_dir = tmp_path / "outcome_head"
    outcome_head_dir.mkdir()
    # Missing outcome_head_v1.pt

    # Should raise FileNotFoundError
    eval_config = {"max_records": None}
    with pytest.raises(FileNotFoundError) as exc_info:
        run_conditioned_evaluation(
            manifest_path=manifest_path,
            policy_id="baseline.first_legal",
            eval_config=eval_config,
            max_records=10,
            outcome_head_path=outcome_head_dir,
        )

    assert "Outcome head files not found" in str(exc_info.value)


def test_runner_outcome_head_without_path(tmp_path: Path) -> None:
    """Test eval runner without outcome head (should not compute outcome metrics) (M10)."""
    # Build a small dataset
    pgn_path = Path(__file__).parent / "data" / "sample.pgn"
    dataset_dir = tmp_path / "dataset"
    config = DatasetBuildConfig(
        pgn_paths=[pgn_path],
        output_dir=dataset_dir,
        max_positions=10,
    )
    build_dataset(config)

    manifest_path = dataset_dir / "manifest.json"

    # Run conditioned evaluation without outcome head
    eval_config = {"max_records": None}
    result = run_conditioned_evaluation(
        manifest_path=manifest_path,
        policy_id="baseline.first_legal",
        eval_config=eval_config,
        max_records=10,
        outcome_head_path=None,
    )

    # Verify outcome metrics are NOT present
    assert "outcome_metrics" not in result
    assert "outcome_metrics_by_skill" not in result
    assert "outcome_metrics_by_time_control" not in result
    assert "outcome_metrics_by_time_pressure" not in result

    # Verify other metrics are still present (conditioned evaluation structure)
    assert "dataset_digest" in result
    assert "by_skill_bucket_id" in result
    assert "by_time_control_class" in result
