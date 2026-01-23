"""Type definitions for ingestion module."""

from dataclasses import dataclass
from typing import Literal

# Lichess preset types
LichessPreset = Literal["standard_rated"]
CompressionType = Literal["zstd"]


@dataclass
class SourceSpec:
    """Source specification for ingestion."""

    uri: str
    preset: LichessPreset | None = None
    month: str | None = None  # YYYY-MM format


@dataclass
class FetchResult:
    """Result of a fetch operation."""

    path: str  # Path to cached artifact
    sha256: str  # SHA-256 hash
    size_bytes: int  # Size in bytes
    etag: str | None = None
    last_modified: str | None = None  # ISO 8601 format
    content_length: int | None = None
