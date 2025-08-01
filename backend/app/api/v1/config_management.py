"""Configuration management API endpoints using existing models."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.dependencies import get_current_superuser
from app.models.auth.base import Administrator
from app.services.config_management import (
    SystemConfigurationService,
    LocationManagementService,
    ServiceManagementService,
    AuditManagementService
)
from app.schemas.config_management import (
    SystemConfigurationCreate,
    SystemConfigurationUpdate,
    SystemConfigurationResponse,
    LocationConfigCreate,
    LocationConfigUpdate,
    LocationConfigResponse,
    ServiceConfigCreate,
    ServiceConfigUpdate,
    ServiceConfigResponse,
    AuditConfigCreate,
    AuditConfigResponse,
    ConfigurationListResponse,
    LocationListResponse,
    ServiceListResponse,
    AuditListResponse,
    ConfigurationStatsResponse
)

router = APIRouter()


# System Configuration Endpoints
@router.post("/configurations", response_model=SystemConfigurationResponse, tags=["System Configuration"])
def create_system_configuration(
    configuration: SystemConfigurationCreate,
    db: Session = Depends(get_db),
    current_user: Administrator = Depends(get_current_superuser)
):
    """Create a new system configuration."""
    service = SystemConfigurationService(db)
    config_data = configuration.model_dump()
    result = service.create_configuration(config_data, current_user)
    return result


@router.get("/configurations", response_model=List[SystemConfigurationResponse], tags=["System Configuration"])
def get_system_configurations(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    category: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: Administrator = Depends(get_current_superuser)
):
    """Get all system configurations with pagination."""
    service = SystemConfigurationService(db)
    configurations = service.get_configurations(skip=skip, limit=limit, category=category)
    return configurations


@router.get("/configurations/key/{config_key}", response_model=SystemConfigurationResponse, tags=["System Configuration"])
def get_system_configuration_by_key(
    config_key: str,
    db: Session = Depends(get_db),
    current_user: Administrator = Depends(get_current_superuser)
):
    """Get a system configuration by key."""
    service = SystemConfigurationService(db)
    configuration = service.get_configuration(config_key)
    if not configuration:
        raise HTTPException(status_code=404, detail="Configuration not found")
    return configuration


@router.get("/configurations/stats", response_model=ConfigurationStatsResponse, tags=["System Configuration"])
def get_configuration_statistics(
    db: Session = Depends(get_db),
    current_user: Administrator = Depends(get_current_superuser)
):
    """Get configuration statistics."""
    service = SystemConfigurationService(db)
    stats = service.get_configuration_stats()
    return stats


# Location Management Endpoints
@router.post("/locations", response_model=LocationConfigResponse, tags=["Location Management"])
def create_location(
    location: LocationConfigCreate,
    db: Session = Depends(get_db),
    current_user: Administrator = Depends(get_current_superuser)
):
    """Create a new location."""
    service = LocationManagementService(db)
    location_data = location.model_dump()
    result = service.create_location(location_data)
    return result


@router.get("/locations", response_model=List[LocationConfigResponse], tags=["Location Management"])
def get_locations(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: Administrator = Depends(get_current_superuser)
):
    """Get all locations with pagination."""
    service = LocationManagementService(db)
    locations = service.get_locations(skip=skip, limit=limit)
    return locations


@router.get("/locations/{location_id}", response_model=LocationConfigResponse, tags=["Location Management"])
def get_location(
    location_id: int,
    db: Session = Depends(get_db),
    current_user: Administrator = Depends(get_current_superuser)
):
    """Get a location by ID."""
    service = LocationManagementService(db)
    location = service.get_location(location_id)
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    return location


@router.put("/locations/{location_id}", response_model=LocationConfigResponse, tags=["Location Management"])
def update_location(
    location_id: int,
    location_update: LocationConfigUpdate,
    db: Session = Depends(get_db),
    current_user: Administrator = Depends(get_current_superuser)
):
    """Update a location."""
    service = LocationManagementService(db)
    location_data = location_update.model_dump(exclude_unset=True)
    location = service.update_location(location_id, location_data)
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    return location


@router.delete("/locations/{location_id}", tags=["Location Management"])
def delete_location(
    location_id: int,
    db: Session = Depends(get_db),
    current_user: Administrator = Depends(get_current_superuser)
):
    """Delete a location."""
    service = LocationManagementService(db)
    success = service.delete_location(location_id)
    if not success:
        raise HTTPException(status_code=404, detail="Location not found")
    return {"message": "Location deleted successfully"}


# Service Configuration Endpoints
@router.post("/services", response_model=ServiceConfigResponse, tags=["Service Configuration"])
def create_service_configuration(
    service_config: ServiceConfigCreate,
    db: Session = Depends(get_db),
    current_user: Administrator = Depends(get_current_superuser)
):
    """Create a new service configuration."""
    service = ServiceManagementService(db)
    service_data = service_config.model_dump()
    # Map schema fields to ServiceType model fields
    service_data["name"] = service_data.pop("service_name")
    service_data["code"] = service_data.pop("service_code", None)
    result = service.create_service_config(service_data)
    return result


@router.get("/services", response_model=List[ServiceConfigResponse], tags=["Service Configuration"])
def get_service_configurations(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: Administrator = Depends(get_current_superuser)
):
    """Get all service configurations with pagination."""
    service = ServiceManagementService(db)
    services = service.get_service_configs(skip=skip, limit=limit)
    # Map ServiceType model fields to schema fields
    result = []
    for svc in services:
        result.append({
            "id": svc.id,
            "service_name": svc.name,
            "service_code": svc.code,
            "description": svc.description,
            "category": getattr(svc, "category", "internet"),
            "is_active": getattr(svc, "is_active", True),
            "configuration": getattr(svc, "configuration", None),
            "created_at": getattr(svc, "created_at", None),
            "updated_at": getattr(svc, "updated_at", None)
        })
    return result


@router.get("/services/{service_id}", response_model=ServiceConfigResponse, tags=["Service Configuration"])
def get_service_configuration(
    service_id: int,
    db: Session = Depends(get_db),
    current_user: Administrator = Depends(get_current_superuser)
):
    """Get a service configuration by ID."""
    service = ServiceManagementService(db)
    svc = service.get_service_config(service_id)
    if not svc:
        raise HTTPException(status_code=404, detail="Service configuration not found")
    
    # Map ServiceType model fields to schema fields
    return {
        "id": svc.id,
        "service_name": svc.name,
        "service_code": svc.code,
        "description": svc.description,
        "category": getattr(svc, "category", "internet"),
        "is_active": getattr(svc, "is_active", True),
        "configuration": getattr(svc, "configuration", None),
        "created_at": getattr(svc, "created_at", None),
        "updated_at": getattr(svc, "updated_at", None)
    }


@router.put("/services/{service_id}", response_model=ServiceConfigResponse, tags=["Service Configuration"])
def update_service_configuration(
    service_id: int,
    service_update: ServiceConfigUpdate,
    db: Session = Depends(get_db),
    current_user: Administrator = Depends(get_current_superuser)
):
    """Update a service configuration."""
    service = ServiceManagementService(db)
    service_data = service_update.model_dump(exclude_unset=True)
    
    # Map schema fields to ServiceType model fields
    if "service_name" in service_data:
        service_data["name"] = service_data.pop("service_name")
    if "service_code" in service_data:
        service_data["code"] = service_data.pop("service_code")
    
    svc = service.update_service_config(service_id, service_data)
    if not svc:
        raise HTTPException(status_code=404, detail="Service configuration not found")
    
    # Map ServiceType model fields to schema fields
    return {
        "id": svc.id,
        "service_name": svc.name,
        "service_code": svc.code,
        "description": svc.description,
        "category": getattr(svc, "category", "internet"),
        "is_active": getattr(svc, "is_active", True),
        "configuration": getattr(svc, "configuration", None),
        "created_at": getattr(svc, "created_at", None),
        "updated_at": getattr(svc, "updated_at", None)
    }


# Audit Management Endpoints
@router.post("/audit", response_model=AuditConfigResponse, tags=["Audit Management"])
def create_audit_entry(
    audit_entry: AuditConfigCreate,
    db: Session = Depends(get_db),
    current_user: Administrator = Depends(get_current_superuser)
):
    """Create a new audit log entry."""
    service = AuditManagementService(db)
    audit_data = audit_entry.model_dump()
    result = service.create_audit_entry(audit_data, current_user)
    return result


@router.get("/audit", response_model=List[AuditConfigResponse], tags=["Audit Management"])
def get_audit_entries(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    event_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: Administrator = Depends(get_current_superuser)
):
    """Get all audit log entries with pagination."""
    service = AuditManagementService(db)
    audit_entries = service.get_audit_entries(skip=skip, limit=limit, event_type=event_type)
    return audit_entries


@router.get("/audit/{audit_id}", response_model=AuditConfigResponse, tags=["Audit Management"])
def get_audit_entry(
    audit_id: int,
    db: Session = Depends(get_db),
    current_user: Administrator = Depends(get_current_superuser)
):
    """Get an audit log entry by ID."""
    service = AuditManagementService(db)
    audit_entry = service.get_audit_entry(audit_id)
    if not audit_entry:
        raise HTTPException(status_code=404, detail="Audit entry not found")
    return audit_entry


@router.get("/audit/statistics", tags=["Audit Management"])
def get_audit_statistics(
    days: int = Query(7, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: Administrator = Depends(get_current_superuser)
):
    """Get audit log statistics."""
    service = AuditManagementService(db)
    stats = service.get_audit_statistics(days=days)
    return stats
