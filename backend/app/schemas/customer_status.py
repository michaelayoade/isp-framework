from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CustomerStatusBase(BaseModel):
    """Base schema for customer statuses."""

    code: str = Field(..., min_length=1, max_length=50, description="Status code")
    name: str = Field(..., min_length=1, max_length=100, description="Display name")
    description: Optional[str] = Field(
        None, max_length=255, description="Optional description"
    )
    is_active: bool = Field(True, description="Is status active")
    sort_order: int = Field(0, description="Sort order for UI")

    # Workflow properties
    allows_service_activation: bool = Field(
        True, description="Can services be activated in this status"
    )
    allows_billing: bool = Field(
        True, description="Should billing continue in this status"
    )
    is_terminal: bool = Field(False, description="Is this a final status")

    # UI properties
    color_hex: str = Field(
        "#6B7280", max_length=7, description="Color for status badges (#RRGGBB)"
    )
    icon_name: Optional[str] = Field(
        None, max_length=50, description="Icon identifier for UI"
    )


class CustomerStatusCreate(CustomerStatusBase):
    """Schema for creating customer status."""

    pass


class CustomerStatusUpdate(BaseModel):
    """Schema for updating customer status."""

    code: Optional[str] = Field(None, min_length=1, max_length=50)
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=255)
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None
    allows_service_activation: Optional[bool] = None
    allows_billing: Optional[bool] = None
    is_terminal: Optional[bool] = None
    color_hex: Optional[str] = Field(None, max_length=7)
    icon_name: Optional[str] = Field(None, max_length=50)


class CustomerStatus(CustomerStatusBase):
    """Schema for customer status response."""

    id: int
    is_system: bool = Field(..., description="System statuses cannot be deleted")
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = {"from_attributes": True}
