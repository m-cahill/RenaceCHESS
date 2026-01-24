"""Tests for baseline policy providers."""

from renacechess.eval.baselines import (
    FirstLegalPolicy,
    UniformRandomLegalPolicy,
    compute_policy_seed,
    create_policy_provider,
)


def test_first_legal_policy() -> None:
    """Test FirstLegalPolicy deterministic behavior."""
    policy = FirstLegalPolicy()

    record = {
        "position": {
            "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
            "sideToMove": "white",
            "legalMoves": ["a2a3", "a2a4", "b2b3", "b2b4"],
        }
    }

    moves = policy.predict(record)
    assert len(moves) == 1
    assert moves[0].uci == "a2a3"  # First sorted legal move
    assert moves[0].p == 1.0


def test_first_legal_policy_empty() -> None:
    """Test FirstLegalPolicy with empty legal moves."""
    policy = FirstLegalPolicy()

    record = {
        "position": {
            "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
            "sideToMove": "white",
            "legalMoves": [],
        }
    }

    moves = policy.predict(record)
    assert len(moves) == 0


def test_uniform_random_legal_policy() -> None:
    """Test UniformRandomLegalPolicy deterministic seeding."""
    policy1 = UniformRandomLegalPolicy(seed=42)
    policy2 = UniformRandomLegalPolicy(seed=42)

    record = {
        "position": {
            "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
            "sideToMove": "white",
            "legalMoves": ["a2a3", "a2a4", "b2b3", "b2b4"],
        }
    }

    moves1 = policy1.predict(record)
    moves2 = policy2.predict(record)

    # Same seed should produce same order
    assert [m.uci for m in moves1] == [m.uci for m in moves2]
    # All moves should have equal probability
    assert all(m.p == 0.25 for m in moves1)
    # All moves should be legal
    legal_moves_set = set(record["position"]["legalMoves"])
    assert all(m.uci in legal_moves_set for m in moves1)


def test_uniform_random_legal_policy_empty() -> None:
    """Test UniformRandomLegalPolicy with empty legal moves."""
    policy = UniformRandomLegalPolicy(seed=42)

    record = {
        "position": {
            "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
            "sideToMove": "white",
            "legalMoves": [],
        }
    }

    moves = policy.predict(record)
    assert len(moves) == 0


def test_create_policy_provider() -> None:
    """Test create_policy_provider factory function."""
    policy1 = create_policy_provider("baseline.first_legal")
    assert isinstance(policy1, FirstLegalPolicy)

    policy2 = create_policy_provider("baseline.uniform_random", seed=42)
    assert isinstance(policy2, UniformRandomLegalPolicy)
    assert policy2.seed == 42

    # Unknown policy should raise
    try:
        create_policy_provider("unknown.policy")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "Unknown policy ID" in str(e)


def test_compute_policy_seed() -> None:
    """Test compute_policy_seed deterministic behavior."""
    dataset_digest = "a" * 64
    policy_id = "baseline.uniform_random"
    eval_config_hash = "b" * 64

    seed1 = compute_policy_seed(dataset_digest, policy_id, eval_config_hash)
    seed2 = compute_policy_seed(dataset_digest, policy_id, eval_config_hash)

    # Same inputs should produce same seed
    assert seed1 == seed2

    # Different inputs should produce different seeds
    seed3 = compute_policy_seed("c" * 64, policy_id, eval_config_hash)
    assert seed1 != seed3
