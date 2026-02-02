"""Tests for M30 frozen evaluation set v2 generator.

Validates:
- Schema compliance for FrozenEvalManifestV2 and EvalSetProvenanceV1
- Deterministic generation (same seed → same output)
- Stratification correctness (7 skill buckets, min 1000 each)
- Shard generation and hash verification
- Position count targets

See docs/milestones/PhaseE/M30/M30_plan.md for the governing specification.
"""

from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest

from renacechess.contracts.models import (
    EvalSetProvenanceV1,
    FrozenEvalManifestV2,
    FrozenEvalRecordV2,
    FrozenEvalStratificationV2,
)
from renacechess.frozen_eval.generator_v2 import (
    FEN_SEEDS,
    M30_MIN_PER_SKILL_BUCKET,
    M30_SELECTION_SEED,
    M30_TOTAL_POSITIONS,
    SKILL_BUCKETS,
    generate_frozen_eval_v2,
    verify_frozen_eval_v2,
)


class TestFrozenEvalManifestV2Schema:
    """Tests for FrozenEvalManifestV2 schema validation."""

    def test_valid_manifest_model(self) -> None:
        """FrozenEvalManifestV2 model accepts valid data."""
        manifest = FrozenEvalManifestV2(
            schema_version=2,
            created_at=datetime.now(timezone.utc),
            synthetic=True,
            selection_strategy="test_strategy",
            position_count=10000,
            provenance_ref="sha256:" + "a" * 64,
            stratification=FrozenEvalStratificationV2(
                total_positions=10000,
                min_per_skill_bucket=1000,
                skill_bucket_count=7,
            ),
            counts_by_skill_bucket_id={"lt_800": 1429},
            counts_by_time_control_class={"bullet": 2500},
            counts_by_time_pressure_bucket={"normal": 3333},
            shard_refs=["shard_000.jsonl"],
            shard_hashes={"shard_000": "a" * 64},
            determinism_hash="sha256:" + "b" * 64,
        )
        assert manifest.schema_version == 2
        assert manifest.synthetic is True
        assert manifest.position_count == 10000

    def test_schema_version_must_be_2(self) -> None:
        """FrozenEvalManifestV2 rejects schema version != 2."""
        with pytest.raises(Exception):  # Pydantic validation error
            FrozenEvalManifestV2(
                schema_version=1,  # type: ignore[arg-type]
                created_at=datetime.now(timezone.utc),
                synthetic=True,
                selection_strategy="test",
                position_count=100,
                provenance_ref="sha256:" + "a" * 64,
                stratification=FrozenEvalStratificationV2(
                    total_positions=10000,
                    min_per_skill_bucket=1000,
                    skill_bucket_count=7,
                ),
                counts_by_skill_bucket_id={},
                counts_by_time_control_class={},
                counts_by_time_pressure_bucket={},
                shard_refs=["test.jsonl"],
                shard_hashes={},
                determinism_hash="sha256:" + "a" * 64,
            )

    def test_synthetic_must_be_true(self) -> None:
        """FrozenEvalManifestV2.synthetic must be True (Literal[True])."""
        with pytest.raises(Exception):
            FrozenEvalManifestV2(
                schema_version=2,
                created_at=datetime.now(timezone.utc),
                synthetic=False,  # type: ignore[arg-type]
                selection_strategy="test",
                position_count=100,
                provenance_ref="sha256:" + "a" * 64,
                stratification=FrozenEvalStratificationV2(
                    total_positions=10000,
                    min_per_skill_bucket=1000,
                    skill_bucket_count=7,
                ),
                counts_by_skill_bucket_id={},
                counts_by_time_control_class={},
                counts_by_time_pressure_bucket={},
                shard_refs=["test.jsonl"],
                shard_hashes={},
                determinism_hash="sha256:" + "a" * 64,
            )


