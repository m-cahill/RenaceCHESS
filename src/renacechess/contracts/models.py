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
    """Conditioning variables for position evaluation."""

    model_config = ConfigDict(validate_by_alias=True, validate_by_name=True)

    skill_bucket: str = Field(
        ..., alias="skillBucket", description="Skill bucket identifier (e.g., '1200-1400')"
    )
    time_pressure_bucket: Literal["NORMAL", "LOW", "TROUBLE"] = Field(
        ..., alias="timePressureBucket", description="Time pressure bucket"
    )
    time_control_class: Literal["blitz", "rapid", "classical"] | None = Field(
        None, alias="timeControlClass", description="Time control class (optional)"
    )


class PolicyMove(BaseModel):
    """Single move in policy distribution."""

    uci: str = Field(..., description="Move in UCI format")
    san: str | None = Field(None, description="Move in SAN format (optional)")
    p: float = Field(..., ge=0.0, le=1.0, description="Probability of this move")


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
            "Percentage of records where policy emits move not in legalMoves "
            "(fixed-decimal string)"
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
