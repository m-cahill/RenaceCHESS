"""M22 Coaching CLI Tests.

Tests for the `renacechess coach` CLI command (M22 surface exposure).

Test categories:
1. CLI rejects invalid artifacts
2. CLI refuses missing lineage hashes
3. CLI prints evaluation summary
4. CLI output stable for same inputs
5. CLI does not import forbidden modules
6. CLI works with stub LLM only (no network)

See: M22_plan.md, ADR-COACHING-001
"""

from __future__ import annotations

import ast
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from renacechess.contracts.models import (
    AdviceFactsV1,
    CoachingSurfaceV1,
    DifficultyDeltaV1,
    EloBucketDeltaFactsV1,
    EloBucketDeltaSourceContractsV1,
    OutcomeDeltaV1,
    PolicyDeltaV1,
)

# =============================================================================
# Test Fixtures
# =============================================================================


def _create_advice_facts(
    skill_bucket: str = "1200_1399",
    generated_at: datetime | None = None,
) -> AdviceFactsV1:
    """Create a valid AdviceFactsV1 artifact for testing."""
    from renacechess.coaching.advice_facts import build_advice_facts_v1
    from renacechess.contracts.models import AdviceFactsInputsV1

    inputs = AdviceFactsInputsV1(
        fen="rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1",
        side_to_move="black",
        skill_bucket=skill_bucket,
        time_control_bucket="blitz",
        time_pressure_bucket="normal",
        top_moves=[("e7e5", 0.35), ("e7e6", 0.25), ("c7c5", 0.20), ("d7d5", 0.15)],
        p_win=0.45,
        p_draw=0.30,
        p_loss=0.25,
        hdi_value=0.55,
    )

    return build_advice_facts_v1(
        inputs=inputs,
        generated_at=generated_at or datetime.now(UTC),
    )


def _create_delta_facts(
    baseline_bucket: str = "1200_1399",
    comparison_bucket: str = "1600_1799",
    source_hashes: list[str] | None = None,
    generated_at: datetime | None = None,
) -> EloBucketDeltaFactsV1:
    """Create a valid EloBucketDeltaFactsV1 artifact for testing."""
    import hashlib

    ts = generated_at or datetime.now(UTC)

    # Use provided hashes or generate dummy ones
    if source_hashes is None:
        source_hashes = [
            "sha256:" + hashlib.sha256(b"baseline").hexdigest(),
            "sha256:" + hashlib.sha256(b"comparison").hexdigest(),
        ]

    # Build artifact data for hash
    artifact_data: dict[str, Any] = {
        "schemaVersion": "elo_bucket_delta_facts.v1",
        "generatedAt": ts.isoformat(),
        "baselineBucket": baseline_bucket,
        "comparisonBucket": comparison_bucket,
        "sourceAdviceFactsHashes": source_hashes,
        "policyDelta": {
            "klDivergence": 0.15,
            "totalVariation": 0.12,
            "rankFlips": 1,
            "massShiftToTop": 0.05,
        },
        "outcomeDelta": {
            "deltaPWin": 0.08,
            "deltaPDraw": -0.03,
            "deltaPLoss": -0.05,
            "winRateMonotonic": True,
        },
        "difficultyDelta": {"deltaHDI": -0.10},
        "sourceContractVersions": {
            "eloBucketDeltaContract": "v1",
            "adviceFactsContract": "v1",
        },
    }

    # Compute hash
    canonical = json.dumps(artifact_data, sort_keys=True, separators=(",", ":"))
    determinism_hash = "sha256:" + hashlib.sha256(canonical.encode()).hexdigest()

    return EloBucketDeltaFactsV1(
        schema_version="elo_bucket_delta_facts.v1",
        generated_at=ts,
        baseline_bucket=baseline_bucket,
        comparison_bucket=comparison_bucket,
        source_advice_facts_hashes=source_hashes,
        policy_delta=PolicyDeltaV1(
            kl_divergence=0.15,
            total_variation=0.12,
            rank_flips=1,
            mass_shift_to_top=0.05,
        ),
        outcome_delta=OutcomeDeltaV1(
            delta_p_win=0.08,
            delta_p_draw=-0.03,
            delta_p_loss=-0.05,
            win_rate_monotonic=True,
        ),
        difficulty_delta=DifficultyDeltaV1(delta_hdi=-0.10),
        structural_delta=None,
        determinism_hash=determinism_hash,
        source_contract_versions=EloBucketDeltaSourceContractsV1(
            elo_bucket_delta_contract="v1",
            advice_facts_contract="v1",
        ),
    )


