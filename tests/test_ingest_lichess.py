"""Tests for Lichess URL builder."""

import pytest

from renacechess.ingest.lichess import build_lichess_url


def test_build_lichess_url_valid() -> None:
    """Test building valid Lichess URLs."""
    url = build_lichess_url("standard_rated", "2024-01")
    assert url == "https://database.lichess.org/standard/lichess_db_standard_rated_2024-01.pgn.zst"

    url2 = build_lichess_url("standard_rated", "2023-12")
    assert url2 == "https://database.lichess.org/standard/lichess_db_standard_rated_2023-12.pgn.zst"


def test_build_lichess_url_invalid_month_format() -> None:
    """Test that invalid month formats raise errors."""
    with pytest.raises(ValueError, match="Month must be in YYYY-MM format"):
        build_lichess_url("standard_rated", "2024-1")

    with pytest.raises(ValueError, match="Month must be in YYYY-MM format"):
        build_lichess_url("standard_rated", "24-01")

    with pytest.raises(ValueError, match="Month must be in YYYY-MM format"):
        build_lichess_url("standard_rated", "2024/01")


def test_build_lichess_url_invalid_month_range() -> None:
    """Test that invalid month numbers raise errors."""
    with pytest.raises(ValueError, match="Month must be 01-12"):
        build_lichess_url("standard_rated", "2024-00")

    with pytest.raises(ValueError, match="Month must be 01-12"):
        build_lichess_url("standard_rated", "2024-13")

    with pytest.raises(ValueError, match="Invalid month format"):
        build_lichess_url("standard_rated", "2024-xx")


def test_build_lichess_url_invalid_preset() -> None:
    """Test that invalid presets raise errors."""
    with pytest.raises(ValueError, match="Unsupported preset"):
        build_lichess_url("invalid_preset", "2024-01")  # type: ignore[arg-type]
