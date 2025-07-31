"""
Service Provisioning API Endpoints - ISP Service Management System

REST API endpoints for managing service provisioning workflows including:
- Service provisioning (workflow management, status tracking)
- Provisioning templates (automation templates, step definitions)
- Provisioning queue (task management, priority handling)

Provides comprehensive automated service deployment and workflow management.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from ..dependencies import get_current_admin
from app.models.auth import Administrator
from app.schemas.service_management import (
    # Service Provisioning Schemas
    ServiceProvisioning, ServiceProvisioningCreate, ServiceProvisioningUpdate,
    ServiceProvisioningListResponse,
    
    # Provisioning Template Schemas
    ProvisioningTemplate, ProvisioningTemplateCreate, ProvisioningTemplateUpdate,
    
    # Statistics and Operations
    ProvisioningStatistics, BulkOperationResult
)
from app.services.service_layer_factory import get_service_layer_factory
from app.models.services.enums import ProvisioningStatus, ServiceType

router = APIRouter()


# ============================================================================
# Service Provisioning Endpoints
# ============================================================================

@router.post("/", response_model=ServiceProvisioning, status_code=status.HTTP_201_CREATED)
async def create_service_provisioning(
    provisioning_data: ServiceProvisioningCreate,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Create a new service provisioning workflow"""
    factory = get_service_layer_factory(db)
    provisioning_service = factory.get_provisioning_service()
    
    try:
        provisioning = await provisioning_service.initiate_provisioning(
            service_id=provisioning_data.service_id,
            template_id=provisioning_data.template_id,
            priority=provisioning_data.priority,
            scheduled_at=provisioning_data.scheduled_at,
            configuration=provisioning_data.configuration,
            admin_id=current_admin.id
        )
        return provisioning
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create provisioning: {str(e)}")


