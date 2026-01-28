"""Conditioning bucket assignment functions for M06.

This module provides deterministic functions for assigning skill buckets,
time control classes, and time pressure buckets according to M06 specifications.
"""

from typing import Literal


# M06 Skill Bucket IDs (frozen)
SkillBucketId = Literal[
    "lt_800",
    "800_999",
    "1000_1199",
    "1200_1399",
    "1400_1599",
    "1600_1799",
    "gte_1800",
    "unknown",
]

# M06 Time Control Classes (frozen)
TimeControlClass = Literal["bullet", "blitz", "rapid", "classical", "unknown"]

# M06 Time Pressure Buckets (frozen)
TimePressureBucket = Literal["early", "normal", "low", "trouble", "unknown"]


def assign_skill_bucket(rating: int | None) -> SkillBucketId:
    """Assign skill bucket ID from player rating.

    Args:
        rating: Player rating (Lichess rating), or None if missing/invalid.

    Returns:
        Skill bucket ID according to M06 spec:
        - lt_800: rating < 800
        - 800_999: 800 <= rating <= 999
        - 1000_1199: 1000 <= rating <= 1199
        - 1200_1399: 1200 <= rating <= 1399
        - 1400_1599: 1400 <= rating <= 1599
        - 1600_1799: 1600 <= rating <= 1799
        - gte_1800: rating >= 1800
        - unknown: missing/invalid rating

    Note:
        Rating source priority (to be implemented in dataset builder):
        1. Mover's rating at move time (if available)
        2. Game player rating (if available)
        3. unknown (if neither available)
    """
    if rating is None:
        return "unknown"

    if rating < 800:
        return "lt_800"
    elif rating < 1000:
        return "800_999"
    elif rating < 1200:
        return "1000_1199"
    elif rating < 1400:
        return "1200_1399"
    elif rating < 1600:
        return "1400_1599"
    elif rating < 1800:
        return "1600_1799"
    else:
        return "gte_1800"


def parse_time_control(time_control_str: str | None) -> tuple[TimeControlClass, str | None]:
    """Parse time control string and assign time control class.

    Args:
        time_control_str: PGN TimeControl header value (e.g., "300+0", "180+2"),
                         or None if missing.

    Returns:
        Tuple of (time_control_class, time_control_raw):
        - time_control_class: One of "bullet", "blitz", "rapid", "classical", "unknown"
        - time_control_raw: Original header string if parseable, else None

    Rules:
        - Parse format: "base+inc" (e.g., "300+0", "180+2")
        - Compute: estimatedTotalSeconds = baseSeconds + 40 * incSeconds
        - Classify:
          - bullet: < 180 seconds
          - blitz: 180-479 seconds
          - rapid: 480-1499 seconds
          - classical: >= 1500 seconds
          - unknown: parse failure / missing
    """
    if time_control_str is None or not time_control_str.strip():
        return "unknown", None

    # Try to parse "base+inc" format
    try:
        parts = time_control_str.strip().split("+")
        if len(parts) != 2:
            return "unknown", time_control_str

        base_seconds = int(parts[0])
        inc_seconds = int(parts[1])

        # Compute estimated total seconds (40 moves assumed)
        estimated_total = base_seconds + 40 * inc_seconds

        # Classify
        if estimated_total < 180:
            return "bullet", time_control_str
        elif estimated_total < 480:
            return "blitz", time_control_str
        elif estimated_total < 1500:
            return "rapid", time_control_str
        else:
            return "classical", time_control_str

    except (ValueError, IndexError):
        # Parse failure
        return "unknown", time_control_str


def assign_time_pressure_bucket(remaining_seconds: float | None) -> TimePressureBucket:
    """Assign time pressure bucket from remaining clock time.

    Args:
        remaining_seconds: Remaining clock time in seconds, or None if unavailable.

    Returns:
        Time pressure bucket according to M06 spec:
        - trouble: <= 10 seconds
        - low: <= 30 seconds
        - normal: <= 120 seconds
        - early: > 120 seconds
        - unknown: if remaining_seconds is None

    Note:
        M06 decision: If dataset does not include per-move remaining time,
        timePressureBucket = "unknown" is acceptable for M06.
        This function implements the plumbing for future use.
    """
    if remaining_seconds is None:
        return "unknown"

    if remaining_seconds <= 10:
        return "trouble"
    elif remaining_seconds <= 30:
        return "low"
    elif remaining_seconds <= 120:
        return "normal"
    else:
        return "early"
