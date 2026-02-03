"""Tests for M32 Post-Training Evaluation Pack.

This module tests:
- Schema validation for all M32 artifacts
- Pydantic model validation
- Delta computation logic
- Determinism of evaluation metrics
- CI-compatible validation (no checkpoint loading)
"""

from __future__ import annotations

import json
import math
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from renacechess.contracts.models import (
    DeltaMetricsArtifactV1,
    DeltaMetricsInlineV1,
    FrozenEvalIntegrityV1,
    HeadDeltaV1,
    OutcomeEvalMetricsArtifactV1,
    OutcomeEvalMetricsInlineV1,
    PolicyEvalMetricsArtifactV1,
    PolicyEvalMetricsInlineV1,
    PostTrainEvalReportV1,
    SkillBucketDeltaV1,
    SkillBucketEvalV1,
    SkillBucketOutcomeMetricsV1,
    SkillBucketPolicyMetricsV1,
)
from renacechess.determinism import canonical_json_dump


# =============================================================================
# Schema Path Helpers
# =============================================================================

SCHEMAS_DIR = Path(__file__).parent.parent / "src" / "renacechess" / "contracts" / "schemas" / "v1"


def load_schema(name: str) -> dict[str, Any]:
    """Load a JSON schema by name."""
    schema_path = SCHEMAS_DIR / name
    return json.loads(schema_path.read_text(encoding="utf-8"))


# =============================================================================
# Schema Existence Tests
# =============================================================================


class TestSchemaExistence:
    """Test that all M32 schemas exist and are valid JSON."""

    def test_post_train_eval_report_schema_exists(self) -> None:
        """PostTrainEvalReportV1 schema exists and is valid JSON."""
        schema = load_schema("post_train_eval_report.v1.schema.json")
        assert schema["title"] == "PostTrainEvalReportV1"
        assert schema["type"] == "object"
        assert "required" in schema
        assert "frozenEvalManifestHash" in schema["required"]

    def test_policy_eval_metrics_schema_exists(self) -> None:
        """PolicyEvalMetricsV1 schema exists and is valid JSON."""
        schema = load_schema("policy_eval_metrics.v1.schema.json")
        assert schema["title"] == "PolicyEvalMetricsV1"
        assert "top1Accuracy" in schema["required"]

    def test_outcome_eval_metrics_schema_exists(self) -> None:
        """OutcomeEvalMetricsV1 schema exists and is valid JSON."""
        schema = load_schema("outcome_eval_metrics.v1.schema.json")
        assert schema["title"] == "OutcomeEvalMetricsV1"
        assert "brierScore" in schema["required"]

    def test_delta_metrics_schema_exists(self) -> None:
        """DeltaMetricsV1 schema exists and is valid JSON."""
        schema = load_schema("delta_metrics.v1.schema.json")
        assert schema["title"] == "DeltaMetricsV1"
        assert "policyDelta" in schema["required"]


# =============================================================================
# Pydantic Model Tests
# =============================================================================


class TestPolicyEvalMetricsInlineV1:
    """Test PolicyEvalMetricsInlineV1 model."""

    def test_valid_metrics(self) -> None:
        """Valid metrics should be accepted."""
        metrics = PolicyEvalMetricsInlineV1(
            top1_accuracy=0.25,
            top3_accuracy=0.45,
            top5_accuracy=0.55,
            nll=2.5,
            entropy=3.0,
            samples_evaluated=1000,
        )
        assert metrics.top1_accuracy == 0.25
        assert metrics.nll == 2.5

    def test_json_serialization_uses_camel_case(self) -> None:
        """JSON output should use camelCase aliases."""
        metrics = PolicyEvalMetricsInlineV1(
            top1_accuracy=0.25,
            top3_accuracy=0.45,
            top5_accuracy=0.55,
            nll=2.5,
            entropy=3.0,
        )
        json_dict = metrics.model_dump(by_alias=True)
        assert "top1Accuracy" in json_dict
        assert "samplesEvaluated" in json_dict

    def test_accuracy_bounds(self) -> None:
        """Accuracy should be between 0 and 1."""
        with pytest.raises(ValueError):
            PolicyEvalMetricsInlineV1(
                top1_accuracy=1.5,  # Invalid: > 1.0
                top3_accuracy=0.45,
                top5_accuracy=0.55,
                nll=2.5,
                entropy=3.0,
            )