@router.get("/queue", response_model=ServiceProvisioningListResponse)
async def list_service_provisioning(
    service_id: Optional[int] = Query(None, description="Filter by service ID"),
    status: Optional[ProvisioningStatus] = Query(None, description="Filter by provisioning status"),
    priority_min: Optional[int] = Query(None, ge=1, le=10, description="Minimum priority"),
    priority_max: Optional[int] = Query(None, ge=1, le=10, description="Maximum priority"),
    scheduled_date_from: Optional[str] = Query(None, description="Filter by scheduled date from (YYYY-MM-DD)"),
    scheduled_date_to: Optional[str] = Query(None, description="Filter by scheduled date to (YYYY-MM-DD)"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """List service provisioning workflows with filtering and pagination"""
    factory = get_service_layer_factory(db)
    provisioning_service = factory.get_provisioning_service()
    
    # Build filters
    filters = {}
    if service_id:
        filters['service_id'] = service_id
    if status:
        filters['status'] = status
    if priority_min:
        filters['priority_min'] = priority_min
    if priority_max:
        filters['priority_max'] = priority_max
    if scheduled_date_from:
        filters['scheduled_date_from'] = scheduled_date_from
    if scheduled_date_to:
        filters['scheduled_date_to'] = scheduled_date_to
    
    try:
        provisioning_list, total = await provisioning_service.search_provisioning_workflows(
            filters=filters,
            page=page,
            size=size
        )
        
        return ServiceProvisioningListResponse(
            items=provisioning_list,
            total=total,
            page=page,
            size=size,
            pages=(total + size - 1) // size if total > 0 else 0
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list provisioning: {str(e)}")


@router.get("/{provisioning_id}", response_model=ServiceProvisioning)
async def get_service_provisioning(
    provisioning_id: int,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Get a specific service provisioning workflow"""
    factory = get_service_layer_factory(db)
    provisioning_service = factory.get_provisioning_service()
    
    try:
        provisioning = await provisioning_service.get_provisioning_by_id(provisioning_id)
        if not provisioning:
            raise HTTPException(status_code=404, detail="Provisioning workflow not found")
        return provisioning
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get provisioning: {str(e)}")


@router.put("/{provisioning_id}", response_model=ServiceProvisioning)
async def update_service_provisioning(
    provisioning_id: int,
    provisioning_data: ServiceProvisioningUpdate,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Update a service provisioning workflow"""
    factory = get_service_layer_factory(db)
    provisioning_service = factory.get_provisioning_service()
    
    try:
        provisioning = await provisioning_service.update_provisioning_workflow(
            provisioning_id=provisioning_id,
            update_data=provisioning_data.dict(exclude_unset=True),
            admin_id=current_admin.id
        )
        if not provisioning:
            raise HTTPException(status_code=404, detail="Provisioning workflow not found")
        return provisioning
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update provisioning: {str(e)}")


# ============================================================================
# Provisioning Workflow Control Endpoints
# ============================================================================

@router.post("/{provisioning_id}/start", response_model=ServiceProvisioning)
async def start_provisioning_workflow(
    provisioning_id: int,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Start a provisioning workflow"""
    factory = get_service_layer_factory(db)
    provisioning_service = factory.get_provisioning_service()
    
    try:
        provisioning = await provisioning_service.start_provisioning(
            provisioning_id=provisioning_id,
            admin_id=current_admin.id
        )
        if not provisioning:
            raise HTTPException(status_code=404, detail="Provisioning workflow not found")
        return provisioning
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start provisioning: {str(e)}")


@router.post("/{provisioning_id}/pause", response_model=ServiceProvisioning)
async def pause_provisioning_workflow(
    provisioning_id: int,
    reason: Optional[str] = Query(None, description="Reason for pausing"),
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Pause a provisioning workflow"""
    factory = get_service_layer_factory(db)
    provisioning_service = factory.get_provisioning_service()
    
    try:
        provisioning = await provisioning_service.pause_provisioning(
            provisioning_id=provisioning_id,
            reason=reason,
            admin_id=current_admin.id
        )
        if not provisioning:
            raise HTTPException(status_code=404, detail="Provisioning workflow not found")
        return provisioning
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to pause provisioning: {str(e)}")


@router.post("/{provisioning_id}/resume", response_model=ServiceProvisioning)
async def resume_provisioning_workflow(
    provisioning_id: int,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Resume a paused provisioning workflow"""
    factory = get_service_layer_factory(db)
    provisioning_service = factory.get_provisioning_service()
    
    try:
        provisioning = await provisioning_service.resume_provisioning(
            provisioning_id=provisioning_id,
            admin_id=current_admin.id
        )
        if not provisioning:
            raise HTTPException(status_code=404, detail="Provisioning workflow not found")
        return provisioning
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to resume provisioning: {str(e)}")


@router.post("/{provisioning_id}/cancel", response_model=ServiceProvisioning)
async def cancel_provisioning_workflow(
    provisioning_id: int,
    reason: str = Query(..., description="Reason for cancellation"),
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Cancel a provisioning workflow"""
    factory = get_service_layer_factory(db)
    provisioning_service = factory.get_provisioning_service()
    
    try:
        provisioning = await provisioning_service.cancel_provisioning(
            provisioning_id=provisioning_id,
            reason=reason,
            admin_id=current_admin.id
        )
        if not provisioning:
            raise HTTPException(status_code=404, detail="Provisioning workflow not found")
        return provisioning
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cancel provisioning: {str(e)}")


@router.post("/{provisioning_id}/retry", response_model=ServiceProvisioning)
async def retry_provisioning_workflow(
    provisioning_id: int,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Retry a failed provisioning workflow"""
    factory = get_service_layer_factory(db)
    provisioning_service = factory.get_provisioning_service()
    
    try:
        provisioning = await provisioning_service.retry_provisioning(
            provisioning_id=provisioning_id,
            admin_id=current_admin.id
        )
        if not provisioning:
            raise HTTPException(status_code=404, detail="Provisioning workflow not found")
        return provisioning
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retry provisioning: {str(e)}")


@router.post("/{provisioning_id}/rollback", response_model=ServiceProvisioning)
async def rollback_provisioning_workflow(
    provisioning_id: int,
    reason: str = Query(..., description="Reason for rollback"),
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Rollback a provisioning workflow"""
    factory = get_service_layer_factory(db)
    provisioning_service = factory.get_provisioning_service()
    
    try:
        provisioning = await provisioning_service.rollback_provisioning(
            provisioning_id=provisioning_id,
            reason=reason,
            admin_id=current_admin.id
        )
        if not provisioning:
            raise HTTPException(status_code=404, detail="Provisioning workflow not found")
        return provisioning
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to rollback provisioning: {str(e)}")


# ============================================================================
# Provisioning Template Endpoints
# ============================================================================

@router.post("/templates", response_model=ProvisioningTemplate, status_code=status.HTTP_201_CREATED)
async def create_provisioning_template(
    template_data: ProvisioningTemplateCreate,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Create a new provisioning template"""
    factory = get_service_layer_factory(db)
    template_service = factory.get_provisioning_template_service()
    
    try:
        template = await template_service.create_provisioning_template(
            template_data=template_data.dict(),
            admin_id=current_admin.id
        )
        return template
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create provisioning template: {str(e)}")


@router.get("/templates", response_model=List[ProvisioningTemplate])
async def list_provisioning_templates(
    service_type: Optional[ServiceType] = Query(None, description="Filter by service type"),
    automation_level: Optional[int] = Query(None, ge=1, le=5, description="Filter by automation level"),
    requires_approval: Optional[bool] = Query(None, description="Filter by approval requirement"),
    is_active: Optional[bool] = Query(True, description="Filter by active status"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """List provisioning templates with filtering"""
    factory = get_service_layer_factory(db)
    template_service = factory.get_provisioning_template_service()
    
    # Build filters
    filters = {}
    if service_type:
        filters['service_type'] = service_type
    if automation_level:
        filters['automation_level'] = automation_level
    if requires_approval is not None:
        filters['requires_approval'] = requires_approval
    if is_active is not None:
        filters['is_active'] = is_active
    
    try:
        templates, _ = await template_service.search_provisioning_templates(
            filters=filters,
            page=page,
            size=size
        )
        return templates
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list provisioning templates: {str(e)}")


@router.get("/templates/{template_id}", response_model=ProvisioningTemplate)
async def get_provisioning_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Get a specific provisioning template"""
    factory = get_service_layer_factory(db)
    template_service = factory.get_provisioning_template_service()
    
    try:
        template = await template_service.get_provisioning_template_by_id(template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Provisioning template not found")
        return template
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get provisioning template: {str(e)}")


@router.put("/templates/{template_id}", response_model=ProvisioningTemplate)
async def update_provisioning_template(
    template_id: int,
    template_data: ProvisioningTemplateUpdate,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Update a provisioning template"""
    factory = get_service_layer_factory(db)
    template_service = factory.get_provisioning_template_service()
    
    try:
        template = await template_service.update_provisioning_template(
            template_id=template_id,
            update_data=template_data.dict(exclude_unset=True),
            admin_id=current_admin.id
        )
        if not template:
            raise HTTPException(status_code=404, detail="Provisioning template not found")
        return template
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update provisioning template: {str(e)}")


@router.delete("/templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_provisioning_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Delete (deactivate) a provisioning template"""
    factory = get_service_layer_factory(db)
    template_service = factory.get_provisioning_template_service()
    
    try:
        success = await template_service.deactivate_provisioning_template(
            template_id=template_id,
            admin_id=current_admin.id
        )
        if not success:
            raise HTTPException(status_code=404, detail="Provisioning template not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete provisioning template: {str(e)}")


# ============================================================================
# Queue Management Endpoints
# ============================================================================

@router.get("/", response_model=List[ServiceProvisioning])
async def get_provisioning_queue(
    status: Optional[ProvisioningStatus] = Query(None, description="Filter by status"),
    priority_min: Optional[int] = Query(None, ge=1, le=10, description="Minimum priority"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of items"),
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Get provisioning queue with priority ordering"""
    factory = get_service_layer_factory(db)
    provisioning_service = factory.get_provisioning_service()
    
    try:
        queue_items = await provisioning_service.get_provisioning_queue(
            status=status,
            priority_min=priority_min,
            limit=limit
        )
        return queue_items
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get provisioning queue: {str(e)}")


@router.post("/queue/process", response_model=Dict[str, Any])
async def process_provisioning_queue(
    max_items: int = Query(10, ge=1, le=50, description="Maximum items to process"),
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Process items in the provisioning queue"""
    factory = get_service_layer_factory(db)
    provisioning_service = factory.get_provisioning_service()
    
    try:
        result = await provisioning_service.process_provisioning_queue(
            max_items=max_items,
            admin_id=current_admin.id
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process provisioning queue: {str(e)}")


@router.post("/{provisioning_id}/priority", response_model=ServiceProvisioning)
async def update_provisioning_priority(
    provisioning_id: int,
    priority: int = Query(..., ge=1, le=10, description="New priority (1=highest, 10=lowest)"),
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Update provisioning workflow priority"""
    factory = get_service_layer_factory(db)
    provisioning_service = factory.get_provisioning_service()
    
    try:
        provisioning = await provisioning_service.update_provisioning_priority(
            provisioning_id=provisioning_id,
            priority=priority,
            admin_id=current_admin.id
        )
        if not provisioning:
            raise HTTPException(status_code=404, detail="Provisioning workflow not found")
        return provisioning
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update priority: {str(e)}")


# ============================================================================
# Provisioning Statistics and Monitoring Endpoints
# ============================================================================

@router.get("/statistics", response_model=ProvisioningStatistics)
async def get_provisioning_statistics(
    service_type: Optional[ServiceType] = Query(None, description="Filter by service type"),
    days: int = Query(30, ge=1, le=365, description="Number of days for statistics"),
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Get provisioning statistics"""
    factory = get_service_layer_factory(db)
    provisioning_service = factory.get_provisioning_service()
    
    try:
        stats = await provisioning_service.get_provisioning_statistics(
            service_type=service_type,
            days=days
        )
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get provisioning statistics: {str(e)}")


@router.get("/{provisioning_id}/status-history", response_model=List[Dict[str, Any]])
async def get_provisioning_status_history(
    provisioning_id: int,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Get status history for a provisioning workflow"""
    factory = get_service_layer_factory(db)
    provisioning_service = factory.get_provisioning_service()
    
    try:
        history = await provisioning_service.get_provisioning_status_history(provisioning_id)
        if history is None:
            raise HTTPException(status_code=404, detail="Provisioning workflow not found")
        return history
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get status history: {str(e)}")


@router.get("/{provisioning_id}/tasks", response_model=List[Dict[str, Any]])
async def get_provisioning_tasks(
    provisioning_id: int,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Get tasks for a provisioning workflow"""
    factory = get_service_layer_factory(db)
    provisioning_service = factory.get_provisioning_service()
    
    try:
        tasks = await provisioning_service.get_provisioning_tasks(provisioning_id)
        if tasks is None:
            raise HTTPException(status_code=404, detail="Provisioning workflow not found")
        return tasks
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get provisioning tasks: {str(e)}")


# ============================================================================
# Bulk Provisioning Operations
# ============================================================================

@router.post("/bulk-create", response_model=BulkOperationResult)
async def bulk_create_provisioning(
    service_ids: List[int] = Query(..., description="List of service IDs to provision"),
    template_id: Optional[int] = Query(None, description="Provisioning template ID"),
    priority: int = Query(5, ge=1, le=10, description="Priority for all provisioning workflows"),
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Create provisioning workflows for multiple services"""
    factory = get_service_layer_factory(db)
    provisioning_service = factory.get_provisioning_service()
    
    try:
        result = await provisioning_service.bulk_create_provisioning(
            service_ids=service_ids,
            template_id=template_id,
            priority=priority,
            admin_id=current_admin.id
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to bulk create provisioning: {str(e)}")


@router.post("/bulk-start", response_model=BulkOperationResult)
async def bulk_start_provisioning(
    provisioning_ids: List[int] = Query(..., description="List of provisioning IDs to start"),
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Start multiple provisioning workflows"""
    factory = get_service_layer_factory(db)
    provisioning_service = factory.get_provisioning_service()
    
    try:
        result = await provisioning_service.bulk_start_provisioning(
            provisioning_ids=provisioning_ids,
            admin_id=current_admin.id
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to bulk start provisioning: {str(e)}")


# ============================================================================
# Template Validation and Testing Endpoints
# ============================================================================

@router.post("/templates/{template_id}/validate", response_model=Dict[str, Any])
async def validate_provisioning_template(
    template_id: int,
    test_configuration: Optional[Dict[str, Any]] = None,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Validate a provisioning template"""
    factory = get_service_layer_factory(db)
    template_service = factory.get_provisioning_template_service()
    
    try:
        validation_result = await template_service.validate_provisioning_template(
            template_id=template_id,
            test_configuration=test_configuration
        )
        return validation_result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to validate template: {str(e)}")


@router.post("/templates/{template_id}/test", response_model=Dict[str, Any])
async def test_provisioning_template(
    template_id: int,
    test_service_id: int = Query(..., description="Service ID to use for testing"),
    dry_run: bool = Query(True, description="Perform dry run without actual changes"),
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Test a provisioning template"""
    factory = get_service_layer_factory(db)
    template_service = factory.get_provisioning_template_service()
    
    try:
        test_result = await template_service.test_provisioning_template(
            template_id=template_id,
            test_service_id=test_service_id,
            dry_run=dry_run,
            admin_id=current_admin.id
        )
        return test_result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to test template: {str(e)}")


# ============================================================================
# Health Check and Monitoring Endpoints
# ============================================================================

@router.get("/health", response_model=Dict[str, Any], include_in_schema=False)
async def get_provisioning_health(
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Get provisioning system health status"""
    factory = get_service_layer_factory(db)
    provisioning_service = factory.get_provisioning_service()
    
    try:
        health_status = await provisioning_service.get_provisioning_health()
        return health_status
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get health status: {str(e)}")
