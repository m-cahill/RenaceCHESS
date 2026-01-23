"""Zstandard decompression for .zst files."""

import hashlib
from pathlib import Path
from typing import Any

try:
    import zstandard as zstd  # type: ignore
except ImportError:
    zstd = None

from renacechess.ingest.cache import CacheManager


def decompress_zst(
    source_path: Path,
    cache: CacheManager,
    source_id: str,
    output_filename: str,
) -> tuple[str, str, int]:
    """Decompress .zst file to .pgn using streaming.

    Args:
        source_path: Path to compressed .zst file.
        cache: Cache manager instance.
        source_id: Source identifier for cache organization.
        output_filename: Target filename for decompressed output.

    Returns:
        Tuple of (output_path, sha256, size_bytes).

    Raises:
        FileNotFoundError: If source file doesn't exist.
        ValueError: If source file doesn't have .zst extension.
    """
    if not source_path.exists():
        raise FileNotFoundError(f"Source file not found: {source_path}")

    if not source_path.suffix == ".zst":
        raise ValueError(f"Source file must have .zst extension, got {source_path.suffix}")

    if zstd is None:
        raise ImportError(
            "zstandard library is required for decompression. Install with: pip install zstandard"
        )

    # Create output directory
    derived_dir = cache.get_derived_dir(source_id)
    derived_dir.mkdir(parents=True, exist_ok=True)
    output_path = derived_dir / output_filename

    # Stream decompress: read compressed, write decompressed, compute hash
    hasher = hashlib.sha256()
    size_bytes = 0

    dctx = zstd.ZstdDecompressor()
    temp_path = output_path.with_suffix(output_path.suffix + ".tmp")

    try:
        with source_path.open("rb") as input_file:
            with temp_path.open("wb") as output_file:
                with dctx.stream_reader(input_file) as reader:
                    while True:
                        chunk = reader.read(8192)
                        if not chunk:
                            break
                        output_file.write(chunk)
                        hasher.update(chunk)
                        size_bytes += len(chunk)

        sha256 = hasher.hexdigest()

        # Atomic rename
        temp_path.replace(output_path)

        return (str(output_path), sha256, size_bytes)

    except Exception:
        # Clean up temp file on error
        if temp_path.exists():
            temp_path.unlink()
        raise