class TestOutcomeEvalMetricsInlineV1:
    """Test OutcomeEvalMetricsInlineV1 model."""

    def test_valid_metrics(self) -> None:
        """Valid metrics should be accepted."""
        metrics = OutcomeEvalMetricsInlineV1(
            accuracy=0.35,
            brier_score=0.45,
            nll=1.2,
            ece=0.08,
            samples_evaluated=1000,
        )
        assert metrics.accuracy == 0.35
        assert metrics.brier_score == 0.45

    def test_optional_per_outcome_accuracy(self) -> None:
        """Per-outcome accuracy fields are optional."""
        metrics = OutcomeEvalMetricsInlineV1(
            accuracy=0.35,
            brier_score=0.45,
            nll=1.2,
            ece=0.08,
            win_accuracy=0.4,
            draw_accuracy=0.2,
            loss_accuracy=0.45,
        )
        assert metrics.win_accuracy == 0.4
        assert metrics.draw_accuracy == 0.2


class TestDeltaMetricsInlineV1:
    """Test DeltaMetricsInlineV1 model."""

    def test_improved_direction(self) -> None:
        """Improved direction should be accepted."""
        delta = DeltaMetricsInlineV1(
            primary_metric="top1Accuracy",
            primary_metric_baseline=0.1,
            primary_metric_trained=0.25,
            primary_metric_delta=0.15,
            direction="improved",
            percentage_change=150.0,
            is_significant=True,
        )
        assert delta.direction == "improved"
        assert delta.is_significant is True

    def test_degraded_direction(self) -> None:
        """Degraded direction should be accepted."""
        delta = DeltaMetricsInlineV1(
            primary_metric="accuracy",
            primary_metric_baseline=0.4,
            primary_metric_trained=0.35,
            primary_metric_delta=-0.05,
            direction="degraded",
            is_significant=True,
        )
        assert delta.direction == "degraded"

    def test_unchanged_direction(self) -> None:
        """Unchanged direction should be accepted."""
        delta = DeltaMetricsInlineV1(
            primary_metric="entropy",
            primary_metric_delta=0.0,
            direction="unchanged",
            is_significant=False,
        )
        assert delta.direction == "unchanged"


