"""Targeted tests for fetch.py to raise coverage."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import requests

from renacechess.ingest.cache import CacheManager
from renacechess.ingest.fetch import HttpFetcher


def test_http_fetcher_success(tmp_path: Path) -> None:
    """Test HttpFetcher successful fetch."""
    cache = CacheManager(tmp_path / "cache")

    # Mock requests.get to return a context manager
    mock_response = Mock()
    mock_response.headers = {
        "ETag": '"test-etag"',
        "Last-Modified": "Mon, 01 Jan 2024 12:00:00 GMT",
        "Content-Length": "10",
    }
    mock_response.iter_content.return_value = [b"test", b"data"]
    mock_response.url = "https://example.com/file.pgn"
    mock_response.__enter__ = Mock(return_value=mock_response)
    mock_response.__exit__ = Mock(return_value=None)

    mock_get = Mock(return_value=mock_response)

    with patch("renacechess.ingest.fetch.requests.get", mock_get):
        fetcher = HttpFetcher(cache)
        result = fetcher.fetch("https://example.com/file.pgn", "test_id", "file.pgn")

        assert result.path is not None
        assert result.etag == '"test-etag"'
        assert result.last_modified == "Mon, 01 Jan 2024 12:00:00 GMT"
        assert result.content_length == 10
        assert result.sha256 is not None
        assert result.size_bytes == 8  # len(b"test") + len(b"data")
        # Verify file was created
        assert Path(result.path).exists()


def test_http_fetcher_no_headers(tmp_path: Path) -> None:
    """Test HttpFetcher with missing headers."""
    cache = CacheManager(tmp_path / "cache")

    # Mock requests.get with no headers
    mock_response = Mock()
    mock_response.headers = {}
    mock_response.iter_content.return_value = [b"test"]
    mock_response.url = "https://example.com/file.pgn"
    mock_response.__enter__ = Mock(return_value=mock_response)
    mock_response.__exit__ = Mock(return_value=None)

    mock_get = Mock(return_value=mock_response)

    with patch("renacechess.ingest.fetch.requests.get", mock_get):
        fetcher = HttpFetcher(cache)
        result = fetcher.fetch("https://example.com/file.pgn", "test_id", "file.pgn")

        assert result.etag is None
        assert result.last_modified is None
        assert result.content_length is None


def test_http_fetcher_http_error(tmp_path: Path) -> None:
    """Test HttpFetcher with HTTP error."""
    cache = CacheManager(tmp_path / "cache")

    # Mock requests.get to raise HTTPError
    mock_response = Mock()
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Not Found")
    mock_response.status_code = 404
    mock_response.__enter__ = Mock(return_value=mock_response)
    mock_response.__exit__ = Mock(return_value=None)

    mock_get = Mock(return_value=mock_response)

    with patch("renacechess.ingest.fetch.requests.get", mock_get):
        fetcher = HttpFetcher(cache)
        with pytest.raises(requests.exceptions.HTTPError):
            fetcher.fetch("https://example.com/file.pgn", "test_id", "file.pgn")


def test_http_fetcher_connection_error(tmp_path: Path) -> None:
    """Test HttpFetcher with connection error."""
    cache = CacheManager(tmp_path / "cache")

    # Mock requests.get to raise ConnectionError
    with patch(
        "renacechess.ingest.fetch.requests.get",
        side_effect=requests.exceptions.ConnectionError("Connection failed"),
    ):
        fetcher = HttpFetcher(cache)
        with pytest.raises(requests.exceptions.ConnectionError):
            fetcher.fetch("https://example.com/file.pgn", "test_id", "file.pgn")


def test_http_fetcher_redirect(tmp_path: Path) -> None:
    """Test HttpFetcher with redirect (resolved_uri differs from uri)."""
    cache = CacheManager(tmp_path / "cache")

    # Mock requests.get with redirect
    mock_response = Mock()
    mock_response.headers = {}
    mock_response.iter_content.return_value = [b"test"]
    mock_response.url = "https://redirected.example.com/file.pgn"  # Different from original
    mock_response.__enter__ = Mock(return_value=mock_response)
    mock_response.__exit__ = Mock(return_value=None)

    mock_get = Mock(return_value=mock_response)

    with patch("renacechess.ingest.fetch.requests.get", mock_get):
        fetcher = HttpFetcher(cache)
        result = fetcher.fetch("https://example.com/file.pgn", "test_id", "file.pgn")

        assert result.path is not None
        # The resolved_uri is stored in the receipt, not in FetchResult
        # FetchResult only has path, sha256, size_bytes, and metadata

