"""FastAPI endpoints for device management and MAC authentication."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.dependencies import get_current_active_admin
from app.services.device import DeviceService
from app.models.auth.base import Administrator
from app.schemas.device import (
    DeviceCreate, DeviceUpdate, DeviceApproval, DeviceResponse, DeviceListResponse,
    DeviceStats, DeviceBulkApproval, DeviceBulkUpdate, DeviceBulkResponse,
    DeviceFilters, DeviceSort, RadiusDeviceRequest, RadiusDeviceResponse
)
from app.core.permissions import require_permission
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/", response_model=DeviceListResponse)
@require_permission("devices.view")
async def list_devices(
    customer_id: Optional[int] = Query(None, description="Filter by customer ID"),
    status: Optional[str] = Query(None, pattern="^(pending|active|blocked|expired)$"),
    device_type: Optional[str] = Query(None, description="Filter by device type"),
    is_approved: Optional[bool] = Query(None, description="Filter by approval status"),
    is_auto_registered: Optional[bool] = Query(None, description="Filter by auto-registration"),
    mac_address: Optional[str] = Query(None, description="Filter by MAC address"),
    name: Optional[str] = Query(None, description="Filter by device name"),
    nas_identifier: Optional[str] = Query(None, description="Filter by NAS identifier"),
    sort_field: str = Query("last_seen", pattern="^(name|mac_address|status|last_seen|created_at)$"),
    sort_direction: str = Query("desc", pattern="^(asc|desc)$"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_active_admin)
):
    """List devices with filtering, sorting, and pagination."""
    try:
        service = DeviceService(db)
        
        filters = DeviceFilters(
            customer_id=customer_id,
            status=status,
            device_type=device_type,
            is_approved=is_approved,
            is_auto_registered=is_auto_registered,
            mac_address=mac_address,
            name=name,
            nas_identifier=nas_identifier
        )
        
        sort = DeviceSort(field=sort_field, direction=sort_direction)
        
        devices, total = service.list_devices(filters, sort, page, per_page)
        
        pages = (total + per_page - 1) // per_page
        
        return DeviceListResponse(
            devices=[DeviceResponse.from_orm(device) for device in devices],
            total=total,
            page=page,
            per_page=per_page,
            pages=pages
        )
        
    except Exception as e:
        logger.error(f"Error listing devices: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve devices"
        )


@router.post("/", response_model=DeviceResponse, status_code=status.HTTP_201_CREATED)
@require_permission("devices.create")
async def create_device(
    device_data: DeviceCreate,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_active_admin)
):
    """Create a new device."""
    try:
        service = DeviceService(db)
        device = service.create_device(device_data)
        
        logger.info(f"Admin {current_admin.username} created device {device.id}")
        return DeviceResponse.from_orm(device)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating device: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create device"
        )


@router.get("/{device_id}", response_model=DeviceResponse)
@require_permission("devices.view")
async def get_device(
    device_id: int,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_active_admin)
):
    """Get device by ID."""
    service = DeviceService(db)
    device = service.get_device(device_id)
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    return DeviceResponse.from_orm(device)


@router.put("/{device_id}", response_model=DeviceResponse)
@require_permission("devices.update")
async def update_device(
    device_id: int,
    device_data: DeviceUpdate,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_active_admin)
):
    """Update device information."""
    try:
        service = DeviceService(db)
        device = service.update_device(device_id, device_data)
        
        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device not found"
            )
        
        logger.info(f"Admin {current_admin.username} updated device {device_id}")
        return DeviceResponse.from_orm(device)
        
    except Exception as e:
        logger.error(f"Error updating device {device_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update device"
        )


@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
@require_permission("devices.delete")
async def delete_device(
    device_id: int,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_active_admin)
):
    """Delete a device."""
    try:
        service = DeviceService(db)
        success = service.delete_device(device_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device not found"
            )
        
        logger.info(f"Admin {current_admin.username} deleted device {device_id}")
        
    except Exception as e:
        logger.error(f"Error deleting device {device_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete device"
        )


@router.post("/{device_id}/approve", response_model=DeviceResponse)
@require_permission("devices.approve")
async def approve_device(
    device_id: int,
    approval_data: DeviceApproval,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_active_admin)
):
    """Approve or reject a device."""
    try:
        service = DeviceService(db)
        device = service.approve_device(device_id, approval_data, current_admin.id)
        
        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device not found"
            )
        
        action = "approved" if approval_data.is_approved else "rejected"
        logger.info(f"Admin {current_admin.username} {action} device {device_id}")
        
        return DeviceResponse.from_orm(device)
        
    except Exception as e:
        logger.error(f"Error approving device {device_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to approve device"
        )


@router.post("/{device_id}/block", response_model=DeviceResponse)
@require_permission("devices.block")
async def block_device(
    device_id: int,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_active_admin)
):
    """Block a device."""
    try:
        service = DeviceService(db)
        device_data = DeviceUpdate(status="blocked")
        device = service.update_device(device_id, device_data)
        
        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device not found"
            )
        
        logger.info(f"Admin {current_admin.username} blocked device {device_id}")
        return DeviceResponse.from_orm(device)
        
    except Exception as e:
        logger.error(f"Error blocking device {device_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to block device"
        )


@router.get("/customer/{customer_id}", response_model=List[DeviceResponse])
@require_permission("devices.view")
async def get_customer_devices(
    customer_id: int,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_active_admin)
):
    """Get all devices for a customer."""
    try:
        service = DeviceService(db)
        devices = service.get_customer_devices(customer_id)
        
        return [DeviceResponse.from_orm(device) for device in devices]
        
    except Exception as e:
        logger.error(f"Error getting devices for customer {customer_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve customer devices"
        )


@router.get("/stats/overview", response_model=DeviceStats)
@require_permission("devices.view")
async def get_device_stats(
    customer_id: Optional[int] = Query(None, description="Filter stats by customer ID"),
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_active_admin)
):
    """Get device statistics."""
    try:
        service = DeviceService(db)
        stats = service.get_device_stats(customer_id)
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting device stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve device statistics"
        )


@router.get("/mac/{mac_address}", response_model=DeviceResponse)
@require_permission("devices.view")
async def get_device_by_mac(
    mac_address: str,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_active_admin)
):
    """Get device by MAC address."""
    try:
        service = DeviceService(db)
        device = service.get_device_by_mac(mac_address)
        
        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device not found"
            )
        
        return DeviceResponse.from_orm(device)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid MAC address format: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error getting device by MAC {mac_address}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve device"
        )


# Bulk Operations
@router.post("/bulk/approve", response_model=DeviceBulkResponse)
@require_permission("devices.approve")
async def bulk_approve_devices(
    bulk_data: DeviceBulkApproval,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_active_admin)
):
    """Bulk approve or reject devices."""
    try:
        service = DeviceService(db)
        result = service.bulk_approve_devices(bulk_data, current_admin.id)
        
        action = "approved" if bulk_data.is_approved else "rejected"
        logger.info(f"Admin {current_admin.username} bulk {action} {len(bulk_data.device_ids)} devices")
        
        return result
        
    except Exception as e:
        logger.error(f"Error bulk approving devices: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to bulk approve devices"
        )


@router.post("/bulk/update", response_model=DeviceBulkResponse)
@require_permission("devices.update")
async def bulk_update_devices(
    bulk_data: DeviceBulkUpdate,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_active_admin)
):
    """Bulk update devices."""
    try:
        service = DeviceService(db)
        result = service.bulk_update_devices(bulk_data)
        
        logger.info(f"Admin {current_admin.username} bulk updated {len(bulk_data.device_ids)} devices")
        
        return result
        
    except Exception as e:
        logger.error(f"Error bulk updating devices: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to bulk update devices"
        )


# RADIUS Integration Endpoint (Internal Use)
@router.post("/radius/authenticate", response_model=RadiusDeviceResponse)
async def radius_authenticate_device(
    request: RadiusDeviceRequest,
    db: Session = Depends(get_db)
):
    """Authenticate device via RADIUS MAC-Auth (internal endpoint)."""
    try:
        service = DeviceService(db)
        response = service.authenticate_device(request)
        
        logger.info(f"RADIUS auth for MAC {request.mac_address}: {'granted' if response.access_granted else 'denied'}")
        
        return response
        
    except Exception as e:
        logger.error(f"Error in RADIUS authentication: {str(e)}")
        return RadiusDeviceResponse(
            access_granted=False,
            rejection_reason="Internal authentication error"
        )
