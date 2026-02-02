"""M29: TrainingBenchmarkReportV1 schema and model validation tests.

These tests validate the schema structure, model constraints, and
serialization/deserialization of M29 benchmark artifacts.

NOTE: This file does NOT test actual GPU benchmarking — that is local-only.
These tests validate contract correctness only.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

import pytest

from renacechess.contracts.models import (
    BenchmarkMetricsV1,
    BenchmarkRunV1,
    DatasetInfoV1,
    EnvironmentMetadataV1,
    TimeToTrainAssumptionsV1,
    TimeToTrainEstimateV1,
    TrainingBenchmarkReportV1,
)
from renacechess.determinism import compute_determinism_hash

# --- Schema Path ---

SCHEMA_PATH = (
    Path(__file__).parent.parent
    / "src"
    / "renacechess"
    / "contracts"
    / "schemas"
    / "v1"
    / "training_benchmark_report.v1.schema.json"
)


# --- Fixtures ---


@pytest.fixture
def valid_environment_metadata() -> EnvironmentMetadataV1:
    """Create valid environment metadata for testing."""
    return EnvironmentMetadataV1(
        gpuName="NVIDIA GeForce RTX 5090",
        vramGb=32.0,
        cudaVersion="12.4",
        driverVersion="560.28.03",
        torchVersion="2.2.0",
        pythonVersion="3.12.0",
        os="Windows 11",
        cpuName="AMD Ryzen 9 7950X",
        cpuCores=32,
        ramGb=64.0,
    )


@pytest.fixture
def valid_dataset_info() -> DatasetInfoV1:
    """Create valid dataset info for testing."""
    return DatasetInfoV1(
        manifestHash="sha256:" + "a" * 64,
        manifestPath="/path/to/manifest.json",
        frozenEvalManifestHash="sha256:" + "b" * 64,
        overlapCheckPassed=True,
        totalPositionsAvailable=1000000,
    )


@pytest.fixture
def valid_benchmark_metrics() -> BenchmarkMetricsV1:
    """Create valid benchmark metrics for testing."""
    return BenchmarkMetricsV1(
        stepsCompleted=100,
        samplesProcessed=6400,
        totalTimeSeconds=10.5,
        stepsPerSecond=9.52,
        samplesPerSecond=609.52,
        stepTimeMeanMs=105.0,
        stepTimeP95Ms=120.0,
        vramPeakGb=8.5,
        vramPeakPercent=26.6,
        dataLoadTimePercent=10.0,
        forwardTimePercent=30.0,
        backwardTimePercent=40.0,
        optimizerTimePercent=20.0,
    )


@pytest.fixture
def valid_benchmark_run(valid_benchmark_metrics: BenchmarkMetricsV1) -> BenchmarkRunV1:
    """Create valid benchmark run for testing."""
    return BenchmarkRunV1(
        runId="batch64_samples1000_fp32_policy",
        batchSize=64,
        sampleCount=1000,
        sampleCountLabel="sanity",
        precisionMode="fp32",
        modelHeads="policy",
        metrics=valid_benchmark_metrics,
        status="success",
    )


@pytest.fixture
def valid_time_estimate() -> TimeToTrainEstimateV1:
    """Create valid time-to-train estimate for testing."""
    return TimeToTrainEstimateV1(
        estimateVersion="heuristic-v1",
        assumptions=TimeToTrainAssumptionsV1(
            targetDatasetSize=10000000,
            targetEpochs=10,
            batchSize=256,
            precisionMode="fp32",
        ),
        projectedTimeHours=4.5,
        projectedTimeFormatted="4h 30m",
        confidenceLevel="medium",
        sensitivityNotes=["Based on 10000 samples at batch size 256"],
    )


@pytest.fixture
def valid_report(
    valid_environment_metadata: EnvironmentMetadataV1,
    valid_dataset_info: DatasetInfoV1,
    valid_benchmark_run: BenchmarkRunV1,
    valid_time_estimate: TimeToTrainEstimateV1,
) -> TrainingBenchmarkReportV1:
    """Create valid benchmark report for testing."""
    return TrainingBenchmarkReportV1(
        version="1.0",
        generatedAt=datetime.now(UTC),
        environment=valid_environment_metadata,
        datasetInfo=valid_dataset_info,
        runMatrix=[valid_benchmark_run],
        timeToTrainEstimate=valid_time_estimate,
        warnings=[],
        determinismHash="sha256:" + "c" * 64,
    )


# --- Schema Existence Tests ---


class TestSchemaExists:
    """Verify schema file exists and is valid JSON."""

    def test_schema_file_exists(self) -> None:
        """Schema file must exist."""
        assert SCHEMA_PATH.exists(), f"Schema not found at {SCHEMA_PATH}"

    def test_schema_is_valid_json(self) -> None:
        """Schema must be valid JSON."""
        with SCHEMA_PATH.open() as f:
            schema = json.load(f)

        assert "$schema" in schema
        assert "title" in schema
        assert schema["title"] == "TrainingBenchmarkReportV1"


# --- EnvironmentMetadataV1 Tests ---


class TestEnvironmentMetadataV1:
    """Test EnvironmentMetadataV1 model."""

    def test_valid_metadata(self, valid_environment_metadata: EnvironmentMetadataV1) -> None:
        """Valid metadata should validate successfully."""
        assert valid_environment_metadata.gpu_name == "NVIDIA GeForce RTX 5090"
        assert valid_environment_metadata.vram_gb == 32.0
        assert valid_environment_metadata.cuda_version == "12.4"

    def test_required_fields_only(self) -> None:
        """Metadata with only required fields should validate."""
        metadata = EnvironmentMetadataV1(
            gpuName="RTX 5090",
            vramGb=32.0,
            cudaVersion="12.4",
            torchVersion="2.2.0",
            pythonVersion="3.12.0",
            os="Linux",
        )
        assert metadata.driver_version is None
        assert metadata.cpu_name is None

    def test_serialization_uses_camel_case(
        self, valid_environment_metadata: EnvironmentMetadataV1
    ) -> None:
        """JSON serialization should use camelCase aliases."""
        data = valid_environment_metadata.model_dump(mode="json", by_alias=True)
        assert "gpuName" in data
        assert "vramGb" in data
        assert "cudaVersion" in data
        assert "gpu_name" not in data


# --- DatasetInfoV1 Tests ---


class TestDatasetInfoV1:
    """Test DatasetInfoV1 model."""

    def test_valid_dataset_info(self, valid_dataset_info: DatasetInfoV1) -> None:
        """Valid dataset info should validate successfully."""
        assert valid_dataset_info.overlap_check_passed is True

    def test_required_fields_only(self) -> None:
        """Dataset info with only required fields should validate."""
        info = DatasetInfoV1(
            manifestHash="sha256:" + "a" * 64,
            frozenEvalManifestHash="sha256:" + "b" * 64,
            overlapCheckPassed=True,
        )
        assert info.manifest_path is None
        assert info.total_positions_available is None


# --- BenchmarkMetricsV1 Tests ---


class TestBenchmarkMetricsV1:
    """Test BenchmarkMetricsV1 model."""

    def test_valid_metrics(self, valid_benchmark_metrics: BenchmarkMetricsV1) -> None:
        """Valid metrics should validate successfully."""
        assert valid_benchmark_metrics.steps_completed == 100
        assert valid_benchmark_metrics.samples_per_second == 609.52

    def test_minimal_metrics(self) -> None:
        """Metrics with only required fields should validate."""
        metrics = BenchmarkMetricsV1(
            stepsCompleted=10,
            totalTimeSeconds=1.0,
        )
        assert metrics.samples_processed is None
        assert metrics.vram_peak_gb is None

    def test_percentage_bounds(self) -> None:
        """Percentage fields should be bounded 0-100."""
        metrics = BenchmarkMetricsV1(
            stepsCompleted=10,
            totalTimeSeconds=1.0,
            gpuUtilizationPercent=95.5,
            vramPeakPercent=50.0,
        )
        assert metrics.gpu_utilization_percent == 95.5
        assert metrics.vram_peak_percent == 50.0


# --- BenchmarkRunV1 Tests ---


class TestBenchmarkRunV1:
    """Test BenchmarkRunV1 model."""

    def test_valid_run(self, valid_benchmark_run: BenchmarkRunV1) -> None:
        """Valid run should validate successfully."""
        assert valid_benchmark_run.batch_size == 64
        assert valid_benchmark_run.precision_mode == "fp32"
        assert valid_benchmark_run.status == "success"

    @pytest.mark.parametrize("batch_size", [64, 128, 256, 512])
    def test_valid_batch_sizes(
        self, batch_size: Literal[64, 128, 256, 512], valid_benchmark_metrics: BenchmarkMetricsV1
    ) -> None:
        """All M29 batch sizes should be valid."""
        run = BenchmarkRunV1(
            runId=f"batch{batch_size}_test",
            batchSize=batch_size,
            sampleCount=1000,
            sampleCountLabel="sanity",
            precisionMode="fp32",
            modelHeads="policy",
            metrics=valid_benchmark_metrics,
        )
        assert run.batch_size == batch_size

    @pytest.mark.parametrize(
        "sample_count,label",
        [(1000, "sanity"), (10000, "medium"), (100000, "large")],
    )
    def test_valid_sample_counts(
        self,
        sample_count: Literal[1000, 10000, 100000],
        label: Literal["sanity", "medium", "large"],
        valid_benchmark_metrics: BenchmarkMetricsV1,
    ) -> None:
        """All M29 sample counts should be valid."""
        run = BenchmarkRunV1(
            runId=f"samples{sample_count}_test",
            batchSize=64,
            sampleCount=sample_count,
            sampleCountLabel=label,
            precisionMode="fp32",
            modelHeads="policy",
            metrics=valid_benchmark_metrics,
        )
        assert run.sample_count == sample_count
        assert run.sample_count_label == label

    @pytest.mark.parametrize("precision", ["fp32", "amp"])
    def test_valid_precision_modes(
        self, precision: Literal["fp32", "amp"], valid_benchmark_metrics: BenchmarkMetricsV1
    ) -> None:
        """Both precision modes should be valid."""
        run = BenchmarkRunV1(
            runId=f"precision_{precision}_test",
            batchSize=64,
            sampleCount=1000,
            sampleCountLabel="sanity",
            precisionMode=precision,
            modelHeads="policy",
            metrics=valid_benchmark_metrics,
        )
        assert run.precision_mode == precision

    @pytest.mark.parametrize("heads", ["policy", "policy+outcome"])
    def test_valid_model_heads(
        self,
        heads: Literal["policy", "policy+outcome"],
        valid_benchmark_metrics: BenchmarkMetricsV1,
    ) -> None:
        """Both model head configurations should be valid."""
        run = BenchmarkRunV1(
            runId=f"heads_{heads}_test",
            batchSize=64,
            sampleCount=1000,
            sampleCountLabel="sanity",
            precisionMode="fp32",
            modelHeads=heads,
            metrics=valid_benchmark_metrics,
        )
        assert run.model_heads == heads

    @pytest.mark.parametrize("status", ["success", "oom", "error", "skipped"])
    def test_valid_status_values(
        self,
        status: Literal["success", "oom", "error", "skipped"],
        valid_benchmark_metrics: BenchmarkMetricsV1,
    ) -> None:
        """All status values should be valid."""
        run = BenchmarkRunV1(
            runId="status_test",
            batchSize=64,
            sampleCount=1000,
            sampleCountLabel="sanity",
            precisionMode="fp32",
            modelHeads="policy",
            metrics=valid_benchmark_metrics,
            status=status,
            errorMessage="Test error" if status != "success" else None,
        )
        assert run.status == status


# --- TimeToTrainEstimateV1 Tests ---


class TestTimeToTrainEstimateV1:
    """Test TimeToTrainEstimateV1 model."""

    def test_valid_estimate(self, valid_time_estimate: TimeToTrainEstimateV1) -> None:
        """Valid estimate should validate successfully."""
        assert valid_time_estimate.estimate_version == "heuristic-v1"
        assert valid_time_estimate.projected_time_hours == 4.5
        assert valid_time_estimate.confidence_level == "medium"

    @pytest.mark.parametrize("confidence", ["low", "medium", "high"])
    def test_valid_confidence_levels(self, confidence: Literal["low", "medium", "high"]) -> None:
        """All confidence levels should be valid."""
        estimate = TimeToTrainEstimateV1(
            assumptions=TimeToTrainAssumptionsV1(
                targetDatasetSize=1000000,
                targetEpochs=5,
                batchSize=128,
                precisionMode="fp32",
            ),
            projectedTimeHours=1.0,
            projectedTimeFormatted="1h 0m",
            confidenceLevel=confidence,
        )
        assert estimate.confidence_level == confidence


# --- TrainingBenchmarkReportV1 Tests ---


class TestTrainingBenchmarkReportV1:
    """Test TrainingBenchmarkReportV1 model."""

    def test_valid_report(self, valid_report: TrainingBenchmarkReportV1) -> None:
        """Valid report should validate successfully."""
        assert valid_report.version == "1.0"
        assert len(valid_report.run_matrix) >= 1

    def test_serialization_roundtrip(self, valid_report: TrainingBenchmarkReportV1) -> None:
        """Report should serialize and deserialize correctly."""
        # Serialize to JSON
        json_data = valid_report.model_dump(mode="json", by_alias=True)

        # Deserialize back
        restored = TrainingBenchmarkReportV1.model_validate(json_data)

        assert restored.version == valid_report.version
        assert restored.environment.gpu_name == valid_report.environment.gpu_name
        assert len(restored.run_matrix) == len(valid_report.run_matrix)

    def test_camel_case_aliases(self, valid_report: TrainingBenchmarkReportV1) -> None:
        """JSON output should use camelCase aliases."""
        json_data = valid_report.model_dump(mode="json", by_alias=True)

        # Top-level fields
        assert "generatedAt" in json_data
        assert "runMatrix" in json_data
        assert "determinismHash" in json_data

        # Nested fields
        assert "gpuName" in json_data["environment"]
        assert "vramGb" in json_data["environment"]

    def test_determinism_hash_format(self, valid_report: TrainingBenchmarkReportV1) -> None:
        """Determinism hash should match expected format."""
        assert valid_report.determinism_hash.startswith("sha256:")
        assert len(valid_report.determinism_hash) == 7 + 64  # "sha256:" + 64 hex chars

    def test_minimal_report(
        self,
        valid_environment_metadata: EnvironmentMetadataV1,
        valid_benchmark_run: BenchmarkRunV1,
    ) -> None:
        """Report with only required fields should validate."""
        report = TrainingBenchmarkReportV1(
            version="1.0",
            generatedAt=datetime.now(UTC),
            environment=valid_environment_metadata,
            runMatrix=[valid_benchmark_run],
            determinismHash="sha256:" + "0" * 64,
        )
        assert report.dataset_info is None
        assert report.time_to_train_estimate is None
        assert report.warnings == []

    def test_multiple_runs(
        self,
        valid_environment_metadata: EnvironmentMetadataV1,
        valid_benchmark_metrics: BenchmarkMetricsV1,
    ) -> None:
        """Report should support multiple runs in matrix."""
        runs = []
        for batch_size in [64, 128, 256]:
            for precision in ["fp32", "amp"]:
                run = BenchmarkRunV1(
                    runId=f"batch{batch_size}_{precision}",
                    batchSize=batch_size,  # type: ignore[arg-type]
                    sampleCount=1000,
                    sampleCountLabel="sanity",
                    precisionMode=precision,  # type: ignore[arg-type]
                    modelHeads="policy",
                    metrics=valid_benchmark_metrics,
                )
                runs.append(run)

        report = TrainingBenchmarkReportV1(
            version="1.0",
            generatedAt=datetime.now(UTC),
            environment=valid_environment_metadata,
            runMatrix=runs,
            determinismHash="sha256:" + "0" * 64,
        )

        assert len(report.run_matrix) == 6


# --- Determinism Tests ---


class TestDeterminism:
    """Test determinism hash computation."""

    def test_determinism_hash_stable(self, valid_report: TrainingBenchmarkReportV1) -> None:
        """Same report content should produce same hash."""
        # Compute hash excluding the hash field itself
        report_dict = valid_report.model_dump(
            mode="json", by_alias=True, exclude={"determinism_hash"}
        )

        hash1 = compute_determinism_hash(report_dict)
        hash2 = compute_determinism_hash(report_dict)

        assert hash1 == hash2

    def test_different_content_different_hash(
        self,
        valid_environment_metadata: EnvironmentMetadataV1,
        valid_benchmark_run: BenchmarkRunV1,
    ) -> None:
        """Different report content should produce different hashes."""
        report1 = TrainingBenchmarkReportV1(
            version="1.0",
            generatedAt=datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC),
            environment=valid_environment_metadata,
            runMatrix=[valid_benchmark_run],
            determinismHash="sha256:" + "0" * 64,
        )

        # Create report with different timestamp
        report2 = TrainingBenchmarkReportV1(
            version="1.0",
            generatedAt=datetime(2026, 1, 2, 0, 0, 0, tzinfo=UTC),
            environment=valid_environment_metadata,
            runMatrix=[valid_benchmark_run],
            determinismHash="sha256:" + "0" * 64,
        )

        dict1 = report1.model_dump(mode="json", by_alias=True, exclude={"determinism_hash"})
        dict2 = report2.model_dump(mode="json", by_alias=True, exclude={"determinism_hash"})

        hash1 = compute_determinism_hash(dict1)
        hash2 = compute_determinism_hash(dict2)

        assert hash1 != hash2


# --- Validation Error Tests ---


class TestValidationErrors:
    """Test that invalid inputs are rejected."""

    def test_invalid_batch_size_rejected(self, valid_benchmark_metrics: BenchmarkMetricsV1) -> None:
        """Invalid batch sizes should be rejected."""
        with pytest.raises(Exception):  # Pydantic ValidationError
            BenchmarkRunV1(
                runId="invalid_batch",
                batchSize=32,  # Not in allowed list
                sampleCount=1000,
                sampleCountLabel="sanity",
                precisionMode="fp32",
                modelHeads="policy",
                metrics=valid_benchmark_metrics,
            )

    def test_invalid_sample_count_rejected(
        self, valid_benchmark_metrics: BenchmarkMetricsV1
    ) -> None:
        """Invalid sample counts should be rejected."""
        with pytest.raises(Exception):  # Pydantic ValidationError
            BenchmarkRunV1(
                runId="invalid_samples",
                batchSize=64,
                sampleCount=5000,  # Not in allowed list
                sampleCountLabel="sanity",
                precisionMode="fp32",
                modelHeads="policy",
                metrics=valid_benchmark_metrics,
            )

    def test_empty_run_matrix_rejected(
        self, valid_environment_metadata: EnvironmentMetadataV1
    ) -> None:
        """Empty run matrix should be rejected."""
        with pytest.raises(Exception):  # Pydantic ValidationError
            TrainingBenchmarkReportV1(
                version="1.0",
                generatedAt=datetime.now(UTC),
                environment=valid_environment_metadata,
                runMatrix=[],  # Empty not allowed
                determinismHash="sha256:" + "0" * 64,
            )
