from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ServiceTypeBase(BaseModel):
    """Base schema for service types."""

    code: str = Field(..., min_length=1, max_length=50, description="Service type code")
    name: str = Field(..., min_length=1, max_length=100, description="Display name")
    description: Optional[str] = Field(None, description="Detailed description")
    is_active: bool = Field(True, description="Is service type active")
    sort_order: int = Field(0, description="Sort order for UI")

    # Service properties
    requires_installation: bool = Field(
        True, description="Does this service need installation"
    )
    supports_bandwidth_limits: bool = Field(
        True, description="Can bandwidth be limited"
    )
    is_recurring: bool = Field(True, description="Is this a recurring service")
    allows_multiple_instances: bool = Field(
        False, description="Can customer have multiple of this type"
    )

    # Billing properties
    default_billing_cycle: str = Field(
        "monthly", max_length=20, description="Default billing cycle"
    )
    requires_equipment: bool = Field(
        False, description="Does service require equipment rental"
    )

    # UI properties
    color_hex: str = Field(
        "#6B7280", max_length=7, description="Color for service type badges (#RRGGBB)"
    )
    icon_name: Optional[str] = Field(
        None, max_length=50, description="Icon identifier for UI"
    )

    # Technical properties
    provisioning_template: Optional[str] = Field(
        None, max_length=100, description="Template identifier for automation"
    )
    qos_profile: Optional[str] = Field(
        None, max_length=50, description="Default QoS profile"
    )


class ServiceTypeCreate(ServiceTypeBase):
    """Schema for creating service type."""

    pass


class ServiceTypeUpdate(BaseModel):
    """Schema for updating service type."""

    code: Optional[str] = Field(None, min_length=1, max_length=50)
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None
    requires_installation: Optional[bool] = None
    supports_bandwidth_limits: Optional[bool] = None
    is_recurring: Optional[bool] = None
    allows_multiple_instances: Optional[bool] = None
    default_billing_cycle: Optional[str] = Field(None, max_length=20)
    requires_equipment: Optional[bool] = None
    color_hex: Optional[str] = Field(None, max_length=7)
    icon_name: Optional[str] = Field(None, max_length=50)
    provisioning_template: Optional[str] = Field(None, max_length=100)
    qos_profile: Optional[str] = Field(None, max_length=50)


class ServiceType(ServiceTypeBase):
    """Schema for service type response."""

    id: int
    is_system: bool = Field(..., description="System service types cannot be deleted")
    created_at: datetime
    updated_at: Optional[datetime] = None
