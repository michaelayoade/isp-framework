"""Configuration management schemas for the ISP Framework."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict
from datetime import datetime


# System Configuration Schemas
class SystemConfigurationBase(BaseModel):
    """Base schema for system configuration."""
    config_key: str
    config_value: str
    config_type: str = "string"  # string, integer, boolean, json
    category: str = "general"
    description: Optional[str] = None
    is_active: bool = True


class SystemConfigurationCreate(SystemConfigurationBase):
    """Schema for creating system configuration."""
    pass


class SystemConfigurationUpdate(BaseModel):
    """Schema for updating system configuration."""
    config_value: Optional[str] = None
    config_type: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class SystemConfigurationResponse(SystemConfigurationBase):
    """Schema for system configuration response."""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


# Location Management Schemas (using existing Location model)
class LocationConfigBase(BaseModel):
    """Base schema for location configuration."""
    name: str
    code: Optional[str] = None
    description: Optional[str] = None
    country: str = "Nigeria"
    state_province: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    timezone: str = "Africa/Lagos"
    is_active: bool = True


class LocationConfigCreate(LocationConfigBase):
    """Schema for creating location configuration."""
    pass


class LocationConfigUpdate(BaseModel):
    """Schema for updating location configuration."""
    name: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None
    country: Optional[str] = None
    state_province: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    timezone: Optional[str] = None
    is_active: Optional[bool] = None


class LocationConfigResponse(LocationConfigBase):
    """Schema for location configuration response."""
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


# Service Configuration Schemas (using existing ServiceType model)
class ServiceConfigBase(BaseModel):
    """Base schema for service configuration."""
    service_name: str
    service_code: Optional[str] = None
    description: Optional[str] = None
    category: str = "internet"
    is_active: bool = True
    configuration: Optional[Dict[str, Any]] = None


class ServiceConfigCreate(ServiceConfigBase):
    """Schema for creating service configuration."""
    pass


class ServiceConfigUpdate(BaseModel):
    """Schema for updating service configuration."""
    service_name: Optional[str] = None
    service_code: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    is_active: Optional[bool] = None
    configuration: Optional[Dict[str, Any]] = None


class ServiceConfigResponse(ServiceConfigBase):
    """Schema for service configuration response."""
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


# Audit Configuration Schemas (using existing AuditLog model)
class AuditConfigBase(BaseModel):
    """Base schema for audit configuration."""
    event_type: str
    event_category: str = "system"
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    action: str
    description: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class AuditConfigCreate(AuditConfigBase):
    """Schema for creating audit configuration."""
    pass


class AuditConfigResponse(AuditConfigBase):
    """Schema for audit configuration response."""
    id: int
    user_id: Optional[int] = None
    timestamp: datetime
    additional_data: Optional[Dict[str, Any]] = None
    
    model_config = ConfigDict(from_attributes=True)


# Configuration List Schemas
class ConfigurationListResponse(BaseModel):
    """Schema for configuration list response."""
    items: List[SystemConfigurationResponse]
    total: int
    page: int
    per_page: int
    pages: int


class LocationListResponse(BaseModel):
    """Schema for location list response."""
    items: List[LocationConfigResponse]
    total: int
    page: int
    per_page: int
    pages: int


class ServiceListResponse(BaseModel):
    """Schema for service list response."""
    items: List[ServiceConfigResponse]
    total: int
    page: int
    per_page: int
    pages: int


class AuditListResponse(BaseModel):
    """Schema for audit list response."""
    items: List[AuditConfigResponse]
    total: int
    page: int
    per_page: int
    pages: int


# Configuration Statistics Schema
class ConfigurationStatsResponse(BaseModel):
    """Schema for configuration statistics response."""
    total_configurations: int
    active_configurations: int
    inactive_configurations: int
    configurations_by_category: Dict[str, int]
    recent_changes: int
    last_updated: Optional[datetime] = None