class TestPostTrainEvalReportV1:
    """Test PostTrainEvalReportV1 model."""

    def test_valid_report(self) -> None:
        """Valid report should be accepted."""
        now = datetime.now(UTC)

        trained_policy = PolicyEvalMetricsInlineV1(
            top1_accuracy=0.25,
            top3_accuracy=0.45,
            top5_accuracy=0.55,
            nll=2.5,
            entropy=3.0,
        )
        trained_outcome = OutcomeEvalMetricsInlineV1(
            accuracy=0.4,
            brier_score=0.4,
            nll=1.0,
            ece=0.05,
        )
        baseline_policy = PolicyEvalMetricsInlineV1(
            top1_accuracy=0.1,
            top3_accuracy=0.2,
            top5_accuracy=0.3,
            nll=4.0,
            entropy=4.0,
        )
        baseline_outcome = OutcomeEvalMetricsInlineV1(
            accuracy=0.33,
            brier_score=0.5,
            nll=1.1,
            ece=0.1,
        )
        policy_delta = DeltaMetricsInlineV1(
            primary_metric="top1Accuracy",
            primary_metric_delta=0.15,
            direction="improved",
            is_significant=True,
        )
        outcome_delta = DeltaMetricsInlineV1(
            primary_metric="accuracy",
            primary_metric_delta=0.07,
            direction="improved",
            is_significant=True,
        )

        report = PostTrainEvalReportV1(
            version="1.0",
            generated_at=now,
            frozen_eval_manifest_hash="sha256:" + "a" * 64,
            training_run_report_hash="sha256:" + "b" * 64,
            policy_checkpoint_hash="sha256:" + "c" * 64,
            outcome_checkpoint_hash="sha256:" + "d" * 64,
            eval_baseline_seed=1337,
            positions_evaluated=10000,
            trained_policy_metrics=trained_policy,
            trained_outcome_metrics=trained_outcome,
            baseline_policy_metrics=baseline_policy,
            baseline_outcome_metrics=baseline_outcome,
            policy_delta=policy_delta,
            outcome_delta=outcome_delta,
            determinism_hash="sha256:" + "e" * 64,
        )

        assert report.eval_baseline_seed == 1337
        assert report.positions_evaluated == 10000

    def test_invalid_hash_format(self) -> None:
        """Invalid hash format should be rejected."""
        now = datetime.now(UTC)

        trained_policy = PolicyEvalMetricsInlineV1(
            top1_accuracy=0.25,
            top3_accuracy=0.45,
            top5_accuracy=0.55,
            nll=2.5,
            entropy=3.0,
        )
        trained_outcome = OutcomeEvalMetricsInlineV1(
            accuracy=0.4,
            brier_score=0.4,
            nll=1.0,
            ece=0.05,
        )
        baseline_policy = PolicyEvalMetricsInlineV1(
            top1_accuracy=0.1,
            top3_accuracy=0.2,
            top5_accuracy=0.3,
            nll=4.0,
            entropy=4.0,
        )
        baseline_outcome = OutcomeEvalMetricsInlineV1(
            accuracy=0.33,
            brier_score=0.5,
            nll=1.1,
            ece=0.1,
        )
        policy_delta = DeltaMetricsInlineV1(
            primary_metric="top1Accuracy",
            primary_metric_delta=0.15,
            direction="improved",
            is_significant=True,
        )
        outcome_delta = DeltaMetricsInlineV1(
            primary_metric="accuracy",
            primary_metric_delta=0.07,
            direction="improved",
            is_significant=True,
        )

        with pytest.raises(ValueError):
            PostTrainEvalReportV1(
                version="1.0",
                generated_at=now,
                frozen_eval_manifest_hash="invalid-hash",  # Invalid format
                training_run_report_hash="sha256:" + "b" * 64,
                policy_checkpoint_hash="sha256:" + "c" * 64,
                outcome_checkpoint_hash="sha256:" + "d" * 64,
                eval_baseline_seed=1337,
                positions_evaluated=10000,
                trained_policy_metrics=trained_policy,
                trained_outcome_metrics=trained_outcome,
                baseline_policy_metrics=baseline_policy,
                baseline_outcome_metrics=baseline_outcome,
                policy_delta=policy_delta,
                outcome_delta=outcome_delta,
                determinism_hash="sha256:" + "e" * 64,
            )


class TestFrozenEvalIntegrityV1:
    """Test FrozenEvalIntegrityV1 model."""

    def test_valid_integrity(self) -> None:
        """Valid integrity proof should be accepted."""
        integrity = FrozenEvalIntegrityV1(
            manifest_hash="sha256:" + "a" * 64,
            position_count=10000,
            shard_count=10,
            skill_bucket_counts={"lt_800": 1429, "800_999": 1429},
            no_training_overlap=True,
            iteration_deterministic=True,
        )
        assert integrity.position_count == 10000
        assert integrity.no_training_overlap is True


class TestSkillBucketEvalV1:
    """Test SkillBucketEvalV1 model."""

    def test_valid_bucket_eval(self) -> None:
        """Valid bucket evaluation should be accepted."""
        trained_policy = PolicyEvalMetricsInlineV1(
            top1_accuracy=0.25,
            top3_accuracy=0.45,
            top5_accuracy=0.55,
            nll=2.5,
            entropy=3.0,
        )

        bucket = SkillBucketEvalV1(
            skill_bucket="1200_1399",
            samples=1429,
            trained_policy_metrics=trained_policy,
        )
        assert bucket.samples == 1429


# =============================================================================
# Delta Computation Tests
# =============================================================================


