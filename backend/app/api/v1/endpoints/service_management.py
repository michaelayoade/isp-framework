"""
Service Management API Endpoints - ISP Service Management System

REST API endpoints for service lifecycle management including:
- Service IP assignments (IP allocation, MAC tracking, expiration)
- Service status history (audit trails, change tracking)
- Service suspensions (grace periods, escalation, restoration)
- Service usage tracking (bandwidth, sessions, quality metrics)
- Service alerts (real-time monitoring, severity management)

Provides comprehensive service lifecycle and operational management.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from ..dependencies import get_current_admin
from app.models.auth import Administrator
from app.schemas.service_management import (
    # Service IP Assignment Schemas
    ServiceIPAssignment, ServiceIPAssignmentCreate, ServiceStatusHistory, ServiceStatusHistoryCreate,
    
    # Service Suspension Schemas
    ServiceSuspension, ServiceSuspensionCreate, ServiceUsageTracking, ServiceUsageTrackingCreate,
    
    # Service Alert Schemas
    ServiceAlert, ServiceAlertCreate, ServiceDashboard
)
from app.services.service_layer_factory import get_service_layer_factory
from app.models.services.enums import (
    IPAssignmentType, SuspensionReason, AlertSeverity, AlertStatus,
    UsageMetricType, ServiceStatus
)

router = APIRouter()


# ============================================================================
# Service IP Assignment Endpoints
# ============================================================================

@router.post("/ip-assignments", response_model=ServiceIPAssignment, status_code=status.HTTP_201_CREATED)
async def create_ip_assignment(
    assignment_data: ServiceIPAssignmentCreate,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Create a new service IP assignment"""
    factory = get_service_layer_factory(db)
    ip_service = factory.get_ip_assignment_service()
    
    try:
        assignment = await ip_service.assign_ip_to_service(
            service_id=assignment_data.service_id,
            ip_address=assignment_data.ip_address,
            assignment_type=assignment_data.assignment_type,
            network_id=assignment_data.network_id,
            mac_address=assignment_data.mac_address,
            hostname=assignment_data.hostname,
            expires_at=assignment_data.expires_at,
            admin_id=current_admin.id
        )
        return assignment
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create IP assignment: {str(e)}")