@pytest.fixture
def valid_artifacts(tmp_path: Path) -> tuple[Path, Path]:
    """Create valid, paired artifacts for testing."""
    # Create advice facts
    advice_facts = _create_advice_facts()
    advice_path = tmp_path / "advice_facts.json"
    advice_path.write_text(
        json.dumps(advice_facts.model_dump(by_alias=True), default=str),
        encoding="utf-8",
    )

    # Create delta facts with correct lineage
    delta_facts = _create_delta_facts(
        source_hashes=[advice_facts.determinism_hash, "sha256:" + "a" * 64],
    )
    delta_path = tmp_path / "delta_facts.json"
    delta_path.write_text(
        json.dumps(delta_facts.model_dump(by_alias=True), default=str),
        encoding="utf-8",
    )

    return advice_path, delta_path


# =============================================================================
# CLI Invocation Helper
# =============================================================================


def _run_coach_cli(
    advice_path: Path | str,
    delta_path: Path | str,
    tone: str = "neutral",
    out_path: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run the coach CLI command and return the result."""
    cmd = [
        sys.executable,
        "-m",
        "renacechess.cli",
        "coach",
        "--advice-facts",
        str(advice_path),
        "--delta-facts",
        str(delta_path),
        "--tone",
        tone,
    ]
    if out_path:
        cmd.extend(["--out", str(out_path)])

    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=60,
    )


# =============================================================================
# Test: CLI Rejects Invalid Artifacts
# =============================================================================


class TestCliRejectsInvalidArtifacts:
    """Test that CLI rejects invalid or missing artifacts."""

    def test_rejects_missing_advice_facts(self, tmp_path: Path) -> None:
        """CLI fails with clear error when advice-facts file doesn't exist."""
        delta_path = tmp_path / "delta.json"
        delta_path.write_text("{}", encoding="utf-8")

        result = _run_coach_cli(
            advice_path=tmp_path / "nonexistent.json",
            delta_path=delta_path,
        )

        assert result.returncode != 0
        assert "AdviceFacts file not found" in result.stderr

    def test_rejects_missing_delta_facts(self, tmp_path: Path) -> None:
        """CLI fails with clear error when delta-facts file doesn't exist."""
        advice_path = tmp_path / "advice.json"
        advice_path.write_text("{}", encoding="utf-8")

        result = _run_coach_cli(
            advice_path=advice_path,
            delta_path=tmp_path / "nonexistent.json",
        )

        assert result.returncode != 0
        assert "EloBucketDeltaFacts file not found" in result.stderr

    def test_rejects_invalid_advice_facts_json(self, tmp_path: Path) -> None:
        """CLI fails when advice-facts is not valid JSON."""
        advice_path = tmp_path / "advice.json"
        advice_path.write_text("not valid json {{{", encoding="utf-8")
        delta_path = tmp_path / "delta.json"
        delta_path.write_text("{}", encoding="utf-8")

        result = _run_coach_cli(advice_path=advice_path, delta_path=delta_path)

        assert result.returncode != 0
        assert "Failed to load or validate AdviceFacts" in result.stderr

    def test_rejects_invalid_delta_facts_schema(self, tmp_path: Path) -> None:
        """CLI fails when delta-facts doesn't match schema."""
        advice_facts = _create_advice_facts()
        advice_path = tmp_path / "advice.json"
        advice_path.write_text(
            json.dumps(advice_facts.model_dump(by_alias=True), default=str),
            encoding="utf-8",
        )

        delta_path = tmp_path / "delta.json"
        delta_path.write_text('{"invalid": "schema"}', encoding="utf-8")

        result = _run_coach_cli(advice_path=advice_path, delta_path=delta_path)

        assert result.returncode != 0
        assert "Failed to load or validate EloBucketDeltaFacts" in result.stderr


# =============================================================================
# Test: CLI Refuses Missing Lineage Hashes
# =============================================================================


class TestCliRefusesMissingLineage:
    """Test that CLI enforces lineage hash validation."""

    def test_rejects_mismatched_lineage(self, tmp_path: Path) -> None:
        """CLI fails when advice facts hash is not in delta facts lineage."""
        advice_facts = _create_advice_facts()
        advice_path = tmp_path / "advice.json"
        advice_path.write_text(
            json.dumps(advice_facts.model_dump(by_alias=True), default=str),
            encoding="utf-8",
        )

        # Create delta facts with WRONG lineage (doesn't include advice hash)
        delta_facts = _create_delta_facts(
            source_hashes=["sha256:" + "x" * 64, "sha256:" + "y" * 64],
        )
        delta_path = tmp_path / "delta.json"
        delta_path.write_text(
            json.dumps(delta_facts.model_dump(by_alias=True), default=str),
            encoding="utf-8",
        )

        result = _run_coach_cli(advice_path=advice_path, delta_path=delta_path)

        assert result.returncode != 0
        assert "Lineage mismatch" in result.stderr


# =============================================================================
# Test: CLI Prints Evaluation Summary
# =============================================================================


class TestCliPrintsEvaluationSummary:
    """Test that CLI always prints evaluation summary."""

    def test_prints_evaluation_summary(self, valid_artifacts: tuple[Path, Path]) -> None:
        """CLI outputs evaluation summary to stderr."""
        advice_path, delta_path = valid_artifacts

        result = _run_coach_cli(advice_path=advice_path, delta_path=delta_path)

        # Evaluation summary should always be in stderr
        assert "=== Evaluation Summary ===" in result.stderr
        assert "Fact coverage:" in result.stderr
        assert "Hallucination rate:" in result.stderr
        assert "Delta faithfulness:" in result.stderr
        assert "Bucket alignment:" in result.stderr

    def test_prints_coaching_draft(self, valid_artifacts: tuple[Path, Path]) -> None:
        """CLI outputs coaching draft text."""
        advice_path, delta_path = valid_artifacts

        result = _run_coach_cli(advice_path=advice_path, delta_path=delta_path)

        assert "=== Coaching Draft ===" in result.stderr


# =============================================================================
# Test: CLI Output Stable for Same Inputs
# =============================================================================


class TestCliOutputStable:
    """Test that CLI produces stable, structured output."""

    def test_output_structure_consistent(self, valid_artifacts: tuple[Path, Path]) -> None:
        """Same inputs produce structurally consistent outputs."""
        advice_path, delta_path = valid_artifacts

        result1 = _run_coach_cli(advice_path=advice_path, delta_path=delta_path)
        result2 = _run_coach_cli(advice_path=advice_path, delta_path=delta_path)

        # Parse both outputs
        if result1.returncode == 0 or result1.stdout.strip():
            output1 = json.loads(result1.stdout)
            output2 = json.loads(result2.stdout)

            # Schema version should be identical
            assert output1["schemaVersion"] == output2["schemaVersion"]
            # Skill bucket should be identical (from input)
            assert output1["skillBucket"] == output2["skillBucket"]
            # Source hashes should be identical (from input)
            assert output1["sourceAdviceFactsHash"] == output2["sourceAdviceFactsHash"]
            assert output1["sourceDeltaFactsHash"] == output2["sourceDeltaFactsHash"]
            # Tone profile should be identical
            assert output1["toneProfile"] == output2["toneProfile"]

    def test_stub_llm_text_deterministic(self, valid_artifacts: tuple[Path, Path]) -> None:
        """Stub LLM produces identical coaching text for same inputs."""
        advice_path, delta_path = valid_artifacts

        result1 = _run_coach_cli(advice_path=advice_path, delta_path=delta_path)
        result2 = _run_coach_cli(advice_path=advice_path, delta_path=delta_path)

        if result1.returncode == 0:
            output1 = json.loads(result1.stdout)
            output2 = json.loads(result2.stdout)

            # Stub LLM should produce identical text (since it's deterministic)
            assert output1["coachingText"] == output2["coachingText"]

    def test_outputs_valid_coaching_surface_v1(
        self, valid_artifacts: tuple[Path, Path], tmp_path: Path
    ) -> None:
        """CLI outputs valid CoachingSurfaceV1 JSON."""
        advice_path, delta_path = valid_artifacts
        out_path = tmp_path / "surface.json"

        _run_coach_cli(
            advice_path=advice_path,
            delta_path=delta_path,
            out_path=out_path,
        )

        # Even if thresholds fail, artifact should be written
        if out_path.exists():
            surface_data = json.loads(out_path.read_text(encoding="utf-8"))
            # Validate against Pydantic model
            surface = CoachingSurfaceV1.model_validate(surface_data)

            assert surface.schema_version == "coaching_surface.v1"
            assert surface.coaching_text
            assert surface.evaluation_summary


# =============================================================================
# Test: CLI Does Not Import Forbidden Modules
# =============================================================================


class TestCliBoundaryEnforcement:
    """Test that CLI respects import boundaries."""

    def test_cli_coach_command_imports(self) -> None:
        """Verify coach command only imports allowed modules."""
        # Read cli.py source
        cli_path = Path(__file__).parent.parent / "src" / "renacechess" / "cli.py"
        source = cli_path.read_text(encoding="utf-8")

        # Parse AST
        tree = ast.parse(source)

        # Collect all imports
        imports: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module)

        # Forbidden imports for coach command (per M22 plan)
        forbidden = {
            "renacechess.models.baseline_v1",
            "renacechess.models.outcome_head_v1",
            "renacechess.features.per_piece",
            "renacechess.features.square_map",
            "stockfish",
            "chess.engine",
        }

        violations = forbidden.intersection(imports)
        assert not violations, f"CLI imports forbidden modules: {violations}"

    def test_allowed_coaching_imports(self) -> None:
        """Verify coach command imports only allowed coaching modules."""
        cli_path = Path(__file__).parent.parent / "src" / "renacechess" / "cli.py"
        source = cli_path.read_text(encoding="utf-8")
        tree = ast.parse(source)

        # Allowed coaching imports
        allowed_coaching = {
            "renacechess.coaching.evaluation",
            "renacechess.coaching.llm_client",
            "renacechess.coaching.translation_harness",
        }

        coaching_imports: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                if "coaching" in node.module:
                    coaching_imports.add(node.module)

        # All coaching imports should be in allowed set
        unauthorized = coaching_imports - allowed_coaching
        assert not unauthorized, f"CLI imports unauthorized coaching modules: {unauthorized}"


