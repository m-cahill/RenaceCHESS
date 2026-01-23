"""Main ingestion orchestration logic."""

import shutil
import sys
from pathlib import Path
from urllib.parse import urlparse

from renacechess.contracts.models import DerivedArtifactRefV1
from renacechess.ingest.cache import CacheManager, compute_source_id
from renacechess.ingest.fetch import FileFetcher, HttpFetcher
from renacechess.ingest.lichess import build_lichess_url
from renacechess.ingest.receipt import create_receipt, load_receipt, save_receipt


def ingest_from_lichess(
    month: str,
    output_dir: Path,
    cache_dir: Path,
    decompress: bool = False,
) -> None:
    """Ingest Lichess monthly dump.

    Args:
        month: Month in YYYY-MM format.
        output_dir: Directory to copy receipt and artifacts.
        cache_dir: Cache directory.
        decompress: Whether to decompress .zst to .pgn.

    Raises:
        ValueError: If month format is invalid.
        FileNotFoundError: If cached artifact not found after fetch.
    """
    # Build URL
    url = build_lichess_url("standard_rated", month)

    # Determine source spec for source_id
    spec = {"preset": "standard_rated", "month": month}
    source_id = compute_source_id(spec)

    # Ingest from URL
    ingest_from_url(url, output_dir, cache_dir, decompress, source_id=source_id)


def ingest_from_url(
    url: str,
    output_dir: Path,
    cache_dir: Path,
    decompress: bool = False,
    source_id: str | None = None,
) -> None:
    """Ingest from explicit URL or file path.

    Args:
        url: HTTP/HTTPS URL or file:// URI or local path.
        output_dir: Directory to copy receipt and artifacts.
        cache_dir: Cache directory.
        decompress: Whether to decompress .zst to .pgn.
        source_id: Optional source ID (computed from URL if not provided).

    Raises:
        FileNotFoundError: If source file not found.
        ValueError: If URL scheme is unsupported.
    """
    # Initialize cache
    cache = CacheManager(cache_dir)

    # Compute source_id if not provided
    if source_id is None:
        parsed = urlparse(url)
        spec = {"url": url, "resolvedUri": None}
        source_id = compute_source_id(spec)

    # Check for existing receipt (cache hit)
    receipt_path = cache.get_receipt_path(source_id)
    if receipt_path.exists():
        receipt = load_receipt(cache, source_id)
        print(f"Cache hit: Using existing receipt {receipt_path}", file=sys.stderr)
    else:
        # Determine fetcher based on URL scheme
        parsed = urlparse(url)
        if parsed.scheme in ("http", "https"):
            fetcher: FileFetcher | HttpFetcher = HttpFetcher(cache)
        elif (
            parsed.scheme == "file"
            or parsed.scheme == ""
            or (len(parsed.scheme) == 1 and parsed.scheme.isalpha())
        ):
            fetcher = FileFetcher(cache)
        else:
            raise ValueError(f"Unsupported URL scheme: {parsed.scheme}")

        # Extract filename from URL
        filename = Path(parsed.path).name
        if not filename:
            filename = "artifact" + (".pgn.zst" if url.endswith(".zst") else ".pgn")

        # Fetch
        print(f"Fetching from {url}...", file=sys.stderr)
        fetch_result = fetcher.fetch(url, source_id, filename)

        # Determine media type and compression
        if filename.endswith(".zst"):
            media_type = "application/zstd"
            compression = "zstd"
        else:
            media_type = "application/x-chess-pgn"
            compression = None

        # Create receipt
        receipt = create_receipt(
            source_uri=url,
            fetch_result=fetch_result,
            cache=cache,
            source_id=source_id,
            media_type=media_type,
            compression=compression,
            resolved_uri=url,  # For file://, resolved is same as original
        )

        # Save receipt
        save_receipt(receipt, cache, source_id)

    # Handle decompression if requested
    derived = None
    if decompress and receipt.artifact.compression == "zstd":
        # Lazy import to avoid requiring zstandard at module import time
        from renacechess.ingest.decompress import decompress_zst

        artifact_path = cache.cache_dir / receipt.artifact.cache_path
        if not artifact_path.exists():
            # Try absolute path
            artifact_path = Path(receipt.artifact.cache_path)
            if not artifact_path.exists():
                raise FileNotFoundError(f"Artifact not found: {receipt.artifact.cache_path}")

        print(f"Decompressing {artifact_path}...", file=sys.stderr)
        output_filename = Path(artifact_path.stem).with_suffix(".pgn").name
        decompressed_path, decompressed_sha256, decompressed_size = decompress_zst(
            artifact_path, cache, source_id, output_filename
        )

        # Get relative path
        decompressed_path_obj = Path(decompressed_path)
        try:
            decompressed_path_rel = decompressed_path_obj.relative_to(cache.cache_dir)
        except ValueError:
            decompressed_path_rel = Path(decompressed_path)

        derived = DerivedArtifactRefV1(
            decompressed_path=str(decompressed_path_rel),
            decompressed_sha256=decompressed_sha256,
            decompressed_size_bytes=decompressed_size,
        )

        # Update receipt with derived artifact
        receipt.derived = derived
        save_receipt(receipt, cache, source_id)

    # Copy receipt to output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    output_receipt_path = output_dir / f"{source_id}.json"
    shutil.copy2(receipt_path, output_receipt_path)

    # Print summary
    print("\nIngestion complete:", file=sys.stderr)
    print(f"  Source: {receipt.source.uri}", file=sys.stderr)
    print(f"  Cached artifact: {receipt.artifact.cache_path}", file=sys.stderr)
    print(f"  SHA-256: {receipt.artifact.sha256}", file=sys.stderr)
    print(f"  Size: {receipt.artifact.size_bytes:,} bytes", file=sys.stderr)
    if derived:
        print(f"  Decompressed: {derived.decompressed_path}", file=sys.stderr)
        print(f"  Decompressed SHA-256: {derived.decompressed_sha256}", file=sys.stderr)
        print(f"  Decompressed size: {derived.decompressed_size_bytes:,} bytes", file=sys.stderr)
    print(f"  Receipt: {output_receipt_path}", file=sys.stderr)