@router.get("/ip-assignments", response_model=List[ServiceIPAssignment])
async def list_ip_assignments(
    service_id: Optional[int] = Query(None, description="Filter by service ID"),
    network_id: Optional[int] = Query(None, description="Filter by network ID"),
    assignment_type: Optional[IPAssignmentType] = Query(None, description="Filter by assignment type"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """List service IP assignments with filtering"""
    factory = get_service_layer_factory(db)
    ip_service = factory.get_ip_assignment_service()
    
    filters = {}
    if service_id:
        filters['service_id'] = service_id
    if network_id:
        filters['network_id'] = network_id
    if assignment_type:
        filters['assignment_type'] = assignment_type
    if is_active is not None:
        filters['is_active'] = is_active
    
    try:
        assignments, _ = await ip_service.search_ip_assignments(
            filters=filters, page=page, size=size
        )
        return assignments
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list IP assignments: {str(e)}")


@router.get("/ip-assignments/{assignment_id}", response_model=ServiceIPAssignment)
async def get_ip_assignment(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Get a specific service IP assignment"""
    factory = get_service_layer_factory(db)
    ip_service = factory.get_ip_assignment_service()
    
    try:
        assignment = await ip_service.get_ip_assignment_by_id(assignment_id)
        if not assignment:
            raise HTTPException(status_code=404, detail="IP assignment not found")
        return assignment
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get IP assignment: {str(e)}")


@router.delete("/ip-assignments/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def release_ip_assignment(
    assignment_id: int,
    reason: Optional[str] = Query(None, description="Reason for releasing IP"),
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Release a service IP assignment"""
    factory = get_service_layer_factory(db)
    ip_service = factory.get_ip_assignment_service()
    
    try:
        success = await ip_service.release_ip_assignment(
            assignment_id=assignment_id, reason=reason, admin_id=current_admin.id
        )
        if not success:
            raise HTTPException(status_code=404, detail="IP assignment not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to release IP assignment: {str(e)}")


# ============================================================================
# Service Status History Endpoints
# ============================================================================

@router.post("/status-history", response_model=ServiceStatusHistory, status_code=status.HTTP_201_CREATED)
async def create_status_history(
    history_data: ServiceStatusHistoryCreate,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Create a new service status history entry"""
    factory = get_service_layer_factory(db)
    history_service = factory.get_status_history_service()
    
    try:
        history = await history_service.record_status_change(
            service_id=history_data.service_id,
            previous_status=history_data.previous_status,
            new_status=history_data.new_status,
            reason=history_data.reason,
            is_automated=history_data.is_automated,
            admin_id=current_admin.id,
            additional_data=history_data.additional_data
        )
        return history
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create status history: {str(e)}")


@router.get("/status-history", response_model=List[ServiceStatusHistory])
async def list_status_history(
    service_id: Optional[int] = Query(None, description="Filter by service ID"),
    new_status: Optional[ServiceStatus] = Query(None, description="Filter by new status"),
    is_automated: Optional[bool] = Query(None, description="Filter by automation"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """List service status history with filtering"""
    factory = get_service_layer_factory(db)
    history_service = factory.get_status_history_service()
    
    filters = {}
    if service_id:
        filters['service_id'] = service_id
    if new_status:
        filters['new_status'] = new_status
    if is_automated is not None:
        filters['is_automated'] = is_automated
    
    try:
        history_list, _ = await history_service.search_status_history(
            filters=filters, page=page, size=size
        )
        return history_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list status history: {str(e)}")


# ============================================================================
# Service Suspension Endpoints
# ============================================================================

@router.post("/suspensions", response_model=ServiceSuspension, status_code=status.HTTP_201_CREATED)
async def create_service_suspension(
    suspension_data: ServiceSuspensionCreate,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Create a new service suspension"""
    factory = get_service_layer_factory(db)
    suspension_service = factory.get_suspension_service()
    
    try:
        suspension = await suspension_service.suspend_service(
            service_id=suspension_data.service_id,
            reason=suspension_data.reason,
            grace_period_hours=suspension_data.grace_period_hours,
            auto_restore_conditions=suspension_data.auto_restore_conditions,
            escalation_level=suspension_data.escalation_level,
            notes=suspension_data.notes,
            admin_id=current_admin.id
        )
        return suspension
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create suspension: {str(e)}")


@router.get("/suspensions", response_model=List[ServiceSuspension])
async def list_service_suspensions(
    service_id: Optional[int] = Query(None, description="Filter by service ID"),
    reason: Optional[SuspensionReason] = Query(None, description="Filter by suspension reason"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """List service suspensions with filtering"""
    factory = get_service_layer_factory(db)
    suspension_service = factory.get_suspension_service()
    
    filters = {}
    if service_id:
        filters['service_id'] = service_id
    if reason:
        filters['reason'] = reason
    if is_active is not None:
        filters['is_active'] = is_active
    
    try:
        suspensions, _ = await suspension_service.search_suspensions(
            filters=filters, page=page, size=size
        )
        return suspensions
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list suspensions: {str(e)}")


@router.post("/suspensions/{suspension_id}/restore", response_model=ServiceSuspension)
async def restore_service_suspension(
    suspension_id: int,
    reason: Optional[str] = Query(None, description="Reason for restoration"),
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Restore a suspended service"""
    factory = get_service_layer_factory(db)
    suspension_service = factory.get_suspension_service()
    
    try:
        suspension = await suspension_service.restore_service(
            suspension_id=suspension_id, reason=reason, admin_id=current_admin.id
        )
        if not suspension:
            raise HTTPException(status_code=404, detail="Suspension not found")
        return suspension
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to restore suspension: {str(e)}")


# ============================================================================
# Service Usage Tracking Endpoints
# ============================================================================

@router.post("/usage-tracking", response_model=ServiceUsageTracking, status_code=status.HTTP_201_CREATED)
async def create_usage_tracking(
    usage_data: ServiceUsageTrackingCreate,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Create a new service usage tracking entry"""
    factory = get_service_layer_factory(db)
    usage_service = factory.get_usage_tracking_service()
    
    try:
        usage = await usage_service.record_service_usage(
            service_id=usage_data.service_id,
            metric_type=usage_data.metric_type,
            value=usage_data.value,
            unit=usage_data.unit,
            recorded_at=usage_data.recorded_at,
            billing_period_start=usage_data.billing_period_start,
            billing_period_end=usage_data.billing_period_end,
            cost=usage_data.cost,
            quality_score=usage_data.quality_score
        )
        return usage
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create usage tracking: {str(e)}")


@router.get("/usage-tracking", response_model=List[ServiceUsageTracking])
async def list_usage_tracking(
    service_id: Optional[int] = Query(None, description="Filter by service ID"),
    metric_type: Optional[UsageMetricType] = Query(None, description="Filter by metric type"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """List service usage tracking with filtering"""
    factory = get_service_layer_factory(db)
    usage_service = factory.get_usage_tracking_service()
    
    filters = {}
    if service_id:
        filters['service_id'] = service_id
    if metric_type:
        filters['metric_type'] = metric_type
    
    try:
        usage_list, _ = await usage_service.search_usage_tracking(
            filters=filters, page=page, size=size
        )
        return usage_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list usage tracking: {str(e)}")


# ============================================================================
# Service Alert Endpoints
# ============================================================================

@router.post("/alerts", response_model=ServiceAlert, status_code=status.HTTP_201_CREATED)
async def create_service_alert(
    alert_data: ServiceAlertCreate,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Create a new service alert"""
    factory = get_service_layer_factory(db)
    alert_service = factory.get_alert_service()
    
    try:
        alert = await alert_service.create_service_alert(
            service_id=alert_data.service_id,
            alert_type=alert_data.alert_type,
            severity=alert_data.severity,
            message=alert_data.message,
            threshold_value=alert_data.threshold_value,
            current_value=alert_data.current_value,
            additional_data=alert_data.additional_data
        )
        return alert
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create alert: {str(e)}")


@router.get("/alerts", response_model=List[ServiceAlert])
async def list_service_alerts(
    service_id: Optional[int] = Query(None, description="Filter by service ID"),
    alert_type: Optional[str] = Query(None, description="Filter by alert type"),
    severity: Optional[AlertSeverity] = Query(None, description="Filter by severity"),
    status: Optional[AlertStatus] = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """List service alerts with filtering"""
    factory = get_service_layer_factory(db)
    alert_service = factory.get_alert_service()
    
    filters = {}
    if service_id:
        filters['service_id'] = service_id
    if alert_type:
        filters['alert_type'] = alert_type
    if severity:
        filters['severity'] = severity
    if status:
        filters['status'] = status
    
    try:
        alerts, _ = await alert_service.search_service_alerts(
            filters=filters, page=page, size=size
        )
        return alerts
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list alerts: {str(e)}")


@router.post("/alerts/{alert_id}/acknowledge", response_model=ServiceAlert)
async def acknowledge_service_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Acknowledge a service alert"""
    factory = get_service_layer_factory(db)
    alert_service = factory.get_alert_service()
    
    try:
        alert = await alert_service.acknowledge_alert(
            alert_id=alert_id, admin_id=current_admin.id
        )
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")
        return alert
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to acknowledge alert: {str(e)}")


@router.post("/alerts/{alert_id}/resolve", response_model=ServiceAlert)
async def resolve_service_alert(
    alert_id: int,
    resolution_notes: str = Query(..., description="Resolution notes"),
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Resolve a service alert"""
    factory = get_service_layer_factory(db)
    alert_service = factory.get_alert_service()
    
    try:
        alert = await alert_service.resolve_alert(
            alert_id=alert_id, resolution_notes=resolution_notes, admin_id=current_admin.id
        )
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")
        return alert
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to resolve alert: {str(e)}")


# ============================================================================
# Dashboard and Statistics Endpoints
# ============================================================================

@router.get("/dashboard", response_model=ServiceDashboard)
async def get_service_dashboard(
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Get comprehensive service management dashboard"""
    factory = get_service_layer_factory(db)
    
    try:
        # Get all service statistics
        service_service = factory.get_customer_service_service()
        service_stats = await service_service.get_service_statistics()
        
        # Get provisioning statistics
        provisioning_service = factory.get_provisioning_service()
        provisioning_stats = await provisioning_service.get_provisioning_statistics()
        
        # Get usage statistics
        usage_service = factory.get_usage_tracking_service()
        usage_stats = await usage_service.get_network_usage_statistics()
        
        # Get alert statistics
        alert_service = factory.get_alert_service()
        alert_stats = await alert_service.get_alert_statistics()
        
        # Get recent alerts
        recent_alerts, _ = await alert_service.search_service_alerts(
            filters={'status': AlertStatus.ACTIVE}, page=1, size=10
        )
        
        dashboard = ServiceDashboard(
            service_stats=service_stats,
            provisioning_stats=provisioning_stats,
            usage_stats=usage_stats,
            alert_stats=alert_stats,
            recent_alerts=recent_alerts,
            top_usage_services=[],  # Placeholder
            pending_provisioning=[]  # Placeholder
        )
        
        return dashboard
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard: {str(e)}")


@router.get("/statistics/overview", response_model=Dict[str, Any])
async def get_service_overview_statistics(
    days: int = Query(30, ge=1, le=365, description="Number of days for statistics"),
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Get service overview statistics"""
    factory = get_service_layer_factory(db)
    
    try:
        # Collect statistics from all services
        stats = {}
        
        # Service statistics
        service_service = factory.get_customer_service_service()
        stats['services'] = await service_service.get_service_statistics()
        
        # Usage statistics
        usage_service = factory.get_usage_tracking_service()
        stats['usage'] = await usage_service.get_network_usage_statistics(days=days)
        
        # Alert statistics
        alert_service = factory.get_alert_service()
        stats['alerts'] = await alert_service.get_alert_statistics(days=days)
        
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get overview statistics: {str(e)}")