class TestDeltaComputation:
    """Test delta metric computation logic."""

    def test_improved_delta_higher_is_better(self) -> None:
        """Positive delta with higher-is-better should be 'improved'."""
        from renacechess.eval.post_train_eval import compute_delta

        baseline = PolicyEvalMetricsInlineV1(
            top1_accuracy=0.1,
            top3_accuracy=0.2,
            top5_accuracy=0.3,
            nll=4.0,
            entropy=4.0,
        )
        trained = PolicyEvalMetricsInlineV1(
            top1_accuracy=0.25,
            top3_accuracy=0.45,
            top5_accuracy=0.55,
            nll=2.5,
            entropy=3.0,
        )

        delta = compute_delta(baseline, trained, "top1_accuracy", higher_is_better=True)
        assert delta.direction == "improved"
        assert delta.primary_metric_delta == pytest.approx(0.15, abs=0.001)
        assert delta.is_significant is True

    def test_degraded_delta_higher_is_better(self) -> None:
        """Negative delta with higher-is-better should be 'degraded'."""
        from renacechess.eval.post_train_eval import compute_delta

        baseline = PolicyEvalMetricsInlineV1(
            top1_accuracy=0.3,
            top3_accuracy=0.5,
            top5_accuracy=0.6,
            nll=2.0,
            entropy=3.0,
        )
        trained = PolicyEvalMetricsInlineV1(
            top1_accuracy=0.2,
            top3_accuracy=0.4,
            top5_accuracy=0.5,
            nll=2.5,
            entropy=3.5,
        )

        delta = compute_delta(baseline, trained, "top1_accuracy", higher_is_better=True)
        assert delta.direction == "degraded"
        assert delta.is_significant is True

    def test_improved_delta_lower_is_better(self) -> None:
        """Negative delta with lower-is-better should be 'improved'."""
        from renacechess.eval.post_train_eval import compute_delta

        baseline = OutcomeEvalMetricsInlineV1(
            accuracy=0.33,
            brier_score=0.5,
            nll=1.5,
            ece=0.15,
        )
        trained = OutcomeEvalMetricsInlineV1(
            accuracy=0.4,
            brier_score=0.35,
            nll=1.0,
            ece=0.08,
        )

        delta = compute_delta(baseline, trained, "brier_score", higher_is_better=False)
        assert delta.direction == "improved"

    def test_unchanged_delta(self) -> None:
        """Zero delta should be 'unchanged'."""
        from renacechess.eval.post_train_eval import compute_delta

        metrics = PolicyEvalMetricsInlineV1(
            top1_accuracy=0.25,
            top3_accuracy=0.45,
            top5_accuracy=0.55,
            nll=2.5,
            entropy=3.0,
        )

        delta = compute_delta(metrics, metrics, "top1_accuracy", higher_is_better=True)
        assert delta.direction == "unchanged"
        assert delta.primary_metric_delta == pytest.approx(0.0, abs=1e-9)
        assert delta.is_significant is False

    def test_percentage_change(self) -> None:
        """Percentage change should be calculated correctly."""
        from renacechess.eval.post_train_eval import compute_delta

        baseline = PolicyEvalMetricsInlineV1(
            top1_accuracy=0.1,
            top3_accuracy=0.2,
            top5_accuracy=0.3,
            nll=4.0,
            entropy=4.0,
        )
        trained = PolicyEvalMetricsInlineV1(
            top1_accuracy=0.15,
            top3_accuracy=0.25,
            top5_accuracy=0.35,
            nll=3.0,
            entropy=3.5,
        )

        delta = compute_delta(baseline, trained, "top1_accuracy", higher_is_better=True)
        # (0.15 - 0.1) / 0.1 * 100 = 50%
        assert delta.percentage_change == pytest.approx(50.0, abs=0.1)


# =============================================================================
# Accumulator Tests
# =============================================================================


