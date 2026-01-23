"""Pydantic models for RenaceCHESS contracts."""

from datetime import datetime
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class Position(BaseModel):
    """Chess position representation."""

    fen: str = Field(..., description="FEN string representation of the position")
    sideToMove: Literal["white", "black"] = Field(..., description="Side to move")
    legalMoves: List[str] = Field(..., description="List of legal moves in UCI format")


class PositionConditioning(BaseModel):
    """Conditioning variables for position evaluation."""

    skillBucket: str = Field(..., description="Skill bucket identifier (e.g., '1200-1400')")
    timePressureBucket: Literal["NORMAL", "LOW", "TROUBLE"] = Field(
        ..., description="Time pressure bucket"
    )
    timeControlClass: Optional[Literal["blitz", "rapid", "classical"]] = Field(
        None, description="Time control class (optional)"
    )


class PolicyMove(BaseModel):
    """Single move in policy distribution."""

    uci: str = Field(..., description="Move in UCI format")
    san: Optional[str] = Field(None, description="Move in SAN format (optional)")
    p: float = Field(..., ge=0.0, le=1.0, description="Probability of this move")


class Policy(BaseModel):
    """Move policy distribution."""

    topMoves: List[PolicyMove] = Field(..., description="Top moves with probabilities")
    entropy: float = Field(..., ge=0.0, description="Policy entropy (Shannon entropy)")
    topGap: float = Field(..., ge=0.0, le=1.0, description="Gap between top move and second move")


class HumanWDL(BaseModel):
    """Human win/draw/loss probabilities."""

    w: float = Field(..., ge=0.0, le=1.0, description="Win probability")
    d: float = Field(..., ge=0.0, le=1.0, description="Draw probability")
    l: float = Field(..., ge=0.0, le=1.0, description="Loss probability")

    def model_post_init(self, __context: object) -> None:
        """Validate that probabilities sum to 1."""
        total = self.w + self.d + self.l
        if abs(total - 1.0) > 1e-6:
            raise ValueError(f"WDL probabilities must sum to 1.0, got {total}")


class HDIComponents(BaseModel):
    """Components of Human Difficulty Index."""

    entropy: float = Field(..., ge=0.0, description="Policy entropy component")
    topGap: float = Field(..., ge=0.0, le=1.0, description="Top gap component")
    wdlSensitivity: float = Field(..., ge=0.0, description="WDL sensitivity component")


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
    facts: List[str] = Field(..., description="Array of factual statements")


class ContextBridgeMeta(BaseModel):
    """Metadata for Context Bridge payload."""

    schemaVersion: Literal["v1"] = Field("v1", description="Schema version")
    generatedAt: datetime = Field(..., description="ISO 8601 timestamp of generation")
    inputHash: str = Field(..., description="Hash of input data (PGN + position)")


class HumanWDLContainer(BaseModel):
    """Container for pre-move and post-move WDL probabilities."""

    pre: HumanWDL = Field(..., description="WDL probabilities before move")
    postByMove: Dict[str, HumanWDL] = Field(
        ..., description="WDL probabilities after each candidate move (keyed by UCI)"
    )


class ContextBridgePayload(BaseModel):
    """LLM Context Bridge payload (v1)."""

    position: Position = Field(..., description="Chess position")
    conditioning: PositionConditioning = Field(..., description="Conditioning variables")
    policy: Policy = Field(..., description="Move policy distribution")
    humanWDL: HumanWDLContainer = Field(..., description="Human WDL probabilities")
    hdi: HDI = Field(..., description="Human Difficulty Index")
    narrativeSeeds: List[NarrativeSeed] = Field(..., description="Narrative seeds for LLM")
    meta: ContextBridgeMeta = Field(..., description="Metadata")


class DatasetManifestShardRef(BaseModel):
    """Reference to a dataset shard."""

    shardId: str = Field(..., description="Unique shard identifier")
    hash: str = Field(..., description="SHA-256 hash of shard file")
    path: str = Field(..., description="Relative or absolute path to shard file")


class DatasetManifestSplitAssignments(BaseModel):
    """Split assignments for dataset."""

    train: List[str] = Field(default_factory=list, description="Training split shard IDs")
    val: List[str] = Field(default_factory=list, description="Validation split shard IDs")
    frozenEval: List[str] = Field(default_factory=list, description="Frozen eval split shard IDs")


class DatasetManifest(BaseModel):
    """Dataset manifest (v1)."""

    schemaVersion: Literal["v1"] = Field("v1", description="Schema version")
    createdAt: datetime = Field(..., description="ISO 8601 timestamp of creation")
    shardRefs: List[DatasetManifestShardRef] = Field(
        default_factory=list, description="List of shard references"
    )
    filterConfigHash: str = Field(..., description="Hash of filter configuration")
    splitAssignments: DatasetManifestSplitAssignments = Field(
        ..., description="Split assignments"
    )

