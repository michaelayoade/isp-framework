"""
Service Instances API Endpoints - ISP Service Management System

REST API endpoints for managing customer service instances including:
- Customer services (CRUD, activation, suspension, termination)
- Internet services (PPPoE, IP assignment, speed management)
- Voice services (SIP, phone numbers, call management)

Provides comprehensive service instance management for active customer subscriptions.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from ..dependencies import get_current_admin
from app.models.auth import Administrator
from app.schemas.service_management import (
    # Customer Service Schemas
    CustomerService, CustomerServiceCreate, CustomerServiceUpdate,
    CustomerServiceSearchFilters, CustomerServiceListResponse,
    
    # Internet Service Schemas
    CustomerInternetService, CustomerInternetServiceCreate, CustomerInternetServiceUpdate,
    
    # Voice Service Schemas
    CustomerVoiceService, CustomerVoiceServiceCreate, CustomerVoiceServiceUpdate,
    
    # Statistics and Operations
    ServiceStatistics, BulkServiceOperation, BulkOperationResult,
    ServiceBillingIntegration, ServiceNetworkIntegration,
    PaginationParams
)
from app.services.service_layer_factory import get_service_layer_factory
from app.models.services.enums import ServiceStatus, ServiceType

router = APIRouter()


# ============================================================================
# Customer Service Instance Endpoints
# ============================================================================

@router.post("/", response_model=CustomerService, status_code=status.HTTP_201_CREATED)
async def create_customer_service(
    service_data: CustomerServiceCreate,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Create a new customer service instance"""
    factory = get_service_layer_factory(db)
    service_service = factory.get_customer_service_service()
    
    try:
        service = await service_service.create_customer_service(
            service_data=service_data.dict(),
            admin_id=current_admin.id
        )
        return service
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create service: {str(e)}")


