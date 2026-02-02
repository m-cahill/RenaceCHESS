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
        populate_by_name=True,
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


# =============================================================================
# AdviceFacts Models (M19) — Phase C Coaching Foundation
# =============================================================================


class AdviceFactsPositionV1(BaseModel):
    """Position representation for AdviceFacts (M19)."""

    model_config = ConfigDict(populate_by_name=True)

    fen: str = Field(..., description="FEN string representing the position")
    side_to_move: Literal["white", "black"] = Field(
        ..., alias="sideToMove", description="Side to move"
    )


class AdviceFactsContextV1(BaseModel):
    """Conditioning context for AdviceFacts (M19)."""

    model_config = ConfigDict(populate_by_name=True)

    skill_bucket: str = Field(..., alias="skillBucket", description="Skill bucket identifier")
    time_control_bucket: str | None = Field(
        None, alias="timeControlBucket", description="Time control bucket"
    )
    time_pressure_bucket: str | None = Field(
        None, alias="timePressureBucket", description="Time pressure bucket"
    )


class AdviceFactsMoveV1(BaseModel):
    """Move entry in policy distribution for AdviceFacts (M19)."""

    model_config = ConfigDict(populate_by_name=True)

    uci: str = Field(..., description="Move in UCI notation")
    san: str | None = Field(None, description="Move in SAN notation (optional)")
    prob: float = Field(..., ge=0.0, le=1.0, description="Probability of this move (0-1)")


class AdviceFactsPolicyV1(BaseModel):
    """Policy distribution for AdviceFacts (M19)."""

    model_config = ConfigDict(populate_by_name=True)

    top_moves: list[AdviceFactsMoveV1] = Field(
        ...,
        alias="topMoves",
        min_length=1,
        description="Top moves ordered by prob desc, then UCI asc",
    )
    recommended_move: AdviceFactsMoveV1 = Field(
        ..., alias="recommendedMove", description="The top recommended move"
    )


class AdviceFactsOutcomeV1(BaseModel):
    """Outcome (W/D/L) probabilities for AdviceFacts (M19)."""

    model_config = ConfigDict(populate_by_name=True)

    p_win: float = Field(..., alias="pWin", ge=0.0, le=1.0, description="Win probability")
    p_draw: float = Field(..., alias="pDraw", ge=0.0, le=1.0, description="Draw probability")
    p_loss: float = Field(..., alias="pLoss", ge=0.0, le=1.0, description="Loss probability")

    @model_validator(mode="after")
    def validate_probabilities_sum(self) -> AdviceFactsOutcomeV1:
        """Validate that probabilities sum to approximately 1.0."""
        total = self.p_win + self.p_draw + self.p_loss
        if abs(total - 1.0) > 1e-4:
            msg = f"Outcome probabilities must sum to 1.0, got {total:.6f}"
            raise ValueError(msg)
        return self


class AdviceFactsHDIV1(BaseModel):
    """Human Difficulty Index for AdviceFacts (M19)."""

    model_config = ConfigDict(populate_by_name=True)

    value: float = Field(
        ..., ge=0.0, le=1.0, description="HDI value (0-1, higher = more difficult)"
    )
    entropy: float | None = Field(None, ge=0.0, description="Entropy component")
    top_gap_inverted: float | None = Field(
        None, alias="topGapInverted", ge=0.0, le=1.0, description="Top gap inverted"
    )
    legal_move_pressure: float | None = Field(
        None, alias="legalMovePressure", ge=0.0, le=1.0, description="Legal move pressure"
    )
    outcome_sensitivity: float | None = Field(
        None, alias="outcomeSensitivity", ge=0.0, le=1.0, description="Outcome sensitivity"
    )


