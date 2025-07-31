"""
Network API Endpoints - Modular Architecture

This module provides REST API endpoints for the new modular network architecture,
featuring vendor-agnostic network management, comprehensive IPAM, and unified
device management across multiple vendors.

Key Features:
- Vendor-agnostic network device management
- Comprehensive IP Address Management (IPAM)
- Network topology visualization
- Multi-vendor device configuration
- Real-time monitoring and alerting
- Network change management
"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.core.database import get_db
from app.api.v1.dependencies import get_current_admin
from app.models.auth import Administrator
from app.services.network_service import (
    get_network_services
)
from app.schemas.network_modular import (
    # Site schemas
    NetworkSiteResponse, NetworkSiteCreate, NetworkSiteUpdate,
    # Device schemas  
    NetworkDeviceResponse, NetworkDeviceCreate, VendorConfigurationCreate,
    # IPAM schemas
    IPPoolResponse, IPPoolCreate, IPAllocationResponse, IPAllocationCreate,
    IPUtilizationResponse,
    # Topology schemas
    NetworkTopologyResponse, DeviceConnectionCreate,
    # Monitoring schemas
    DeviceMetricCreate, NetworkAlertResponse,
    # General schemas
    PaginatedResponse
)

router = APIRouter(tags=["network"])


# Network Site Management
@router.post("/sites", response_model=NetworkSiteResponse)
async def create_network_site(
    site_data: NetworkSiteCreate,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Create a new network site with modern architecture"""
    try:
        services = get_network_services(db)
        site = services["site_service"].create_site(site_data.dict())
        return NetworkSiteResponse.from_orm(site)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/sites", response_model=PaginatedResponse[NetworkSiteResponse])
