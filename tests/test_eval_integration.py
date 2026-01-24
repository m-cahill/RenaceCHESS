"""Integration tests for evaluation harness."""

import json
from datetime import datetime
from pathlib import Path

import jsonschema

from renacechess.dataset.builder import build_dataset
from renacechess.dataset.config import DatasetBuildConfig
from renacechess.eval.report import build_eval_report, write_eval_report
from renacechess.eval.runner import load_manifest, run_evaluation


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


def test_eval_run_first_legal(tmp_path: Path) -> None:
    """Test evaluation run with first_legal baseline."""
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

    # Run evaluation
    eval_config = {"max_records": None}
    eval_results = run_evaluation(
        manifest_path=manifest_path,
        policy_id="baseline.first_legal",
        eval_config=eval_config,
        max_records=10,
    )

    # Verify results structure
    assert "dataset_digest" in eval_results
    assert "assembly_config_hash" in eval_results
    assert "policy_id" in eval_results
    assert eval_results["policy_id"] == "baseline.first_legal"
    assert "overall_metrics" in eval_results
    assert eval_results["overall_metrics"]["records_evaluated"] > 0


def test_eval_report_golden_bytes(tmp_path: Path) -> None:
    """Test that evaluation reports are byte-identical across runs (determinism)."""
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

    # Lock timestamp for determinism
    created_at = datetime(2024, 1, 1, 12, 0, 0)

    # Run evaluation twice
    eval_config = {"max_records": None}
    eval_results1 = run_evaluation(
        manifest_path=manifest_path,
        policy_id="baseline.first_legal",
        eval_config=eval_config,
        max_records=10,
    )
    eval_results2 = run_evaluation(
        manifest_path=manifest_path,
        policy_id="baseline.first_legal",
        eval_config=eval_config,
        max_records=10,
    )

    # Build reports with locked timestamp
    report1 = build_eval_report(eval_results1, created_at=created_at)
    report2 = build_eval_report(eval_results2, created_at=created_at)

    # Write reports
    report_path1 = tmp_path / "report1.json"
    report_path2 = tmp_path / "report2.json"
    write_eval_report(report1, report_path1)
    write_eval_report(report2, report_path2)

    # Read bytes
    bytes1 = report_path1.read_bytes()
    bytes2 = report_path2.read_bytes()

    # Assert byte-identical
    assert bytes1 == bytes2, "Reports should be byte-identical for determinism"

    # Validate schema
    report_dict = json.loads(bytes1.decode("utf-8"))
    schema = load_schema("eval_report.v1")
    jsonschema.validate(report_dict, schema)


def test_eval_run_uniform_random(tmp_path: Path) -> None:
    """Test evaluation run with uniform_random baseline."""
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

    # Run evaluation
    eval_config = {"max_records": None}
    eval_results = run_evaluation(
        manifest_path=manifest_path,
        policy_id="baseline.uniform_random",
        eval_config=eval_config,
        max_records=10,
    )

    # Verify results
    assert eval_results["policy_id"] == "baseline.uniform_random"
    assert eval_results["overall_metrics"]["records_evaluated"] > 0
    # Uniform random should have entropy > 0
    entropy_mean = eval_results["overall_metrics"]["policy_entropy"]["mean"]
    if entropy_mean != "N/A":
        assert float(entropy_mean) > 0.0


def test_load_manifest_v2(tmp_path: Path) -> None:
    """Test loading dataset manifest v2."""
    # Build a small dataset
    pgn_path = Path(__file__).parent / "data" / "sample.pgn"
    dataset_dir = tmp_path / "dataset"
    config = DatasetBuildConfig(
        pgn_paths=[pgn_path],
        output_dir=dataset_dir,
        max_positions=5,
    )
    build_dataset(config)

    manifest_path = dataset_dir / "manifest.json"

    # Load manifest
    manifest = load_manifest(manifest_path)

    # Verify structure
    assert manifest.schema_version == "v2"
    assert len(manifest.shard_refs) > 0
    assert manifest.dataset_digest is not None
    assert manifest.assembly_config_hash is not None


def test_eval_run_max_records(tmp_path: Path) -> None:
    """Test evaluation with max_records limit."""
    # Build a small dataset
    pgn_path = Path(__file__).parent / "data" / "sample.pgn"
    dataset_dir = tmp_path / "dataset"
    config = DatasetBuildConfig(
        pgn_paths=[pgn_path],
        output_dir=dataset_dir,
        max_positions=20,
    )
    build_dataset(config)

    manifest_path = dataset_dir / "manifest.json"

    # Run evaluation with limit
    eval_config = {"max_records": None}
    eval_results = run_evaluation(
        manifest_path=manifest_path,
        policy_id="baseline.first_legal",
        eval_config=eval_config,
        max_records=5,
    )

    # Should have evaluated exactly 5 records
    assert eval_results["overall_metrics"]["records_evaluated"] == 5
