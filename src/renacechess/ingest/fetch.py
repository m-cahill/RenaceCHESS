"""Fetchers for downloading/copying artifacts."""

import hashlib
from pathlib import Path
from urllib.parse import urlparse

import requests  # type: ignore[import-untyped]

from renacechess.determinism import stable_hash
from renacechess.ingest.cache import CacheManager
from renacechess.ingest.types import FetchResult


class FileFetcher:
    """Fetcher for local files and file:// URIs."""

    def __init__(self, cache: CacheManager) -> None:
        """Initialize file fetcher.

        Args:
            cache: Cache manager instance.
        """
        self.cache = cache

    def fetch(self, uri: str, source_id: str, filename: str) -> FetchResult:
        """Fetch file from local path or file:// URI.

        Args:
            uri: File path or file:// URI.
            source_id: Source identifier for cache organization.
            filename: Target filename in cache.

        Returns:
            FetchResult with path, sha256, and size.

        Raises:
            FileNotFoundError: If source file doesn't exist.
            ValueError: If URI scheme is not file:// or not a local path.
        """
        # Parse URI
        parsed = urlparse(uri)
        if parsed.scheme == "file":
            # Handle Windows paths: file:///C:/path or file:///path
            path_str = parsed.path
            # Remove leading slash for Windows absolute paths
            if path_str.startswith("/") and len(path_str) > 1 and path_str[1].isalpha():
                # Windows drive letter: /C:/path -> C:/path
                path_str = path_str[1:]
            source_path = Path(path_str)
        elif parsed.scheme == "" or (len(parsed.scheme) == 1 and parsed.scheme.isalpha()):
            # No scheme, or Windows drive letter (C:, D:, etc.) - treat as local path
            source_path = Path(uri)
        else:
            raise ValueError(f"FileFetcher only supports file:// URIs or local paths, got {uri}")

        if not source_path.exists():
            raise FileNotFoundError(f"Source file not found: {source_path}")

        # Compute hash and size
        file_bytes = source_path.read_bytes()
        sha256 = stable_hash(file_bytes)
        size_bytes = len(file_bytes)

        # Copy to cache (atomic write)
        cache_dir = self.cache.get_source_dir(source_id)
        cache_path = cache_dir / filename
        self.cache.atomic_write(cache_path, file_bytes)

        return FetchResult(
            path=str(cache_path),
            sha256=sha256,
            size_bytes=size_bytes,
        )


class HttpFetcher:
    """Fetcher for HTTP/HTTPS URLs with streaming download."""

    def __init__(self, cache: CacheManager) -> None:
        """Initialize HTTP fetcher.

        Args:
            cache: Cache manager instance.
        """
        self.cache = cache

    def fetch(
        self,
        url: str,
        source_id: str,
        filename: str,
        timeout: int = 300,
    ) -> FetchResult:
        """Fetch file from HTTP/HTTPS URL with streaming.

        Args:
            url: HTTP/HTTPS URL.
            source_id: Source identifier for cache organization.
            filename: Target filename in cache.
            timeout: Request timeout in seconds.

        Returns:
            FetchResult with path, sha256, size, and optional metadata.

        Raises:
            requests.RequestException: If download fails.
            ValueError: If URL scheme is not http:// or https://.
        """
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            raise ValueError(f"HttpFetcher only supports http:// or https:// URLs, got {url}")

        # Stream download to temp file, computing hash while streaming
        cache_dir = self.cache.get_source_dir(source_id)
        temp_path = cache_dir / f"{filename}.tmp"
        cache_dir.mkdir(parents=True, exist_ok=True)

        hasher = hashlib.sha256()
        size_bytes = 0
        etag: str | None = None
        last_modified: str | None = None
        content_length: int | None = None

        try:
            with requests.get(url, stream=True, timeout=timeout) as response:
                response.raise_for_status()

                # Capture metadata
                etag = response.headers.get("ETag")
                last_modified = response.headers.get("Last-Modified")
                content_length_header = response.headers.get("Content-Length")
                if content_length_header:
                    try:
                        content_length = int(content_length_header)
                    except ValueError:
                        pass

                # Stream to temp file and compute hash
                with temp_path.open("wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            hasher.update(chunk)
                            size_bytes += len(chunk)

            sha256 = hasher.hexdigest()

            # Atomic rename
            cache_path = cache_dir / filename
            temp_path.replace(cache_path)

            return FetchResult(
                path=str(cache_path),
                sha256=sha256,
                size_bytes=size_bytes,
                etag=etag,
                last_modified=last_modified,
                content_length=content_length,
            )

        except Exception:
            # Clean up temp file on error
            if temp_path.exists():
                temp_path.unlink()
            raise
