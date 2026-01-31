"""RenaceCHESS base model for Pydantic v2 compatibility.

This module provides a base model class that normalizes dict-based inputs
to alias-based keys before validation, including during nested model validation.

Background:
    In Pydantic v2, nested model validation converts child models to dicts using
    field names (snake_case), then re-validates them. However, when aliases are
    defined, validation expects alias keys (camelCase). The `populate_by_name=True`
    config only works for keyword arguments, not dict inputs.

    This base model intercepts dict inputs before validation and normalizes them
    to use alias keys, ensuring consistent behavior for both explicit and nested
    model validation.

M12.1 Reference:
    This is the architectural adaptation layer introduced by M12.1 to restore
    Pydantic v2 compatibility without changing PoC semantics.
"""

from typing import Any

from pydantic import BaseModel, model_validator


def _normalize_to_aliases(cls: type[BaseModel], data: dict[str, Any]) -> dict[str, Any]:
    """Normalize dict keys from field names to aliases.

    Args:
        cls: The model class being validated
        data: Dictionary with either snake_case field names or camelCase aliases

    Returns:
        Dictionary with alias keys where aliases are defined
    """
    # Build field name to alias mapping
    field_to_alias: dict[str, str] = {}
    for field_name, field_info in cls.model_fields.items():
        if field_info.alias:
            field_to_alias[field_name] = field_info.alias

    if not field_to_alias:
        # No aliases defined, return as-is
        return data

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
            # Unknown key (no alias defined), pass through
            normalized_data[key] = value

    return normalized_data


class RenaceBaseModel(BaseModel):
    """RenaceCHESS base model with Pydantic v2 compatibility normalization.

    All RenaceCHESS contract models should inherit from this class to ensure
    consistent dict-to-model validation behavior under pinned Pydantic v2.

    This base model:
    - Accepts both snake_case field names and camelCase aliases in dict inputs
    - Normalizes dict inputs to alias keys before validation
    - Preserves JSON serialization using camelCase aliases
    - Works correctly for nested model validation

    Usage:
        >>> class MyModel(RenaceBaseModel):
        ...     my_field: str = Field(..., alias="myField")
        ...
        >>> # Both work:
        >>> MyModel(my_field="value")  # kwargs
        >>> MyModel.model_validate({"my_field": "value"})  # snake_case dict
        >>> MyModel.model_validate({"myField": "value"})  # alias dict
    """

    @model_validator(mode="before")
    @classmethod
    def normalize_dict_input(cls, data: Any) -> Any:
        """Normalize dict inputs to use alias keys before validation.

        This validator intercepts dict inputs (including those from nested model
        validation) and converts snake_case field names to camelCase aliases.
        """
        if isinstance(data, dict):
            return _normalize_to_aliases(cls, data)
        return data
