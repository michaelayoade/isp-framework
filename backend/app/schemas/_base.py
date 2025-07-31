from pydantic import BaseModel, ConfigDict
"""Shared base Pydantic model.

This centralises common Pydantic v2 configuration so we don’t have to repeat it
in every schema module.  All project schemas should inherit from
`BaseSchema` instead of `pydantic.BaseSchema`.

Key settings
------------
populate_by_name
    Enable aliased fields to still be filled when the payload uses the model
    attribute names.  This was previously `allow_population_by_field_name` in
    pydantic v1.
from_attributes
    Replacement for ``orm_mode = True`` from v1 so ORM objects can be passed
    directly to schema constructors.

Using a single base class avoids dozens of duplicated Config blocks and keeps
our code free of Pydantic-v2 deprecation warnings.
"""

# ConfigDict already imported above


class BaseSchema(BaseModel):
    """Project-wide base schema class."""

    # Global configuration for all child schemas
    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
        str_strip_whitespace=True,
        validate_default=True,
    )

    # Future helpers / shared validators can be added here