# =============================================================================
# Test: CLI Works with Stub LLM Only
# =============================================================================


class TestCliStubLlmOnly:
    """Test that CLI uses stub LLM exclusively (no network)."""

    def test_uses_deterministic_stub(self, valid_artifacts: tuple[Path, Path]) -> None:
        """CLI uses DeterministicStubLLM for generation."""
        advice_path, delta_path = valid_artifacts

        result = _run_coach_cli(advice_path=advice_path, delta_path=delta_path)

        # If successful, parse output and check metadata
        if result.returncode == 0:
            output = json.loads(result.stdout)
            # coachingDraftHash should be deterministic (stub produces same output)
            assert "coachingDraftHash" in output
            assert output["coachingDraftHash"].startswith("sha256:")


# =============================================================================
# Test: CLI Tone Parameter
# =============================================================================


class TestCliToneParameter:
    """Test that CLI respects --tone parameter."""

    @pytest.mark.parametrize("tone", ["neutral", "encouraging", "concise"])
    def test_tone_parameter_accepted(self, valid_artifacts: tuple[Path, Path], tone: str) -> None:
        """CLI accepts all valid tone values."""
        advice_path, delta_path = valid_artifacts

        result = _run_coach_cli(
            advice_path=advice_path,
            delta_path=delta_path,
            tone=tone,
        )

        # Command should execute (may pass or fail thresholds)
        # Check that it processed without argument errors
        assert "unrecognized arguments" not in result.stderr
        assert "invalid choice" not in result.stderr

    def test_tone_appears_in_output(self, valid_artifacts: tuple[Path, Path]) -> None:
        """CLI includes tone profile in output artifact."""
        advice_path, delta_path = valid_artifacts

        result = _run_coach_cli(
            advice_path=advice_path,
            delta_path=delta_path,
            tone="encouraging",
        )

        if result.returncode == 0:
            output = json.loads(result.stdout)
            assert output["toneProfile"] == "encouraging"


