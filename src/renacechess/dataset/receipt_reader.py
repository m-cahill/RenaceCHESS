"""Utilities for reading PGN files from ingest receipts."""

import json
from pathlib import Path

from renacechess.contracts.models import IngestReceiptV1
from renacechess.determinism import stable_hash


def load_receipt_from_path(receipt_path: Path) -> IngestReceiptV1:
    """Load ingest receipt from file path.

    Args:
        receipt_path: Path to receipt JSON file.

    Returns:
        IngestReceiptV1 instance.

    Raises:
        FileNotFoundError: If receipt doesn't exist.
    """
    if not receipt_path.exists():
        raise FileNotFoundError(f"Receipt not found: {receipt_path}")

    receipt_dict = json.loads(receipt_path.read_text())
    return IngestReceiptV1.model_validate(receipt_dict)


def get_pgn_path_from_receipt(
    receipt_path: Path, cache_dir: Path | None = None
) -> tuple[Path, str]:
    """Get PGN file path from an ingest receipt.

    Args:
        receipt_path: Path to ingest receipt JSON file.
        cache_dir: Optional cache directory for resolving relative paths.
                  If None, uses receipt file's directory.

    Returns:
        Tuple of (pgn_path, digest) where:
        - pgn_path: Resolved path to PGN file
        - digest: SHA-256 hash of the artifact (from receipt)

    Raises:
        FileNotFoundError: If receipt doesn't exist.
        ValueError: If receipt points to compressed file without decompressed path.
    """
    receipt = load_receipt_from_path(receipt_path)

    # Prefer decompressed path if available
    if receipt.derived is not None:
        pgn_path_str = receipt.derived.decompressed_path
        digest = receipt.derived.decompressed_sha256
    else:
        pgn_path_str = receipt.artifact.cache_path
        digest = receipt.artifact.sha256

        # Check if pointing to compressed file
        if receipt.artifact.compression == "zstd" or (
            receipt.artifact.media_type == "application/zstd"
        ):
            raise ValueError(
                f"Receipt {receipt_path} points to compressed PGN (.zst). "
                "Re-run `renacechess ingest ... --decompress` and retry dataset build."
            )

    # Resolve path
    pgn_path = Path(pgn_path_str)

    if pgn_path.is_absolute():
        resolved_path = pgn_path
    else:
        # Resolve relative to cache_dir or receipt directory
        if cache_dir is not None:
            base_dir = cache_dir
        else:
            base_dir = receipt_path.parent

        resolved_path = (base_dir / pgn_path).resolve()

    if not resolved_path.exists():
        raise FileNotFoundError(
            f"PGN file not found: {resolved_path} (from receipt {receipt_path})"
        )

    return resolved_path, digest


def compute_pgn_digest(pgn_path: Path) -> str:
    """Compute SHA-256 digest of PGN file (normalized line endings).

    Args:
        pgn_path: Path to PGN file.

    Returns:
        SHA-256 hash (lowercase hex) of file content with normalized line endings.
    """
    # Read file content and normalize line endings to \n
    content = pgn_path.read_bytes()
    # Normalize line endings: \r\n -> \n, standalone \r -> \n
    normalized = content.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return stable_hash(normalized)
