"""Stub Pydantic schemas for Bundle Service used during testing.
Replace with full schema definitions when implementing Bundle Service.
"""

from datetime import datetime
from typing import List as _List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class BundleServiceBase(BaseModel):
    name: str = Field(..., json_schema_extra={"example": "Family Bundle"})
    description: Optional[str] = None


class BundleServiceCreate(BundleServiceBase):
    pass


class BundleServiceUpdate(BundleServiceBase):
    pass


class BundleServiceInDB(BundleServiceBase):
    id: UUID

    model_config = ConfigDict(from_attributes=True)


# Alias expected by endpoints that import `BundleService`
BundleService = BundleServiceInDB

# Common list alias used in responses
BundleServiceList = _List[BundleServiceInDB]


# Provisioning request/response schemas
class BundleServiceProvisioningRequest(BaseModel):
    """Request schema for bundle service provisioning"""

    bundle_id: UUID
    customer_id: UUID
    priority: str = "normal"
    scheduled_date: Optional[datetime] = None
    provisioning_notes: Optional[str] = None


class BundleServiceProvisioningResponse(BaseModel):
    """Response schema for bundle service provisioning"""

    job_id: UUID
    status: str = "queued"
    estimated_completion: Optional[datetime] = None
    message: Optional[str] = None
