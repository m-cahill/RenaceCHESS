"""Tests for M06 conditioning bucket assignment functions."""

from renacechess.conditioning.buckets import (
    assign_skill_bucket,
    assign_time_pressure_bucket,
    parse_time_control,
)


class TestSkillBucketAssignment:
    """Test skill bucket assignment function."""

    def test_assign_skill_bucket_lt_800(self) -> None:
        """Test skill bucket assignment for rating < 800."""
        assert assign_skill_bucket(799) == "lt_800"
        assert assign_skill_bucket(500) == "lt_800"
        assert assign_skill_bucket(0) == "lt_800"

    def test_assign_skill_bucket_800_999(self) -> None:
        """Test skill bucket assignment for 800-999."""
        assert assign_skill_bucket(800) == "800_999"
        assert assign_skill_bucket(900) == "800_999"
        assert assign_skill_bucket(999) == "800_999"

    def test_assign_skill_bucket_1000_1199(self) -> None:
        """Test skill bucket assignment for 1000-1199."""
        assert assign_skill_bucket(1000) == "1000_1199"
        assert assign_skill_bucket(1100) == "1000_1199"
        assert assign_skill_bucket(1199) == "1000_1199"

    def test_assign_skill_bucket_1200_1399(self) -> None:
        """Test skill bucket assignment for 1200-1399."""
        assert assign_skill_bucket(1200) == "1200_1399"
        assert assign_skill_bucket(1300) == "1200_1399"
        assert assign_skill_bucket(1399) == "1200_1399"

    def test_assign_skill_bucket_1400_1599(self) -> None:
        """Test skill bucket assignment for 1400-1599."""
        assert assign_skill_bucket(1400) == "1400_1599"
        assert assign_skill_bucket(1500) == "1400_1599"
        assert assign_skill_bucket(1599) == "1400_1599"

    def test_assign_skill_bucket_1600_1799(self) -> None:
        """Test skill bucket assignment for 1600-1799."""
        assert assign_skill_bucket(1600) == "1600_1799"
        assert assign_skill_bucket(1700) == "1600_1799"
        assert assign_skill_bucket(1799) == "1600_1799"

    def test_assign_skill_bucket_gte_1800(self) -> None:
        """Test skill bucket assignment for rating >= 1800."""
        assert assign_skill_bucket(1800) == "gte_1800"
        assert assign_skill_bucket(2000) == "gte_1800"
        assert assign_skill_bucket(3000) == "gte_1800"

    def test_assign_skill_bucket_unknown(self) -> None:
        """Test skill bucket assignment for None rating."""
        assert assign_skill_bucket(None) == "unknown"


class TestTimeControlParsing:
    """Test time control parsing and classification."""

    def test_parse_bullet_time_control(self) -> None:
        """Test bullet time control classification (< 180s)."""
        tc_class, tc_raw = parse_time_control("60+0")
        assert tc_class == "bullet"
        assert tc_raw == "60+0"

        tc_class, tc_raw = parse_time_control("120+1")
        assert tc_class == "bullet"  # 120 + 40 * 1 = 160s
        assert tc_raw == "120+1"

    def test_parse_blitz_time_control(self) -> None:
        """Test blitz time control classification (180-479s)."""
        tc_class, tc_raw = parse_time_control("180+0")
        assert tc_class == "blitz"
        assert tc_raw == "180+0"

        tc_class, tc_raw = parse_time_control("300+0")
        assert tc_class == "blitz"
        assert tc_raw == "300+0"

        tc_class, tc_raw = parse_time_control("180+2")
        assert tc_class == "blitz"  # 180 + 40*2 = 260s
        assert tc_raw == "180+2"

    def test_parse_rapid_time_control(self) -> None:
        """Test rapid time control classification (480-1499s)."""
        tc_class, tc_raw = parse_time_control("600+0")
        assert tc_class == "rapid"
        assert tc_raw == "600+0"

        tc_class, tc_raw = parse_time_control("900+10")
        assert tc_class == "rapid"  # 900 + 40*10 = 1300s
        assert tc_raw == "900+10"

    def test_parse_classical_time_control(self) -> None:
        """Test classical time control classification (>= 1500s)."""
        tc_class, tc_raw = parse_time_control("1800+0")
        assert tc_class == "classical"
        assert tc_raw == "1800+0"

        tc_class, tc_raw = parse_time_control("3600+30")
        assert tc_class == "classical"  # 3600 + 40*30 = 4800s
        assert tc_raw == "3600+30"

    def test_parse_time_control_none(self) -> None:
        """Test time control parsing for None input."""
        tc_class, tc_raw = parse_time_control(None)
        assert tc_class == "unknown"
        assert tc_raw is None

    def test_parse_time_control_empty(self) -> None:
        """Test time control parsing for empty string."""
        tc_class, tc_raw = parse_time_control("")
        assert tc_class == "unknown"
        assert tc_raw is None

    def test_parse_time_control_invalid_format(self) -> None:
        """Test time control parsing for invalid format."""
        tc_class, tc_raw = parse_time_control("invalid")
        assert tc_class == "unknown"
        assert tc_raw == "invalid"

        tc_class, tc_raw = parse_time_control("300")  # Missing increment
        assert tc_class == "unknown"
        assert tc_raw == "300"

    def test_parse_time_control_deterministic(self) -> None:
        """Test that time control parsing is deterministic."""
        tc1, raw1 = parse_time_control("300+5")
        tc2, raw2 = parse_time_control("300+5")
        assert tc1 == tc2
        assert raw1 == raw2


class TestTimePressureBucketAssignment:
    """Test time pressure bucket assignment function."""

    def test_assign_time_pressure_trouble(self) -> None:
        """Test time pressure bucket assignment for trouble (<= 10s)."""
        assert assign_time_pressure_bucket(10.0) == "trouble"
        assert assign_time_pressure_bucket(5.0) == "trouble"
        assert assign_time_pressure_bucket(0.5) == "trouble"

    def test_assign_time_pressure_low(self) -> None:
        """Test time pressure bucket assignment for low (<= 30s)."""
        assert assign_time_pressure_bucket(30.0) == "low"
        assert assign_time_pressure_bucket(20.0) == "low"
        assert assign_time_pressure_bucket(11.0) == "low"

    def test_assign_time_pressure_normal(self) -> None:
        """Test time pressure bucket assignment for normal (<= 120s)."""
        assert assign_time_pressure_bucket(120.0) == "normal"
        assert assign_time_pressure_bucket(60.0) == "normal"
        assert assign_time_pressure_bucket(31.0) == "normal"

    def test_assign_time_pressure_early(self) -> None:
        """Test time pressure bucket assignment for early (> 120s)."""
        assert assign_time_pressure_bucket(121.0) == "early"
        assert assign_time_pressure_bucket(300.0) == "early"
        assert assign_time_pressure_bucket(1000.0) == "early"

    def test_assign_time_pressure_unknown(self) -> None:
        """Test time pressure bucket assignment for None."""
        assert assign_time_pressure_bucket(None) == "unknown"