class TestEvalSetProvenanceV1Schema:
    """Tests for EvalSetProvenanceV1 schema validation."""

    def test_valid_provenance_model(self) -> None:
        """EvalSetProvenanceV1 model accepts valid data."""
        provenance = EvalSetProvenanceV1(
            version="1.0",
            created_at=datetime.now(timezone.utc),
            generator_version="v2.0.0",
            selection_seed=42,
            position_sources=["test_source"],
            skill_bucket_strategy="uniform",
            time_control_strategy="random",
            time_pressure_strategy="random",
            audit_notes="Test audit notes.",
            determinism_hash="sha256:" + "a" * 64,
        )
        assert provenance.version == "1.0"
        assert provenance.selection_seed == 42

    def test_requires_audit_notes(self) -> None:
        """EvalSetProvenanceV1 requires audit_notes field."""
        with pytest.raises(Exception):
            EvalSetProvenanceV1(
                version="1.0",
                created_at=datetime.now(timezone.utc),
                generator_version="v2.0.0",
                selection_seed=42,
                position_sources=["test"],
                skill_bucket_strategy="uniform",
                time_control_strategy="random",
                time_pressure_strategy="random",
                # audit_notes missing
                determinism_hash="sha256:" + "a" * 64,
            )


class TestFrozenEvalRecordV2Schema:
    """Tests for FrozenEvalRecordV2 schema validation."""

    def test_valid_record(self) -> None:
        """FrozenEvalRecordV2 accepts valid skill/time bucket values."""
        record = FrozenEvalRecordV2(
            record_key="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1:0",
            shard_id="shard_000",
            skill_bucket_id="1200_1399",
            time_control_class="blitz",
            time_pressure_bucket="normal",
        )
        assert record.skill_bucket_id == "1200_1399"

    def test_rejects_unknown_skill_bucket(self) -> None:
        """FrozenEvalRecordV2 rejects 'unknown' skill bucket (V2 is strict)."""
        with pytest.raises(Exception):
            FrozenEvalRecordV2(
                record_key="test:0",
                shard_id="shard_000",
                skill_bucket_id="unknown",  # type: ignore[arg-type]
                time_control_class="blitz",
                time_pressure_bucket="normal",
            )


class TestGenerateFrozenEvalV2:
    """Tests for the frozen eval v2 generator function."""

    def test_generates_correct_position_count(self) -> None:
        """Generator produces exactly the target number of positions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            manifest, _ = generate_frozen_eval_v2(
                output_dir=output_dir,
                total_positions=1000,
                min_per_skill_bucket=100,
                seed=42,
            )
            assert manifest.position_count == 1000

    def test_generates_all_seven_skill_buckets(self) -> None:
        """Generator produces positions for all 7 skill buckets."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            manifest, _ = generate_frozen_eval_v2(
                output_dir=output_dir,
                total_positions=1400,  # 7 buckets × 200 minimum
                min_per_skill_bucket=200,
                seed=42,
            )
            assert len(manifest.counts_by_skill_bucket_id) == 7
            for bucket in SKILL_BUCKETS:
                assert bucket in manifest.counts_by_skill_bucket_id
                assert manifest.counts_by_skill_bucket_id[bucket] >= 200

    def test_generates_shards(self) -> None:
        """Generator creates shard files with correct content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            manifest, _ = generate_frozen_eval_v2(
                output_dir=output_dir,
                total_positions=1500,
                min_per_skill_bucket=100,
                seed=42,
            )
            # Should have 2 shards (1000 per shard, 1500 total)
            assert len(manifest.shard_refs) == 2
            assert "shard_000.jsonl" in manifest.shard_refs
            assert "shard_001.jsonl" in manifest.shard_refs

            # Verify shard files exist
            for shard_ref in manifest.shard_refs:
                shard_path = output_dir / shard_ref
                assert shard_path.exists()

    def test_generates_provenance_file(self) -> None:
        """Generator creates provenance.json file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            _, provenance = generate_frozen_eval_v2(
                output_dir=output_dir,
                total_positions=1400,
                min_per_skill_bucket=200,
                seed=42,
            )
            provenance_path = output_dir / "provenance.json"
            assert provenance_path.exists()

            # Verify provenance content
            with provenance_path.open() as f:
                provenance_data = json.load(f)
            assert provenance_data["version"] == "1.0"
            assert provenance_data["selectionSeed"] == 42

    def test_generates_manifest_file(self) -> None:
        """Generator creates manifest.json file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            manifest, _ = generate_frozen_eval_v2(
                output_dir=output_dir,
                total_positions=1400,
                min_per_skill_bucket=200,
                seed=42,
            )
            manifest_path = output_dir / "manifest.json"
            assert manifest_path.exists()

            # Verify manifest content
            with manifest_path.open() as f:
                manifest_data = json.load(f)
            assert manifest_data["schemaVersion"] == 2
            assert manifest_data["synthetic"] is True

    def test_rejects_impossible_stratification(self) -> None:
        """Generator rejects impossible stratification targets."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            with pytest.raises(ValueError, match="must be >="):
                generate_frozen_eval_v2(
                    output_dir=output_dir,
                    total_positions=100,  # Too few for 7 buckets × 100 minimum
                    min_per_skill_bucket=100,
                    seed=42,
                )


