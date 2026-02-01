"""M23 Performance Benchmark Tests.

These tests measure performance characteristics of critical paths.
Per M23 locked decisions:
- Required job in CI, no timing thresholds
- Benchmark results uploaded as artifacts
- Thresholds can be added in later milestone after variance is observed

Benchmarks focus on:
1. Structural cognition extraction (audit recommendation - Context Bridge v2 substrate)
2. Per-piece feature extraction
3. Square-map feature extraction
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import chess
import pytest

from renacechess.contracts.models import StructuralCognition
from renacechess.features.context_bridge_v2 import extract_structural_cognition
from renacechess.features.per_piece import extract_per_piece_features
from renacechess.features.square_map import extract_square_map_features

if TYPE_CHECKING:
    from pytest_benchmark.fixture import BenchmarkFixture


# Representative FEN positions for benchmarking
# Selected to cover different game phases and complexity levels
BENCHMARK_FENS = [
    # Starting position
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    # Italian Game (opening)
    "r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4",
    # Complex middlegame position
    "r1bq1rk1/ppp2ppp/2np1n2/2b1p3/2B1P3/2NP1N2/PPP2PPP/R1BQ1RK1 w - - 0 8",
    # Endgame position
    "8/5pk1/6p1/8/5P2/6P1/5K2/8 w - - 0 50",
    # Tactical position with lots of tension
    "r2qkb1r/ppp2ppp/2n1bn2/3pp3/2B1P3/2N2N2/PPPP1PPP/R1BQK2R w KQkq d6 0 6",
]


class TestStructuralCognitionBenchmarks:
    """Benchmark structural cognition extraction (primary audit recommendation)."""

    @pytest.mark.benchmark(group="structural_cognition")
    def test_structural_cognition_starting_position(
        self, benchmark: BenchmarkFixture
    ) -> None:
        """Benchmark structural cognition extraction for starting position."""
        board = chess.Board(BENCHMARK_FENS[0])

        def generate() -> StructuralCognition:
            return extract_structural_cognition(board)

        result = benchmark(generate)
        # Validate output structure (not timing)
        assert result is not None
        assert result.per_piece is not None
        assert result.square_map is not None

    @pytest.mark.benchmark(group="structural_cognition")
    def test_structural_cognition_complex_middlegame(
        self, benchmark: BenchmarkFixture
    ) -> None:
        """Benchmark structural cognition extraction for complex middlegame."""
        board = chess.Board(BENCHMARK_FENS[2])

        def generate() -> StructuralCognition:
            return extract_structural_cognition(board)

        result = benchmark(generate)
        assert result is not None

    @pytest.mark.benchmark(group="structural_cognition")
    def test_structural_cognition_endgame(self, benchmark: BenchmarkFixture) -> None:
        """Benchmark structural cognition extraction for endgame position."""
        board = chess.Board(BENCHMARK_FENS[3])

        def generate() -> StructuralCognition:
            return extract_structural_cognition(board)

        result = benchmark(generate)
        assert result is not None


class TestFeatureExtractionBenchmarks:
    """Benchmark structural feature extraction paths."""

    @pytest.mark.benchmark(group="features")
    def test_per_piece_features_starting_position(
        self, benchmark: BenchmarkFixture
    ) -> None:
        """Benchmark per-piece feature extraction for starting position."""
        board = chess.Board(BENCHMARK_FENS[0])

        def extract() -> Any:
            return extract_per_piece_features(board)

        result = benchmark(extract)
        assert result is not None
        assert hasattr(result, "pieces")
        assert len(result.pieces) == 32

    @pytest.mark.benchmark(group="features")
    def test_per_piece_features_complex_middlegame(
        self, benchmark: BenchmarkFixture
    ) -> None:
        """Benchmark per-piece feature extraction for complex middlegame."""
        board = chess.Board(BENCHMARK_FENS[2])

        def extract() -> Any:
            return extract_per_piece_features(board)

        result = benchmark(extract)
        assert result is not None

    @pytest.mark.benchmark(group="features")
    def test_square_map_features_starting_position(
        self, benchmark: BenchmarkFixture
    ) -> None:
        """Benchmark square map feature extraction for starting position."""
        board = chess.Board(BENCHMARK_FENS[0])

        def extract() -> Any:
            return extract_square_map_features(board)

        result = benchmark(extract)
        assert result is not None
        assert hasattr(result, "weak_for_white")
        assert hasattr(result, "weak_for_black")

    @pytest.mark.benchmark(group="features")
    def test_square_map_features_tactical_position(
        self, benchmark: BenchmarkFixture
    ) -> None:
        """Benchmark square map feature extraction for tactical position."""
        board = chess.Board(BENCHMARK_FENS[4])

        def extract() -> Any:
            return extract_square_map_features(board)

        result = benchmark(extract)
        assert result is not None


class TestCombinedBenchmarks:
    """Benchmark combined operation paths (realistic usage patterns)."""

    @pytest.mark.benchmark(group="combined")
    def test_full_analysis_pipeline(self, benchmark: BenchmarkFixture) -> None:
        """Benchmark full analysis pipeline: all features for a single position."""
        board = chess.Board(BENCHMARK_FENS[2])  # Complex middlegame

        def analyze() -> tuple:
            cognition = extract_structural_cognition(board)
            pieces = extract_per_piece_features(board)
            squares = extract_square_map_features(board)
            return cognition, pieces, squares

        result = benchmark(analyze)
        assert result is not None
        assert len(result) == 3

    @pytest.mark.benchmark(group="combined")
    def test_multi_position_batch(self, benchmark: BenchmarkFixture) -> None:
        """Benchmark processing multiple positions (batch simulation)."""
        boards = [chess.Board(fen) for fen in BENCHMARK_FENS]

        def process_batch() -> list:
            results = []
            for board in boards:
                cognition = extract_structural_cognition(board)
                results.append(cognition)
            return results

        result = benchmark(process_batch)
        assert len(result) == len(BENCHMARK_FENS)