class TestPolicyMetricsAccumulator:
    """Test PolicyMetricsAccumulator."""

    def test_top1_accuracy(self) -> None:
        """Top-1 accuracy should count exact matches."""
        from renacechess.eval.post_train_eval import PolicyMetricsAccumulator

        acc = PolicyMetricsAccumulator()
        acc.add({"e2e4": 0.5, "d2d4": 0.3, "c2c4": 0.2}, "e2e4")  # Top-1 match
        acc.add({"e2e4": 0.5, "d2d4": 0.3, "c2c4": 0.2}, "d2d4")  # Not top-1

        metrics = acc.compute()
        assert metrics.top1_accuracy == pytest.approx(0.5, abs=0.01)
        assert metrics.top3_accuracy == pytest.approx(1.0, abs=0.01)

    def test_entropy_calculation(self) -> None:
        """Entropy should be calculated correctly."""
        from renacechess.eval.post_train_eval import PolicyMetricsAccumulator

        acc = PolicyMetricsAccumulator()
        # Uniform distribution over 2 moves: entropy = -2 * 0.5 * ln(0.5) = ln(2) ≈ 0.693
        acc.add({"e2e4": 0.5, "d2d4": 0.5}, "e2e4")

        metrics = acc.compute()
        assert metrics.entropy == pytest.approx(math.log(2), abs=0.01)

    def test_nll_calculation(self) -> None:
        """NLL should be calculated correctly."""
        from renacechess.eval.post_train_eval import PolicyMetricsAccumulator

        acc = PolicyMetricsAccumulator()
        # If chosen move has probability 0.5, NLL = -ln(0.5) = ln(2) ≈ 0.693
        acc.add({"e2e4": 0.5, "d2d4": 0.5}, "e2e4")

        metrics = acc.compute()
        assert metrics.nll == pytest.approx(math.log(2), abs=0.01)


class TestOutcomeMetricsAccumulator:
    """Test OutcomeMetricsAccumulator."""

    def test_accuracy(self) -> None:
        """Accuracy should count correct predictions."""
        from renacechess.eval.post_train_eval import OutcomeMetricsAccumulator

        acc = OutcomeMetricsAccumulator()
        acc.add({"w": 0.5, "d": 0.3, "l": 0.2}, "win")  # Correct (w is max)
        acc.add({"w": 0.3, "d": 0.5, "l": 0.2}, "win")  # Wrong (d is max)

        metrics = acc.compute()
        assert metrics.accuracy == pytest.approx(0.5, abs=0.01)

    def test_brier_score(self) -> None:
        """Brier score should measure calibration."""
        from renacechess.eval.post_train_eval import OutcomeMetricsAccumulator

        acc = OutcomeMetricsAccumulator()
        # Perfect prediction for win: (0-0)^2 + (0-0)^2 + (1-1)^2 = 0
        acc.add({"w": 1.0, "d": 0.0, "l": 0.0}, "win")

        metrics = acc.compute()
        assert metrics.brier_score == pytest.approx(0.0, abs=0.01)


# =============================================================================
# Standalone Artifact Tests
# =============================================================================


class TestPolicyEvalMetricsArtifactV1:
    """Test PolicyEvalMetricsArtifactV1 standalone artifact."""

    def test_valid_artifact(self) -> None:
        """Valid artifact should be accepted."""
        now = datetime.now(UTC)
        artifact = PolicyEvalMetricsArtifactV1(
            version="1.0",
            generated_at=now,
            source_manifest_hash="sha256:" + "a" * 64,
            model_id="trained",
            checkpoint_hash="sha256:" + "b" * 64,
            top1_accuracy=0.25,
            top3_accuracy=0.45,
            top5_accuracy=0.55,
            nll=2.5,
            entropy=3.0,
            samples_evaluated=10000,
            determinism_hash="sha256:" + "c" * 64,
        )
        assert artifact.model_id == "trained"


class TestOutcomeEvalMetricsArtifactV1:
    """Test OutcomeEvalMetricsArtifactV1 standalone artifact."""

    def test_valid_artifact(self) -> None:
        """Valid artifact should be accepted."""
        now = datetime.now(UTC)
        artifact = OutcomeEvalMetricsArtifactV1(
            version="1.0",
            generated_at=now,
            source_manifest_hash="sha256:" + "a" * 64,
            model_id="baseline-1337",
            accuracy=0.35,
            brier_score=0.45,
            nll=1.2,
            ece=0.08,
            samples_evaluated=10000,
            determinism_hash="sha256:" + "c" * 64,
        )
        assert artifact.model_id == "baseline-1337"


class TestDeltaMetricsArtifactV1:
    """Test DeltaMetricsArtifactV1 standalone artifact."""

    def test_valid_artifact(self) -> None:
        """Valid artifact should be accepted."""
        now = datetime.now(UTC)
        policy_delta = HeadDeltaV1(
            primary_metric="top1Accuracy",
            primary_metric_delta=0.15,
            direction="improved",
            is_significant=True,
        )
        outcome_delta = HeadDeltaV1(
            primary_metric="accuracy",
            primary_metric_delta=0.07,
            direction="improved",
            is_significant=True,
        )

        artifact = DeltaMetricsArtifactV1(
            version="1.0",
            generated_at=now,
            baseline_model_id="baseline-1337",
            trained_model_id="trained",
            eval_baseline_seed=1337,
            policy_delta=policy_delta,
            outcome_delta=outcome_delta,
            determinism_hash="sha256:" + "c" * 64,
        )
        assert artifact.eval_baseline_seed == 1337