class TestDeterminism:
    """Tests for deterministic generation."""

    def test_same_seed_produces_same_manifest_hash(self) -> None:
        """Same seed + timestamp → identical manifest hash."""
        fixed_time = datetime(2026, 2, 2, 12, 0, 0, tzinfo=timezone.utc)

        with tempfile.TemporaryDirectory() as tmpdir1:
            output_dir1 = Path(tmpdir1)
            manifest1, _ = generate_frozen_eval_v2(
                output_dir=output_dir1,
                total_positions=1400,
                min_per_skill_bucket=200,
                seed=42,
                created_at=fixed_time,
            )

        with tempfile.TemporaryDirectory() as tmpdir2:
            output_dir2 = Path(tmpdir2)
            manifest2, _ = generate_frozen_eval_v2(
                output_dir=output_dir2,
                total_positions=1400,
                min_per_skill_bucket=200,
                seed=42,
                created_at=fixed_time,
            )

        assert manifest1.determinism_hash == manifest2.determinism_hash

    def test_different_seed_produces_different_hash(self) -> None:
        """Different seed → different manifest hash."""
        fixed_time = datetime(2026, 2, 2, 12, 0, 0, tzinfo=timezone.utc)

        with tempfile.TemporaryDirectory() as tmpdir1:
            output_dir1 = Path(tmpdir1)
            manifest1, _ = generate_frozen_eval_v2(
                output_dir=output_dir1,
                total_positions=1400,
                min_per_skill_bucket=200,
                seed=42,
                created_at=fixed_time,
            )

        with tempfile.TemporaryDirectory() as tmpdir2:
            output_dir2 = Path(tmpdir2)
            manifest2, _ = generate_frozen_eval_v2(
                output_dir=output_dir2,
                total_positions=1400,
                min_per_skill_bucket=200,
                seed=99,  # Different seed
                created_at=fixed_time,
            )

        assert manifest1.determinism_hash != manifest2.determinism_hash


class TestVerifyFrozenEvalV2:
    """Tests for manifest verification function."""

    def test_verify_valid_manifest(self) -> None:
        """verify_frozen_eval_v2 returns True for valid manifest."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            generate_frozen_eval_v2(
                output_dir=output_dir,
                total_positions=1400,
                min_per_skill_bucket=200,
                seed=42,
            )
            manifest_path = output_dir / "manifest.json"
            assert verify_frozen_eval_v2(manifest_path) is True

    def test_verify_tampered_manifest(self) -> None:
        """verify_frozen_eval_v2 returns False for tampered manifest."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            generate_frozen_eval_v2(
                output_dir=output_dir,
                total_positions=1400,
                min_per_skill_bucket=200,
                seed=42,
            )
            manifest_path = output_dir / "manifest.json"

            # Tamper with the manifest
            with manifest_path.open() as f:
                manifest_data = json.load(f)
            manifest_data["positionCount"] = 9999  # Tamper
            with manifest_path.open("w") as f:
                json.dump(manifest_data, f)

            assert verify_frozen_eval_v2(manifest_path) is False