@router.get("/", response_model=CustomerServiceListResponse)
async def list_customer_services(
    customer_id: Optional[int] = Query(None, description="Filter by customer ID"),
    template_id: Optional[int] = Query(None, description="Filter by template ID"),
    status: Optional[ServiceStatus] = Query(None, description="Filter by service status"),
    service_type: Optional[ServiceType] = Query(None, description="Filter by service type"),
    activation_date_from: Optional[str] = Query(None, description="Filter by activation date from (YYYY-MM-DD)"),
    activation_date_to: Optional[str] = Query(None, description="Filter by activation date to (YYYY-MM-DD)"),
    search_query: Optional[str] = Query(None, description="Search in service notes and configuration"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """List customer services with filtering and pagination"""
    factory = get_service_layer_factory(db)
    service_service = factory.get_customer_service_service()
    
    # Build filters
    filters = {}
    if customer_id:
        filters['customer_id'] = customer_id
    if template_id:
        filters['template_id'] = template_id
    if status:
        filters['status'] = status
    if service_type:
        filters['service_type'] = service_type
    if activation_date_from:
        filters['activation_date_from'] = activation_date_from
    if activation_date_to:
        filters['activation_date_to'] = activation_date_to
    if search_query:
        filters['search_query'] = search_query
    
    try:
        services, total = await service_service.search_customer_services(
            filters=filters,
            page=page,
            size=size
        )
        
        return CustomerServiceListResponse(
            items=services,
            total=total,
            page=page,
            size=size,
            pages=(total + size - 1) // size if total > 0 else 0
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list services: {str(e)}")


@router.get("/{service_id}", response_model=CustomerService)
async def get_customer_service(
    service_id: int,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Get a specific customer service"""
    factory = get_service_layer_factory(db)
    service_service = factory.get_customer_service_service()
    
    try:
        service = await service_service.get_customer_service_by_id(service_id)
        if not service:
            raise HTTPException(status_code=404, detail="Service not found")
        return service
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get service: {str(e)}")


@router.put("/{service_id}", response_model=CustomerService)
async def update_customer_service(
    service_id: int,
    service_data: CustomerServiceUpdate,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Update a customer service"""
    factory = get_service_layer_factory(db)
    service_service = factory.get_customer_service_service()
    
    try:
        service = await service_service.update_customer_service(
            service_id=service_id,
            update_data=service_data.dict(exclude_unset=True),
            admin_id=current_admin.id
        )
        if not service:
            raise HTTPException(status_code=404, detail="Service not found")
        return service
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update service: {str(e)}")


@router.delete("/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
async def terminate_customer_service(
    service_id: int,
    reason: Optional[str] = Query(None, description="Termination reason"),
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Terminate a customer service"""
    factory = get_service_layer_factory(db)
    service_service = factory.get_customer_service_service()
    
    try:
        success = await service_service.terminate_customer_service(
            service_id=service_id,
            reason=reason,
            admin_id=current_admin.id
        )
        if not success:
            raise HTTPException(status_code=404, detail="Service not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to terminate service: {str(e)}")


# ============================================================================
# Service Lifecycle Management Endpoints
# ============================================================================

@router.post("/{service_id}/activate", response_model=CustomerService)
async def activate_customer_service(
    service_id: int,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Activate a customer service"""
    factory = get_service_layer_factory(db)
    service_service = factory.get_customer_service_service()
    
    try:
        service = await service_service.activate_customer_service(
            service_id=service_id,
            admin_id=current_admin.id
        )
        if not service:
            raise HTTPException(status_code=404, detail="Service not found")
        return service
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to activate service: {str(e)}")


@router.post("/{service_id}/suspend", response_model=CustomerService)
async def suspend_customer_service(
    service_id: int,
    reason: str = Query(..., description="Suspension reason"),
    grace_period_hours: Optional[int] = Query(None, description="Grace period in hours"),
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Suspend a customer service"""
    factory = get_service_layer_factory(db)
    service_service = factory.get_customer_service_service()
    
    try:
        service = await service_service.suspend_customer_service(
            service_id=service_id,
            reason=reason,
            grace_period_hours=grace_period_hours,
            admin_id=current_admin.id
        )
        if not service:
            raise HTTPException(status_code=404, detail="Service not found")
        return service
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to suspend service: {str(e)}")


@router.post("/{service_id}/restore", response_model=CustomerService)
async def restore_customer_service(
    service_id: int,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Restore a suspended customer service"""
    factory = get_service_layer_factory(db)
    service_service = factory.get_customer_service_service()
    
    try:
        service = await service_service.restore_customer_service(
            service_id=service_id,
            admin_id=current_admin.id
        )
        if not service:
            raise HTTPException(status_code=404, detail="Service not found")
        return service
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to restore service: {str(e)}")


# ============================================================================
# Internet Service Instance Endpoints
# ============================================================================

@router.post("/internet", response_model=CustomerInternetService, status_code=status.HTTP_201_CREATED)
async def create_internet_service(
    service_data: CustomerInternetServiceCreate,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Create a new customer internet service"""
    factory = get_service_layer_factory(db)
    internet_service = factory.get_internet_service_service()
    
    try:
        service = await internet_service.create_internet_service(
            service_data=service_data.dict(),
            admin_id=current_admin.id
        )
        return service
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create internet service: {str(e)}")


@router.get("/internet", response_model=List[CustomerInternetService])
async def list_internet_services(
    customer_id: Optional[int] = Query(None, description="Filter by customer ID"),
    router_id: Optional[int] = Query(None, description="Filter by router ID"),
    sector_id: Optional[int] = Query(None, description="Filter by sector ID"),
    fup_exceeded: Optional[bool] = Query(None, description="Filter by FUP status"),
    has_assigned_ip: Optional[bool] = Query(None, description="Filter by IP assignment"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """List internet services with filtering"""
    factory = get_service_layer_factory(db)
    internet_service = factory.get_internet_service_service()
    
    # Build filters
    filters = {}
    if customer_id:
        filters['customer_id'] = customer_id
    if router_id:
        filters['router_id'] = router_id
    if sector_id:
        filters['sector_id'] = sector_id
    if fup_exceeded is not None:
        filters['fup_exceeded'] = fup_exceeded
    if has_assigned_ip is not None:
        filters['has_assigned_ip'] = has_assigned_ip
    
    try:
        services, _ = await internet_service.search_internet_services(
            filters=filters,
            page=page,
            size=size
        )
        return services
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list internet services: {str(e)}")


@router.get("/internet/{service_id}", response_model=CustomerInternetService)
async def get_internet_service(
    service_id: int,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Get a specific internet service"""
    factory = get_service_layer_factory(db)
    internet_service = factory.get_internet_service_service()
    
    try:
        service = await internet_service.get_internet_service_by_id(service_id)
        if not service:
            raise HTTPException(status_code=404, detail="Internet service not found")
        return service
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get internet service: {str(e)}")


@router.put("/internet/{service_id}", response_model=CustomerInternetService)
async def update_internet_service(
    service_id: int,
    service_data: CustomerInternetServiceUpdate,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Update an internet service"""
    factory = get_service_layer_factory(db)
    internet_service = factory.get_internet_service_service()
    
    try:
        service = await internet_service.update_internet_service(
            service_id=service_id,
            update_data=service_data.dict(exclude_unset=True),
            admin_id=current_admin.id
        )
        if not service:
            raise HTTPException(status_code=404, detail="Internet service not found")
        return service
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update internet service: {str(e)}")


@router.post("/internet/{service_id}/reset-fup", response_model=CustomerInternetService)
async def reset_internet_service_fup(
    service_id: int,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Reset FUP status for an internet service"""
    factory = get_service_layer_factory(db)
    internet_service = factory.get_internet_service_service()
    
    try:
        service = await internet_service.reset_fup_status(
            service_id=service_id,
            admin_id=current_admin.id
        )
        if not service:
            raise HTTPException(status_code=404, detail="Internet service not found")
        return service
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reset FUP: {str(e)}")


@router.post("/internet/{service_id}/change-speed", response_model=CustomerInternetService)
async def change_internet_service_speed(
    service_id: int,
    download_speed: int = Query(..., gt=0, description="New download speed in kbps"),
    upload_speed: int = Query(..., gt=0, description="New upload speed in kbps"),
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Change speed for an internet service"""
    factory = get_service_layer_factory(db)
    internet_service = factory.get_internet_service_service()
    
    try:
        service = await internet_service.change_service_speed(
            service_id=service_id,
            download_speed=download_speed,
            upload_speed=upload_speed,
            admin_id=current_admin.id
        )
        if not service:
            raise HTTPException(status_code=404, detail="Internet service not found")
        return service
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to change speed: {str(e)}")


# ============================================================================
# Voice Service Instance Endpoints
# ============================================================================

@router.post("/voice", response_model=CustomerVoiceService, status_code=status.HTTP_201_CREATED)
async def create_voice_service(
    service_data: CustomerVoiceServiceCreate,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Create a new customer voice service"""
    factory = get_service_layer_factory(db)
    voice_service = factory.get_voice_service_service()
    
    try:
        service = await voice_service.create_voice_service(
            service_data=service_data.dict(),
            admin_id=current_admin.id
        )
        return service
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create voice service: {str(e)}")


@router.get("/voice", response_model=List[CustomerVoiceService])
async def list_voice_services(
    customer_id: Optional[int] = Query(None, description="Filter by customer ID"),
    phone_number: Optional[str] = Query(None, description="Filter by phone number"),
    has_balance: Optional[bool] = Query(None, description="Filter by call balance presence"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """List voice services with filtering"""
    factory = get_service_layer_factory(db)
    voice_service = factory.get_voice_service_service()
    
    # Build filters
    filters = {}
    if customer_id:
        filters['customer_id'] = customer_id
    if phone_number:
        filters['phone_number'] = phone_number
    if has_balance is not None:
        filters['has_balance'] = has_balance
    
    try:
        services, _ = await voice_service.search_voice_services(
            filters=filters,
            page=page,
            size=size
        )
        return services
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list voice services: {str(e)}")


@router.get("/voice/{service_id}", response_model=CustomerVoiceService)
async def get_voice_service(
    service_id: int,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Get a specific voice service"""
    factory = get_service_layer_factory(db)
    voice_service = factory.get_voice_service_service()
    
    try:
        service = await voice_service.get_voice_service_by_id(service_id)
        if not service:
            raise HTTPException(status_code=404, detail="Voice service not found")
        return service
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get voice service: {str(e)}")


@router.post("/voice/{service_id}/add-balance", response_model=CustomerVoiceService)
async def add_voice_service_balance(
    service_id: int,
    amount: float = Query(..., gt=0, description="Amount to add to balance"),
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Add balance to a voice service"""
    factory = get_service_layer_factory(db)
    voice_service = factory.get_voice_service_service()
    
    try:
        service = await voice_service.add_call_balance(
            service_id=service_id,
            amount=amount,
            admin_id=current_admin.id
        )
        if not service:
            raise HTTPException(status_code=404, detail="Voice service not found")
        return service
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add balance: {str(e)}")


# ============================================================================
# Bulk Operations Endpoints
# ============================================================================

@router.post("/bulk-operation", response_model=BulkOperationResult)
async def perform_bulk_service_operation(
    operation_data: BulkServiceOperation,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Perform bulk operations on multiple services"""
    factory = get_service_layer_factory(db)
    service_service = factory.get_customer_service_service()
    
    try:
        result = await service_service.perform_bulk_operation(
            service_ids=operation_data.service_ids,
            operation=operation_data.operation,
            parameters=operation_data.parameters,
            reason=operation_data.reason,
            admin_id=current_admin.id
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to perform bulk operation: {str(e)}")


# ============================================================================
# Service Statistics and Analytics Endpoints
# ============================================================================

@router.get("/statistics", response_model=ServiceStatistics)
async def get_service_statistics(
    customer_id: Optional[int] = Query(None, description="Filter by customer ID"),
    service_type: Optional[ServiceType] = Query(None, description="Filter by service type"),
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Get service statistics"""
    factory = get_service_layer_factory(db)
    service_service = factory.get_customer_service_service()
    
    try:
        stats = await service_service.get_service_statistics(
            customer_id=customer_id,
            service_type=service_type
        )
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")


@router.get("/{service_id}/usage-summary", response_model=Dict[str, Any])
async def get_service_usage_summary(
    service_id: int,
    days: int = Query(30, ge=1, le=365, description="Number of days for usage summary"),
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Get usage summary for a service"""
    factory = get_service_layer_factory(db)
    usage_service = factory.get_usage_tracking_service()
    
    try:
        summary = await usage_service.get_service_usage_summary(
            service_id=service_id,
            days=days
        )
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get usage summary: {str(e)}")


# ============================================================================
# Integration Endpoints
# ============================================================================

@router.get("/{service_id}/billing-integration", response_model=ServiceBillingIntegration)
async def get_service_billing_integration(
    service_id: int,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Get billing integration data for a service"""
    factory = get_service_layer_factory(db)
    service_service = factory.get_customer_service_service()
    
    try:
        billing_data = await service_service.get_billing_integration_data(service_id)
        if not billing_data:
            raise HTTPException(status_code=404, detail="Service or billing data not found")
        return billing_data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get billing integration: {str(e)}")


@router.get("/{service_id}/network-integration", response_model=ServiceNetworkIntegration)
async def get_service_network_integration(
    service_id: int,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Get network integration data for a service"""
    factory = get_service_layer_factory(db)
    service_service = factory.get_customer_service_service()
    
    try:
        network_data = await service_service.get_network_integration_data(service_id)
        if not network_data:
            raise HTTPException(status_code=404, detail="Service or network data not found")
        return network_data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get network integration: {str(e)}")


# ============================================================================
# Customer Service Overview Endpoints
# ============================================================================

@router.get("/customers/{customer_id}/services", response_model=List[CustomerService])
async def get_customer_services(
    customer_id: int,
    status: Optional[ServiceStatus] = Query(None, description="Filter by service status"),
    service_type: Optional[ServiceType] = Query(None, description="Filter by service type"),
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Get all services for a specific customer"""
    factory = get_service_layer_factory(db)
    service_service = factory.get_customer_service_service()
    
    filters = {'customer_id': customer_id}
    if status:
        filters['status'] = status
    if service_type:
        filters['service_type'] = service_type
    
    try:
        services, _ = await service_service.search_customer_services(
            filters=filters,
            page=1,
            size=100  # Large size for customer overview
        )
        return services
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get customer services: {str(e)}")


@router.get("/customers/{customer_id}/services/summary", response_model=Dict[str, Any])
async def get_customer_services_summary(
    customer_id: int,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Get services summary for a customer"""
    factory = get_service_layer_factory(db)
    service_service = factory.get_customer_service_service()
    
    try:
        summary = await service_service.get_customer_services_summary(customer_id)
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get customer services summary: {str(e)}")
