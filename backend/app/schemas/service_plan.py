from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ServicePlanBase(BaseModel):
    """Base service plan schema with common fields."""

    name: str = Field(
        ..., min_length=1, max_length=255, description="Service plan name"
    )
    display_name: Optional[str] = Field(
        None, max_length=255, description="Display name for customers"
    )
    service_type: str = Field(
        "internet",
        description="Service type: internet, voice, bundle, recurring, onetime",
    )
    price: int = Field(
        ..., gt=0, description="Price in smallest currency unit (e.g., kobo/cents)"
    )
    currency: str = Field("NGN", max_length=3, description="Currency code")
    billing_cycle: str = Field(
        "monthly", description="Billing cycle: monthly, quarterly, yearly"
    )

    # Internet-specific fields
    download_speed: Optional[int] = Field(
        None, gt=0, description="Download speed in Mbps"
    )
    upload_speed: Optional[int] = Field(None, gt=0, description="Upload speed in Mbps")
    data_limit: Optional[int] = Field(
        None, gt=0, description="Data limit in GB (null for unlimited)"
    )


class ServicePlanCreate(ServicePlanBase):
    """Schema for creating a new service plan."""

    pass


class ServicePlanUpdate(BaseModel):
    """Schema for updating an existing service plan."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    display_name: Optional[str] = Field(None, max_length=255)
    service_type: Optional[str] = None
    price: Optional[int] = Field(None, gt=0)
    currency: Optional[str] = Field(None, max_length=3)
    billing_cycle: Optional[str] = None
    download_speed: Optional[int] = Field(None, gt=0)
    upload_speed: Optional[int] = Field(None, gt=0)
    data_limit: Optional[int] = Field(None, gt=0)


class ServicePlan(ServicePlanBase):
    """Schema for service plan response."""

    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None


class ServicePlanSummary(BaseModel):
    """Simplified service plan schema for lists."""

    id: int
    name: str
    display_name: Optional[str]
    service_type: str
    price: int
    currency: str
    billing_cycle: str
    is_active: bool