class TestCommittedFrozenEvalV2:
    """Tests for the committed frozen eval v2 in data/frozen_eval_v2/."""

    @pytest.fixture
    def frozen_eval_v2_path(self) -> Path:
        """Path to committed frozen eval v2 directory."""
        return Path("data/frozen_eval_v2")

    def test_committed_manifest_exists(self, frozen_eval_v2_path: Path) -> None:
        """Committed manifest.json exists."""
        manifest_path = frozen_eval_v2_path / "manifest.json"
        assert manifest_path.exists(), "data/frozen_eval_v2/manifest.json must exist"

    def test_committed_provenance_exists(self, frozen_eval_v2_path: Path) -> None:
        """Committed provenance.json exists."""
        provenance_path = frozen_eval_v2_path / "provenance.json"
        assert provenance_path.exists(), "data/frozen_eval_v2/provenance.json must exist"

    def test_committed_manifest_schema_valid(self, frozen_eval_v2_path: Path) -> None:
        """Committed manifest validates against FrozenEvalManifestV2 schema."""
        manifest_path = frozen_eval_v2_path / "manifest.json"
        with manifest_path.open() as f:
            manifest_data = json.load(f)
        manifest = FrozenEvalManifestV2.model_validate(manifest_data)
        assert manifest.schema_version == 2
        assert manifest.synthetic is True
        assert manifest.position_count == 10000

    def test_committed_provenance_schema_valid(self, frozen_eval_v2_path: Path) -> None:
        """Committed provenance validates against EvalSetProvenanceV1 schema."""
        provenance_path = frozen_eval_v2_path / "provenance.json"
        with provenance_path.open() as f:
            provenance_data = json.load(f)
        provenance = EvalSetProvenanceV1.model_validate(provenance_data)
        assert provenance.version == "1.0"

    def test_committed_manifest_determinism_hash_valid(
        self, frozen_eval_v2_path: Path
    ) -> None:
        """Committed manifest's determinism hash is valid."""
        manifest_path = frozen_eval_v2_path / "manifest.json"
        assert verify_frozen_eval_v2(manifest_path) is True

    def test_committed_shards_exist(self, frozen_eval_v2_path: Path) -> None:
        """All referenced shard files exist."""
        manifest_path = frozen_eval_v2_path / "manifest.json"
        with manifest_path.open() as f:
            manifest_data = json.load(f)

        for shard_ref in manifest_data["shardRefs"]:
            shard_path = frozen_eval_v2_path / shard_ref
            assert shard_path.exists(), f"Shard {shard_ref} must exist"

    def test_committed_skill_bucket_minimums(self, frozen_eval_v2_path: Path) -> None:
        """Each skill bucket has at least 1000 positions."""
        manifest_path = frozen_eval_v2_path / "manifest.json"
        with manifest_path.open() as f:
            manifest_data = json.load(f)

        for bucket, count in manifest_data["countsBySkillBucketId"].items():
            assert count >= 1000, f"Bucket {bucket} has only {count} positions (min: 1000)"


class TestConstants:
    """Tests for M30 constants."""

    def test_m30_total_positions(self) -> None:
        """M30 total positions is locked at 10,000."""
        assert M30_TOTAL_POSITIONS == 10000

    def test_m30_min_per_skill_bucket(self) -> None:
        """M30 minimum per skill bucket is locked at 1,000."""
        assert M30_MIN_PER_SKILL_BUCKET == 1000

    def test_m30_selection_seed(self) -> None:
        """M30 selection seed is 42."""
        assert M30_SELECTION_SEED == 42

    def test_skill_buckets_count(self) -> None:
        """There are exactly 7 skill buckets."""
        assert len(SKILL_BUCKETS) == 7

    def test_fen_seeds_are_valid_fens(self) -> None:
        """All FEN seeds have the correct number of fields."""
        for fen in FEN_SEEDS:
            parts = fen.split(" ")
            assert len(parts) == 6, f"Invalid FEN: {fen}"