# =============================================================================
# Constants Tests
# =============================================================================


class TestM32Constants:
    """Test M32 constants and configuration."""

    def test_eval_baseline_seed_is_1337(self) -> None:
        """Baseline seed should be 1337 per locked decision."""
        from renacechess.eval.post_train_eval import M32_EVAL_BASELINE_SEED

        assert M32_EVAL_BASELINE_SEED == 1337

    def test_significance_threshold_is_1_percent(self) -> None:
        """Significance threshold should be 1%."""
        from renacechess.eval.post_train_eval import SIGNIFICANCE_THRESHOLD

        assert SIGNIFICANCE_THRESHOLD == 0.01


# =============================================================================
# Skill Bucket Tests
# =============================================================================


class TestSkillBucketModels:
    """Test per-skill bucket models."""

    def test_skill_bucket_policy_metrics(self) -> None:
        """SkillBucketPolicyMetricsV1 should be valid."""
        metrics = SkillBucketPolicyMetricsV1(
            skill_bucket="1200_1399",
            samples=1429,
            top1_accuracy=0.25,
            top3_accuracy=0.45,
            top5_accuracy=0.55,
            nll=2.5,
            entropy=3.0,
        )
        assert metrics.skill_bucket == "1200_1399"

    def test_skill_bucket_outcome_metrics(self) -> None:
        """SkillBucketOutcomeMetricsV1 should be valid."""
        metrics = SkillBucketOutcomeMetricsV1(
            skill_bucket="gte_1800",
            samples=1428,
            accuracy=0.4,
            brier_score=0.35,
            nll=1.0,
            ece=0.05,
        )
        assert metrics.skill_bucket == "gte_1800"

    def test_skill_bucket_delta(self) -> None:
        """SkillBucketDeltaV1 should be valid."""
        policy_delta = HeadDeltaV1(
            primary_metric="top1Accuracy",
            primary_metric_delta=0.1,
            direction="improved",
            is_significant=True,
        )
        outcome_delta = HeadDeltaV1(
            primary_metric="accuracy",
            primary_metric_delta=0.05,
            direction="improved",
            is_significant=True,
        )

        bucket_delta = SkillBucketDeltaV1(
            skill_bucket="lt_800",
            samples=1429,
            policy_delta=policy_delta,
            outcome_delta=outcome_delta,
        )
        assert bucket_delta.samples == 1429


# =============================================================================
# Determinism Tests
# =============================================================================


class TestDeterminism:
    """Test determinism of M32 artifacts."""

    def test_canonical_json_produces_stable_hash(self) -> None:
        """Canonical JSON should produce stable hashes."""
        import hashlib

        data = {
            "version": "1.0",
            "positions": 10000,
            "nested": {"a": 1, "b": 2},
        }

        # Compute hash twice
        json1 = canonical_json_dump(data)
        json2 = canonical_json_dump(data)

        hash1 = hashlib.sha256(json1).hexdigest()
        hash2 = hashlib.sha256(json2).hexdigest()

        assert hash1 == hash2

    def test_pydantic_model_dump_is_deterministic(self) -> None:
        """Pydantic model dump should be deterministic."""
        import hashlib

        now = datetime.now(UTC)
        metrics = PolicyEvalMetricsInlineV1(
            top1_accuracy=0.25,
            top3_accuracy=0.45,
            top5_accuracy=0.55,
            nll=2.5,
            entropy=3.0,
        )

        json1 = canonical_json_dump(metrics.model_dump(mode="json", by_alias=True))
        json2 = canonical_json_dump(metrics.model_dump(mode="json", by_alias=True))

        hash1 = hashlib.sha256(json1).hexdigest()
        hash2 = hashlib.sha256(json2).hexdigest()

        assert hash1 == hash2