class AdviceFactsStructuralCognitionV1(BaseModel):
    """Summarized structural cognition for AdviceFacts (M19, optional)."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    mobility_delta: float | None = Field(
        None, alias="mobilityDelta", description="Change in mobility"
    )
    weak_squares_delta: float | None = Field(
        None, alias="weakSquaresDelta", description="Change in weak squares count"
    )
    strong_squares_delta: float | None = Field(
        None, alias="strongSquaresDelta", description="Change in strong squares count"
    )
    summary: str | None = Field(None, description="Brief structural summary")


class AdviceFactsExplanationHintV1(BaseModel):
    """Explanation hint tag for future coaching (M19 placeholder for M20+)."""

    model_config = ConfigDict(populate_by_name=True)

    tag: str = Field(..., description="Hint tag identifier")
    weight: float | None = Field(None, description="Relative importance weight")


class AdviceFactsSourceContractsV1(BaseModel):
    """Source contract versions for traceability (M19)."""

    model_config = ConfigDict(populate_by_name=True)

    advice_facts_contract: str = Field(
        ..., alias="adviceFactsContract", description="Version of ADVICE_FACTS_CONTRACT"
    )
    input_semantics_contract: str = Field(
        ..., alias="inputSemanticsContract", description="Version of CONTRACT_INPUT_SEMANTICS"
    )
    structural_cognition_contract: str | None = Field(
        None,
        alias="structuralCognitionContract",
        description="Version of StructuralCognitionContract (if structuralCognition present)",
    )


class AdviceFactsV1(BaseModel):
    """AdviceFacts v1 — deterministic, schema-stable facts-only artifact for LLM coaching.

    This artifact contains pre-computed signals that LLMs may translate into
    Elo-appropriate coaching. LLMs must NOT invent analysis beyond these facts.

    See: ADR-COACHING-001, ADVICE_FACTS_CONTRACT_v1.md

    Canonical ordering rules:
    - topMoves: ordered by prob descending, then UCI ascending for ties
    - Float rounding: 6 decimal places for determinism hash
    - Key ordering: alphabetical for canonical JSON
    """

    model_config = ConfigDict(populate_by_name=True)

    version: Literal["1.0"] = Field("1.0", description="Schema version")
    generated_at: datetime = Field(..., alias="generatedAt", description="ISO 8601 timestamp")
    position: AdviceFactsPositionV1 = Field(..., description="Chess position")
    context: AdviceFactsContextV1 = Field(..., description="Conditioning context")
    policy: AdviceFactsPolicyV1 = Field(..., description="Policy distribution")
    outcome: AdviceFactsOutcomeV1 = Field(..., description="W/D/L probabilities")
    hdi: AdviceFactsHDIV1 = Field(..., description="Human Difficulty Index")
    structural_cognition: AdviceFactsStructuralCognitionV1 | None = Field(
        None,
        alias="structuralCognition",
        description="Structural cognition deltas (optional)",
    )
    explanation_hints: list[AdviceFactsExplanationHintV1] | None = Field(
        None,
        alias="explanationHints",
        description="Explanation hints for M20+ (optional placeholder)",
    )
    determinism_hash: str = Field(
        ...,
        alias="determinismHash",
        pattern="^sha256:[a-f0-9]{64}$",
        description="SHA-256 hash of canonical JSON",
    )
    source_contract_versions: AdviceFactsSourceContractsV1 = Field(
        ..., alias="sourceContractVersions", description="Source contract versions"
    )


class AdviceFactsInputsV1(BaseModel):
    """Input container for AdviceFacts builder (M19).

    This is the input to `build_advice_facts_v1()` — a pure function that
    accepts pre-computed signals and produces AdviceFactsV1.

    All inputs are already-computed values from policy/outcome/HDI providers.
    The builder does not orchestrate provider calls.
    """

    model_config = ConfigDict(populate_by_name=True)

    # Position
    fen: str = Field(..., description="FEN string")
    side_to_move: Literal["white", "black"] = Field(
        ..., alias="sideToMove", description="Side to move"
    )

    # Context
    skill_bucket: str = Field(..., alias="skillBucket", description="Skill bucket")
    time_control_bucket: str | None = Field(
        None, alias="timeControlBucket", description="Time control bucket"
    )
    time_pressure_bucket: str | None = Field(
        None, alias="timePressureBucket", description="Time pressure bucket"
    )

    # Policy (already ordered by probability descending)
    top_moves: list[tuple[str, float]] = Field(
        ...,
        alias="topMoves",
        min_length=1,
        description="Top moves as (uci, prob) tuples, ordered by prob desc",
    )
    top_moves_san: list[str] | None = Field(
        None, alias="topMovesSan", description="SAN for top moves (optional, same order)"
    )

    # Outcome
    p_win: float = Field(..., alias="pWin", ge=0.0, le=1.0)
    p_draw: float = Field(..., alias="pDraw", ge=0.0, le=1.0)
    p_loss: float = Field(..., alias="pLoss", ge=0.0, le=1.0)

    # HDI
    hdi_value: float = Field(..., alias="hdiValue", ge=0.0, le=1.0)
    hdi_entropy: float | None = Field(None, alias="hdiEntropy", ge=0.0)
    hdi_top_gap_inverted: float | None = Field(None, alias="hdiTopGapInverted", ge=0.0, le=1.0)
    hdi_legal_move_pressure: float | None = Field(
        None, alias="hdiLegalMovePressure", ge=0.0, le=1.0
    )
    hdi_outcome_sensitivity: float | None = Field(
        None, alias="hdiOutcomeSensitivity", ge=0.0, le=1.0
    )

    # Structural cognition (optional)
    mobility_delta: float | None = Field(None, alias="mobilityDelta")
    weak_squares_delta: float | None = Field(None, alias="weakSquaresDelta")
    strong_squares_delta: float | None = Field(None, alias="strongSquaresDelta")
    structural_summary: str | None = Field(None, alias="structuralSummary")


# =============================================================================
# Elo-Bucket Delta Facts Models (M20) — Phase C Elo-Relative Reasoning
# =============================================================================


class PolicySummaryMoveV1(BaseModel):
    """Move entry in a policy summary for delta comparison (M20)."""

    model_config = ConfigDict(populate_by_name=True)

    uci: str = Field(..., description="Move in UCI notation")
    prob: float = Field(..., ge=0.0, le=1.0, description="Probability of this move")


class PolicySummaryV1(BaseModel):
    """Policy summary for delta comparison (M20).

    A compact representation of a policy distribution for computing deltas.
    """

    model_config = ConfigDict(populate_by_name=True)

    top_moves: list[PolicySummaryMoveV1] = Field(
        ...,
        alias="topMoves",
        min_length=1,
        description="Top moves ordered by prob descending",
    )
    top_k: int = Field(
        ...,
        alias="topK",
        ge=1,
        description="Number of top moves included",
    )


class OutcomeSummaryV1(BaseModel):
    """Outcome (W/D/L) summary for delta comparison (M20)."""

    model_config = ConfigDict(populate_by_name=True)

    p_win: float = Field(..., alias="pWin", ge=0.0, le=1.0, description="Win probability")
    p_draw: float = Field(..., alias="pDraw", ge=0.0, le=1.0, description="Draw probability")
    p_loss: float = Field(..., alias="pLoss", ge=0.0, le=1.0, description="Loss probability")

    @model_validator(mode="after")
    def validate_probabilities_sum(self) -> OutcomeSummaryV1:
        """Validate that probabilities sum to approximately 1.0."""
        total = self.p_win + self.p_draw + self.p_loss
        if abs(total - 1.0) > 1e-4:
            msg = f"Outcome probabilities must sum to 1.0, got {total:.6f}"
            raise ValueError(msg)
        return self


class PolicyDeltaV1(BaseModel):
    """Policy divergence metrics between two buckets (M20).

    All metrics are computed by comparing baseline_bucket to comparison_bucket.
    """

    model_config = ConfigDict(populate_by_name=True)

    kl_divergence: float = Field(
        ...,
        alias="klDivergence",
        ge=0.0,
        description="KL divergence from baseline to comparison (bits)",
    )
    total_variation: float = Field(
        ...,
        alias="totalVariation",
        ge=0.0,
        le=1.0,
        description="Total Variation distance [0.0, 1.0]",
    )
    rank_flips: int = Field(
        ...,
        alias="rankFlips",
        ge=0,
        description="Number of moves ranked differently between buckets",
    )
    mass_shift_to_top: float = Field(
        ...,
        alias="massShiftToTop",
        ge=-1.0,
        le=1.0,
        description="Probability mass shift toward top-1 (positive = comparison favors top move)",
    )


class OutcomeDeltaV1(BaseModel):
    """Outcome expectation shifts between two buckets (M20)."""

    model_config = ConfigDict(populate_by_name=True)

    delta_p_win: float = Field(
        ...,
        alias="deltaPWin",
        ge=-1.0,
        le=1.0,
        description="Change in win probability (comparison - baseline)",
    )
    delta_p_draw: float = Field(
        ...,
        alias="deltaPDraw",
        ge=-1.0,
        le=1.0,
        description="Change in draw probability (comparison - baseline)",
    )
    delta_p_loss: float = Field(
        ...,
        alias="deltaPLoss",
        ge=-1.0,
        le=1.0,
        description="Change in loss probability (comparison - baseline)",
    )
    win_rate_monotonic: bool = Field(
        ...,
        alias="winRateMonotonic",
        description="True if win rate change is in expected direction (higher skill → higher win)",
    )


class DifficultyDeltaV1(BaseModel):
    """Difficulty sensitivity metrics between two buckets (M20)."""

    model_config = ConfigDict(populate_by_name=True)

    delta_hdi: float = Field(
        ...,
        alias="deltaHDI",
        ge=-1.0,
        le=1.0,
        description="Change in Human Difficulty Index (comparison - baseline)",
    )


class StructuralEmphasisDeltaV1(BaseModel):
    """Structural emphasis shifts between two buckets (M20, optional).

    Captures how structural features influence move selection differently
    across skill levels.
    """

    model_config = ConfigDict(populate_by_name=True)

    mobility_emphasis_delta: float | None = Field(
        None,
        alias="mobilityEmphasisDelta",
        description="Change in mobility reliance (positive = comparison values mobility more)",
    )
    weak_square_sensitivity_delta: float | None = Field(
        None,
        alias="weakSquareSensitivityDelta",
        description="Change in weak square sensitivity",
    )
    king_safety_weight_delta: float | None = Field(
        None,
        alias="kingSafetyWeightDelta",
        description="Change in king safety weighting",
    )


class EloBucketDeltaSourceContractsV1(BaseModel):
    """Source contract versions for traceability (M20)."""

    model_config = ConfigDict(populate_by_name=True)

    elo_bucket_delta_contract: str = Field(
        ...,
        alias="eloBucketDeltaContract",
        description="Version of ELO_BUCKET_DELTA_FACTS_CONTRACT",
    )
    advice_facts_contract: str = Field(
        ...,
        alias="adviceFactsContract",
        description="Version of ADVICE_FACTS_CONTRACT used for source artifacts",
    )


class EloBucketDeltaFactsV1(BaseModel):
    """Elo-bucket delta facts artifact (M20).

    Describes statistical and structural differences between two Elo buckets
    for the same position. This is a facts-only artifact — no prose, no advice.

    Lineage:
    - Derived from two AdviceFactsV1 artifacts (baseline + comparison buckets)
    - sourceAdviceFactsHashes provides audit trail

    See: ELO_BUCKET_DELTA_FACTS_CONTRACT_v1.md
    """

    model_config = ConfigDict(populate_by_name=True)

    schema_version: Literal["elo_bucket_delta_facts.v1"] = Field(
        "elo_bucket_delta_facts.v1",
        alias="schemaVersion",
        description="Schema version identifier",
    )
    generated_at: datetime = Field(
        ...,
        alias="generatedAt",
        description="ISO 8601 timestamp of artifact creation",
    )

    # Bucket identification
    baseline_bucket: str = Field(
        ...,
        alias="baselineBucket",
        description="Baseline skill bucket ID (e.g., '1200_1399')",
    )
    comparison_bucket: str = Field(
        ...,
        alias="comparisonBucket",
        description="Comparison skill bucket ID (e.g., '1600_1799')",
    )

    # Lineage (required for governance/auditability)
    source_advice_facts_hashes: list[str] = Field(
        ...,
        alias="sourceAdviceFactsHashes",
        min_length=2,
        max_length=2,
        description="SHA-256 hashes of source AdviceFacts [baseline_hash, comparison_hash]",
    )

    # Delta categories
    policy_delta: PolicyDeltaV1 = Field(
        ...,
        alias="policyDelta",
        description="Policy divergence metrics",
    )
    outcome_delta: OutcomeDeltaV1 = Field(
        ...,
        alias="outcomeDelta",
        description="Outcome expectation shifts",
    )
    difficulty_delta: DifficultyDeltaV1 = Field(
        ...,
        alias="difficultyDelta",
        description="Difficulty sensitivity metrics",
    )
    structural_delta: StructuralEmphasisDeltaV1 | None = Field(
        None,
        alias="structuralDelta",
        description="Structural emphasis shifts (optional, present if structural data available)",
    )

    # Governance
    determinism_hash: str = Field(
        ...,
        alias="determinismHash",
        pattern="^sha256:[a-f0-9]{64}$",
        description="SHA-256 hash of canonical JSON for determinism verification",
    )
    source_contract_versions: EloBucketDeltaSourceContractsV1 = Field(
        ...,
        alias="sourceContractVersions",
        description="Source contract versions for traceability",
    )


# =============================================================================
# Coaching Draft Models (M21) — LLM Translation Artifacts
# =============================================================================


class ToneProfileV1(BaseModel):
    """Tone profile for coaching output (M21).

    Fixed enum for v1: NEUTRAL, ENCOURAGING, CONCISE
    """

    model_config = ConfigDict(populate_by_name=True)

    value: Literal["neutral", "encouraging", "concise"] = Field(
        ..., description="Tone profile value"
    )


class CoachingDraftReferencedFactV1(BaseModel):
    """Reference to a specific fact used in the draft (M21).

    Tracks which facts from AdviceFactsV1/EloBucketDeltaFactsV1 were
    referenced in the generated prose.
    """

    model_config = ConfigDict(populate_by_name=True)

    source_artifact: Literal["advice_facts", "delta_facts"] = Field(
        ..., alias="sourceArtifact", description="Source artifact type"
    )
    field_path: str = Field(..., alias="fieldPath", description="JSON path to the referenced field")
    value_summary: str = Field(
        ..., alias="valueSummary", description="Summary of the referenced value"
    )


class CoachingDraftDeterminismMetadataV1(BaseModel):
    """Determinism metadata for audit trail (M21).

    Records all parameters needed to reproduce the draft.
    """

    model_config = ConfigDict(populate_by_name=True)

    prompt_template_version: str = Field(
        ..., alias="promptTemplateVersion", description="Version of prompt template used"
    )
    prompt_hash: str = Field(
        ...,
        alias="promptHash",
        pattern="^[a-f0-9]{64}$",
        description="SHA-256 hash of the actual prompt sent",
    )
    model_id: str = Field(
        ..., alias="modelId", description="LLM model identifier (e.g., 'stub-v1', 'gpt-4')"
    )
    temperature: float = Field(
        ..., ge=0.0, le=2.0, description="Temperature setting (0 for deterministic)"
    )
    provider: str = Field(..., description="Provider name (e.g., 'stub', 'openai')")


class CoachingDraftV1(BaseModel):
    """Coaching draft artifact (M21).

    An intermediate, evaluable artifact produced by LLM translation of facts.
    This is NOT user-facing output — it's for evaluation and audit.

    Key properties:
    - draftText: The generated prose
    - referencedFacts: Explicit list of facts used
    - determinismMetadata: Full reproducibility info

    See: COACHING_TRANSLATION_PROMPT_v1.md, ADR-COACHING-001
    """

    model_config = ConfigDict(populate_by_name=True)

    schema_version: Literal["coaching_draft.v1"] = Field(
        "coaching_draft.v1",
        alias="schemaVersion",
        description="Schema version identifier",
    )
    generated_at: datetime = Field(
        ..., alias="generatedAt", description="ISO 8601 timestamp of generation"
    )

    # Core content
    draft_text: str = Field(
        ..., alias="draftText", min_length=1, description="Generated coaching prose"
    )
    skill_bucket: str = Field(
        ..., alias="skillBucket", description="Target skill bucket for this draft"
    )
    tone_profile: Literal["neutral", "encouraging", "concise"] = Field(
        ..., alias="toneProfile", description="Tone profile used"
    )

    # Fact references (for hallucination detection)
    referenced_facts: list[CoachingDraftReferencedFactV1] = Field(
        default_factory=list,
        alias="referencedFacts",
        description="Explicit list of facts referenced in the draft",
    )

    # Source hashes (for lineage)
    source_advice_facts_hash: str = Field(
        ...,
        alias="sourceAdviceFactsHash",
        pattern="^sha256:[a-f0-9]{64}$",
        description="Determinism hash of source AdviceFactsV1",
    )
    source_delta_facts_hash: str | None = Field(
        None,
        alias="sourceDeltaFactsHash",
        pattern="^sha256:[a-f0-9]{64}$",
        description="Determinism hash of source EloBucketDeltaFactsV1 (optional)",
    )

    # Determinism metadata
    determinism_metadata: CoachingDraftDeterminismMetadataV1 = Field(
        ..., alias="determinismMetadata", description="Metadata for reproducibility"
    )

    # Artifact hash
    determinism_hash: str = Field(
        ...,
        alias="determinismHash",
        pattern="^sha256:[a-f0-9]{64}$",
        description="SHA-256 hash of canonical JSON for this artifact",
    )


# =============================================================================
# Coaching Evaluation Models (M21) — Offline Quality Metrics
# =============================================================================


class HallucinationMetricsV1(BaseModel):
    """Hallucination detection metrics (M21).

    Rule-based metrics for detecting unsupported claims.
    """

    model_config = ConfigDict(populate_by_name=True)

    forbidden_terms_found: list[str] = Field(
        default_factory=list,
        alias="forbiddenTermsFound",
        description="List of forbidden terms detected in the draft",
    )
    unsupported_moves: list[str] = Field(
        default_factory=list,
        alias="unsupportedMoves",
        description="UCI moves mentioned but not in source facts",
    )
    unsupported_percentages: list[str] = Field(
        default_factory=list,
        alias="unsupportedPercentages",
        description="Percentages mentioned but not matching source facts",
    )
    unsupported_structural_claims: list[str] = Field(
        default_factory=list,
        alias="unsupportedStructuralClaims",
        description="Structural vocabulary not supported by facts",
    )
    total_unsupported_claims: int = Field(
        ..., alias="totalUnsupportedClaims", ge=0, description="Total unsupported claims"
    )
    total_sentences: int = Field(
        ..., alias="totalSentences", ge=1, description="Total sentences in draft"
    )


class CoachingEvaluationMetricsV1(BaseModel):
    """Evaluation metrics for coaching draft (M21).

    Numeric, deterministic metrics for offline scoring.
    """

    model_config = ConfigDict(populate_by_name=True)

    fact_coverage: float = Field(
        ...,
        alias="factCoverage",
        ge=0.0,
        le=1.0,
        description="Fraction of salient facts referenced (0.0-1.0)",
    )
    hallucination_rate: float = Field(
        ...,
        alias="hallucinationRate",
        ge=0.0,
        le=1.0,
        description="Fraction of sentences with unsupported claims (0.0-1.0)",
    )
    bucket_alignment: bool = Field(
        ...,
        alias="bucketAlignment",
        description="True if language matches target skill bucket",
    )
    delta_faithfulness: float = Field(
        ...,
        alias="deltaFaithfulness",
        ge=0.0,
        le=1.0,
        description="Accuracy of Elo delta claims (1.0 if no deltas or all correct)",
    )
    verbosity_score: float = Field(
        ...,
        alias="verbosityScore",
        ge=0.0,
        le=1.0,
        description="Verbosity score (0.0=too short, 0.5=ideal, 1.0=too long)",
    )


class CoachingEvaluationV1(BaseModel):
    """Coaching evaluation artifact (M21).

    Offline evaluation of a CoachingDraftV1 against source facts.
    This artifact is used for quality assurance, not runtime.

    See: COACHING_TRANSLATION_PROMPT_v1.md, ADR-COACHING-001
    """

    model_config = ConfigDict(populate_by_name=True)

    schema_version: Literal["coaching_evaluation.v1"] = Field(
        "coaching_evaluation.v1",
        alias="schemaVersion",
        description="Schema version identifier",
    )
    evaluated_at: datetime = Field(
        ..., alias="evaluatedAt", description="ISO 8601 timestamp of evaluation"
    )

    # Source references
    source_draft_hash: str = Field(
        ...,
        alias="sourceDraftHash",
        pattern="^sha256:[a-f0-9]{64}$",
        description="Determinism hash of evaluated CoachingDraftV1",
    )
    source_advice_facts_hash: str = Field(
        ...,
        alias="sourceAdviceFactsHash",
        pattern="^sha256:[a-f0-9]{64}$",
        description="Determinism hash of source AdviceFactsV1",
    )
    source_delta_facts_hash: str | None = Field(
        None,
        alias="sourceDeltaFactsHash",
        pattern="^sha256:[a-f0-9]{64}$",
        description="Determinism hash of source EloBucketDeltaFactsV1 (optional)",
    )

    # Metrics
    metrics: CoachingEvaluationMetricsV1 = Field(..., description="Evaluation metrics")
    hallucination_details: HallucinationMetricsV1 = Field(
        ..., alias="hallucinationDetails", description="Detailed hallucination analysis"
    )

    # Verdict
    passed: bool = Field(..., description="True if draft passes all quality gates")
    failure_reasons: list[str] = Field(
        default_factory=list,
        alias="failureReasons",
        description="Reasons for failure (empty if passed)",
    )

    # Determinism
    determinism_hash: str = Field(
        ...,
        alias="determinismHash",
        pattern="^sha256:[a-f0-9]{64}$",
        description="SHA-256 hash of canonical JSON for this artifact",
    )


# =============================================================================
# Coaching Surface Models (M22) — CLI Exposure Artifact
# =============================================================================


class CoachingSurfaceEvaluationSummaryV1(BaseModel):
    """Evaluation summary for CLI surface output (M22).

    A subset of CoachingEvaluationV1 metrics for human-readable display.
    This is a projection, not a transformation — values come directly
    from the source CoachingEvaluationV1.
    """

    model_config = ConfigDict(populate_by_name=True)

    fact_coverage: float = Field(
        ...,
        alias="factCoverage",
        ge=0.0,
        le=1.0,
        description="Fraction of salient facts referenced (0.0-1.0)",
    )
    hallucination_rate: float = Field(
        ...,
        alias="hallucinationRate",
        ge=0.0,
        le=1.0,
        description="Fraction of sentences with unsupported claims (0.0-1.0)",
    )
    bucket_alignment: bool = Field(
        ...,
        alias="bucketAlignment",
        description="True if language matches target skill bucket",
    )
    delta_faithfulness: float = Field(
        ...,
        alias="deltaFaithfulness",
        ge=0.0,
        le=1.0,
        description="Accuracy of Elo delta claims",
    )
    verbosity_score: float = Field(
        ...,
        alias="verbosityScore",
        ge=0.0,
        le=1.0,
        description="Verbosity score (0.0=too short, 0.5=ideal, 1.0=too long)",
    )
    passed: bool = Field(
        ...,
        description="True if evaluation passed all quality gates",
    )
    failure_reasons: list[str] = Field(
        default_factory=list,
        alias="failureReasons",
        description="Reasons for failure (empty if passed)",
    )


class CoachingSurfaceV1(BaseModel):
    """Coaching surface artifact (M22).

    A contracted, auditable projection of coaching output for CLI consumption.
    This artifact wraps CoachingDraftV1 and CoachingEvaluationV1 into a
    stable CLI output contract.

    Key properties:
    - This is a PROJECTION, not a transformation
    - All fields come from existing artifacts
    - Evaluation summary is ALWAYS visible (never hidden)
    - Lineage hashes enable audit trail

    See: M22_plan.md, ADR-COACHING-001
    """

    model_config = ConfigDict(populate_by_name=True)

    schema_version: Literal["coaching_surface.v1"] = Field(
        "coaching_surface.v1",
        alias="schemaVersion",
        description="Schema version identifier",
    )
    generated_at: datetime = Field(
        ...,
        alias="generatedAt",
        description="ISO 8601 timestamp of surface artifact creation",
    )

    # Core content (from CoachingDraftV1)
    coaching_text: str = Field(
        ...,
        alias="coachingText",
        min_length=1,
        description="Generated coaching prose (from CoachingDraftV1.draftText)",
    )
    skill_bucket: str = Field(
        ...,
        alias="skillBucket",
        description="Target skill bucket for this coaching",
    )
    tone_profile: Literal["neutral", "encouraging", "concise"] = Field(
        ...,
        alias="toneProfile",
        description="Tone profile used for generation",
    )

    # Evaluation summary (always visible, never suppressed)
    evaluation_summary: CoachingSurfaceEvaluationSummaryV1 = Field(
        ...,
        alias="evaluationSummary",
        description="Evaluation metrics (always displayed, never hidden)",
    )

    # Lineage hashes (for audit trail)
    source_advice_facts_hash: str = Field(
        ...,
        alias="sourceAdviceFactsHash",
        pattern="^sha256:[a-f0-9]{64}$",
        description="Determinism hash of source AdviceFactsV1",
    )
    source_delta_facts_hash: str = Field(
        ...,
        alias="sourceDeltaFactsHash",
        pattern="^sha256:[a-f0-9]{64}$",
        description="Determinism hash of source EloBucketDeltaFactsV1 (required in M22)",
    )
    coaching_draft_hash: str = Field(
        ...,
        alias="coachingDraftHash",
        pattern="^sha256:[a-f0-9]{64}$",
        description="Determinism hash of source CoachingDraftV1",
    )
    coaching_evaluation_hash: str = Field(
        ...,
        alias="coachingEvaluationHash",
        pattern="^sha256:[a-f0-9]{64}$",
        description="Determinism hash of source CoachingEvaluationV1",
    )


# =============================================================================
# M24 — Calibration Metrics v1 (Phase D Calibration)
# =============================================================================


class CalibrationBinV1(BaseModel):
    """Single calibration bin with histogram statistics.

    Represents one bin in a fixed 10-bin calibration histogram [0.0, 1.0].
    """

    model_config = ConfigDict(populate_by_name=True)

    bin_start: float = Field(
        ...,
        alias="binStart",
        ge=0.0,
        le=1.0,
        description="Lower bound of bin (inclusive)",
    )
    bin_end: float = Field(
        ...,
        alias="binEnd",
        ge=0.0,
        le=1.0,
        description="Upper bound of bin (exclusive, except last bin)",
    )
    count: int = Field(
        ...,
        ge=0,
        description="Number of samples in this bin",
    )
    avg_confidence: float | None = Field(
        None,
        alias="avgConfidence",
        ge=0.0,
        le=1.0,
        description="Average predicted confidence in this bin (None if count=0)",
    )
    empirical_accuracy: float | None = Field(
        None,
        alias="empiricalAccuracy",
        ge=0.0,
        le=1.0,
        description="Empirical accuracy in this bin (None if count=0)",
    )


class CalibrationHistogramV1(BaseModel):
    """Calibration histogram with fixed bin edges.

    Uses 10 equal-width bins from 0.0 to 1.0.
    """

    model_config = ConfigDict(populate_by_name=True)

    bin_edges: list[float] = Field(
        ...,
        alias="binEdges",
        min_length=11,
        max_length=11,
        description="Fixed bin edges: [0.0, 0.1, 0.2, ..., 1.0] (11 values for 10 bins)",
    )
    bins: list[CalibrationBinV1] = Field(
        ...,
        min_length=10,
        max_length=10,
        description="Per-bin statistics (exactly 10 bins)",
    )


class OutcomeCalibrationMetricsV1(BaseModel):
    """Outcome head (W/D/L) calibration metrics.

    Measures calibration quality for the human outcome prediction head.
    """

    model_config = ConfigDict(populate_by_name=True)

    brier_score: float = Field(
        ...,
        alias="brierScore",
        ge=0.0,
        le=1.0,
        description="Brier score for outcome predictions (lower is better)",
    )
    nll: float = Field(
        ...,
        ge=0.0,
        description="Negative log-likelihood of true outcome under predicted distribution",
    )
    ece: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Expected Calibration Error (lower is better)",
    )
    histogram: CalibrationHistogramV1 = Field(
        ...,
        description="Calibration histogram for outcome confidence",
    )


class PolicyCalibrationMetricsV1(BaseModel):
    """Policy head (move distribution) calibration metrics.

    Measures calibration quality for the human move prediction head.
    """

    model_config = ConfigDict(populate_by_name=True)

    nll: float = Field(
        ...,
        ge=0.0,
        description="Negative log-likelihood of chosen move under predicted distribution",
    )
    top1_ece: float = Field(
        ...,
        alias="top1Ece",
        ge=0.0,
        le=1.0,
        description="Expected Calibration Error for top-1 move confidence",
    )
    histogram: CalibrationHistogramV1 = Field(
        ...,
        description="Calibration histogram for top-1 move confidence",
    )


class EloBucketCalibrationV1(BaseModel):
    """Calibration metrics for a single Elo bucket.

    Contains both outcome and policy calibration metrics for one skill bucket.
    """

    model_config = ConfigDict(populate_by_name=True)

    elo_bucket: Literal[
        "lt_800",
        "800_999",
        "1000_1199",
        "1200_1399",
        "1400_1599",
        "1600_1799",
        "gte_1800",
        "unknown",
    ] = Field(
        ...,
        alias="eloBucket",
        description="Skill bucket ID from conditioning.buckets (M06)",
    )
    samples: int = Field(
        ...,
        ge=0,
        description="Number of samples evaluated in this bucket",
    )
    outcome_calibration: OutcomeCalibrationMetricsV1 | None = Field(
        None,
        alias="outcomeCalibration",
        description="Outcome head calibration metrics (None if no labeled outcomes)",
    )
    policy_calibration: PolicyCalibrationMetricsV1 | None = Field(
        None,
        alias="policyCalibration",
        description="Policy head calibration metrics (None if no chosen move labels)",
    )


class CalibrationMetricsV1(BaseModel):
    """Top-level calibration metrics artifact (M24).

    Offline diagnostic artifact for measuring human-aligned calibration.
    This artifact is measurement-only and does not feed runtime logic.

    See docs/milestones/PhaseD/M24/M24_plan.md for the governing plan.
    """

    model_config = ConfigDict(populate_by_name=True)

    version: Literal["1.0"] = Field(
        "1.0",
        description="Schema version identifier",
    )
    generated_at: datetime = Field(
        ...,
        alias="generatedAt",
        description="ISO 8601 timestamp of metrics generation",
    )
    source_manifest_hash: str = Field(
        ...,
        alias="sourceManifestHash",
        pattern="^[a-f0-9]{64}$",
        description="SHA-256 hash of the frozen eval manifest used",
    )
    policy_id: str = Field(
        ...,
        alias="policyId",
        description="Policy provider identifier used for evaluation",
    )
    outcome_head_id: str | None = Field(
        None,
        alias="outcomeHeadId",
        description="Outcome head identifier used (None if using baselines)",
    )

    # Overall metrics (aggregated across all buckets)
    overall_samples: int = Field(
        ...,
        alias="overallSamples",
        ge=0,
        description="Total number of samples evaluated",
    )
    overall_outcome_calibration: OutcomeCalibrationMetricsV1 | None = Field(
        None,
        alias="overallOutcomeCalibration",
        description="Aggregated outcome calibration metrics",
    )
    overall_policy_calibration: PolicyCalibrationMetricsV1 | None = Field(
        None,
        alias="overallPolicyCalibration",
        description="Aggregated policy calibration metrics",
    )

    # Per-bucket breakdown
    by_elo_bucket: list[EloBucketCalibrationV1] = Field(
        ...,
        alias="byEloBucket",
        description="Calibration metrics per Elo bucket",
    )

    # Determinism
    determinism_hash: str = Field(
        ...,
        alias="determinismHash",
        pattern="^sha256:[a-f0-9]{64}$",
        description="SHA-256 hash for determinism verification",
    )


# =============================================================================
# M25 — Recalibration Parameters v1 (Phase D Recalibration)
# =============================================================================


class RecalibrationBucketParametersV1(BaseModel):
    """Recalibration parameters for a single Elo bucket.

    Contains fitted temperature scaling parameters for outcome and policy heads.
    """

    model_config = ConfigDict(populate_by_name=True)

    elo_bucket: str = Field(
        ...,
        alias="eloBucket",
        description="Canonical skill bucket ID (from conditioning.buckets.SkillBucketId)",
    )
    outcome_temperature: float = Field(
        ...,
        alias="outcomeTemperature",
        ge=0.25,
        le=3.0,
        description="Fitted temperature for outcome head (W/D/L) recalibration",
    )
    policy_temperature: float = Field(
        ...,
        alias="policyTemperature",
        ge=0.25,
        le=3.0,
        description="Fitted temperature for policy head (move probabilities) recalibration",
    )
    fit_method: Literal["grid_search"] = Field(
        "grid_search",
        alias="fitMethod",
        description="Method used for fitting (M25: grid_search only)",
    )
    fit_metric: Literal["nll"] = Field(
        "nll",
        alias="fitMetric",
        description="Metric optimized during fitting (M25: NLL only)",
    )


class RecalibrationParametersV1(BaseModel):
    """Top-level recalibration parameters artifact (M25).

    Pure parameter artifact containing fitted temperature scaling parameters per Elo bucket.
    Contains no logic and no metrics, only fitted parameters + provenance.

    See docs/milestones/PhaseD/M25/M25_plan.md for the governing plan.
    """

    model_config = ConfigDict(populate_by_name=True)

    version: Literal["1.0"] = Field(
        "1.0",
        description="Schema version identifier",
    )
    generated_at: datetime = Field(
        ...,
        alias="generatedAt",
        description="ISO 8601 timestamp of parameters generation",
    )
    source_calibration_metrics_hash: str = Field(
        ...,
        alias="sourceCalibrationMetricsHash",
        pattern="^sha256:[a-f0-9]{64}$",
        description="SHA-256 hash of the CalibrationMetricsV1 artifact used for fitting",
    )
    source_manifest_hash: str = Field(
        ...,
        alias="sourceManifestHash",
        pattern="^[a-f0-9]{64}$",
        description="SHA-256 hash of the frozen eval manifest used",
    )
    policy_id: str = Field(
        ...,
        alias="policyId",
        description="Policy provider identifier used for evaluation",
    )
    outcome_head_id: str | None = Field(
        None,
        alias="outcomeHeadId",
        description="Outcome head identifier used (None if using baselines)",
    )

    # Per-bucket parameters
    by_elo_bucket: list[RecalibrationBucketParametersV1] = Field(
        ...,
        alias="byEloBucket",
        description="Recalibration parameters per Elo bucket",
    )

    # Determinism
    determinism_hash: str = Field(
        ...,
        alias="determinismHash",
        pattern="^sha256:[a-f0-9]{64}$",
        description="SHA-256 hash for determinism verification",
    )


# =============================================================================
# M25 — Calibration Delta v1 (Before/After Comparison)
# =============================================================================


class CalibrationDeltaV1(BaseModel):
    """Calibration improvement/deterioration delta for a single metric and bucket.

    Represents before/after comparison for a single calibration metric.
    """

    model_config = ConfigDict(populate_by_name=True)

    elo_bucket: str = Field(
        ...,
        alias="eloBucket",
        description="Canonical skill bucket ID",
    )
    metric: Literal[
        "outcome_ece", "outcome_nll", "outcome_brier", "policy_nll", "policy_top1_ece"
    ] = Field(
        ...,
        description="Metric name being compared",
    )
    before: float = Field(
        ...,
        description="Metric value before recalibration",
    )
    after: float = Field(
        ...,
        description="Metric value after recalibration",
    )
    delta: float = Field(
        ...,
        description="Change in metric (after - before). Negative = improvement for ECE/NLL/Brier",
    )
    improved: bool = Field(
        ...,
        description=(
            "Whether recalibration improved this metric (True if delta < 0 for ECE/NLL/Brier)"
        ),
    )


class CalibrationDeltaArtifactV1(BaseModel):
    """Top-level calibration delta artifact (M25).

    Before/after comparison artifact showing calibration changes after recalibration.
    Separate from RecalibrationParametersV1 (parameters vs. evaluation).

    See docs/milestones/PhaseD/M25/M25_plan.md for the governing plan.
    """

    model_config = ConfigDict(populate_by_name=True)

    version: Literal["1.0"] = Field(
        "1.0",
        description="Schema version identifier",
    )
    generated_at: datetime = Field(
        ...,
        alias="generatedAt",
        description="ISO 8601 timestamp of delta generation",
    )
    source_recalibration_parameters_hash: str = Field(
        ...,
        alias="sourceRecalibrationParametersHash",
        pattern="^sha256:[a-f0-9]{64}$",
        description="SHA-256 hash of the RecalibrationParametersV1 artifact used",
    )
    source_calibration_metrics_before_hash: str = Field(
        ...,
        alias="sourceCalibrationMetricsBeforeHash",
        pattern="^sha256:[a-f0-9]{64}$",
        description="SHA-256 hash of the CalibrationMetricsV1 artifact (before recalibration)",
    )
    source_calibration_metrics_after_hash: str = Field(
        ...,
        alias="sourceCalibrationMetricsAfterHash",
        pattern="^sha256:[a-f0-9]{64}$",
        description="SHA-256 hash of the CalibrationMetricsV1 artifact (after recalibration)",
    )

    # Per-bucket deltas
    by_elo_bucket: list[list[CalibrationDeltaV1]] = Field(
        ...,
        alias="byEloBucket",
        description="List of deltas per bucket (each bucket has multiple metrics)",
    )

    # Determinism
    determinism_hash: str = Field(
        ...,
        alias="determinismHash",
        pattern="^sha256:[a-f0-9]{64}$",
        description="SHA-256 hash for determinism verification",
    )


# =============================================================================
# M26 — Recalibration Gate v1 (Phase D Runtime Gating)
# =============================================================================


class RecalibrationGateV1(BaseModel):
    """Runtime gate artifact for enabling recalibration (M26).

    This is the only authority that allows runtime recalibration to be applied.
    Must be explicitly provided as a file artifact (no environment variables or defaults).

    See docs/milestones/PhaseD/M26/M26_plan.md for the governing plan.
    """

    model_config = ConfigDict(populate_by_name=True)

    version: Literal["1.0"] = Field(
        "1.0",
        description="Schema version identifier",
    )
    enabled: bool = Field(
        ...,
        description="Whether recalibration is enabled (false = no change to runtime behavior)",
    )
    parameters_ref: str | None = Field(
        None,
        alias="parametersRef",
        description=(
            "Path or hash reference to RecalibrationParametersV1 artifact "
            "(required if enabled=True)"
        ),
    )
    scope: Literal["outcome", "policy", "both"] = Field(
        "both",
        description=(
            "Which heads to apply recalibration to: outcome (W/D/L), "
            "policy (move probabilities), or both"
        ),
    )
    applied_at: datetime | None = Field(
        None,
        alias="appliedAt",
        description="ISO 8601 timestamp when gate was applied (set at runtime, not in artifact)",
    )
    notes: str | None = Field(
        None,
        description="Optional notes about why this gate is enabled (for audit/debugging)",
    )

    @model_validator(mode="after")
    def validate_enabled_requires_params_ref(self) -> RecalibrationGateV1:
        """Validate that enabled=True requires parametersRef to be set."""
        if self.enabled and not self.parameters_ref:
            msg = "RecalibrationGateV1.enabled=True requires parametersRef to be set"
            raise ValueError(msg)
        return self


# =============================================================================
# M27 — Runtime Recalibration Evaluation (Phase D Runtime Evaluation)
# =============================================================================


class RuntimeCalibrationSnapshotV1(BaseModel):
    """Calibration metrics snapshot for a single evaluation run.

    Contains outcome and policy calibration metrics from either baseline
    (gate disabled) or recalibrated (gate enabled) evaluation.
    """

    model_config = ConfigDict(populate_by_name=True)

    outcome_ece: float = Field(
        ...,
        alias="outcomeEce",
        ge=0.0,
        le=1.0,
        description="Expected Calibration Error for outcome predictions",
    )
    outcome_nll: float = Field(
        ...,
        alias="outcomeNll",
        ge=0.0,
        description="Negative log-likelihood for outcome predictions",
    )
    outcome_brier: float = Field(
        ...,
        alias="outcomeBrier",
        ge=0.0,
        le=1.0,
        description="Brier score for outcome predictions",
    )
    policy_nll: float = Field(
        ...,
        alias="policyNll",
        ge=0.0,
        description="Negative log-likelihood for policy predictions",
    )
    policy_top1_ece: float = Field(
        ...,
        alias="policyTop1Ece",
        ge=0.0,
        le=1.0,
        description="Expected Calibration Error for top-1 move confidence",
    )
    mean_entropy: float = Field(
        ...,
        alias="meanEntropy",
        ge=0.0,
        description="Mean entropy of policy distribution",
    )


class RuntimeRecalibrationReportV1(BaseModel):
    """Paired runtime evaluation report comparing baseline vs recalibrated (M27).

    This artifact is evaluation-only and does not change default runtime behavior.
    Compares predictions with gate disabled (baseline) vs gate enabled (recalibrated).

    See docs/milestones/PhaseD/M27/M27_plan.md for the governing plan.
    """

    model_config = ConfigDict(populate_by_name=True)

    version: Literal["1.0"] = Field(
        "1.0",
        description="Schema version identifier",
    )
    generated_at: datetime = Field(
        ...,
        alias="generatedAt",
        description="ISO 8601 timestamp of report generation",
    )
    gate_ref: str = Field(
        ...,
        alias="gateRef",
        pattern=r"^sha256:[a-f0-9]{64}$",
        description="SHA-256 hash of the RecalibrationGateV1 artifact used",
    )
    parameters_ref: str = Field(
        ...,
        alias="parametersRef",
        pattern=r"^sha256:[a-f0-9]{64}$",
        description="SHA-256 hash of the RecalibrationParametersV1 artifact used",
    )
    dataset_ref: str = Field(
        ...,
        alias="datasetRef",
        pattern=r"^[a-f0-9]{64}$",
        description="SHA-256 hash of the frozen eval manifest used",
    )
    total_samples: int = Field(
        ...,
        alias="totalSamples",
        ge=0,
        description="Total number of samples evaluated",
    )
    baseline_metrics: RuntimeCalibrationSnapshotV1 = Field(
        ...,
        alias="baselineMetrics",
        description="Metrics from baseline run (gate disabled)",
    )
    recalibrated_metrics: RuntimeCalibrationSnapshotV1 = Field(
        ...,
        alias="recalibratedMetrics",
        description="Metrics from recalibrated run (gate enabled)",
    )
    determinism_hash: str = Field(
        ...,
        alias="determinismHash",
        pattern=r"^sha256:[a-f0-9]{64}$",
        description="SHA-256 hash for determinism verification of entire report",
    )


class MetricsDeltaV1(BaseModel):
    """Delta metrics comparing baseline vs recalibrated predictions.

    Contains calibration metric deltas plus policy-specific stability metrics.
    Negative deltas indicate improvement (lower ECE/NLL/Brier is better).
    """

    model_config = ConfigDict(populate_by_name=True)

    outcome_ece_delta: float = Field(
        ...,
        alias="outcomeEceDelta",
        description="Change in outcome ECE (negative = improvement)",
    )
    outcome_nll_delta: float = Field(
        ...,
        alias="outcomeNllDelta",
        description="Change in outcome NLL (negative = improvement)",
    )
    outcome_brier_delta: float = Field(
        ...,
        alias="outcomeBrierDelta",
        description="Change in outcome Brier score (negative = improvement)",
    )
    policy_nll_delta: float = Field(
        ...,
        alias="policyNllDelta",
        description="Change in policy NLL (negative = improvement)",
    )
    policy_top1_ece_delta: float = Field(
        ...,
        alias="policyTop1EceDelta",
        description="Change in policy top-1 ECE (negative = improvement)",
    )
    entropy_delta: float = Field(
        ...,
        alias="entropyDelta",
        description="Change in mean policy entropy",
    )
    top1_stability: float = Field(
        ...,
        alias="top1Stability",
        ge=0.0,
        le=1.0,
        description="Fraction of positions where top-1 move unchanged after recalibration",
    )
    top3_stability: float = Field(
        ...,
        alias="top3Stability",
        ge=0.0,
        le=1.0,
        description="Fraction of positions where top-3 moves unchanged after recalibration",
    )
    top1_flip_rate: float = Field(
        ...,
        alias="top1FlipRate",
        ge=0.0,
        le=1.0,
        description="Fraction of positions where top-1 move changed (1 - top1Stability)",
    )


class BucketDeltaV1(BaseModel):
    """Delta metrics for a single bucket (Elo or time pressure).

    Contains the bucket identifier, sample count, and delta metrics.
    """

    model_config = ConfigDict(populate_by_name=True)

    bucket_id: str = Field(
        ...,
        alias="bucketId",
        description="Bucket identifier (Elo bucket or time pressure bucket)",
    )
    samples: int = Field(
        ...,
        ge=0,
        description="Number of samples in this bucket",
    )
    metrics: MetricsDeltaV1 = Field(
        ...,
        description="Delta metrics for this bucket",
    )


class RuntimeRecalibrationDeltaV1(BaseModel):
    """Per-bucket delta artifact showing impact of runtime recalibration (M27).

    Contains calibration metric deltas plus policy-specific stability metrics,
    stratified by Elo bucket and optionally by time pressure bucket.

    See docs/milestones/PhaseD/M27/M27_plan.md for the governing plan.
    """

    model_config = ConfigDict(populate_by_name=True)

    version: Literal["1.0"] = Field(
        "1.0",
        description="Schema version identifier",
    )
    generated_at: datetime = Field(
        ...,
        alias="generatedAt",
        description="ISO 8601 timestamp of delta generation",
    )
    source_report_hash: str = Field(
        ...,
        alias="sourceReportHash",
        pattern=r"^sha256:[a-f0-9]{64}$",
        description="SHA-256 hash of the RuntimeRecalibrationReportV1 artifact used",
    )
    by_elo_bucket: list[BucketDeltaV1] = Field(
        ...,
        alias="byEloBucket",
        description="Delta metrics per Elo bucket (always present)",
    )
    by_time_pressure_bucket: list[BucketDeltaV1] | None = Field(
        None,
        alias="byTimePressureBucket",
        description="Delta metrics per time pressure bucket (null if not present in dataset)",
    )
    overall: MetricsDeltaV1 = Field(
        ...,
        description="Overall delta metrics aggregated across all buckets",
    )
    determinism_hash: str = Field(
        ...,
        alias="determinismHash",
        pattern=r"^sha256:[a-f0-9]{64}$",
        description="SHA-256 hash for determinism verification",
    )


# =============================================================================
# M28 — Runtime Recalibration Decision Models
# =============================================================================


class BucketActivationOverrideV1(BaseModel):
    """Per-bucket activation override for recalibration policy.

    Allows enabling or disabling recalibration for specific Elo buckets,
    overriding the policy's defaultEnabled setting.
    """

    model_config = ConfigDict(populate_by_name=True)

    bucket_id: str = Field(
        ...,
        alias="bucketId",
        description="Elo bucket identifier (M06 canonical buckets)",
    )
    enabled: bool = Field(
        ...,
        description="Whether recalibration is enabled for this bucket",
    )
    scope: Literal["outcome", "policy", "both"] | None = Field(
        None,
        description="Per-bucket scope override (null = use policy default)",
    )
    reason: str | None = Field(
        None,
        description="Optional justification for this override",
    )


class RuntimeRecalibrationActivationPolicyV1(BaseModel):
    """Declarative activation policy for runtime recalibration (M28).

    Defines per-bucket activation rules. Default is conservative: all buckets
    disabled. This policy, combined with RecalibrationGateV1, determines
    whether recalibration is applied at runtime.

    See docs/milestones/PhaseD/M28/M28_plan.md for the governing plan.
    """

    model_config = ConfigDict(populate_by_name=True)

    version: Literal["1.0"] = Field(
        "1.0",
        description="Schema version identifier",
    )
    default_enabled: bool = Field(
        ...,
        alias="defaultEnabled",
        description="Default activation state for all buckets (false = conservative default)",
    )
    scope: Literal["outcome", "policy", "both"] = Field(
        "both",
        description="Which heads to apply recalibration to when enabled",
    )
    bucket_overrides: list[BucketActivationOverrideV1] = Field(
        ...,
        alias="bucketOverrides",
        description="Per-bucket overrides of the default activation state",
    )
    created_at: datetime | None = Field(
        None,
        alias="createdAt",
        description="ISO 8601 timestamp of policy creation",
    )
    notes: str | None = Field(
        None,
        description="Optional notes about this policy (for audit/debugging)",
    )


class ValidationCheckV1(BaseModel):
    """Individual validation check result.

    Records the outcome of a single validation check performed during
    policy-to-evidence validation.
    """

    model_config = ConfigDict(populate_by_name=True)

    check_name: str = Field(
        ...,
        alias="checkName",
        description="Name of the validation check",
    )
    passed: bool = Field(
        ...,
        description="Whether the check passed",
    )
    details: str | None = Field(
        None,
        description="Additional details about the check result",
    )


class ValidationResultV1(BaseModel):
    """Result of validating policy against evidence.

    Contains the overall validation status and individual check results.
    """

    model_config = ConfigDict(populate_by_name=True)

    valid: bool = Field(
        ...,
        description="Whether the policy is valid against evidence",
    )
    checks: list[ValidationCheckV1] = Field(
        ...,
        description="Individual validation checks performed",
    )
    errors: list[str] | None = Field(
        None,
        description="Validation errors (if any)",
    )


class BucketDecisionV1(BaseModel):
    """Per-bucket decision details.

    Records the activation decision for a single Elo bucket, including
    the scope and evidence summary.
    """

    model_config = ConfigDict(populate_by_name=True)

    bucket_id: str = Field(
        ...,
        alias="bucketId",
        description="Elo bucket identifier",
    )
    enabled: bool = Field(
        ...,
        description="Whether recalibration is enabled for this bucket",
    )
    scope: Literal["outcome", "policy", "both", "none"] = Field(
        ...,
        description="Which heads have recalibration enabled (none if disabled)",
    )
    evidence_summary: str | None = Field(
        None,
        alias="evidenceSummary",
        description="Summary of M27 evidence for this bucket",
    )
    policy_reason: str | None = Field(
        None,
        alias="policyReason",
        description="Reason from policy (if override specified)",
    )


class RuntimeRecalibrationDecisionV1(BaseModel):
    """Human-readable decision record for runtime recalibration activation (M28).

    Links a RuntimeRecalibrationActivationPolicyV1 to M27 evidence. This artifact
    is the authoritative record of why recalibration is or is not activated.

    See docs/milestones/PhaseD/M28/M28_plan.md for the governing plan.
    """

    model_config = ConfigDict(populate_by_name=True)

    version: Literal["1.0"] = Field(
        "1.0",
        description="Schema version identifier",
    )
    generated_at: datetime = Field(
        ...,
        alias="generatedAt",
        description="ISO 8601 timestamp of decision generation",
    )
    decision_outcome: Literal["rejected", "restricted", "activated"] = Field(
        ...,
        alias="decisionOutcome",
        description="Overall decision outcome: rejected, restricted, or activated",
    )
    source_report_hash: str = Field(
        ...,
        alias="sourceReportHash",
        pattern=r"^sha256:[a-f0-9]{64}$",
        description="SHA-256 hash of the RuntimeRecalibrationReportV1 artifact",
    )
    source_delta_hash: str = Field(
        ...,
        alias="sourceDeltaHash",
        pattern=r"^sha256:[a-f0-9]{64}$",
        description="SHA-256 hash of the RuntimeRecalibrationDeltaV1 artifact",
    )
    policy_hash: str = Field(
        ...,
        alias="policyHash",
        pattern=r"^sha256:[a-f0-9]{64}$",
        description="SHA-256 hash of the RuntimeRecalibrationActivationPolicyV1 artifact",
    )
    activated_bucket_count: int = Field(
        ...,
        alias="activatedBucketCount",
        ge=0,
        description="Number of Elo buckets with recalibration enabled",
    )
    total_bucket_count: int = Field(
        ...,
        alias="totalBucketCount",
        ge=0,
        description="Total number of Elo buckets evaluated",
    )
    bucket_decisions: list[BucketDecisionV1] = Field(
        ...,
        alias="bucketDecisions",
        description="Per-bucket decision details",
    )
    validation_result: ValidationResultV1 = Field(
        ...,
        alias="validationResult",
        description="Result of validating policy against evidence",
    )
    human_summary: str = Field(
        ...,
        alias="humanSummary",
        description="Human-readable summary of the decision",
    )
    determinism_hash: str = Field(
        ...,
        alias="determinismHash",
        pattern=r"^sha256:[a-f0-9]{64}$",
        description="SHA-256 hash for determinism verification of entire decision",
    )


# =============================================================================
# M29: GPU Training Benchmark Models (Phase E)
# =============================================================================


class EnvironmentMetadataV1(BaseModel):
    """Hardware and software environment metadata for GPU training benchmarks.

    Captures all relevant details about the execution environment to ensure
    reproducibility and enable cross-hardware comparison.

    See docs/milestones/PhaseE/M29/M29_plan.md for the governing specification.
    """

    model_config = ConfigDict(populate_by_name=True)

    gpu_name: str = Field(
        ...,
        alias="gpuName",
        description="GPU device name (e.g., 'NVIDIA GeForce RTX 5090')",
    )
    vram_gb: float = Field(
        ...,
        alias="vramGb",
        ge=0,
        description="Total VRAM in gigabytes",
    )
    cuda_version: str = Field(
        ...,
        alias="cudaVersion",
        description="CUDA runtime version",
    )
    driver_version: str | None = Field(
        None,
        alias="driverVersion",
        description="GPU driver version (optional)",
    )
    torch_version: str = Field(
        ...,
        alias="torchVersion",
        description="PyTorch version",
    )
    python_version: str = Field(
        ...,
        alias="pythonVersion",
        description="Python version",
    )
    os: str = Field(
        ...,
        description="Operating system (e.g., 'Windows 10', 'Ubuntu 22.04')",
    )
    cpu_name: str | None = Field(
        None,
        alias="cpuName",
        description="CPU model name (optional)",
    )
    cpu_cores: int | None = Field(
        None,
        alias="cpuCores",
        ge=1,
        description="Number of CPU cores/threads available",
    )
    ram_gb: float | None = Field(
        None,
        alias="ramGb",
        ge=0,
        description="Total system RAM in gigabytes (optional)",
    )


class DatasetInfoV1(BaseModel):
    """Dataset manifest and shard information for benchmark context.

    Records provenance information about the dataset used for benchmarking.
    """

    model_config = ConfigDict(populate_by_name=True)

    manifest_hash: str = Field(
        ...,
        alias="manifestHash",
        description="SHA-256 hash of dataset manifest",
    )
    manifest_path: str | None = Field(
        None,
        alias="manifestPath",
        description="Path to dataset manifest (informational)",
    )
    frozen_eval_manifest_hash: str = Field(
        ...,
        alias="frozenEvalManifestHash",
        description="SHA-256 hash of frozen eval manifest",
    )
    overlap_check_passed: bool = Field(
        ...,
        alias="overlapCheckPassed",
        description="True if no overlap between training and frozen eval data",
    )
    total_positions_available: int | None = Field(
        None,
        alias="totalPositionsAvailable",
        ge=0,
        description="Total positions available in dataset",
    )


class BenchmarkMetricsV1(BaseModel):
    """Measured performance metrics for a single benchmark run.

    Captures throughput, timing breakdowns, and resource utilization.
    """

    model_config = ConfigDict(populate_by_name=True)

    steps_completed: int = Field(
        ...,
        alias="stepsCompleted",
        ge=0,
        description="Number of training steps completed",
    )
    samples_processed: int | None = Field(
        None,
        alias="samplesProcessed",
        ge=0,
        description="Total samples processed",
    )
    total_time_seconds: float = Field(
        ...,
        alias="totalTimeSeconds",
        ge=0,
        description="Total wall-clock time in seconds",
    )
    steps_per_second: float | None = Field(
        None,
        alias="stepsPerSecond",
        ge=0,
        description="Training steps per second",
    )
    samples_per_second: float | None = Field(
        None,
        alias="samplesPerSecond",
        ge=0,
        description="Samples processed per second",
    )
    step_time_mean_ms: float | None = Field(
        None,
        alias="stepTimeMeanMs",
        ge=0,
        description="Mean time per step in milliseconds",
    )
    step_time_p95_ms: float | None = Field(
        None,
        alias="stepTimeP95Ms",
        ge=0,
        description="95th percentile step time in milliseconds",
    )
    gpu_utilization_percent: float | None = Field(
        None,
        alias="gpuUtilizationPercent",
        ge=0,
        le=100,
        description="Average GPU utilization percentage (optional)",
    )
    vram_peak_gb: float | None = Field(
        None,
        alias="vramPeakGb",
        ge=0,
        description="Peak VRAM usage in gigabytes",
    )
    vram_peak_percent: float | None = Field(
        None,
        alias="vramPeakPercent",
        ge=0,
        le=100,
        description="Peak VRAM as percentage of total",
    )
    data_load_time_percent: float | None = Field(
        None,
        alias="dataLoadTimePercent",
        ge=0,
        le=100,
        description="Percentage of time spent in data loading",
    )
    forward_time_percent: float | None = Field(
        None,
        alias="forwardTimePercent",
        ge=0,
        le=100,
        description="Percentage of time spent in forward pass",
    )
    backward_time_percent: float | None = Field(
        None,
        alias="backwardTimePercent",
        ge=0,
        le=100,
        description="Percentage of time spent in backward pass",
    )
    optimizer_time_percent: float | None = Field(
        None,
        alias="optimizerTimePercent",
        ge=0,
        le=100,
        description="Percentage of time spent in optimizer step",
    )
    power_draw_watts: float | None = Field(
        None,
        alias="powerDrawWatts",
        ge=0,
        description="Average GPU power draw in watts (optional, nice-to-have)",
    )


class BenchmarkRunV1(BaseModel):
    """A single benchmark run with specific configuration.

    Each run varies one axis at a time to isolate performance characteristics.
    """

    model_config = ConfigDict(populate_by_name=True)

    run_id: str = Field(
        ...,
        alias="runId",
        description="Unique identifier for this run (e.g., 'batch64_samples1000_fp32_policy')",
    )
    batch_size: Literal[64, 128, 256, 512] = Field(
        ...,
        alias="batchSize",
        description="Training batch size",
    )
    sample_count: Literal[1000, 10000, 100000] = Field(
        ...,
        alias="sampleCount",
        description="Number of positions used (sanity=1K, medium=10K, large=100K)",
    )
    sample_count_label: Literal["sanity", "medium", "large"] = Field(
        ...,
        alias="sampleCountLabel",
        description="Human-readable shard size label",
    )
    precision_mode: Literal["fp32", "amp"] = Field(
        ...,
        alias="precisionMode",
        description="Training precision mode",
    )
    model_heads: Literal["policy", "policy+outcome"] = Field(
        ...,
        alias="modelHeads",
        description="Which model heads were trained",
    )
    metrics: BenchmarkMetricsV1 = Field(
        ...,
        description="Measured performance metrics",
    )
    status: Literal["success", "oom", "error", "skipped"] = Field(
        "success",
        description="Run completion status",
    )
    error_message: str | None = Field(
        None,
        alias="errorMessage",
        description="Error message if status is not 'success'",
    )


class TimeToTrainAssumptionsV1(BaseModel):
    """Assumptions underlying a time-to-train estimate.

    These must be explicitly stated so the estimate can be validated.
    """

    model_config = ConfigDict(populate_by_name=True)

    target_dataset_size: int = Field(
        ...,
        alias="targetDatasetSize",
        gt=0,
        description="Target dataset size for full training (positions)",
    )
    target_epochs: int = Field(
        ...,
        alias="targetEpochs",
        gt=0,
        description="Target number of epochs",
    )
    batch_size: int = Field(
        ...,
        alias="batchSize",
        gt=0,
        description="Assumed batch size for estimate",
    )
    precision_mode: Literal["fp32", "amp"] = Field(
        ...,
        alias="precisionMode",
        description="Assumed precision mode",
    )


class TimeToTrainEstimateV1(BaseModel):
    """Derived time-to-train projection from benchmark runs.

    Explicitly labeled as heuristic, not a guarantee.
    """

    model_config = ConfigDict(populate_by_name=True)

    estimate_version: Literal["heuristic-v1"] = Field(
        "heuristic-v1",
        alias="estimateVersion",
        description="Version of estimation method (explicitly labeled as heuristic)",
    )
    assumptions: TimeToTrainAssumptionsV1 = Field(
        ...,
        description="Assumptions underlying the estimate",
    )
    projected_time_hours: float = Field(
        ...,
        alias="projectedTimeHours",
        ge=0,
        description="Projected wall-clock time for full training in hours",
    )
    projected_time_formatted: str = Field(
        ...,
        alias="projectedTimeFormatted",
        description="Human-readable time estimate (e.g., '2h 30m')",
    )
    confidence_level: Literal["low", "medium", "high"] = Field(
        ...,
        alias="confidenceLevel",
        description="Confidence in estimate based on measurement quality",
    )
    sensitivity_notes: list[str] = Field(
        default_factory=list,
        alias="sensitivityNotes",
        description="Notes about factors that could affect actual training time",
    )


class TrainingBenchmarkReportV1(BaseModel):
    """GPU training benchmark report for RenaceCHESS (M29).

    Captures hardware-specific training throughput to estimate time-to-train
    for full runs. This is a measurement-only artifact — it does not alter
    model architectures, hyperparameters, or CI pipelines.

    See docs/milestones/PhaseE/M29/M29_plan.md for the governing specification.
    """

    model_config = ConfigDict(populate_by_name=True)

    version: Literal["1.0"] = Field(
        "1.0",
        description="Schema version identifier",
    )
    generated_at: datetime = Field(
        ...,
        alias="generatedAt",
        description="ISO 8601 timestamp when report was generated",
    )
    environment: EnvironmentMetadataV1 = Field(
        ...,
        description="Hardware and software environment metadata",
    )
    dataset_info: DatasetInfoV1 | None = Field(
        None,
        alias="datasetInfo",
        description="Dataset manifest and shard information",
    )
    run_matrix: list[BenchmarkRunV1] = Field(
        ...,
        alias="runMatrix",
        min_length=1,
        description="Array of benchmark runs with varying configurations",
    )
    time_to_train_estimate: TimeToTrainEstimateV1 | None = Field(
        None,
        alias="timeToTrainEstimate",
        description="Derived time-to-train projections (optional, computed from runs)",
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Non-fatal warnings encountered during benchmarking",
    )
    determinism_hash: str = Field(
        ...,
        alias="determinismHash",
        pattern=r"^sha256:[a-f0-9]{64}$",
        description="SHA-256 hash of canonical report content for reproducibility verification",
    )
