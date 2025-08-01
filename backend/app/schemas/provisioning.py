"""
Provisioning Queue Schemas

Pydantic schemas for provisioning queue management including:
- Job creation and updates
- Status tracking and history
- Worker management
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, field_validator


class ProvisioningJobBase(BaseModel):
    """Base schema for provisioning jobs."""
    
    service_id: int = Field(..., description="ID of the service to provision")
    service_type: str = Field(..., description="Type of service (internet, voice, bundle)")
    customer_id: int = Field(..., description="Customer ID")
    priority: str = Field(default="normal", description="Job priority (low, normal, high, urgent)")
    action: str = Field(..., description="Provisioning action (create, modify, delete, suspend, resume)")
    parameters: Optional[Dict[str, Any]] = Field(default=None, description="Job parameters")
    scheduled_for: Optional[datetime] = Field(default=None, description="When to execute the job")
    max_retries: int = Field(default=3, description="Maximum retry attempts")
    timeout_seconds: int = Field(default=300, description="Job timeout in seconds")
    
    @field_validator('priority')
    @classmethod
    def validate_priority(cls, v):
        if v not in ['low', 'normal', 'high', 'urgent']:
            raise ValueError('Priority must be one of: low, normal, high, urgent')
        return v
    
    @field_validator('service_type')
    @classmethod
    def validate_service_type(cls, v):
        if v not in ['internet', 'voice', 'bundle']:
            raise ValueError('Service type must be one of: internet, voice, bundle')
        return v
    
    @field_validator('action')
    @classmethod
    def validate_action(cls, v):
        if v not in ['create', 'modify', 'delete', 'suspend', 'resume']:
            raise ValueError('Action must be one of: create, modify, delete, suspend, resume')
        return v


class ProvisioningJobCreate(ProvisioningJobBase):
    """Schema for creating provisioning jobs."""
    pass


class ProvisioningJobUpdate(BaseModel):
    """Schema for updating provisioning jobs."""
    
    status: Optional[str] = Field(default=None, description="Job status")
    status_message: Optional[str] = Field(default=None, description="Status message")
    result_data: Optional[Dict[str, Any]] = Field(default=None, description="Job result data")
    error_message: Optional[str] = Field(default=None, description="Error message")
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        if v and v not in ['queued', 'processing', 'completed', 'failed', 'cancelled']:
            raise ValueError('Status must be one of: queued, processing, completed, failed, cancelled')
        return v


class ProvisioningJobResponse(ProvisioningJobBase):
    """Schema for provisioning job responses."""
    
    id: int
    job_id: str
    status: str
    status_message: Optional[str] = None
    worker_id: Optional[str] = None
    retry_count: int = 0
    result_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_by: Optional[int] = None

    class Config:
        from_attributes = True


class ProvisioningJobList(BaseModel):
    """Schema for paginated provisioning job lists."""
    
    jobs: List[ProvisioningJobResponse]
    total: int
    page: int
    per_page: int
    pages: int


class ProvisioningJobHistoryResponse(BaseModel):
    """Schema for provisioning job history responses."""
    
    id: int
    job_id: int
    old_status: Optional[str] = None
    new_status: str
    message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    created_at: datetime
    created_by: Optional[int] = None

    class Config:
        from_attributes = True


class ProvisioningWorkerBase(BaseModel):
    """Base schema for provisioning workers."""
    
    worker_id: str = Field(..., description="Unique worker identifier")
    worker_name: str = Field(..., description="Human-readable worker name")
    supported_service_types: List[str] = Field(..., description="Supported service types")
    max_concurrent_jobs: int = Field(default=1, description="Maximum concurrent jobs")


class ProvisioningWorkerCreate(ProvisioningWorkerBase):
    """Schema for creating provisioning workers."""
    pass


class ProvisioningWorkerResponse(ProvisioningWorkerBase):
    """Schema for provisioning worker responses."""
    
    id: int
    status: str
    current_job_id: Optional[str] = None
    jobs_processed: int = 0
    jobs_succeeded: int = 0
    jobs_failed: int = 0
    last_heartbeat: datetime
    last_job_started: Optional[datetime] = None
    last_job_completed: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ProvisioningQueueStats(BaseModel):
    """Schema for provisioning queue statistics."""
    
    by_status: Dict[str, int] = Field(..., description="Job counts by status")
    by_priority: Dict[str, int] = Field(..., description="Job counts by priority")
    by_service_type: Dict[str, int] = Field(..., description="Job counts by service type")
    avg_processing_time_seconds: float = Field(..., description="Average processing time in seconds")


class ProvisioningJobFilter(BaseModel):
    """Schema for filtering provisioning jobs."""
    
    status: Optional[str] = None
    service_type: Optional[str] = None
    customer_id: Optional[int] = None
    priority: Optional[str] = None
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=25, ge=1, le=100)
