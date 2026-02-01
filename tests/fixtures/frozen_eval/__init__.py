"""Frozen eval CI fixture for M24 calibration testing.

This fixture provides a minimal, deterministic frozen eval dataset for CI-only calibration
testing. It does NOT depend on external files or checkpoints.

Per M24 locked decisions:
- CI uses this fixture via --manifest flag
- Baselines only (no checkpoints required)
- Deterministic, reproducible data
"""