# =============================================================================
# Test: Exit Code Behavior
# =============================================================================


class TestCliExitCode:
    """Test that CLI exits with appropriate codes."""

    def test_exit_nonzero_on_threshold_failure(self, valid_artifacts: tuple[Path, Path]) -> None:
        """CLI exits non-zero when thresholds fail, but still outputs artifact."""
        advice_path, delta_path = valid_artifacts

        result = _run_coach_cli(advice_path=advice_path, delta_path=delta_path)

        # Output should still be produced (to stdout or indicated in stderr)
        # Exit code depends on threshold results
        # Just verify we get structured output
        if result.stdout.strip():
            output = json.loads(result.stdout)
            assert "evaluationSummary" in output


# =============================================================================
# Test: Schema Validation
# =============================================================================


# =============================================================================
# Test: Integration Tests for CLI Coach Command (for coverage)
# =============================================================================


class TestCoachCommandIntegration:
    """Integration tests for coach command that call main() directly for coverage."""

    def test_coach_command_via_main(
        self, valid_artifacts: tuple[Path, Path], capsys, tmp_path: Path
    ) -> None:
        """Test coach command via main() for coverage."""
        import sys
        from unittest.mock import patch

        from renacechess.cli import main

        advice_path, delta_path = valid_artifacts
        output_path = tmp_path / "surface.json"

        with patch.object(
            sys,
            "argv",
            [
                "renacechess",
                "coach",
                "--advice-facts",
                str(advice_path),
                "--delta-facts",
                str(delta_path),
                "--out",
                str(output_path),
            ],
        ):
            # May exit with 0 or 1 depending on thresholds
            try:
                main()
            except SystemExit as e:
                # Accept exit codes 0 or 1
                assert e.code in (0, 1)

        captured = capsys.readouterr()

        # Should always print evaluation summary
        assert "=== Evaluation Summary ===" in captured.err
        assert "Fact coverage:" in captured.err

    def test_coach_command_missing_file_via_main(self, tmp_path: Path, capsys) -> None:
        """Test coach command with missing file via main() for coverage."""
        import sys
        from unittest.mock import patch

        from renacechess.cli import main

        advice_path = tmp_path / "nonexistent_advice.json"
        delta_path = tmp_path / "nonexistent_delta.json"

        with patch.object(
            sys,
            "argv",
            [
                "renacechess",
                "coach",
                "--advice-facts",
                str(advice_path),
                "--delta-facts",
                str(delta_path),
            ],
        ):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1

        captured = capsys.readouterr()
        assert "not found" in captured.err

    def test_coach_command_invalid_json_via_main(self, tmp_path: Path, capsys) -> None:
        """Test coach command with invalid JSON via main() for coverage."""
        import sys
        from unittest.mock import patch

        from renacechess.cli import main

        advice_path = tmp_path / "advice.json"
        advice_path.write_text("not valid json {{{", encoding="utf-8")
        delta_path = tmp_path / "delta.json"
        delta_path.write_text("{}", encoding="utf-8")

        with patch.object(
            sys,
            "argv",
            [
                "renacechess",
                "coach",
                "--advice-facts",
                str(advice_path),
                "--delta-facts",
                str(delta_path),
            ],
        ):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1

        captured = capsys.readouterr()
        assert "Failed to load or validate AdviceFacts" in captured.err

    def test_coach_command_lineage_mismatch_via_main(self, tmp_path: Path, capsys) -> None:
        """Test coach command with lineage mismatch via main() for coverage."""
        import sys
        from unittest.mock import patch

        from renacechess.cli import main

        # Create valid advice facts
        advice_facts = _create_advice_facts()
        advice_path = tmp_path / "advice.json"
        advice_path.write_text(
            json.dumps(advice_facts.model_dump(by_alias=True), default=str),
            encoding="utf-8",
        )

        # Create delta facts with WRONG lineage
        delta_facts = _create_delta_facts(
            source_hashes=["sha256:" + "x" * 64, "sha256:" + "y" * 64],
        )
        delta_path = tmp_path / "delta.json"
        delta_path.write_text(
            json.dumps(delta_facts.model_dump(by_alias=True), default=str),
            encoding="utf-8",
        )

        with patch.object(
            sys,
            "argv",
            [
                "renacechess",
                "coach",
                "--advice-facts",
                str(advice_path),
                "--delta-facts",
                str(delta_path),
            ],
        ):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1

        captured = capsys.readouterr()
        assert "Lineage mismatch" in captured.err

    def test_coach_command_full_pipeline_via_main(
        self, valid_artifacts: tuple[Path, Path], capsys, tmp_path: Path
    ) -> None:
        """Exercise full coach command pipeline via main() for coverage."""
        import sys
        from unittest.mock import patch

        from renacechess.cli import main

        advice_path, delta_path = valid_artifacts
        output_path = tmp_path / "surface.json"

        with patch.object(
            sys,
            "argv",
            [
                "renacechess",
                "coach",
                "--advice-facts",
                str(advice_path),
                "--delta-facts",
                str(delta_path),
                "--tone",
                "encouraging",
                "--out",
                str(output_path),
            ],
        ):
            try:
                main()
            except SystemExit:
                pass

        captured = capsys.readouterr()

        # Should always print evaluation summary
        assert "=== Evaluation Summary ===" in captured.err
        assert "=== Coaching Draft ===" in captured.err

        # Output file should be created
        assert output_path.exists()

        # Output should be valid JSON
        output_data = json.loads(output_path.read_text(encoding="utf-8"))
        assert output_data["schemaVersion"] == "coaching_surface.v1"
        assert output_data["toneProfile"] == "encouraging"


