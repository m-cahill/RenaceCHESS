"""Integration tests for labeled evaluation with accuracy metrics (M05)."""

import json
from datetime import datetime
from pathlib import Path

import jsonschema

from renacechess.dataset.builder import build_dataset
from renacechess.dataset.config import DatasetBuildConfig
from renacechess.eval.report import build_eval_report_v2, write_eval_report
from renacechess.eval.runner import run_evaluation


def load_schema(schema_name: str) -> dict:
    """Load JSON schema from schemas directory."""
    schema_path = (
        Path(__file__).parent.parent
        / "src"
        / "renacechess"
        / "contracts"
        / "schemas"
        / "v1"
        / f"{schema_name}.schema.json"
    )
    return json.loads(schema_path.read_text())


def test_labeled_dataset_build(tmp_path: Path) -> None:
    """Test that dataset builder captures chosenMove from PGN."""
    pgn_path = Path(__file__).parent / "data" / "sample.pgn"
    dataset_dir = tmp_path / "dataset"
    config = DatasetBuildConfig(
        pgn_paths=[pgn_path],
        output_dir=dataset_dir,
        max_positions=10,
    )
    build_dataset(config)

    # Check that shard contains chosenMove fields
    manifest_path = dataset_dir / "manifest.json"
    manifest_dict = json.loads(manifest_path.read_text())
    shard_refs = manifest_dict["shardRefs"]

    assert len(shard_refs) > 0
    shard_path = dataset_dir / shard_refs[0]["path"]

    # Read first few records
    labeled_count = 0
    with shard_path.open() as f:
        for i, line in enumerate(f):
            if i >= 5:  # Check first 5 records
                break
            record = json.loads(line)
            if "chosenMove" in record:
                labeled_count += 1
                assert "uci" in record["chosenMove"]
                # SAN may or may not be present

    # At least some records should be labeled (positions after moves)
    assert labeled_count > 0


def test_accuracy_evaluation(tmp_path: Path) -> None:
    """Test evaluation with accuracy metrics enabled."""
    pgn_path = Path(__file__).parent / "data" / "sample.pgn"
    dataset_dir = tmp_path / "dataset"
    config = DatasetBuildConfig(
        pgn_paths=[pgn_path],
        output_dir=dataset_dir,
        max_positions=20,
    )
    build_dataset(config)

    manifest_path = dataset_dir / "manifest.json"

    # Run evaluation with accuracy enabled
    eval_config = {"max_records": None, "compute_accuracy": True, "top_k_values": [1, 3]}
    eval_results = run_evaluation(
        manifest_path=manifest_path,
        policy_id="baseline.first_legal",
        eval_config=eval_config,
        max_records=20,
        compute_accuracy=True,
        top_k_values=[1, 3],
    )

    # Verify accuracy metrics are present
    overall_metrics = eval_results["overall_metrics"]
    assert "labeled_record_count" in overall_metrics
    assert "accuracy" in overall_metrics
    assert "top1" in overall_metrics["accuracy"]
    assert "top3" in overall_metrics["accuracy"]
    assert "coverage" in overall_metrics["accuracy"]

    # Verify labeled count > 0 (some records should be labeled)
    assert overall_metrics["labeled_record_count"] > 0


def test_accuracy_report_v2(tmp_path: Path) -> None:
    """Test building evaluation report v2 with accuracy metrics."""
    pgn_path = Path(__file__).parent / "data" / "sample.pgn"
    dataset_dir = tmp_path / "dataset"
    config = DatasetBuildConfig(
        pgn_paths=[pgn_path],
        output_dir=dataset_dir,
        max_positions=10,
    )
    build_dataset(config)

    manifest_path = dataset_dir / "manifest.json"

    # Run evaluation with accuracy
    eval_config = {"max_records": None, "compute_accuracy": True, "top_k_values": [1]}
    eval_results = run_evaluation(
        manifest_path=manifest_path,
        policy_id="baseline.first_legal",
        eval_config=eval_config,
        max_records=10,
        compute_accuracy=True,
        top_k_values=[1],
    )

    # Build v2 report
    created_at = datetime(2024, 1, 1, 12, 0, 0)
    report = build_eval_report_v2(eval_results, created_at=created_at)

    # Verify report structure
    assert report.schema_version == "eval_report.v2"
    assert report.total_record_count > 0
    assert report.labeled_record_count > 0
    assert report.accuracy is not None
    assert report.accuracy.coverage is not None

    # Write and validate schema
    report_path = tmp_path / "report.json"
    write_eval_report(report, report_path)

    report_dict = json.loads(report_path.read_text())
    schema = load_schema("eval_report.v2")
    jsonschema.validate(report_dict, schema)


