"""Receipt creation and management."""

import json
import platform
import sys
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from pathlib import Path

from renacechess.contracts.models import (
    ArtifactRefV1,
    DerivedArtifactRefV1,
    IngestReceiptV1,
    ProvenanceV1,
    SourceArtifactRefV1,
)
from renacechess.contracts.validation import validate_with_aliases
from renacechess.ingest.cache import CacheManager
from renacechess.ingest.types import FetchResult


def create_receipt(
    source_uri: str,
    fetch_result: FetchResult,
    cache: CacheManager,
    source_id: str,
    media_type: str,
    compression: str | None = None,
    resolved_uri: str | None = None,
    created_at: datetime | None = None,
    derived: DerivedArtifactRefV1 | None = None,
) -> IngestReceiptV1:
    """Create an ingest receipt.

    Args:
        source_uri: Original source URI.
        fetch_result: Result from fetch operation.
        cache: Cache manager instance.
        source_id: Source identifier.
        media_type: MIME type of artifact.
        compression: Compression format if applicable.
        resolved_uri: Resolved URI after redirects (optional).
        created_at: Override creation timestamp (for testing).
        derived: Derived artifact reference (optional).

    Returns:
        IngestReceiptV1 instance.
    """
    if created_at is None:
        created_at = datetime.now(UTC)

    # Get relative path from cache root
    cache_path = Path(fetch_result.path)
    try:
        cache_path_rel = cache_path.relative_to(cache.cache_dir)
    except ValueError:
        # If not relative, use absolute path
        cache_path_rel = Path(cache_path)

    source = SourceArtifactRefV1(
        uri=source_uri,
        resolved_uri=resolved_uri,
        etag=fetch_result.etag,
        last_modified=(
            parsedate_to_datetime(fetch_result.last_modified)
            if fetch_result.last_modified
            else None
        ),
        content_length=fetch_result.content_length,
    )

    artifact = ArtifactRefV1(
        cache_path=str(cache_path_rel),
        sha256=fetch_result.sha256,
        size_bytes=fetch_result.size_bytes,
        media_type=media_type,
        compression=compression,
    )

    provenance = ProvenanceV1(
        tool_version=_get_tool_version(),
        platform=_get_platform(),
        python_version=_get_python_version(),
    )

    return IngestReceiptV1(
        schema_version="v1",
        created_at=created_at,
        source=source,
        artifact=artifact,
        derived=derived,
        provenance=provenance,
    )


def save_receipt(receipt: IngestReceiptV1, cache: CacheManager, source_id: str) -> Path:
    """Save receipt to cache.

    Args:
        receipt: Receipt to save.
        cache: Cache manager instance.
        source_id: Source identifier.

    Returns:
        Path to saved receipt file.
    """
    receipt_path = cache.get_receipt_path(source_id)
    receipt_dict = receipt.model_dump(mode="json", by_alias=True, exclude_none=True)
    cache.atomic_write_json(receipt_path, receipt_dict)
    return receipt_path


def load_receipt(cache: CacheManager, source_id: str) -> IngestReceiptV1:
    """Load receipt from cache.

    Args:
        cache: Cache manager instance.
        source_id: Source identifier.

    Returns:
        IngestReceiptV1 instance.

    Raises:
        FileNotFoundError: If receipt doesn't exist.
    """
    receipt_path = cache.get_receipt_path(source_id)
    if not receipt_path.exists():
        raise FileNotFoundError(f"Receipt not found: {receipt_path}")

    receipt_dict = json.loads(receipt_path.read_text())
    return validate_with_aliases(IngestReceiptV1, receipt_dict)


def _get_tool_version() -> str:
    """Get renacechess tool version."""
    from renacechess import __version__

    return __version__


def _get_platform() -> str:
    """Get platform identifier."""
    system = platform.system().lower()
    machine = platform.machine().lower()
    return f"{system}-{machine}"


def _get_python_version() -> str:
    """Get Python version."""
    return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
