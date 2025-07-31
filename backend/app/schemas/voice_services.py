"""Voice Services Pydantic Schemas."""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class VoiceServiceBase(BaseModel):
    """Base voice service schema."""

    plan_id: int = Field(..., description="Service plan ID")
    phone_number: Optional[str] = Field(None, description="Assigned phone number")
    monthly_fee: Optional[Decimal] = Field(None, description="Monthly service fee")
    setup_fee: Optional[Decimal] = Field(None, description="One-time setup fee")
    features: Optional[List[str]] = Field(
        default_factory=list, description="Service features"
    )
    notes: Optional[str] = Field(None, description="Service notes")


class VoiceServiceCreate(VoiceServiceBase):
    """Schema for creating voice service."""

    pass


class VoiceServiceUpdate(BaseModel):
    """Schema for updating voice service."""

    plan_id: Optional[int] = None
    phone_number: Optional[str] = None
    monthly_fee: Optional[Decimal] = None
    setup_fee: Optional[Decimal] = None
    features: Optional[List[str]] = None
    notes: Optional[str] = None


class VoiceService(VoiceServiceBase):
    """Voice service response schema."""

    id: int
    customer_id: int
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class VoiceServiceList(BaseModel):
    """Voice service list response."""

    services: List[VoiceService]
    total: int
    page: int
    per_page: int


class VoiceServiceProvisioningRequest(BaseModel):
    """Voice service provisioning request."""

    phone_number: str = Field(..., description="Phone number to assign")
    sip_domain: Optional[str] = Field(None, description="SIP domain")
    features: Optional[List[str]] = Field(
        default_factory=list, description="Features to enable"
    )
    priority: Optional[str] = Field("normal", description="Provisioning priority")

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, v):
        if not v or len(v) < 10:
            raise ValueError("Phone number must be at least 10 digits")
        return v