def test_labeled_evaluation_determinism(tmp_path: Path) -> None:
    """Test that labeled evaluation reports are deterministic."""
    pgn_path = Path(__file__).parent / "data" / "sample.pgn"
    dataset_dir = tmp_path / "dataset"
    config = DatasetBuildConfig(
        pgn_paths=[pgn_path],
        output_dir=dataset_dir,
        max_positions=10,
    )
    build_dataset(config)

    manifest_path = dataset_dir / "manifest.json"
    created_at = datetime(2024, 1, 1, 12, 0, 0)

    # Run evaluation twice
    eval_config = {"max_records": None, "compute_accuracy": True, "top_k_values": [1, 3]}
    eval_results1 = run_evaluation(
        manifest_path=manifest_path,
        policy_id="baseline.first_legal",
        eval_config=eval_config,
        max_records=10,
        compute_accuracy=True,
        top_k_values=[1, 3],
    )
    eval_results2 = run_evaluation(
        manifest_path=manifest_path,
        policy_id="baseline.first_legal",
        eval_config=eval_config,
        max_records=10,
        compute_accuracy=True,
        top_k_values=[1, 3],
    )

    # Build reports
    report1 = build_eval_report_v2(eval_results1, created_at=created_at)
    report2 = build_eval_report_v2(eval_results2, created_at=created_at)

    # Write reports
    report_path1 = tmp_path / "report1.json"
    report_path2 = tmp_path / "report2.json"
    write_eval_report(report1, report_path1)
    write_eval_report(report2, report_path2)

    # Compare bytes
    bytes1 = report_path1.read_bytes()
    bytes2 = report_path2.read_bytes()

    assert bytes1 == bytes2, "Reports should be byte-identical for determinism"


def test_backward_compatibility_unlabeled_dataset(tmp_path: Path) -> None:
    """Test that unlabeled datasets still work (backward compatibility)."""
    # This test verifies that datasets without chosenMove still work
    # We'll create a dataset and then manually remove chosenMove from records
    pgn_path = Path(__file__).parent / "data" / "sample.pgn"
    dataset_dir = tmp_path / "dataset"
    config = DatasetBuildConfig(
        pgn_paths=[pgn_path],
        output_dir=dataset_dir,
        max_positions=10,
    )
    build_dataset(config)

    # Remove chosenMove from records (simulate old dataset)
    manifest_path = dataset_dir / "manifest.json"
    manifest_dict = json.loads(manifest_path.read_text())
    shard_path = dataset_dir / manifest_dict["shardRefs"][0]["path"]

    # Read, remove chosenMove, write back
    records = []
    with shard_path.open() as f:
        for line in f:
            record = json.loads(line)
            if "chosenMove" in record:
                del record["chosenMove"]
            records.append(record)

    with shard_path.open("w") as f:
        for record in records:
            f.write(json.dumps(record, separators=(",", ":")) + "\n")

    # Evaluation should still work (without accuracy)
    eval_config = {"max_records": None}
    eval_results = run_evaluation(
        manifest_path=manifest_path,
        policy_id="baseline.first_legal",
        eval_config=eval_config,
        max_records=10,
        compute_accuracy=False,
    )

    # Should have no accuracy metrics
    assert "accuracy" not in eval_results["overall_metrics"]
    assert "labeled_record_count" not in eval_results["overall_metrics"]
