"""Pydantic models for RenaceCHESS contracts."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

# =============================================================================
# Personality Models (M15)
# =============================================================================


class SafetyEnvelopeV1(BaseModel):
    """Safety envelope parameters for personality transformations.

    Defines the bounded region within which a personality may operate.
    See docs/contracts/PERSONALITY_SAFETY_CONTRACT_v1.md for the governing contract.
    """

    model_config = ConfigDict(populate_by_name=True)

    top_k: int = Field(
        5,
        alias="topK",
        ge=1,
        le=100,
        description="Maximum number of candidate moves considered",
    )
    delta_p_max: float = Field(
        0.15,
        alias="deltaPMax",
        ge=0.0,
        le=1.0,
        description="Maximum probability shift allowed per move",
    )
    entropy_min: float = Field(
        0.5,
        alias="entropyMin",
        ge=0.0,
        description="Minimum output entropy (prevents over-sharpening)",
    )
    entropy_max: float = Field(
        3.0,
        alias="entropyMax",
        ge=0.0,
        description="Maximum output entropy (prevents over-softening)",
    )
    base_reachable: bool = Field(
        True,
        alias="baseReachable",
        description="Require that identity configuration exists",
    )

    @model_validator(mode="after")
    def validate_entropy_bounds(self) -> SafetyEnvelopeV1:
        """Validate that entropy bounds are consistent."""
        if self.entropy_min > self.entropy_max:
            msg = f"entropy_min ({self.entropy_min}) must be <= entropy_max ({self.entropy_max})"
            raise ValueError(msg)
        return self


class PersonalityConfigV1(BaseModel):
    """Personality configuration schema (v1).

    Defines tunable parameters for a personality module.
    See docs/contracts/PERSONALITY_SAFETY_CONTRACT_v1.md for the governing contract.
    """

    model_config = ConfigDict(populate_by_name=True)

    schema_version: Literal["personality_config.v1"] = Field(
        "personality_config.v1",
        alias="schemaVersion",
        description="Schema version identifier",
    )
    personality_id: str = Field(
        ...,
        alias="personalityId",
        description="Unique personality identifier (e.g., 'style.pawn_clamp.v1')",
        pattern=r"^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+$",
    )
    display_name: str = Field(
        ...,
        alias="displayName",
        description="Human-readable personality name",
    )
    description: str = Field(
        ...,
        description="Description of personality behavior and style",
    )
    safety_envelope: SafetyEnvelopeV1 = Field(
        default_factory=SafetyEnvelopeV1,
        alias="safetyEnvelope",
        description="Safety envelope parameters for this personality",
    )
    tunable_parameters: dict[str, float] = Field(
        default_factory=dict,
        alias="tunableParameters",
        description="Personality-specific tunable parameters (keyed by parameter name)",
    )
    enabled: bool = Field(
        True,
        description="Whether this personality is enabled",
    )


# =============================================================================
# Structural Cognition Models (M11)
# =============================================================================


class PieceFeatures(BaseModel):
    """Per-piece structural features (Structural Cognition Contract v1)."""

    model_config = ConfigDict(populate_by_name=True)

    # Identity fields
    slot_id: int = Field(..., alias="slotId", ge=0, le=31, description="Fixed slot index (0-31)")
    color: Literal["white", "black"] = Field(..., description="Piece color")
    piece_type: Literal["K", "Q", "R", "B", "N", "P"] = Field(
        ..., alias="pieceType", description="Original piece type"
    )
    starting_file: Literal["a", "b", "c", "d", "e", "f", "g", "h"] = Field(
        ..., alias="startingFile", description="Starting file for piece identity"
    )

    # State fields
    alive: bool = Field(..., description="Is the piece still on the board?")
    square: str | None = Field(..., description="Current square (e.g., 'e4') or null if captured")
    is_promoted: bool = Field(False, alias="isPromoted", description="Has this pawn promoted?")
    promoted_to: Literal["Q", "R", "B", "N"] | None = Field(
        None, alias="promotedTo", description="Promotion target (only if is_promoted)"
    )

    # Mobility fields
    mobility_legal: int = Field(
        ..., alias="mobilityLegal", ge=0, description="Count of legal moves for this piece"
    )
    mobility_safe: int = Field(..., alias="mobilitySafe", ge=0, description="Count of 'safe' moves")

    # Tension fields
    attacked_by: int = Field(
        ..., alias="attackedBy", ge=0, description="Count of enemy pieces attacking this piece"
    )
    defended_by: int = Field(
        ..., alias="defendedBy", ge=0, description="Count of friendly pieces defending this piece"
    )
    net_defense: int = Field(..., alias="netDefense", description="defended_by - attacked_by")

    # Tactical flags
    is_hanging: bool = Field(
        ..., alias="isHanging", description="attacked_by > 0 AND defended_by == 0"
    )
    is_pinned: bool = Field(..., alias="isPinned", description="Piece is pinned to the king")
    is_restricted: bool = Field(..., alias="isRestricted", description="mobility_legal < 3")
    is_dominated: bool = Field(..., alias="isDominated", description="net_defense < -1")
    is_attacker: bool = Field(
        ..., alias="isAttacker", description="Attacks enemy pieces or key squares"
    )
    is_defender_of_king: bool = Field(
        ..., alias="isDefenderOfKing", description="Defends squares around friendly king"
    )


class PerPieceFeaturesV1(BaseModel):
    """Per-piece features container (32 slots, Structural Cognition Contract v1)."""

    model_config = ConfigDict(populate_by_name=True)

    schema_version: Literal["per_piece.v1"] = Field(
        "per_piece.v1", alias="schemaVersion", description="Schema version identifier"
    )
    pieces: list[PieceFeatures] = Field(
        ...,
        min_length=32,
        max_length=32,
        description="Fixed 32-slot array of piece features",
    )


class SquareMapFeaturesV1(BaseModel):
    """Square-level structural maps (Structural Cognition Contract v1)."""

    model_config = ConfigDict(populate_by_name=True)

    schema_version: Literal["square_map.v1"] = Field(
        "square_map.v1", alias="schemaVersion", description="Schema version identifier"
    )

    # Required maps
    weak_for_white: list[bool] = Field(
        ...,
        alias="weakForWhite",
        min_length=64,
        max_length=64,
        description="Squares that are weak for White",
    )
    strong_for_white: list[bool] = Field(
        ...,
        alias="strongForWhite",
        min_length=64,
        max_length=64,
        description="Squares that are strong for White",
    )
    weak_for_black: list[bool] = Field(
        ...,
        alias="weakForBlack",
        min_length=64,
        max_length=64,
        description="Squares that are weak for Black",
    )
    strong_for_black: list[bool] = Field(
        ...,
        alias="strongForBlack",
        min_length=64,
        max_length=64,
        description="Squares that are strong for Black",
    )
    is_hole_for_white: list[bool] = Field(
        ...,
        alias="isHoleForWhite",
        min_length=64,
        max_length=64,
        description="Holes for White",
    )
    is_hole_for_black: list[bool] = Field(
        ...,
        alias="isHoleForBlack",
        min_length=64,
        max_length=64,
        description="Holes for Black",
    )

    # Optional diagnostic maps
    control_diff_white: list[int] | None = Field(
        None,
        alias="controlDiffWhite",
        min_length=64,
        max_length=64,
        description="Control differential for White per square",
    )
    control_diff_black: list[int] | None = Field(
        None,
        alias="controlDiffBlack",
        min_length=64,
        max_length=64,
        description="Control differential for Black per square",
    )
    pawn_contestable_white: list[bool] | None = Field(
        None,
        alias="pawnContestableWhite",
        min_length=64,
        max_length=64,
        description="Squares contestable by White pawns",
    )
    pawn_contestable_black: list[bool] | None = Field(
        None,
        alias="pawnContestableBlack",
        min_length=64,
        max_length=64,
        description="Squares contestable by Black pawns",
    )


class StructuralLabel(BaseModel):
    """Semantic label for narrative seeding (Context Bridge v2)."""

    model_config = ConfigDict(populate_by_name=True)

    type: Literal[
        "dominated-piece",
        "hole",
        "overextended-pawn",
        "key-defender",
        "weak-square",
        "strong-square",
        "hanging-piece",
        "pinned-piece",
    ] = Field(..., description="Structural label type")
    target: str = Field(..., description="Target (square like 'd5' or piece slot like 'P_e')")
    description: str = Field(..., description="Human-readable description for LLM grounding")


class StructuralCognition(BaseModel):
    """Structural cognition container (Context Bridge v2)."""

    model_config = ConfigDict(populate_by_name=True)

    per_piece: PerPieceFeaturesV1 | None = Field(
        None, alias="perPiece", description="Per-piece structural features"
    )
    square_map: SquareMapFeaturesV1 | None = Field(
        None, alias="squareMap", description="Square-level structural maps"
    )
    structural_labels: list[StructuralLabel] | None = Field(
        None, alias="structuralLabels", description="Semantic labels for narrative seeding"
    )


class Position(BaseModel):
    """Chess position representation."""

    model_config = ConfigDict(populate_by_name=True)

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

    model_config = ConfigDict(populate_by_name=True)

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

    model_config = ConfigDict(populate_by_name=True)

    uci: str = Field(..., description="Move in UCI format (required)")
    san: str | None = Field(None, description="Move in SAN format (optional)")


class Policy(BaseModel):
    """Move policy distribution."""

    model_config = ConfigDict(populate_by_name=True)

    top_moves: list[PolicyMove] = Field(
        ..., alias="topMoves", description="Top moves with probabilities"
    )
    entropy: float = Field(..., ge=0.0, description="Policy entropy (Shannon entropy)")
    top_gap: float = Field(
        ..., alias="topGap", ge=0.0, le=1.0, description="Gap between top move and second move"
    )


class HumanWDL(BaseModel):
    """Human win/draw/loss probabilities."""

    model_config = ConfigDict(populate_by_name=True)

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

    model_config = ConfigDict(populate_by_name=True)

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

    model_config = ConfigDict(populate_by_name=True)

    schema_version: Literal["v1"] = Field("v1", alias="schemaVersion", description="Schema version")
    generated_at: datetime = Field(
        ..., alias="generatedAt", description="ISO 8601 timestamp of generation"
    )
    input_hash: str = Field(
        ..., alias="inputHash", description="Hash of input data (PGN + position)"
    )


class ContextBridgeMetaV2(BaseModel):
    """Metadata for Context Bridge payload (v2)."""

    model_config = ConfigDict(populate_by_name=True)

    schema_version: Literal["v2"] = Field("v2", alias="schemaVersion", description="Schema version")
    generated_at: datetime = Field(
        ..., alias="generatedAt", description="ISO 8601 timestamp of generation"
    )
    input_hash: str = Field(
        ..., alias="inputHash", description="Hash of input data (PGN + position)"
    )


class HumanWDLContainer(BaseModel):
    """Container for pre-move and post-move WDL probabilities."""

    model_config = ConfigDict(populate_by_name=True)

    pre: HumanWDL = Field(..., description="WDL probabilities before move")
    post_by_move: dict[str, HumanWDL] = Field(
        ...,
        alias="postByMove",
        description="WDL probabilities after each candidate move (keyed by UCI)",
    )


class ContextBridgePayload(BaseModel):
    """LLM Context Bridge payload (v1)."""

    model_config = ConfigDict(populate_by_name=True)

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


class NarrativeSeedV2(BaseModel):
    """Narrative seed for LLM context (v2 with structural types)."""

    type: Literal[
        "trap-risk",
        "confusing",
        "time-sensitive",
        "critical",
        "dominated-piece",
        "hole",
        "weak-square",
        "key-defender",
    ] = Field(..., description="Narrative seed type (v2 adds structural types)")
    severity: Literal["low", "medium", "high"] = Field(..., description="Severity level")
    facts: list[str] = Field(..., description="Array of factual statements")


class ContextBridgePayloadV2(BaseModel):
    """LLM Context Bridge payload (v2) - extends v1 with structural cognition."""

    model_config = ConfigDict(populate_by_name=True)

    position: Position = Field(..., description="Chess position")
    conditioning: PositionConditioning = Field(..., description="Conditioning variables")
    policy: Policy = Field(..., description="Move policy distribution")
    human_wdl: HumanWDLContainer = Field(
        ..., alias="humanWDL", description="Human WDL probabilities"
    )
    hdi: HDI = Field(..., description="Human Difficulty Index")
    narrative_seeds: list[NarrativeSeedV2] = Field(
        ...,
        alias="narrativeSeeds",
        description="Narrative seeds for LLM (v2 with structural types)",
    )
    meta: ContextBridgeMetaV2 = Field(..., description="Metadata (v2)")
    chosen_move: ChosenMove | None = Field(
        None,
        alias="chosenMove",
        description="Ground-truth move that was actually played (optional label)",
    )
    structural_cognition: StructuralCognition | None = Field(
        None,
        alias="structuralCognition",
        description="Structural cognition features (v2, optional for backward compatibility)",
    )


class DatasetManifestShardRef(BaseModel):
    """Reference to a dataset shard."""

    model_config = ConfigDict(populate_by_name=True)

    shard_id: str = Field(..., alias="shardId", description="Unique shard identifier")
    hash: str = Field(..., description="SHA-256 hash of shard file")
    path: str = Field(..., description="Relative or absolute path to shard file")


class DatasetManifestSplitAssignments(BaseModel):
    """Split assignments for dataset."""

    model_config = ConfigDict(populate_by_name=True)

    train: list[str] = Field(default_factory=list, description="Training split shard IDs")
    val: list[str] = Field(default_factory=list, description="Validation split shard IDs")
    frozen_eval: list[str] = Field(
        default_factory=list, alias="frozenEval", description="Frozen eval split shard IDs"
    )


class DatasetManifest(BaseModel):
    """Dataset manifest (v1)."""

    model_config = ConfigDict(populate_by_name=True)

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

    model_config = ConfigDict(populate_by_name=True)

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

    model_config = ConfigDict(populate_by_name=True)

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

    model_config = ConfigDict(populate_by_name=True)

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

    model_config = ConfigDict(populate_by_name=True)

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

    model_config = ConfigDict(populate_by_name=True)

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

    model_config = ConfigDict(populate_by_name=True)

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

    model_config = ConfigDict(populate_by_name=True)

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

    model_config = ConfigDict(populate_by_name=True)

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

    model_config = ConfigDict(populate_by_name=True)

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

    model_config = ConfigDict(populate_by_name=True)

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

    model_config = ConfigDict(populate_by_name=True)

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

    model_config = ConfigDict(populate_by_name=True)

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

    model_config = ConfigDict(populate_by_name=True)

    train: EvalMetricsV1 | None = Field(None, description="Training split metrics (if evaluated)")
    val: EvalMetricsV1 | None = Field(None, description="Validation split metrics (if evaluated)")
    frozen_eval: EvalMetricsV1 | None = Field(
        None, alias="frozenEval", description="Frozen evaluation split metrics (if evaluated)"
    )


class EvalReportV1(BaseModel):
    """Evaluation report (v1) - policy validity evaluation over dataset manifests."""

    model_config = ConfigDict(populate_by_name=True)

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

    model_config = ConfigDict(populate_by_name=True)

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

    model_config = ConfigDict(populate_by_name=True)

    train: EvalMetricsV2 | None = Field(None, description="Training split metrics (if evaluated)")
    val: EvalMetricsV2 | None = Field(None, description="Validation split metrics (if evaluated)")
    frozen_eval: EvalMetricsV2 | None = Field(
        None, alias="frozenEval", description="Frozen evaluation split metrics (if evaluated)"
    )


# Evaluation Report Models (v3) - Conditioned Metrics


class DistributionStats(BaseModel):
    """Distribution statistics for a metric."""

    model_config = ConfigDict(populate_by_name=True)

    mean: str = Field(..., description="Mean value (fixed-decimal string)")
    median: str | None = Field(None, description="Median value (fixed-decimal string, optional)")
    stddev: str | None = Field(
        None, description="Standard deviation (fixed-decimal string, optional)"
    )


class ConditionedDistributionMetrics(BaseModel):
    """Distribution metrics for conditioned evaluation."""

    model_config = ConfigDict(populate_by_name=True)

    entropy: DistributionStats | None = Field(None, description="Policy entropy statistics")
    top_gap: DistributionStats | None = Field(
        None, alias="topGap", description="Top gap statistics"
    )
    legal_moves_count: DistributionStats | None = Field(
        None, alias="legalMovesCount", description="Legal moves count statistics"
    )


class ConditionedValidityMetrics(BaseModel):
    """Policy validity metrics for conditioned evaluation."""

    model_config = ConfigDict(populate_by_name=True)

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

    model_config = ConfigDict(populate_by_name=True)

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
    """Metrics for a single conditioning stratum (v3 report, extended with HDI in v4)."""

    model_config = ConfigDict(populate_by_name=True)

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
    hdi: HDIMetrics | None = Field(
        None,
        description="Human Difficulty Index (HDI) metrics (M07, optional for v3 compatibility)",
    )


class EvalReportV3(BaseModel):
    """Evaluation report (v3) - adds conditioned metrics stratified by skill/time."""

    model_config = ConfigDict(populate_by_name=True)

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


class EvalReportV4(BaseModel):
    """Evaluation report (v4) - extends v3 with Human Difficulty Index (HDI) metrics (M07)."""

    model_config = ConfigDict(populate_by_name=True)

    schema_version: Literal["eval_report.v4"] = Field(
        "eval_report.v4", alias="schemaVersion", description="Schema version"
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


class EvalReportV5(BaseModel):
    """Evaluation report (v5) - extends v4 with outcome metrics (M09)."""

    model_config = ConfigDict(populate_by_name=True)

    schema_version: Literal["eval_report.v5"] = Field(
        "eval_report.v5", alias="schemaVersion", description="Schema version"
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
    outcome_metrics: OutcomeMetrics | None = Field(
        None,
        alias="outcomeMetrics",
        description="Outcome head metrics (present only if outcome head was used)",
    )
    outcome_metrics_by_skill: dict[str, OutcomeMetrics] | None = Field(
        None,
        alias="outcomeMetricsBySkill",
        description=(
            "Outcome metrics stratified by skill bucket (present only if outcome head was used)"
        ),
    )
    outcome_metrics_by_time_control: dict[str, OutcomeMetrics] | None = Field(
        None,
        alias="outcomeMetricsByTimeControl",
        description=(
            "Outcome metrics stratified by time control class "
            "(present only if outcome head was used)"
        ),
    )
    outcome_metrics_by_time_pressure: dict[str, OutcomeMetrics] | None = Field(
        None,
        alias="outcomeMetricsByTimePressure",
        description=(
            "Outcome metrics stratified by time pressure bucket "
            "(present only if outcome head was used)"
        ),
    )


# HDI Models (M07) - for Evaluation Reports


class HDIOutcomeSensitivity(BaseModel):
    """Outcome sensitivity component for HDI (M07)."""

    model_config = ConfigDict(populate_by_name=True)

    value: float = Field(
        ..., ge=0.0, le=1.0, description="Outcome sensitivity value (normalized to [0.0, 1.0])"
    )
    source: Literal["proxy", "outcome_head"] = Field(
        ..., description="Source of outcome sensitivity (proxy or outcome_head)"
    )
    note: str = Field(
        ...,
        description=(
            "Note about the source "
            "(e.g., 'entropy * (1 - topGap); replaced when outcome head exists')"
        ),
    )


class HDIMetricsComponents(BaseModel):
    """HDI component values for evaluation reports (M07)."""

    model_config = ConfigDict(populate_by_name=True)

    entropy: float = Field(
        ..., ge=0.0, le=1.0, description="Normalized policy entropy component [0.0, 1.0]"
    )
    top_gap_inverted: float = Field(
        ...,
        alias="topGapInverted",
        ge=0.0,
        le=1.0,
        description="Inverted normalized top gap (higher = more ambiguous) [0.0, 1.0]",
    )
    legal_move_pressure: float = Field(
        ...,
        alias="legalMovePressure",
        ge=0.0,
        le=1.0,
        description="Normalized legal move pressure [0.0, 1.0]",
    )
    outcome_sensitivity: HDIOutcomeSensitivity = Field(
        ...,
        alias="outcomeSensitivity",
        description="Outcome sensitivity component (with source metadata)",
    )


class HDIMetrics(BaseModel):
    """Human Difficulty Index (HDI) metrics for evaluation reports (M07)."""

    model_config = ConfigDict(populate_by_name=True)

    value: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Human Difficulty Index scalar value [0.0, 1.0]",
    )
    spec_version: int = Field(
        ..., alias="specVersion", description="HDI specification version (1 for M07)"
    )
    components: HDIMetricsComponents = Field(..., description="HDI component values")


# Outcome Metrics Models (M09)


class OutcomeMetrics(BaseModel):
    """Outcome metrics for human W/D/L evaluation (M09)."""

    model_config = ConfigDict(populate_by_name=True)

    total_predictions: int = Field(
        ..., alias="totalPredictions", ge=0, description="Total number of outcome predictions"
    )
    cross_entropy: float | None = Field(
        None,
        alias="crossEntropy",
        ge=0.0,
        description="Average cross-entropy (log loss) - lower is better",
    )
    brier_score: float | None = Field(
        None, alias="brierScore", ge=0.0, description="Average Brier score - lower is better"
    )
    ece: float | None = Field(
        None,
        alias="ece",
        ge=0.0,
        le=1.0,
        description="Expected Calibration Error (10-bin equal-width) - lower is better",
    )


# Frozen Eval Manifest Models


class FrozenEvalManifestSourceRef(BaseModel):
    """Reference to source dataset manifest v2 for frozen eval manifest."""

    model_config = ConfigDict(populate_by_name=True)

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

    model_config = ConfigDict(populate_by_name=True)

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

    model_config = ConfigDict(populate_by_name=True)

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

    model_config = ConfigDict(populate_by_name=True)

    axis: Literal["skillBucketId", "timeControlClass", "timePressureBucket"] = Field(
        ..., description="Conditioning axis with shortfall"
    )
    value: str = Field(..., description="Specific bucket/class/value with shortfall")
    target: int = Field(..., ge=0, description="Target record count")
    actual: int = Field(..., ge=0, description="Actual record count")


class FrozenEvalManifestV1(BaseModel):
    """Frozen evaluation manifest (v1) - immutable evaluation set with stratification metadata."""

    model_config = ConfigDict(populate_by_name=True)

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

    model_config = ConfigDict(populate_by_name=True)

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


# =============================================================================
# Personality Evaluation Artifact Models (M18)
# =============================================================================


class ComponentStatsV1(BaseModel):
    """Statistics for a single component or feature (M18)."""

    model_config = ConfigDict(populate_by_name=True)

    mean: float = Field(..., description="Mean value")
    min: float | None = Field(None, description="Minimum value")
    max: float | None = Field(None, description="Maximum value")


class DivergenceMetricsV1(BaseModel):
    """Divergence metrics between personality output and baseline (M18)."""

    model_config = ConfigDict(populate_by_name=True)

    kl_divergence: float = Field(
        ...,
        alias="klDivergence",
        ge=0.0,
        description="Kullback-Leibler divergence from baseline (bits)",
    )
    total_variation: float = Field(
        ...,
        alias="totalVariation",
        ge=0.0,
        le=1.0,
        description="Total Variation distance [0.0, 1.0]",
    )
    jensen_shannon: float | None = Field(
        None,
        alias="jensenShannon",
        ge=0.0,
        le=1.0,
        description="Jensen-Shannon divergence [0.0, 1.0] (optional)",
    )
    max_probability_delta: float = Field(
        ...,
        alias="maxProbabilityDelta",
        ge=0.0,
        le=1.0,
        description="Maximum probability shift for any move",
    )
    mean_probability_delta: float = Field(
        ...,
        alias="meanProbabilityDelta",
        ge=0.0,
        le=1.0,
        description="Mean absolute probability shift across moves",
    )


class EnvelopeUtilizationV1(BaseModel):
    """Safety envelope utilization statistics (M18)."""

    model_config = ConfigDict(populate_by_name=True)

    delta_p_max_used_pct: float = Field(
        ...,
        alias="deltaPMaxUsedPct",
        ge=0.0,
        le=100.0,
        description="Percentage of delta_p_max utilized [0.0, 100.0]",
    )
    delta_p_max_used_abs: float | None = Field(
        None,
        alias="deltaPMaxUsedAbs",
        ge=0.0,
        le=1.0,
        description="Absolute delta_p_max utilization",
    )
    delta_p_max_limit: float = Field(
        ...,
        alias="deltaPMaxLimit",
        ge=0.0,
        le=1.0,
        description="The delta_p_max limit from constraints",
    )
    top_k_binding: bool = Field(
        ...,
        alias="topKBinding",
        description="Whether top_k constraint was binding (moves were truncated)",
    )
    top_k_limit: int = Field(
        ..., alias="topKLimit", ge=1, description="The top_k limit from constraints"
    )
    moves_considered: int = Field(
        ..., alias="movesConsidered", ge=0, description="Actual number of moves considered"
    )
    entropy_in_bounds: bool = Field(
        ..., alias="entropyInBounds", description="Whether output entropy is within bounds"
    )
    output_entropy: float = Field(
        ..., alias="outputEntropy", ge=0.0, description="Actual output entropy"
    )


class StructuralAttributionV1(BaseModel):
    """Attribution of divergence to structural features (M18)."""

    model_config = ConfigDict(populate_by_name=True)

    style_score_components: dict[str, ComponentStatsV1] | None = Field(
        None,
        alias="styleScoreComponents",
        description="Per-component style score statistics",
    )
    feature_deltas: dict[str, ComponentStatsV1] | None = Field(
        None,
        alias="featureDeltas",
        description="Per-feature delta statistics",
    )
    correlation_proxy: float | None = Field(
        None,
        alias="correlationProxy",
        ge=-1.0,
        le=1.0,
        description="Normalized dot product between style scores and divergence (proxy)",
    )


class PolicyStatsV1(BaseModel):
    """Policy distribution statistics (M18)."""

    model_config = ConfigDict(populate_by_name=True)

    base_entropy: float = Field(
        ..., alias="baseEntropy", ge=0.0, description="Entropy of base policy"
    )
    output_entropy: float = Field(
        ..., alias="outputEntropy", ge=0.0, description="Entropy of output policy"
    )
    entropy_delta: float = Field(
        ..., alias="entropyDelta", description="Change in entropy (output - base)"
    )
    move_count: int = Field(..., alias="moveCount", ge=0, description="Number of moves in policy")
    base_top_gap: float | None = Field(
        None, alias="baseTopGap", ge=0.0, le=1.0, description="Top gap in base policy"
    )
    output_top_gap: float | None = Field(
        None, alias="outputTopGap", ge=0.0, le=1.0, description="Top gap in output policy"
    )


class PersonalityEvalArtifactV1(BaseModel):
    """Personality evaluation artifact (M18).

    Captures divergence metrics, envelope utilization, and structural attribution
    for offline personality evaluation and comparison.

    This artifact is output-only (not used for runtime wiring) and supports:
    - Scientific claims about personality effects
    - Determinism verification via hash
    - Traceable attribution to structural features
    """

    model_config = ConfigDict(populate_by_name=True)

    schema_version: Literal["personality_eval_artifact.v1"] = Field(
        "personality_eval_artifact.v1",
        alias="schemaVersion",
        description="Schema version identifier",
    )
    created_at: datetime = Field(
        ..., alias="createdAt", description="ISO 8601 timestamp of artifact creation"
    )
    personality_id: str = Field(
        ...,
        alias="personalityId",
        pattern=r"^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+$",
        description="Personality being evaluated (e.g., 'style.pawn_clamp.v1')",
    )
    baseline_id: str = Field(
        ...,
        alias="baselineId",
        pattern=r"^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+$",
        description="Baseline personality for comparison (e.g., 'control.neutral_baseline.v1')",
    )
    config_hash: str = Field(
        ...,
        alias="configHash",
        pattern="^[a-f0-9]{64}$",
        description="SHA-256 hash of personality configuration used",
    )
    determinism_hash: str = Field(
        ...,
        alias="determinismHash",
        pattern="^[a-f0-9]{64}$",
        description="SHA-256 hash for determinism verification (hash of all inputs + outputs)",
    )
    fixture_id: str | None = Field(
        None, alias="fixtureId", description="Identifier of the fixture used (for traceability)"
    )
    divergence_metrics: DivergenceMetricsV1 = Field(
        ...,
        alias="divergenceMetrics",
        description="Divergence metrics between personality and baseline",
    )
    envelope_utilization: EnvelopeUtilizationV1 = Field(
        ...,
        alias="envelopeUtilization",
        description="Safety envelope utilization statistics",
    )
    structural_attribution: StructuralAttributionV1 | None = Field(
        None,
        alias="structuralAttribution",
        description="Attribution of divergence to structural features (optional)",
    )
    policy_stats: PolicyStatsV1 = Field(
        ..., alias="policyStats", description="Policy distribution statistics"
    )
