"""Lichess URL builder and preset metadata."""

from renacechess.ingest.types import LichessPreset


def build_lichess_url(preset: LichessPreset, month: str) -> str:
    """Build Lichess database export URL.

    Args:
        preset: Lichess preset (currently only "standard_rated").
        month: Month in YYYY-MM format.

    Returns:
        Full URL to Lichess database export.

    Raises:
        ValueError: If preset is invalid or month format is incorrect.
    """
    if preset != "standard_rated":
        raise ValueError(f"Unsupported preset: {preset}")

    # Validate month format (YYYY-MM)
    parts = month.split("-")
    if len(parts) != 2 or len(parts[0]) != 4 or len(parts[1]) != 2:
        raise ValueError(f"Month must be in YYYY-MM format, got {month}")

    try:
        int(parts[0])  # Validate year is numeric
        month_num = int(parts[1])
        if not (1 <= month_num <= 12):
            raise ValueError(f"Month must be 01-12, got {month_num:02d}")
    except ValueError as e:
        # Re-raise if it's our custom error, otherwise wrap
        if "Month must be 01-12" in str(e):
            raise
        raise ValueError(f"Invalid month format: {month}") from e

    # Build URL: https://database.lichess.org/standard/lichess_db_standard_rated_YYYY-MM.pgn.zst
    filename = f"lichess_db_standard_rated_{month}.pgn.zst"
    return f"https://database.lichess.org/standard/{filename}"
