"""Pydantic validation utilities for RenaceCHESS contracts.

This module provides normalization helpers to ensure compatibility with
Pydantic v2's alias-based dict validation while allowing snake_case field names
in Python code.
"""

from typing import Any, Type, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


def validate_with_aliases(
    model: Type[T],
    data: dict[str, Any],
) -> T:
    """
    Normalize dict input to alias-based keys before Pydantic v2 validation.

    In Pydantic v2, `populate_by_name=True` only works for keyword arguments,
    not for dict inputs. When a model has aliases defined, dict inputs must
    use the alias keys (camelCase), not the field names (snake_case).

    This helper accepts dicts with either snake_case field names or
    camelCase alias keys, and normalizes them to alias keys before validation.

    Args:
        model: The Pydantic model class to instantiate
        data: Dictionary with either snake_case field names or camelCase aliases

    Returns:
        Validated model instance

    Example:
        >>> from renacechess.contracts.models import PieceFeatures
        >>> data = {"slot_id": 0, "color": "white", ...}  # snake_case
        >>> piece = validate_with_aliases(PieceFeatures, data)
        >>> # Works! Internally converts to alias keys before validation
    """
    # Build field name to alias mapping
    field_to_alias: dict[str, str] = {}
    for field_name, field_info in model.model_fields.items():
        if field_info.alias:
            field_to_alias[field_name] = field_info.alias

    # Convert dict keys from field names to aliases if needed
    normalized_data: dict[str, Any] = {}
    alias_set = set(field_to_alias.values())

    for key, value in data.items():
        if key in alias_set:
            # Already an alias, use as-is
            normalized_data[key] = value
        elif key in field_to_alias:
            # Field name, convert to alias
            normalized_data[field_to_alias[key]] = value
        else:
            # Unknown key (no alias), pass through (Pydantic will validate)
            normalized_data[key] = value

    # Validate with alias keys (Pydantic v2 expects aliases for dict inputs)
    return model.model_validate(normalized_data)
