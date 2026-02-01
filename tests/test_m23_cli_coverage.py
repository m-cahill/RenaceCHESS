"""M23 CLI Coverage Tests.

Systematic coverage uplift for src/renacechess/cli.py to ≥90%.

Per M23 locked decisions:
- Cover all paths systematically: error paths, dispatch paths, help/usage
- Priority order: 1) error paths, 2) dispatch paths, 3) help/usage

Test categories:
1. No-command and help paths
2. Subcommand dispatch (fallback to print_help)
3. Error handling paths (missing files, malformed JSON, exit codes)
4. Parameter validation (top-k parsing, mutual exclusivity)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from renacechess.cli import main


# =============================================================================
# No-command and Help Paths
# =============================================================================


class TestHelpAndUsagePaths:
    """Test help and usage paths for CLI coverage."""

    def test_no_command_shows_help(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Invoking with no command prints help and exits 1."""
        with patch.object(sys, "argv", ["renacechess"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1

        captured = capsys.readouterr()
        assert "RenaceCHESS" in captured.out or "usage" in captured.out.lower()

    def test_demo_help(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Demo subcommand help."""
        with patch.object(sys, "argv", ["renacechess", "demo", "--help"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0

        captured = capsys.readouterr()
        assert "--pgn" in captured.out

    def test_dataset_help(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Dataset subcommand help."""
        with patch.object(sys, "argv", ["renacechess", "dataset", "--help"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0

        captured = capsys.readouterr()
        assert "build" in captured.out

    def test_eval_help(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Eval subcommand help."""
        with patch.object(sys, "argv", ["renacechess", "eval", "--help"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0

        captured = capsys.readouterr()
        assert "run" in captured.out

    def test_ingest_help(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Ingest subcommand help."""
        with patch.object(sys, "argv", ["renacechess", "ingest", "--help"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0

        captured = capsys.readouterr()
        assert "lichess" in captured.out

    def test_train_policy_help(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Train-policy subcommand help."""
        with patch.object(sys, "argv", ["renacechess", "train-policy", "--help"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0

        captured = capsys.readouterr()
        assert "--dataset-manifest" in captured.out

    def test_train_outcome_head_help(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Train-outcome-head subcommand help."""
        with patch.object(sys, "argv", ["renacechess", "train-outcome-head", "--help"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0

        captured = capsys.readouterr()
        assert "--dataset-manifest" in captured.out

    def test_coach_help(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Coach subcommand help."""
        with patch.object(sys, "argv", ["renacechess", "coach", "--help"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0

        captured = capsys.readouterr()
        assert "--advice-facts" in captured.out


# =============================================================================
# Subcommand Dispatch Fallbacks
# =============================================================================


class TestSubcommandDispatch:
    """Test subcommand dispatch paths (no sub-subcommand triggers help)."""

    def test_dataset_no_subcommand(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Dataset with no subcommand shows help and exits 1."""
        with patch.object(sys, "argv", ["renacechess", "dataset"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1

        captured = capsys.readouterr()
        # Should show help
        assert "build" in captured.out or "usage" in captured.out.lower()

    def test_eval_no_subcommand(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Eval with no subcommand shows help and exits 1."""
        with patch.object(sys, "argv", ["renacechess", "eval"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1

        captured = capsys.readouterr()
        assert "run" in captured.out or "usage" in captured.out.lower()

    def test_ingest_no_subcommand(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Ingest with no subcommand shows help and exits 1."""
        with patch.object(sys, "argv", ["renacechess", "ingest"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1

        captured = capsys.readouterr()
        assert "lichess" in captured.out or "usage" in captured.out.lower()


# =============================================================================
# Error Handling Paths
# =============================================================================


class TestErrorHandlingPaths:
    """Test error handling paths for coverage."""

    def test_eval_run_invalid_top_k_format(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Eval run with invalid top-k format exits with error."""
        manifest_path = tmp_path / "manifest.json"
        manifest_data = {
            "schemaVersion": "v2",
            "createdAt": "2024-01-01T00:00:00",
            "datasetDigest": "a" * 64,
            "assemblyConfig": {"shardSize": 10000},
            "assemblyConfigHash": "b" * 64,
            "shardRefs": [],
            "splitAssignments": {"train": [], "val": [], "frozenEval": []},
        }
        manifest_path.write_text(json.dumps(manifest_data), encoding="utf-8")

        with patch.object(
            sys,
            "argv",
            [
                "renacechess",
                "eval",
                "run",
                "--dataset-manifest",
                str(manifest_path),
                "--policy",
                "baseline.uniform_random",
                "--out",
                str(tmp_path / "out"),
                "--top-k",
                "not,numbers",  # Invalid format
            ],
        ):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1

        captured = capsys.readouterr()
        assert "Error" in captured.err
        assert "top-k" in captured.err.lower() or "comma-separated" in captured.err.lower()

    def test_eval_run_negative_top_k_values(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Eval run with negative top-k values exits with error."""
        manifest_path = tmp_path / "manifest.json"
        manifest_data = {
            "schemaVersion": "v2",
            "createdAt": "2024-01-01T00:00:00",
            "datasetDigest": "a" * 64,
            "assemblyConfig": {"shardSize": 10000},
            "assemblyConfigHash": "b" * 64,
            "shardRefs": [],
            "splitAssignments": {"train": [], "val": [], "frozenEval": []},
        }
        manifest_path.write_text(json.dumps(manifest_data), encoding="utf-8")

        with patch.object(
            sys,
            "argv",
            [
                "renacechess",
                "eval",
                "run",
                "--dataset-manifest",
                str(manifest_path),
                "--policy",
                "baseline.uniform_random",
                "--out",
                str(tmp_path / "out"),
                "--top-k",
                "1,-3,5",  # Contains negative
            ],
        ):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1

        captured = capsys.readouterr()
        assert "Error" in captured.err
        assert "positive" in captured.err.lower()

    def test_eval_run_conditioned_without_frozen_manifest(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Eval run with --conditioned-metrics but no --frozen-eval-manifest exits with error."""
        manifest_path = tmp_path / "manifest.json"
        manifest_data = {
            "schemaVersion": "v2",
            "createdAt": "2024-01-01T00:00:00",
            "datasetDigest": "a" * 64,
            "assemblyConfig": {"shardSize": 10000},
            "assemblyConfigHash": "b" * 64,
            "shardRefs": [],
            "splitAssignments": {"train": [], "val": [], "frozenEval": []},
        }
        manifest_path.write_text(json.dumps(manifest_data), encoding="utf-8")

        with patch.object(
            sys,
            "argv",
            [
                "renacechess",
                "eval",
                "run",
                "--dataset-manifest",
                str(manifest_path),
                "--policy",
                "baseline.uniform_random",
                "--out",
                str(tmp_path / "out"),
                "--conditioned-metrics",  # Missing --frozen-eval-manifest
            ],
        ):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1

        captured = capsys.readouterr()
        assert "Error" in captured.err
        assert "frozen-eval-manifest" in captured.err.lower() or "required" in captured.err.lower()

    def test_eval_run_invalid_frozen_manifest(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Eval run with invalid frozen eval manifest exits with error."""
        manifest_path = tmp_path / "manifest.json"
        manifest_data = {
            "schemaVersion": "v2",
            "createdAt": "2024-01-01T00:00:00",
            "datasetDigest": "a" * 64,
            "assemblyConfig": {"shardSize": 10000},
            "assemblyConfigHash": "b" * 64,
            "shardRefs": [],
            "splitAssignments": {"train": [], "val": [], "frozenEval": []},
        }
        manifest_path.write_text(json.dumps(manifest_data), encoding="utf-8")

        # Invalid frozen manifest (missing required fields)
        frozen_path = tmp_path / "frozen.json"
        frozen_path.write_text('{"invalid": "schema"}', encoding="utf-8")

        with patch.object(
            sys,
            "argv",
            [
                "renacechess",
                "eval",
                "run",
                "--dataset-manifest",
                str(manifest_path),
                "--policy",
                "baseline.uniform_random",
                "--out",
                str(tmp_path / "out"),
                "--conditioned-metrics",
                "--frozen-eval-manifest",
                str(frozen_path),
            ],
        ):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1

        captured = capsys.readouterr()
        assert "Error" in captured.err

    def test_train_policy_error_handling(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Train-policy command error handling."""
        manifest_path = tmp_path / "manifest.json"
        manifest_data = {
            "schemaVersion": "v2",
            "createdAt": "2024-01-01T00:00:00",
            "datasetDigest": "a" * 64,
            "assemblyConfig": {"shardSize": 10000},
            "assemblyConfigHash": "b" * 64,
            "shardRefs": [],
            "splitAssignments": {"train": [], "val": [], "frozenEval": []},
        }
        manifest_path.write_text(json.dumps(manifest_data), encoding="utf-8")

        def mock_train_baseline_policy(*args: Any, **kwargs: Any) -> Path:
            raise ValueError("Training failed intentionally")

        monkeypatch.setattr(
            "renacechess.models.training.train_baseline_policy", mock_train_baseline_policy
        )

        with patch.object(
            sys,
            "argv",
            [
                "renacechess",
                "train-policy",
                "--dataset-manifest",
                str(manifest_path),
                "--out",
                str(tmp_path / "output"),
            ],
        ):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1

        captured = capsys.readouterr()
        assert "Error" in captured.err

    def test_ingest_lichess_error_handling(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Ingest lichess command error handling."""

        def mock_ingest_from_lichess(*args: Any, **kwargs: Any) -> None:
            raise ValueError("Ingest failed intentionally")

        # Patch the imported reference in the cli module
        import renacechess.cli as cli_module

        monkeypatch.setattr(cli_module, "ingest_from_lichess", mock_ingest_from_lichess)

        with patch.object(
            sys,
            "argv",
            [
                "renacechess",
                "ingest",
                "lichess",
                "--month",
                "2024-01",
                "--out",
                str(tmp_path / "output"),
            ],
        ):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1

        captured = capsys.readouterr()
        assert "Error" in captured.err

    def test_ingest_url_error_handling(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Ingest url command error handling."""

        def mock_ingest_from_url(*args: Any, **kwargs: Any) -> None:
            raise ValueError("Ingest failed intentionally")

        # Patch the imported reference in the cli module
        import renacechess.cli as cli_module

        monkeypatch.setattr(cli_module, "ingest_from_url", mock_ingest_from_url)

        with patch.object(
            sys,
            "argv",
            [
                "renacechess",
                "ingest",
                "url",
                "--url",
                "https://example.com/test.pgn",
                "--out",
                str(tmp_path / "output"),
            ],
        ):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1

        captured = capsys.readouterr()
        assert "Error" in captured.err

    def test_dataset_build_error_handling(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Dataset build command error handling."""

        def mock_build_dataset(*args: Any, **kwargs: Any) -> None:
            raise ValueError("Build failed intentionally")

        # Patch the imported reference in the cli module
        import renacechess.cli as cli_module

        monkeypatch.setattr(cli_module, "build_dataset", mock_build_dataset)

        sample_pgn = Path(__file__).parent / "data" / "sample.pgn"

        with patch.object(
            sys,
            "argv",
            [
                "renacechess",
                "dataset",
                "build",
                "--pgn",
                str(sample_pgn),
                "--out",
                str(tmp_path / "output"),
            ],
        ):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1

        captured = capsys.readouterr()
        assert "Error" in captured.err

    def test_eval_generate_frozen_error_handling(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Eval generate-frozen command error handling."""
        manifest_path = tmp_path / "manifest.json"
        manifest_data = {
            "schemaVersion": "v2",
            "createdAt": "2024-01-01T00:00:00",
            "datasetDigest": "a" * 64,
            "assemblyConfig": {"shardSize": 10000},
            "assemblyConfigHash": "b" * 64,
            "shardRefs": [],
            "splitAssignments": {"train": [], "val": [], "frozenEval": []},
        }
        manifest_path.write_text(json.dumps(manifest_data), encoding="utf-8")

        def mock_generate_frozen_eval_manifest(*args: Any, **kwargs: Any) -> None:
            raise ValueError("Generation failed intentionally")

        monkeypatch.setattr(
            "renacechess.frozen_eval.generator.generate_frozen_eval_manifest",
            mock_generate_frozen_eval_manifest,
        )

        with patch.object(
            sys,
            "argv",
            [
                "renacechess",
                "eval",
                "generate-frozen",
                "--dataset-manifest",
                str(manifest_path),
                "--out",
                str(tmp_path / "frozen.json"),
            ],
        ):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1

        captured = capsys.readouterr()
        assert "Error" in captured.err


# =============================================================================
# Coach Command Error Paths (supplement M22 tests)
# =============================================================================


class TestCoachCommandErrors:
    """Test coach command error paths for coverage."""

    def test_coach_missing_advice_facts_file(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Coach with missing advice facts file exits with error."""
        delta_path = tmp_path / "delta.json"
        delta_path.write_text("{}", encoding="utf-8")

        with patch.object(
            sys,
            "argv",
            [
                "renacechess",
                "coach",
                "--advice-facts",
                str(tmp_path / "nonexistent.json"),
                "--delta-facts",
                str(delta_path),
            ],
        ):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1

        captured = capsys.readouterr()
        assert "Error" in captured.err
        assert "not found" in captured.err.lower()

    def test_coach_missing_delta_facts_file(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Coach with missing delta facts file exits with error."""
        advice_path = tmp_path / "advice.json"
        advice_path.write_text("{}", encoding="utf-8")

        with patch.object(
            sys,
            "argv",
            [
                "renacechess",
                "coach",
                "--advice-facts",
                str(advice_path),
                "--delta-facts",
                str(tmp_path / "nonexistent.json"),
            ],
        ):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1

        captured = capsys.readouterr()
        assert "Error" in captured.err
        assert "not found" in captured.err.lower()

    def test_coach_invalid_advice_facts_json(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Coach with invalid advice facts JSON exits with error."""
        advice_path = tmp_path / "advice.json"
        advice_path.write_text("not valid json", encoding="utf-8")

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
        assert "Error" in captured.err

    def test_coach_invalid_delta_facts_schema(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Coach with invalid delta facts schema exits with error."""
        # Create valid advice facts
        from datetime import UTC, datetime

        from renacechess.coaching.advice_facts import build_advice_facts_v1
        from renacechess.contracts.models import AdviceFactsInputsV1
        from renacechess.determinism import canonical_json_dump

        inputs = AdviceFactsInputsV1(
            fen="rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1",
            side_to_move="black",
            skill_bucket="1200_1399",
            time_control_bucket="blitz",
            time_pressure_bucket="normal",
            top_moves=[("e7e5", 0.35)],
            p_win=0.45,
            p_draw=0.30,
            p_loss=0.25,
            hdi_value=0.55,
        )
        advice_facts = build_advice_facts_v1(inputs=inputs, generated_at=datetime.now(UTC))

        advice_path = tmp_path / "advice.json"
        advice_path.write_bytes(
            canonical_json_dump(advice_facts.model_dump(by_alias=True, mode="json"))
        )

        # Invalid delta facts
        delta_path = tmp_path / "delta.json"
        delta_path.write_text('{"invalid": "schema"}', encoding="utf-8")

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
        assert "Error" in captured.err


# =============================================================================
# Additional Coverage Paths
# =============================================================================


class TestAdditionalCoveragePaths:
    """Additional tests to reach ≥90% coverage."""

    def test_train_policy_success_path(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Train-policy command success path with frozen eval manifest."""
        manifest_path = tmp_path / "manifest.json"
        manifest_data = {
            "schemaVersion": "v2",
            "createdAt": "2024-01-01T00:00:00",
            "datasetDigest": "a" * 64,
            "assemblyConfig": {"shardSize": 10000},
            "assemblyConfigHash": "b" * 64,
            "shardRefs": [],
            "splitAssignments": {"train": [], "val": [], "frozenEval": []},
        }
        manifest_path.write_text(json.dumps(manifest_data), encoding="utf-8")

        frozen_path = tmp_path / "frozen.json"
        frozen_data = {
            "schemaVersion": "v1",
            "createdAt": "2024-01-01T00:00:00",
            "manifestHash": "c" * 64,
            "records": [],
        }
        frozen_path.write_text(json.dumps(frozen_data), encoding="utf-8")

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        def mock_train_baseline_policy(*args: Any, **kwargs: Any) -> Path:
            model_path = output_dir / "model.pt"
            model_path.write_bytes(b"fake")
            metadata_path = output_dir / "model_metadata.json"
            metadata_path.write_text("{}", encoding="utf-8")
            return model_path

        monkeypatch.setattr(
            "renacechess.models.training.train_baseline_policy", mock_train_baseline_policy
        )

        with patch.object(
            sys,
            "argv",
            [
                "renacechess",
                "train-policy",
                "--dataset-manifest",
                str(manifest_path),
                "--frozen-eval-manifest",
                str(frozen_path),
                "--out",
                str(output_dir),
                "--epochs",
                "1",
            ],
        ):
            main()

        captured = capsys.readouterr()
        assert "Model trained and saved" in captured.err

    def test_ingest_lichess_success_path(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Ingest lichess command success path."""
        called = {"ingest": False}

        def mock_ingest_from_lichess(
            month: str, output_dir: Path, cache_dir: Path, decompress: bool
        ) -> None:
            called["ingest"] = True
            assert month == "2024-01"
            assert decompress is True

        # Patch the imported reference in the cli module
        import renacechess.cli as cli_module

        monkeypatch.setattr(cli_module, "ingest_from_lichess", mock_ingest_from_lichess)

        with patch.object(
            sys,
            "argv",
            [
                "renacechess",
                "ingest",
                "lichess",
                "--month",
                "2024-01",
                "--out",
                str(tmp_path / "output"),
                "--decompress",
            ],
        ):
            main()

        assert called["ingest"]

    def test_ingest_url_success_path(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Ingest url command success path."""
        called = {"ingest": False}

        def mock_ingest_from_url(
            url: str, output_dir: Path, cache_dir: Path, decompress: bool
        ) -> None:
            called["ingest"] = True
            assert "example.com" in url

        # Patch the imported reference in the cli module
        import renacechess.cli as cli_module

        monkeypatch.setattr(cli_module, "ingest_from_url", mock_ingest_from_url)

        with patch.object(
            sys,
            "argv",
            [
                "renacechess",
                "ingest",
                "url",
                "--url",
                "https://example.com/test.pgn",
                "--out",
                str(tmp_path / "output"),
            ],
        ):
            main()

        assert called["ingest"]

