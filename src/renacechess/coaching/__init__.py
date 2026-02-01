"""Coaching module for RenaceCHESS (Phase C).

This module provides grounded, facts-only artifacts for LLM coaching translation.
See ADR-COACHING-001 for the governing principle: "LLMs translate facts, not invent."
"""

from renacechess.coaching.advice_facts import build_advice_facts_v1
from renacechess.coaching.elo_bucket_deltas import build_elo_bucket_delta_facts_v1

__all__ = ["build_advice_facts_v1", "build_elo_bucket_delta_facts_v1"]
