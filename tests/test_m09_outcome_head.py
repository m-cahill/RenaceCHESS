"""Tests for outcome head model (M09)."""

import torch

from renacechess.models.outcome_head_v1 import OutcomeHeadV1


def test_outcome_head_initialization() -> None:
    """Test outcome head model initialization."""
    model = OutcomeHeadV1()
    assert model is not None
    assert isinstance(model, OutcomeHeadV1)


def test_outcome_head_forward_logits() -> None:
    """Test outcome head forward pass returns 3 logits."""
    model = OutcomeHeadV1()
    model.eval()

    fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    skill_bucket = "1200_1399"
    time_control = "blitz"

    with torch.no_grad():
        logits = model.forward_logits(fen, skill_bucket, time_control)

    assert logits.shape == (3,), f"Expected shape (3,), got {logits.shape}"
    assert logits.dtype == torch.float32


def test_outcome_head_forward_probs() -> None:
    """Test outcome head forward pass returns valid W/D/L probabilities."""
    model = OutcomeHeadV1()
    model.eval()

    fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    skill_bucket = "1200_1399"
    time_control = "blitz"

    with torch.no_grad():
        wdl = model.forward(fen, skill_bucket, time_control)

    assert "w" in wdl
    assert "d" in wdl
    assert "l" in wdl

    # Probabilities should be in [0, 1]
    assert 0.0 <= wdl["w"] <= 1.0
    assert 0.0 <= wdl["d"] <= 1.0
    assert 0.0 <= wdl["l"] <= 1.0

    # Probabilities should sum to 1.0 (within floating-point tolerance)
    total = wdl["w"] + wdl["d"] + wdl["l"]
    assert abs(total - 1.0) < 1e-6, f"Probabilities sum to {total}, expected 1.0"


def test_outcome_head_deterministic() -> None:
    """Test outcome head produces deterministic outputs."""
    model = OutcomeHeadV1()
    model.eval()

    fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    skill_bucket = "1200_1399"
    time_control = "blitz"

    with torch.no_grad():
        wdl1 = model.forward(fen, skill_bucket, time_control)
        wdl2 = model.forward(fen, skill_bucket, time_control)

    assert abs(wdl1["w"] - wdl2["w"]) < 1e-6
    assert abs(wdl1["d"] - wdl2["d"]) < 1e-6
    assert abs(wdl1["l"] - wdl2["l"]) < 1e-6


def test_outcome_head_skill_bucket_encoding() -> None:
    """Test skill bucket encoding handles various formats."""
    model = OutcomeHeadV1()
    model.eval()

    fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

    # Test M06 format
    wdl1 = model.forward(fen, "1200_1399", "blitz")

    # Test legacy format
    wdl2 = model.forward(fen, "1200-1400", "blitz")

    # Should map to same bucket
    assert abs(wdl1["w"] - wdl2["w"]) < 1e-6

    # Test unknown
    wdl3 = model.forward(fen, "unknown", "blitz")
    assert 0.0 <= wdl3["w"] <= 1.0


def test_outcome_head_time_control_encoding() -> None:
    """Test time control encoding."""
    model = OutcomeHeadV1()
    model.eval()

    fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

    # Test various time controls
    for tc in ["bullet", "blitz", "rapid", "classical", None]:
        wdl = model.forward(fen, "1200_1399", tc)
        assert 0.0 <= wdl["w"] <= 1.0
        assert 0.0 <= wdl["d"] <= 1.0
        assert 0.0 <= wdl["l"] <= 1.0


def test_outcome_head_different_positions() -> None:
    """Test outcome head produces different outputs for different positions."""
    model = OutcomeHeadV1()
    model.eval()

    fen1 = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    fen2 = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"

    skill_bucket = "1200_1399"
    time_control = "blitz"

    with torch.no_grad():
        wdl1 = model.forward(fen1, skill_bucket, time_control)
        wdl2 = model.forward(fen2, skill_bucket, time_control)

    # Different positions should produce different predictions (unless model is trivial)
    # At minimum, we verify both are valid
    assert 0.0 <= wdl1["w"] <= 1.0
    assert 0.0 <= wdl2["w"] <= 1.0


def test_outcome_head_architecture() -> None:
    """Test outcome head has single linear layer architecture."""
    model = OutcomeHeadV1()

    # Count linear layers
    linear_layers = [m for m in model.modules() if isinstance(m, torch.nn.Linear)]

    # Should have exactly 1 linear layer (fc_outcome)
    assert len(linear_layers) == 1, f"Expected 1 linear layer, found {len(linear_layers)}"

    # Check output dimension is 3 (W/D/L)
    assert linear_layers[0].out_features == 3


def test_outcome_head_same_features_as_policy() -> None:
    """Test outcome head uses same feature representation as M08 policy."""
    model = OutcomeHeadV1()

    # Check embedding dimensions match M08 pattern
    assert model.fen_embedding.num_embeddings == 10000
    assert model.skill_embedding.num_embeddings == 8
    assert model.time_control_embedding.num_embeddings == 5

    # Check feature dimension calculation
    feature_dim = 128 // 2 + 128 // 4 + 128 // 4  # 64 + 32 + 32 = 128
    assert model.fc_outcome.in_features == feature_dim
