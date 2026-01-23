"""Tests for dataset schema validation."""

import json
from pathlib import Path

import jsonschema

from renacechess.dataset.builder import build_dataset
from renacechess.dataset.config import DatasetBuildConfig


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


def test_context_bridge_schema_validation():
    """Test that generated payloads validate against Context Bridge schema."""
    schema = load_schema("context_bridge")

    # Generate a test payload
    from renacechess.demo.pgn_overlay import generate_demo_payload

    pgn_path = Path(__file__).parent / "data" / "sample.pgn"
    payload = generate_demo_payload(pgn_path, ply=6)

    # Validate against schema
    jsonschema.validate(instance=payload, schema=schema)


def test_dataset_manifest_schema_validation(tmp_path: Path):
    """Test that generated manifests validate against Dataset Manifest schema."""
    schema = load_schema("dataset_manifest")

    # Build a test dataset
    pgn_path = Path(__file__).parent / "data" / "sample.pgn"
    config = DatasetBuildConfig(
        pgn_paths=[pgn_path],
        output_dir=tmp_path,
        max_positions=10,
    )
    build_dataset(config)

    # Load and validate manifest
    manifest_path = tmp_path / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    jsonschema.validate(instance=manifest, schema=schema)


def test_jsonl_schema_validation(tmp_path: Path):
    """Test that every JSONL line validates against Context Bridge schema."""
    schema = load_schema("context_bridge")

    # Build a test dataset
    pgn_path = Path(__file__).parent / "data" / "sample.pgn"
    config = DatasetBuildConfig(
        pgn_paths=[pgn_path],
        output_dir=tmp_path,
        max_positions=10,
    )
    build_dataset(config)

    # Validate each JSONL line
    shard_path = tmp_path / "shards" / "shard_000.jsonl"
    with shard_path.open() as f:
        for line_num, line in enumerate(f, 1):
            if line.strip():
                record = json.loads(line)
                jsonschema.validate(instance=record, schema=schema)
