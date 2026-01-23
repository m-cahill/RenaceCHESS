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