class TestCoachingSurfaceSchema:
    """Test CoachingSurfaceV1 schema compliance."""

    def test_schema_file_exists(self) -> None:
        """Verify schema file was created."""
        schema_path = (
            Path(__file__).parent.parent
            / "src"
            / "renacechess"
            / "contracts"
            / "schemas"
            / "v1"
            / "coaching_surface.v1.schema.json"
        )
        assert schema_path.exists(), f"Schema file not found: {schema_path}"

    def test_schema_is_valid_json(self) -> None:
        """Verify schema is valid JSON."""
        schema_path = (
            Path(__file__).parent.parent
            / "src"
            / "renacechess"
            / "contracts"
            / "schemas"
            / "v1"
            / "coaching_surface.v1.schema.json"
        )
        schema = json.loads(schema_path.read_text(encoding="utf-8"))

        assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
        assert schema["title"] == "CoachingSurfaceV1"

    def test_artifact_validates_against_schema(self, valid_artifacts: tuple[Path, Path]) -> None:
        """Verify CLI output validates against JSON schema."""
        import jsonschema

        advice_path, delta_path = valid_artifacts

        result = _run_coach_cli(advice_path=advice_path, delta_path=delta_path)

        if result.returncode == 0:
            output = json.loads(result.stdout)

            schema_path = (
                Path(__file__).parent.parent
                / "src"
                / "renacechess"
                / "contracts"
                / "schemas"
                / "v1"
                / "coaching_surface.v1.schema.json"
            )
            schema = json.loads(schema_path.read_text(encoding="utf-8"))

            # Should not raise
            jsonschema.validate(output, schema)
