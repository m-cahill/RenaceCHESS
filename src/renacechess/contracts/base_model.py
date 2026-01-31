"""RenaceCHESS base model for Pydantic v2 compatibility.

This module provides a base model class that normalizes dict-based inputs
to alias-based keys before validation.

Background:
    In Pydantic v2, `populate_by_name=True` only works for keyword arguments,
    not for dict inputs. When a model has aliases defined, dict inputs must
    use the alias keys (camelCase), not the field names (snake_case).

    This base model intercepts direct dict inputs before validation and
    normalizes them to use alias keys.

    Note: For nested model validation, use `field_validator(mode="before")`
    on container fields (see M12.1 documentation).

M12.1 Reference:
    This is the architectural adaptation layer introduced by M12.1 to restore
    Pydantic v2 compatibility without changing PoC semantics.
"""

from typing import Any

from pydantic import BaseModel, model_validator

from renacechess.contracts.validation import normalize_dict_keys_to_aliases


class RenaceBaseModel(BaseModel):
    """RenaceCHESS base model with Pydantic v2 compatibility normalization.

    All RenaceCHESS contract models should inherit from this class to ensure
    consistent dict-to-model validation behavior under pinned Pydantic v2.

    This base model:
    - Accepts both snake_case field names and camelCase aliases in dict inputs
    - Normalizes direct dict inputs to alias keys before validation
    - Preserves JSON serialization using camelCase aliases

    For nested model validation (e.g., lists of models), use `field_validator`
    on the container field (see M12.1 documentation).

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

        This validator intercepts direct dict inputs and converts snake_case
        field names to camelCase aliases. For nested model validation, use
        `field_validator` on container fields instead.
        """
        if isinstance(data, dict):
            return normalize_dict_keys_to_aliases(data, cls)
        return data
