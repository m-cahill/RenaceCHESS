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
        # Normalize the key
        if key in alias_set:
            # Already an alias, use as-is
            normalized_key = key
        elif key in field_to_alias:
            # Field name, convert to alias
            normalized_key = field_to_alias[key]
        else:
            # Unknown key (no alias defined), pass through
            normalized_key = key

        # Recursively normalize nested dicts (for nested model validation)
        if isinstance(value, dict):
            # Check if this field is a nested model type
            if key in cls.model_fields:
                field_info = cls.model_fields[key]
                # Try to get the inner type (could be a model or list of models)
                # For now, try to normalize if it looks like a model dict
                # This is a heuristic - we'll normalize if it has common model keys
                if any(
                    k in value for k in ["schema_version", "schemaVersion", "slot_id", "slotId"]
                ):
                    # Likely a nested model dict, try to normalize recursively
                    # We need the nested model class, but we can't easily get it here
                    # So we'll just pass it through and let Pydantic handle it
                    normalized_data[normalized_key] = value
                else:
                    normalized_data[normalized_key] = value
        elif isinstance(value, list):
            # Check if list contains dicts that might be nested models
            if value and isinstance(value[0], dict):
                # Get the field annotation to determine the nested model type
                nested_model_cls = None
                if key in cls.model_fields:
                    field_info = cls.model_fields[key]
                    # Try to extract the inner type from list[T] or list[T] | None
                    annotation = field_info.annotation
                    # Handle typing.List, list, and Optional/Union types
                    if hasattr(annotation, "__args__"):
                        args = annotation.__args__
                        if args:
                            # Get the first argument (the inner type)
                            inner_type = args[0]
                            # Check if it's a BaseModel subclass
                            if isinstance(inner_type, type) and issubclass(inner_type, BaseModel):
                                nested_model_cls = inner_type

                # Recursively normalize each dict in the list
                normalized_list = []
                for item in value:
                    if isinstance(item, dict) and nested_model_cls:
                        # Normalize using the nested model's field-to-alias mapping
                        normalized_list.append(_normalize_to_aliases(nested_model_cls, item))
                    else:
                        normalized_list.append(item)
                normalized_data[normalized_key] = normalized_list
            else:
                normalized_data[normalized_key] = value
        else:
            normalized_data[normalized_key] = value

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
