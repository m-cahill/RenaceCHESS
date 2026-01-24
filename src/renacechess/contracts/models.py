"""Pydantic models for RenaceCHESS contracts."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Position(BaseModel):
    """Chess position representation."""

    model_config = ConfigDict(validate_by_alias=True, validate_by_name=True)

    fen: str = Field(..., description="FEN string representation of the position")
    side_to_move: Literal["white", "black"] = Field(
        ..., alias="sideToMove", description="Side to move"
    )
    legal_moves: list[str] = Field(
        ..., alias="legalMoves", description="List of legal moves in UCI format"
    )


class PositionConditioning(BaseModel):
    """Conditioning variables for position evaluation.

    M06 Extension:
    - Added optional M06-specific fields (skillBucketId, spec versions, timeControlRaw)
    - Extended enums to support both legacy and M06 values for backward compatibility
    - Legacy fields (skillBucket, timePressureBucket, timeControlClass)
      remain required/optional as before
    """

    model_config = ConfigDict(validate_by_alias=True, validate_by_name=True)

    # Legacy fields (backward compatible)
    skill_bucket: str = Field(
        ..., alias="skillBucket", description="Skill bucket identifier (e.g., '1200-1400', legacy)"
    )
    time_pressure_bucket: Literal[
        "NORMAL", "LOW", "TROUBLE", "early", "normal", "low", "trouble", "unknown"
    ] = Field(
        ...,
        alias="timePressureBucket",
        description="Time pressure bucket (legacy uppercase or M06 lowercase values)",
    )
    time_control_class: Literal["blitz", "rapid", "classical", "bullet", "unknown"] | None = Field(
        None,
        alias="timeControlClass",
        description="Time control class (optional, legacy or M06 values)",
    )

    # M06-specific fields (optional, additive)
    skill_bucket_id: (
        Literal[
            "lt_800",
            "800_999",
            "1000_1199",
            "1200_1399",
            "1400_1599",
            "1600_1799",
            "gte_1800",
            "unknown",
        ]
        | None
    ) = Field(
        None,
        alias="skillBucketId",
        description="M06 skill bucket ID (optional, M06 spec v1)",
    )
    skill_bucket_spec_version: int | None = Field(
        None,
        alias="skillBucketSpecVersion",
        description="Skill bucket spec version (1 for M06, None for legacy)",
    )
    time_control_raw: str | None = Field(
        None,
        alias="timeControlRaw",
        description="Original PGN TimeControl header string (optional, M06)",
    )
    time_control_spec_version: int | None = Field(
        None,
        alias="timeControlSpecVersion",
        description="Time control spec version (1 for M06, None for legacy)",
    )
    time_pressure_spec_version: int | None = Field(
        None,
        alias="timePressureSpecVersion",
        description="Time pressure spec version (1 for M06, None for legacy)",
    )


class PolicyMove(BaseModel):
    """Single move in policy distribution."""

    uci: str = Field(..., description="Move in UCI format")
    san: str | None = Field(None, description="Move in SAN format (optional)")
    p: float = Field(..., ge=0.0, le=1.0, description="Probability of this move")


class ChosenMove(BaseModel):
    """Ground-truth move that was actually played (optional label)."""

    model_config = ConfigDict(validate_by_alias=True, validate_by_name=True)

    uci: str = Field(..., description="Move in UCI format (required)")
    san: str | None = Field(None, description="Move in SAN format (optional)")


class Policy(BaseModel):
    """Move policy distribution."""

    model_config = ConfigDict(validate_by_alias=True, validate_by_name=True)

    top_moves: list[PolicyMove] = Field(
        ..., alias="topMoves", description="Top moves with probabilities"
    )
    entropy: float = Field(..., ge=0.0, description="Policy entropy (Shannon entropy)")
    top_gap: float = Field(
        ..., alias="topGap", ge=0.0, le=1.0, description="Gap between top move and second move"
    )


class HumanWDL(BaseModel):
    """Human win/draw/loss probabilities."""

    model_config = ConfigDict(validate_by_alias=True, validate_by_name=True)

    w: float = Field(..., ge=0.0, le=1.0, description="Win probability")
    d: float = Field(..., ge=0.0, le=1.0, description="Draw probability")
    loss: float = Field(..., alias="l", ge=0.0, le=1.0, description="Loss probability")

    def model_post_init(self, __context: object) -> None:
        """Validate that probabilities sum to 1."""
        total = self.w + self.d + self.loss
        if abs(total - 1.0) > 1e-6:
            raise ValueError(f"WDL probabilities must sum to 1.0, got {total}")


class HDIComponents(BaseModel):
    """Components of Human Difficulty Index."""

    model_config = ConfigDict(validate_by_alias=True, validate_by_name=True)

    entropy: float = Field(..., ge=0.0, description="Policy entropy component")
    top_gap: float = Field(..., alias="topGap", ge=0.0, le=1.0, description="Top gap component")
    wdl_sensitivity: float = Field(
        ..., alias="wdlSensitivity", ge=0.0, description="WDL sensitivity component"
    )


class HDI(BaseModel):
    """Human Difficulty Index."""

    value: float = Field(..., ge=0.0, description="Human Difficulty Index (scalar)")
    components: HDIComponents = Field(..., description="HDI component values")


class NarrativeSeed(BaseModel):
    """Narrative seed for LLM context."""

    type: Literal["trap-risk", "confusing", "time-sensitive", "critical"] = Field(
        ..., description="Narrative seed type"
    )
    severity: Literal["low", "medium", "high"] = Field(..., description="Severity level")
    facts: list[str] = Field(..., description="Array of factual statements")


class ContextBridgeMeta(BaseModel):
    """Metadata for Context Bridge payload."""

    model_config = ConfigDict(validate_by_alias=True, validate_by_name=True)

    schema_version: Literal["v1"] = Field("v1", alias="schemaVersion", description="Schema version")
    generated_at: datetime = Field(
        ..., alias="generatedAt", description="ISO 8601 timestamp of generation"
    )
    input_hash: str = Field(
        ..., alias="inputHash", description="Hash of input data (PGN + position)"
    )


class HumanWDLContainer(BaseModel):
    """Container for pre-move and post-move WDL probabilities."""

    model_config = ConfigDict(validate_by_alias=True, validate_by_name=True)

    pre: HumanWDL = Field(..., description="WDL probabilities before move")
    post_by_move: dict[str, HumanWDL] = Field(
        ...,
        alias="postByMove",
        description="WDL probabilities after each candidate move (keyed by UCI)",
    )


class ContextBridgePayload(BaseModel):
    """LLM Context Bridge payload (v1)."""

    model_config = ConfigDict(validate_by_alias=True, validate_by_name=True)

    position: Position = Field(..., description="Chess position")
    conditioning: PositionConditioning = Field(..., description="Conditioning variables")
    policy: Policy = Field(..., description="Move policy distribution")
    human_wdl: HumanWDLContainer = Field(
        ..., alias="humanWDL", description="Human WDL probabilities"
    )
    hdi: HDI = Field(..., description="Human Difficulty Index")
    narrative_seeds: list[NarrativeSeed] = Field(
        ..., alias="narrativeSeeds", description="Narrative seeds for LLM"
    )
    meta: ContextBridgeMeta = Field(..., description="Metadata")
    chosen_move: ChosenMove | None = Field(
        None,
        alias="chosenMove",
        description="Ground-truth move that was actually played (optional label)",
    )


class DatasetManifestShardRef(BaseModel):
    """Reference to a dataset shard."""

    model_config = ConfigDict(validate_by_alias=True, validate_by_name=True)

    shard_id: str = Field(..., alias="shardId", description="Unique shard identifier")
    hash: str = Field(..., description="SHA-256 hash of shard file")
    path: str = Field(..., description="Relative or absolute path to shard file")


class DatasetManifestSplitAssignments(BaseModel):
    """Split assignments for dataset."""

    model_config = ConfigDict(validate_by_alias=True, validate_by_name=True)

    train: list[str] = Field(default_factory=list, description="Training split shard IDs")
    val: list[str] = Field(default_factory=list, description="Validation split shard IDs")
    frozen_eval: list[str] = Field(
        default_factory=list, alias="frozenEval", description="Frozen eval split shard IDs"
    )


class DatasetManifest(BaseModel):
    """Dataset manifest (v1)."""

    model_config = ConfigDict(validate_by_alias=True, validate_by_name=True)

    schema_version: Literal["v1"] = Field("v1", alias="schemaVersion", description="Schema version")
    created_at: datetime = Field(
        ..., alias="createdAt", description="ISO 8601 timestamp of creation"
    )
    shard_refs: list[DatasetManifestShardRef] = Field(
        default_factory=list, alias="shardRefs", description="List of shard references"
    )
    filter_config_hash: str = Field(
        ..., alias="filterConfigHash", description="Hash of filter configuration"
    )
    split_assignments: DatasetManifestSplitAssignments = Field(
        ..., alias="splitAssignments", description="Split assignments"
    )


class DatasetManifestShardRefV2(BaseModel):
    """Reference to a dataset shard (v2) - includes record count."""

    model_config = ConfigDict(validate_by_alias=True, validate_by_name=True)

    shard_id: str = Field(..., alias="shardId", description="Unique shard identifier")
    hash: str = Field(
        ...,
        description="SHA-256 hash of shard file (lowercase hex)",
        pattern="^[a-f0-9]{64}$",
    )
    path: str = Field(..., description="Relative or absolute path to shard file")
    records: int = Field(..., ge=0, description="Number of records in this shard")


class DatasetManifestInputV2(BaseModel):
    """Input source reference (v2) - receipt or PGN file."""

    model_config = ConfigDict(validate_by_alias=True, validate_by_name=True)

    type: Literal["ingest_receipt", "pgn_file"] = Field(..., description="Input type")
    digest: str = Field(
        ...,
        description=(
            "SHA-256 hash: for receipts, use receipt.artifact.sha256 "
            "(or derived if available); for PGN files, compute from file content"
        ),
        pattern="^[a-f0-9]{64}$",
    )
    receipt_id: str | None = Field(
        None, alias="receiptId", description="Receipt identifier (only for type='ingest_receipt')"
    )
    path: str | None = Field(None, description="Path to input (receipt path or PGN file path)")


class DatasetManifestAssemblyConfigV2(BaseModel):
    """Assembly configuration (v2)."""

    model_config = ConfigDict(validate_by_alias=True, validate_by_name=True)

    shard_size: int = Field(
        ..., alias="shardSize", ge=1, description="Maximum number of records per shard"
    )
    max_games: int | None = Field(
        None,
        alias="maxGames",
        ge=1,
        description="Maximum number of games to process (null = no limit)",
    )
    max_positions: int | None = Field(
        None,
        alias="maxPositions",
        ge=1,
        description="Maximum number of positions to process (null = no limit)",
    )
    start_ply: int | None = Field(
        None,
        alias="startPly",
        ge=0,
        description="Start processing from this ply number (inclusive, null = no lower bound)",
    )
    end_ply: int | None = Field(
        None,
        alias="endPly",
        ge=0,
        description="Stop processing at this ply number (exclusive, null = no upper bound)",
    )


class DatasetManifestV2(BaseModel):
    """Dataset manifest (v2) - includes assembly config and input provenance."""

    model_config = ConfigDict(validate_by_alias=True, validate_by_name=True)

    schema_version: Literal["v2"] = Field("v2", alias="schemaVersion", description="Schema version")
    created_at: datetime = Field(
        ..., alias="createdAt", description="ISO 8601 timestamp of creation"
    )
    shard_refs: list[DatasetManifestShardRefV2] = Field(
        ..., alias="shardRefs", description="List of shard references"
    )
    assembly_config_hash: str = Field(
        ...,
        alias="assemblyConfigHash",
        description="SHA-256 hash of canonical JSON for assembly parameters",
        pattern="^[a-f0-9]{64}$",
    )
    dataset_digest: str = Field(
        ...,
        alias="datasetDigest",
        description=(
            "SHA-256 hash combining assemblyConfigHash, input digests, "
            "and schema versions (stable dataset identity)"
        ),
        pattern="^[a-f0-9]{64}$",
    )
    inputs: list[DatasetManifestInputV2] = Field(
        default_factory=list,
        description="List of input sources (receipts or PGN files) used to build this dataset",
    )
    assembly_config: DatasetManifestAssemblyConfigV2 = Field(
        ..., alias="assemblyConfig", description="Assembly configuration parameters"
    )
    split_assignments: DatasetManifestSplitAssignments = Field(
        ...,
        alias="splitAssignments",
        description="Split assignments (record-level, not shard-level)",
    )
    filter_config_hash: str | None = Field(
        None,
        alias="filterConfigHash",
        description="Legacy filter config hash (kept for v1 compatibility, deprecated in v2)",
        pattern="^[a-f0-9]{64}$",
    )


class SourceArtifactRefV1(BaseModel):
    """Source artifact reference (v1)."""

    model_config = ConfigDict(validate_by_alias=True, validate_by_name=True)

    uri: str = Field(..., description="Original source URI (URL or file:// path)")
    resolved_uri: str | None = Field(
        None, alias="resolvedUri", description="Resolved/final URI after redirects (optional)"
    )
    etag: str | None = Field(None, description="HTTP ETag if available (optional)")
    last_modified: datetime | None = Field(
        None, alias="lastModified", description="Last modified timestamp from source (optional)"
    )
    content_length: int | None = Field(
        None, alias="contentLength", description="Content length in bytes from source (optional)"
    )


class ArtifactRefV1(BaseModel):
    """Cached artifact reference (v1)."""

    model_config = ConfigDict(validate_by_alias=True, validate_by_name=True)

    cache_path: str = Field(
        ...,
        alias="cachePath",
        description="Path to cached artifact (relative to cache root or absolute)",
    )
    sha256: str = Field(
        ...,
        description="SHA-256 hash of artifact (lowercase hex)",
        pattern="^[a-f0-9]{64}$",
    )
    size_bytes: int = Field(..., alias="sizeBytes", ge=0, description="Size of artifact in bytes")
    media_type: str = Field(
        ...,
        alias="mediaType",
        description="MIME type of artifact (e.g., 'application/x-chess-pgn', 'application/zstd')",
    )
    compression: Literal["zstd"] | None = Field(
        None, description="Compression format if applicable (optional)"
    )


class DerivedArtifactRefV1(BaseModel):
    """Derived artifact reference (v1) - e.g., decompressed files."""

    model_config = ConfigDict(validate_by_alias=True, validate_by_name=True)

    decompressed_path: str = Field(
        ..., alias="decompressedPath", description="Path to decompressed artifact"
    )
    decompressed_sha256: str = Field(
        ...,
        alias="decompressedSha256",
        description="SHA-256 hash of decompressed artifact (lowercase hex)",
        pattern="^[a-f0-9]{64}$",
    )
    decompressed_size_bytes: int = Field(
        ...,
        alias="decompressedSizeBytes",
        ge=0,
        description="Size of decompressed artifact in bytes",
    )


class ProvenanceV1(BaseModel):
    """Provenance information (v1)."""

    model_config = ConfigDict(validate_by_alias=True, validate_by_name=True)

    tool_version: str = Field(
        ..., alias="toolVersion", description="Version of renacechess tool used"
    )
    platform: str | None = Field(
        None, description="Platform identifier (e.g., 'linux-x86_64') - optional"
    )
    python_version: str | None = Field(
        None, alias="pythonVersion", description="Python version (e.g., '3.11.0') - optional"
    )


class IngestReceiptV1(BaseModel):
    """Ingest receipt (v1) - documents downloaded/cached artifacts."""

    model_config = ConfigDict(validate_by_alias=True, validate_by_name=True)

    schema_version: Literal["v1"] = Field("v1", alias="schemaVersion", description="Schema version")
    created_at: datetime = Field(
        ..., alias="createdAt", description="ISO 8601 timestamp of receipt creation"
    )
    source: SourceArtifactRefV1 = Field(..., description="Source artifact reference")
    artifact: ArtifactRefV1 = Field(..., description="Cached artifact reference")
    derived: DerivedArtifactRefV1 | None = Field(
        None, description="Derived artifacts (e.g., decompressed files) - optional"
    )
    provenance: ProvenanceV1 = Field(..., description="Provenance information")


# Evaluation Report Models (v1)


class TopKLegalCoverage(BaseModel):
    """Top-K legal coverage metrics."""

    model_config = ConfigDict(validate_by_alias=True, validate_by_name=True)

    top1: str = Field(
        ...,
        description=(
            "Percentage of records where policy's top-1 move is in legalMoves "
            "(fixed-decimal string)"
        ),
    )
    top3: str = Field(
        ...,
        description=(
            "Percentage of records where policy's top-3 moves intersect legalMoves "
            "(fixed-decimal string)"
        ),
    )


class PolicyEntropyStats(BaseModel):
    """Policy entropy statistics."""

    model_config = ConfigDict(validate_by_alias=True, validate_by_name=True)

    mean: str = Field(
        ...,
        description=(
            "Mean Shannon entropy of policy distribution "
            "(fixed-decimal string, or 'N/A' if not applicable)"
        ),
    )
    stddev: str | None = Field(
        None, description="Standard deviation of policy entropy (fixed-decimal string, optional)"
    )


class EvalMetricsV1(BaseModel):
    """Evaluation metrics (v1) - policy validity metrics."""

    model_config = ConfigDict(validate_by_alias=True, validate_by_name=True)

    records_evaluated: int = Field(
        ..., alias="recordsEvaluated", ge=0, description="Total number of records evaluated"
    )
    illegal_move_rate: str = Field(
        ...,
        alias="illegalMoveRate",
        description=(
            "Percentage of records where policy emits move not in legalMoves (fixed-decimal string)"
        ),
    )
    top_k_legal_coverage: TopKLegalCoverage = Field(
        ..., alias="topKLegalCoverage", description="Top-K legal coverage metrics"
    )
    policy_entropy: PolicyEntropyStats = Field(
        ..., alias="policyEntropy", description="Policy entropy statistics"
    )
    unique_moves_emitted: int = Field(
        ...,
        alias="uniqueMovesEmitted",
        ge=0,
        description="Number of unique moves emitted across dataset",
    )


class EvalReportSplitsV1(BaseModel):
    """Per-split evaluation metrics (v1)."""

    model_config = ConfigDict(validate_by_alias=True, validate_by_name=True)

    train: EvalMetricsV1 | None = Field(None, description="Training split metrics (if evaluated)")
    val: EvalMetricsV1 | None = Field(None, description="Validation split metrics (if evaluated)")
    frozen_eval: EvalMetricsV1 | None = Field(
        None, alias="frozenEval", description="Frozen evaluation split metrics (if evaluated)"
    )


class EvalReportV1(BaseModel):
    """Evaluation report (v1) - policy validity evaluation over dataset manifests."""

    model_config = ConfigDict(validate_by_alias=True, validate_by_name=True)

    schema_version: Literal["eval_report.v1"] = Field(
        "eval_report.v1", alias="schemaVersion", description="Schema version"
    )
    created_at: datetime = Field(
        ...,
        alias="createdAt",
        description="ISO 8601 timestamp of creation (injectable for determinism tests)",
    )
    dataset_digest: str = Field(
        ...,
        alias="datasetDigest",
        description="SHA-256 hash copied from dataset manifest v2 (stable dataset identity)",
        pattern="^[a-f0-9]{64}$",
    )
    assembly_config_hash: str = Field(
        ...,
        alias="assemblyConfigHash",
        description="SHA-256 hash copied from dataset manifest v2 (assembly configuration hash)",
        pattern="^[a-f0-9]{64}$",
    )
    policy_id: str = Field(
        ..., alias="policyId", description="Policy identifier (e.g., 'baseline.uniform_random')"
    )
    eval_config_hash: str = Field(
        ...,
        alias="evalConfigHash",
        description="SHA-256 hash of canonical JSON config (sorted keys, stable)",
        pattern="^[a-f0-9]{64}$",
    )
    metrics: EvalMetricsV1 = Field(..., description="Policy validity metrics")
    splits: EvalReportSplitsV1 | None = Field(
        None, description="Per-split metric breakdown (only includes splits that were evaluated)"
    )


# Evaluation Report Models (v2)


class AccuracyMetrics(BaseModel):
    """Ground-truth accuracy metrics (computed only over labeled records)."""

    model_config = ConfigDict(
        validate_by_alias=True,
        validate_by_name=True,
        extra="allow",  # Allow dynamic top-K fields (top1, top3, top5, etc.)
    )

    coverage: str = Field(
        ...,
        description=(
            "Percentage of records that are labeled (fixed-decimal string, "
            "labeledRecordCount / totalRecordCount)"
        ),
    )


class EvalMetricsV2(BaseModel):
    """Evaluation metrics (v2) - policy validity metrics + accuracy metrics."""

    model_config = ConfigDict(validate_by_alias=True, validate_by_name=True)

    records_evaluated: int = Field(
        ..., alias="recordsEvaluated", ge=0, description="Total number of records evaluated"
    )
    illegal_move_rate: str = Field(
        ...,
        alias="illegalMoveRate",
        description=(
            "Percentage of records where policy emits move not in legalMoves (fixed-decimal string)"
        ),
    )
    top_k_legal_coverage: TopKLegalCoverage = Field(
        ..., alias="topKLegalCoverage", description="Top-K legal coverage metrics"
    )
    policy_entropy: PolicyEntropyStats = Field(
        ..., alias="policyEntropy", description="Policy entropy statistics"
    )
    unique_moves_emitted: int = Field(
        ...,
        alias="uniqueMovesEmitted",
        ge=0,
        description="Number of unique moves emitted across dataset",
    )
    total_record_count: int = Field(
        ..., alias="totalRecordCount", ge=0, description="Total number of records in the dataset"
    )
    labeled_record_count: int = Field(
        ...,
        alias="labeledRecordCount",
        ge=0,
        description="Number of records that have chosenMove label (ground-truth move)",
    )
    accuracy: AccuracyMetrics | None = Field(
        None,
        description="Ground-truth accuracy metrics (computed only over labeled records, optional)",
    )


class EvalReportSplitsV2(BaseModel):
    """Per-split evaluation metrics (v2)."""

    model_config = ConfigDict(validate_by_alias=True, validate_by_name=True)

    train: EvalMetricsV2 | None = Field(None, description="Training split metrics (if evaluated)")
    val: EvalMetricsV2 | None = Field(None, description="Validation split metrics (if evaluated)")
    frozen_eval: EvalMetricsV2 | None = Field(
        None, alias="frozenEval", description="Frozen evaluation split metrics (if evaluated)"
    )


# Evaluation Report Models (v3) - Conditioned Metrics


class DistributionStats(BaseModel):
    """Distribution statistics for a metric."""

    model_config = ConfigDict(validate_by_alias=True, validate_by_name=True)

    mean: str = Field(..., description="Mean value (fixed-decimal string)")
    median: str | None = Field(None, description="Median value (fixed-decimal string, optional)")
    stddev: str | None = Field(
        None, description="Standard deviation (fixed-decimal string, optional)"
    )


class ConditionedDistributionMetrics(BaseModel):
    """Distribution metrics for conditioned evaluation."""

    model_config = ConfigDict(validate_by_alias=True, validate_by_name=True)

    entropy: DistributionStats | None = Field(None, description="Policy entropy statistics")
    top_gap: DistributionStats | None = Field(
        None, alias="topGap", description="Top gap statistics"
    )
    legal_moves_count: DistributionStats | None = Field(
        None, alias="legalMovesCount", description="Legal moves count statistics"
    )


class ConditionedValidityMetrics(BaseModel):
    """Policy validity metrics for conditioned evaluation."""

    model_config = ConfigDict(validate_by_alias=True, validate_by_name=True)

    illegal_rate: str = Field(
        ..., alias="illegalRate", description="Illegal move rate (fixed-decimal string)"
    )
    top_k_legal_coverage: dict[str, str] = Field(
        default_factory=dict,
        alias="topKLegalCoverage",
        description="Top-K legal coverage (keyed by K as string)",
    )
    policy_entropy: str | None = Field(
        None, alias="policyEntropy", description="Mean policy entropy (fixed-decimal string)"
    )
    unique_moves_emitted: int | None = Field(
        None, alias="uniqueMovesEmitted", ge=0, description="Unique moves emitted"
    )


class ConditionedAccuracyMetrics(BaseModel):
    """Accuracy metrics for conditioned evaluation."""

    model_config = ConfigDict(validate_by_alias=True, validate_by_name=True)

    top1: str = Field(..., description="Top-1 accuracy (fixed-decimal string)")
    top_k: dict[str, str] = Field(
        default_factory=dict,
        alias="topK",
        description="Top-K accuracy metrics (keyed by K as string, e.g., '3', '5', '10')",
    )
    coverage: str = Field(
        ..., description="Coverage (labeled / total records, fixed-decimal string)"
    )


class ConditionedMetrics(BaseModel):
    """Metrics for a single conditioning stratum (v3 report)."""

    model_config = ConfigDict(validate_by_alias=True, validate_by_name=True)

    total_records: int = Field(
        ..., alias="totalRecords", ge=0, description="Total number of records in this stratum"
    )
    labeled_records: int = Field(
        ..., alias="labeledRecords", ge=0, description="Number of records with chosenMove label"
    )
    records_with_policy: int = Field(
        ...,
        alias="recordsWithPolicy",
        ge=0,
        description="Number of records with policy output",
    )
    accuracy: ConditionedAccuracyMetrics | None = Field(
        None, description="Accuracy metrics (computed only over labeled records, optional)"
    )
    distribution: ConditionedDistributionMetrics | None = Field(
        None, description="Distribution metrics (computed over all records with policy)"
    )
    validity: ConditionedValidityMetrics | None = Field(
        None, description="Policy validity metrics (from v1/v2 reports)"
    )


class EvalReportV3(BaseModel):
    """Evaluation report (v3) - adds conditioned metrics stratified by skill/time."""

    model_config = ConfigDict(validate_by_alias=True, validate_by_name=True)

    schema_version: Literal["eval_report.v3"] = Field(
        "eval_report.v3", alias="schemaVersion", description="Schema version"
    )
    created_at: datetime = Field(
        ..., alias="createdAt", description="ISO 8601 timestamp of creation"
    )
    dataset_digest: str = Field(
        ...,
        alias="datasetDigest",
        description="SHA-256 hash from dataset manifest v2 (stable dataset identity)",
        pattern="^[a-f0-9]{64}$",
    )
    assembly_config_hash: str = Field(
        ...,
        alias="assemblyConfigHash",
        description="SHA-256 hash from dataset manifest v2 (assembly configuration hash)",
        pattern="^[a-f0-9]{64}$",
    )
    policy_id: str = Field(
        ..., alias="policyId", description="Policy identifier (e.g., 'baseline.uniform_random')"
    )
    eval_config_hash: str = Field(
        ...,
        alias="evalConfigHash",
        description="SHA-256 hash of canonical JSON config",
        pattern="^[a-f0-9]{64}$",
    )
    frozen_eval_manifest_hash: str | None = Field(
        None,
        alias="frozenEvalManifestHash",
        description="SHA-256 hash of frozen eval manifest (if frozen eval was used)",
        pattern="^[a-f0-9]{64}$",
    )
    overall: ConditionedMetrics = Field(..., description="Overall metrics (all records)")
    by_skill_bucket_id: dict[str, ConditionedMetrics] = Field(
        default_factory=dict,
        alias="bySkillBucketId",
        description="Metrics stratified by M06 skill bucket ID",
    )
    by_time_control_class: dict[str, ConditionedMetrics] = Field(
        default_factory=dict,
        alias="byTimeControlClass",
        description="Metrics stratified by time control class",
    )
    by_time_pressure_bucket: dict[str, ConditionedMetrics] = Field(
        default_factory=dict,
        alias="byTimePressureBucket",
        description="Metrics stratified by time pressure bucket",
    )


# Frozen Eval Manifest Models


class FrozenEvalManifestSourceRef(BaseModel):
    """Reference to source dataset manifest v2 for frozen eval manifest."""

    model_config = ConfigDict(validate_by_alias=True, validate_by_name=True)

    dataset_digest: str = Field(
        ...,
        alias="datasetDigest",
        description="SHA-256 hash from source dataset manifest v2 (stable dataset identity)",
        pattern="^[a-f0-9]{64}$",
    )
    manifest_path: str = Field(
        ..., alias="manifestPath", description="Path to source dataset manifest v2"
    )


class FrozenEvalManifestRecord(BaseModel):
    """Record reference in frozen eval manifest."""

    model_config = ConfigDict(validate_by_alias=True, validate_by_name=True)

    record_key: str = Field(
        ..., alias="recordKey", description="Record identifier (e.g., 'fen:ply')"
    )
    shard_id: str = Field(
        ..., alias="shardId", description="Shard identifier containing this record"
    )
    shard_hash: str = Field(
        ...,
        alias="shardHash",
        description="SHA-256 hash of the shard file",
        pattern="^[a-f0-9]{64}$",
    )
    skill_bucket_id: (
        Literal[
            "lt_800",
            "800_999",
            "1000_1199",
            "1200_1399",
            "1400_1599",
            "1600_1799",
            "gte_1800",
            "unknown",
        ]
        | None
    ) = Field(
        None,
        alias="skillBucketId",
        description="M06 skill bucket ID for this record (if available)",
    )
    time_control_class: Literal["bullet", "blitz", "rapid", "classical", "unknown"] | None = Field(
        None,
        alias="timeControlClass",
        description="Time control class for this record (if available)",
    )
    time_pressure_bucket: Literal["early", "normal", "low", "trouble", "unknown"] | None = Field(
        None,
        alias="timePressureBucket",
        description="Time pressure bucket for this record (if available)",
    )


class FrozenEvalManifestStratificationTargets(BaseModel):
    """Stratification targets for frozen eval manifest."""

    model_config = ConfigDict(validate_by_alias=True, validate_by_name=True)

    total_records: int = Field(
        ..., alias="totalRecords", ge=0, description="Target total record count"
    )
    min_per_skill_bucket: int = Field(
        ...,
        alias="minPerSkillBucket",
        ge=0,
        description="Hard minimum records per skill bucket (if available)",
    )


class FrozenEvalManifestCoverageShortfall(BaseModel):
    """Coverage shortfall in frozen eval manifest."""

    model_config = ConfigDict(validate_by_alias=True, validate_by_name=True)

    axis: Literal["skillBucketId", "timeControlClass", "timePressureBucket"] = Field(
        ..., description="Conditioning axis with shortfall"
    )
    value: str = Field(..., description="Specific bucket/class/value with shortfall")
    target: int = Field(..., ge=0, description="Target record count")
    actual: int = Field(..., ge=0, description="Actual record count")


class FrozenEvalManifestV1(BaseModel):
    """Frozen evaluation manifest (v1) - immutable evaluation set with stratification metadata."""

    model_config = ConfigDict(validate_by_alias=True, validate_by_name=True)

    schema_version: Literal[1] = Field(1, alias="schemaVersion", description="Schema version")
    created_at: datetime = Field(
        ..., alias="createdAt", description="ISO 8601 timestamp of creation"
    )
    source_manifest_ref: FrozenEvalManifestSourceRef = Field(
        ..., alias="sourceManifestRef", description="Reference to source dataset manifest v2"
    )
    records: list[FrozenEvalManifestRecord] = Field(
        ..., description="Array of record references with conditioning metadata"
    )
    stratification_targets: FrozenEvalManifestStratificationTargets | None = Field(
        None,
        alias="stratificationTargets",
        description="Stratification targets used during selection",
    )
    counts_by_skill_bucket_id: dict[str, int] = Field(
        default_factory=dict,
        alias="countsBySkillBucketId",
        description="Record counts by M06 skill bucket ID (keyed by bucket ID)",
    )
    counts_by_time_control_class: dict[str, int] = Field(
        default_factory=dict,
        alias="countsByTimeControlClass",
        description="Record counts by time control class (keyed by class)",
    )
    counts_by_time_pressure_bucket: dict[str, int] = Field(
        default_factory=dict,
        alias="countsByTimePressureBucket",
        description="Record counts by time pressure bucket (keyed by bucket)",
    )
    coverage_shortfalls: list[FrozenEvalManifestCoverageShortfall] = Field(
        default_factory=list,
        alias="coverageShortfalls",
        description="Coverage shortfalls (where targets not met)",
    )
    manifest_hash: str = Field(
        ...,
        alias="manifestHash",
        description=(
            "SHA-256 hash of canonical JSON for this manifest (computed after all other fields)"
        ),
        pattern="^[a-f0-9]{64}$",
    )


class EvalReportV2(BaseModel):
    """Evaluation report (v2) - policy validity evaluation + ground-truth accuracy metrics."""

    model_config = ConfigDict(validate_by_alias=True, validate_by_name=True)

    schema_version: Literal["eval_report.v2"] = Field(
        "eval_report.v2", alias="schemaVersion", description="Schema version"
    )
    created_at: datetime = Field(
        ...,
        alias="createdAt",
        description="ISO 8601 timestamp of creation (injectable for determinism tests)",
    )
    dataset_digest: str = Field(
        ...,
        alias="datasetDigest",
        description="SHA-256 hash copied from dataset manifest v2 (stable dataset identity)",
        pattern="^[a-f0-9]{64}$",
    )
    assembly_config_hash: str = Field(
        ...,
        alias="assemblyConfigHash",
        description="SHA-256 hash copied from dataset manifest v2 (assembly configuration hash)",
        pattern="^[a-f0-9]{64}$",
    )
    policy_id: str = Field(
        ..., alias="policyId", description="Policy identifier (e.g., 'baseline.uniform_random')"
    )
    eval_config_hash: str = Field(
        ...,
        alias="evalConfigHash",
        description="SHA-256 hash of canonical JSON config (sorted keys, stable)",
        pattern="^[a-f0-9]{64}$",
    )
    metrics: EvalMetricsV1 = Field(..., description="Policy validity metrics (unchanged from v1)")
    total_record_count: int = Field(
        ..., alias="totalRecordCount", ge=0, description="Total number of records in the dataset"
    )
    labeled_record_count: int = Field(
        ...,
        alias="labeledRecordCount",
        ge=0,
        description="Number of records that have chosenMove label (ground-truth move)",
    )
    accuracy: AccuracyMetrics | None = Field(
        None,
        description="Ground-truth accuracy metrics (computed only over labeled records, optional)",
    )
    splits: EvalReportSplitsV2 | None = Field(
        None, description="Per-split metric breakdown (only includes splits that were evaluated)"
    )
