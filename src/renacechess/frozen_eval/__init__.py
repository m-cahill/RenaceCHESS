"""Frozen evaluation module for M06 and M30."""

from renacechess.frozen_eval.generator import (
    generate_frozen_eval_manifest,
    write_frozen_eval_manifest,
)
from renacechess.frozen_eval.generator_v2 import (
    generate_frozen_eval_v2,
    verify_frozen_eval_v2,
)

__all__ = [
    # V1 (M06)
    "generate_frozen_eval_manifest",
    "write_frozen_eval_manifest",
    # V2 (M30)
    "generate_frozen_eval_v2",
    "verify_frozen_eval_v2",
]