async def get_network_sites(
    site_type: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Get network sites with filtering and pagination"""
    try:
        services = get_network_services(db)
        filters = {}
        if site_type:
            filters["site_type"] = site_type
        if is_active is not None:
            filters["is_active"] = is_active
        
        sites = services["site_service"].repository.get_all(
            filters=filters, skip=skip, limit=limit
        )
        total = services["site_service"].repository.count(filters=filters)
        
        return PaginatedResponse(
            items=[NetworkSiteResponse.from_orm(site) for site in sites],
            total=total,
            skip=skip,
            limit=limit
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/sites/{site_id}", response_model=NetworkSiteResponse)
async def get_network_site(
    site_id: int,
    include_devices: bool = Query(False),
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Get a specific network site by ID"""
    try:
        services = get_network_services(db)
        if include_devices:
            site = services["site_service"].get_site_with_devices(site_id)
        else:
            site = services["site_service"].repository.get_by_id(site_id)
        
        if not site:
            raise HTTPException(status_code=404, detail="Network site not found")
        
        return NetworkSiteResponse.from_orm(site)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/sites/{site_id}", response_model=NetworkSiteResponse)
async def update_network_site(
    site_id: int,
    site_data: NetworkSiteUpdate,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Update a network site"""
    try:
        services = get_network_services(db)
        site = services["site_service"].repository.update(site_id, site_data.dict(exclude_unset=True))
        if not site:
            raise HTTPException(status_code=404, detail="Network site not found")
        
        return NetworkSiteResponse.from_orm(site)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Network Device Management
@router.post("/devices", response_model=NetworkDeviceResponse)
async def create_network_device(
    device_data: NetworkDeviceCreate,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Create a new network device"""
    try:
        services = get_network_services(db)
        device = services["device_service"].create_device(device_data.dict())
        return NetworkDeviceResponse.from_orm(device)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/devices", response_model=PaginatedResponse[NetworkDeviceResponse])
async def get_network_devices(
    site_id: Optional[int] = Query(None),
    device_type: Optional[str] = Query(None),
    vendor: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Get network devices with filtering"""
    try:
        services = get_network_services(db)
        filters = {}
        if site_id:
            filters["site_id"] = site_id
        if device_type:
            filters["device_type"] = device_type
        if vendor:
            filters["vendor"] = vendor
        if is_active is not None:
            filters["is_active"] = is_active
        
        devices = services["device_service"].repository.get_all(
            filters=filters, skip=skip, limit=limit
        )
        total = services["device_service"].repository.count(filters=filters)
        
        return PaginatedResponse(
            items=[NetworkDeviceResponse.from_orm(device) for device in devices],
            total=total,
            skip=skip,
            limit=limit
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/devices/{device_id}", response_model=Dict[str, Any])
async def get_network_device(
    device_id: int,
    include_vendor_config: bool = Query(True),
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Get a specific network device with optional vendor configuration"""
    try:
        services = get_network_services(db)
        if include_vendor_config:
            result = services["device_service"].get_device_with_vendor_config(device_id)
            if not result:
                raise HTTPException(status_code=404, detail="Network device not found")
            return {
                "device": NetworkDeviceResponse.from_orm(result["device"]),
                "vendor_config": result["vendor_config"]
            }
        else:
            device = services["device_service"].repository.get_by_id(device_id)
            if not device:
                raise HTTPException(status_code=404, detail="Network device not found")
            return {"device": NetworkDeviceResponse.from_orm(device)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/devices/{device_id}/vendor-config")
async def add_vendor_configuration(
    device_id: int,
    config_data: VendorConfigurationCreate,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Add vendor-specific configuration to a device"""
    try:
        services = get_network_services(db)
        success = services["device_service"].add_vendor_configuration(
            device_id, config_data.vendor, config_data.configuration
        )
        if not success:
            raise HTTPException(status_code=404, detail="Network device not found")
        
        return {"message": f"Added {config_data.vendor} configuration successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# IP Address Management (IPAM)
@router.post("/ipam/pools", response_model=IPPoolResponse)
async def create_ip_pool(
    pool_data: IPPoolCreate,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Create a new IP address pool"""
    try:
        services = get_network_services(db)
        pool = services["ipam_service"].create_ip_pool(pool_data.dict())
        return IPPoolResponse.from_orm(pool)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/ipam/pools", response_model=PaginatedResponse[IPPoolResponse])
async def get_ip_pools(
    pool_type: Optional[str] = Query(None),
    location_id: Optional[int] = Query(None),
    is_active: Optional[bool] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Get IP pools with filtering"""
    try:
        services = get_network_services(db)
        filters = {}
        if pool_type:
            filters["pool_type"] = pool_type
        if location_id:
            filters["location_id"] = location_id
        if is_active is not None:
            filters["is_active"] = is_active
        
        pools = services["ipam_service"].pool_repository.get_all(
            filters=filters, skip=skip, limit=limit
        )
        total = services["ipam_service"].pool_repository.count(filters=filters)
        
        return PaginatedResponse(
            items=[IPPoolResponse.from_orm(pool) for pool in pools],
            total=total,
            skip=skip,
            limit=limit
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/ipam/pools/{pool_id}/utilization", response_model=IPUtilizationResponse)
async def get_pool_utilization(
    pool_id: int,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Get IP pool utilization statistics"""
    try:
        services = get_network_services(db)
        utilization = services["ipam_service"].get_pool_utilization(pool_id)
        if not utilization:
            raise HTTPException(status_code=404, detail="IP pool not found")
        
        return IPUtilizationResponse(**utilization)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/ipam/pools/{pool_id}/allocate", response_model=IPAllocationResponse)
async def allocate_ip_address(
    pool_id: int,
    allocation_data: IPAllocationCreate,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Allocate an IP address from a pool"""
    try:
        services = get_network_services(db)
        allocation = services["ipam_service"].allocate_ip_address(
            pool_id, allocation_data.dict()
        )
        if not allocation:
            raise HTTPException(status_code=400, detail="Failed to allocate IP address")
        
        return IPAllocationResponse.from_orm(allocation)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/ipam/allocations/{allocation_id}")
async def release_ip_address(
    allocation_id: int,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Release an allocated IP address"""
    try:
        services = get_network_services(db)
        success = services["ipam_service"].release_ip_address(allocation_id)
        if not success:
            raise HTTPException(status_code=404, detail="IP allocation not found")
        
        return {"message": "IP address released successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Network Topology Management
@router.get("/topology", response_model=NetworkTopologyResponse)
async def get_network_topology(
    site_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Get network topology for visualization"""
    try:
        services = get_network_services(db)
        topology = services["topology_service"].get_network_topology(site_id)
        return NetworkTopologyResponse(**topology)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/topology/connections")
async def create_device_connection(
    connection_data: DeviceConnectionCreate,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Create a connection between two devices"""
    try:
        services = get_network_services(db)
        connection = services["topology_service"].create_device_connection(
            connection_data.dict()
        )
        return {"message": "Device connection created successfully", "id": connection.id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Network Monitoring
@router.post("/monitoring/metrics")
async def record_device_metric(
    metric_data: DeviceMetricCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Record a device performance metric"""
    try:
        services = get_network_services(db)
        metric = services["monitoring_service"].record_device_metric(metric_data.dict())
        return {"message": "Metric recorded successfully", "id": metric.id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/monitoring/alerts", response_model=List[NetworkAlertResponse])
async def get_network_alerts(
    device_id: Optional[int] = Query(None),
    active_only: bool = Query(True),
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Get network alerts"""
    try:
        services = get_network_services(db)
        if active_only:
            alerts = services["monitoring_service"].get_active_alerts(device_id)
        else:
            filters = {}
            if device_id:
                filters["device_id"] = device_id
            alerts = services["monitoring_service"].alert_repository.get_all(filters=filters)
        
        return [NetworkAlertResponse.from_orm(alert) for alert in alerts]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/monitoring/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Acknowledge a network alert"""
    try:
        services = get_network_services(db)
        success = services["monitoring_service"].acknowledge_alert(alert_id, current_admin.id)
        if not success:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        return {"message": "Alert acknowledged successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Network Statistics and Overview
@router.get("/overview")
async def get_network_overview(
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Get comprehensive network overview and statistics"""
    try:
        services = get_network_services(db)
        
        # Gather statistics from all services
        site_stats = services["site_service"].repository.count()
        device_stats = services["device_service"].repository.count()
        pool_stats = services["ipam_service"].pool_repository.count()
        active_alerts = len(services["monitoring_service"].get_active_alerts())
        
        return {
            "sites": {
                "total": site_stats,
                "active": services["site_service"].repository.count({"is_active": True})
            },
            "devices": {
                "total": device_stats,
                "active": services["device_service"].repository.count({"is_active": True}),
                "by_type": {}  # Could be expanded with device type breakdown
            },
            "ip_pools": {
                "total": pool_stats,
                "active": services["ipam_service"].pool_repository.count({"is_active": True})
            },
            "monitoring": {
                "active_alerts": active_alerts
            },
            "timestamp": datetime.now()
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
