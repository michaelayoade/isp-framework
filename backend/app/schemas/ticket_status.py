from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class TicketStatusBase(BaseModel):
    """Base schema for ticket statuses."""

    code: str = Field(..., min_length=1, max_length=50, description="Status code")
    name: str = Field(..., min_length=1, max_length=100, description="Display name")
    description: Optional[str] = Field(
        None, max_length=255, description="Optional description"
    )
    is_active: bool = Field(True, description="Is status active")
    sort_order: int = Field(0, description="Sort order for UI")

    # Workflow properties
    is_initial: bool = Field(
        False, description="Is this a starting status for new tickets"
    )
    is_final: bool = Field(False, description="Is this a final status")
    requires_assignment: bool = Field(
        False, description="Must ticket be assigned to proceed"
    )
    auto_close_after_days: Optional[int] = Field(
        None, description="Auto-close after N days"
    )

    # Customer visibility
    is_customer_visible: bool = Field(
        True, description="Should customers see this status"
    )
    customer_description: Optional[str] = Field(
        None, max_length=255, description="Customer-friendly description"
    )

    # SLA properties
    pauses_sla: bool = Field(False, description="Does this status pause SLA timers")
    escalation_hours: Optional[int] = Field(None, description="Hours before escalation")

    # UI properties
    color_hex: str = Field(
        "#6B7280", max_length=7, description="Color for status badges (#RRGGBB)"
    )
    icon_name: Optional[str] = Field(
        None, max_length=50, description="Icon identifier for UI"
    )


class TicketStatusCreate(TicketStatusBase):
    """Schema for creating ticket status."""

    pass


class TicketStatusUpdate(BaseModel):
    """Schema for updating ticket status."""

    code: Optional[str] = Field(None, min_length=1, max_length=50)
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=255)
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None
    is_initial: Optional[bool] = None
    is_final: Optional[bool] = None
    requires_assignment: Optional[bool] = None
    auto_close_after_days: Optional[int] = None
    is_customer_visible: Optional[bool] = None
    customer_description: Optional[str] = Field(None, max_length=255)
    pauses_sla: Optional[bool] = None
    escalation_hours: Optional[int] = None
    color_hex: Optional[str] = Field(None, max_length=7)
    icon_name: Optional[str] = Field(None, max_length=50)


class TicketStatus(TicketStatusBase):
    """Schema for ticket status response."""

    id: int
    is_system: bool = Field(..., description="System ticket statuses cannot be deleted")
    created_at: datetime
    updated_at: Optional[datetime] = None
