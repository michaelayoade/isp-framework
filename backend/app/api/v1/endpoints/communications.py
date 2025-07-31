"""
Communications API Endpoints for ISP Framework

REST API endpoints for communication templates, providers, sending communications,
managing preferences, and tracking delivery status.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from app.core.database import get_db
from app.api.dependencies import get_current_admin
from app.models.auth.base import Administrator
from app.models.communications import (
    CommunicationType,
    CommunicationStatus,
    TemplateCategory
)
from app.schemas.communications import (
    # Template schemas
    CommunicationTemplate,
    CommunicationTemplateCreate,
    CommunicationTemplateUpdate,
    PaginatedTemplates,
    TemplateTestRequest,
    TemplateTestResponse,
    
    # Provider schemas
    CommunicationProvider,
    CommunicationProviderCreate,
    CommunicationProviderUpdate,
    PaginatedProviders,
    CommunicationLog,
    SendCommunicationRequest,
    SendCommunicationResponse,
    BulkCommunicationRequest,
    BulkCommunicationResponse,
    PaginatedCommunicationLogs,
    CommunicationStatsResponse,
    
    # Queue schemas
    CommunicationQueue,
    PaginatedQueues,
    
    # Preference schemas
    CommunicationPreference,
    CommunicationPreferenceUpdate
)
from app.services.communications_service import (
    TemplateService,
    ProviderService,
    CommunicationService,
    PreferenceService
)

router = APIRouter()


# Template Management Endpoints
@router.post("/templates", response_model=CommunicationTemplate)
async def create_template(
    template_data: CommunicationTemplateCreate,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Create a new communication template"""
    template_service = TemplateService(db)
    try:
        return template_service.create_template(template_data, current_admin.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/templates", response_model=PaginatedTemplates)
async def get_templates(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    category: Optional[TemplateCategory] = None,
    communication_type: Optional[CommunicationType] = None,
    is_active: Optional[bool] = None,
    search_term: Optional[str] = None,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Get communication templates with filtering and pagination"""
    template_service = TemplateService(db)
    skip = (page - 1) * size
    
    templates, total = template_service.get_templates(
        skip=skip,
        limit=size,
        category=category,
        communication_type=communication_type,
        is_active=is_active,
        search_term=search_term
    )
    
    return PaginatedTemplates(
        items=templates,
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size
    )


@router.get("/templates/{template_id}", response_model=CommunicationTemplate)
async def get_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Get a specific communication template"""
    template_service = TemplateService(db)
    template = template_service.get_template(template_id)
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    return template


@router.put("/templates/{template_id}", response_model=CommunicationTemplate)
async def update_template(
    template_id: int,
    template_data: CommunicationTemplateUpdate,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Update a communication template"""
    template_service = TemplateService(db)
    
    try:
        template = template_service.update_template(template_id, template_data)
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        return template
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/templates/{template_id}")
async def delete_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Delete a communication template"""
    template_service = TemplateService(db)
    
    try:
        success = template_service.delete_template(template_id)
        if not success:
            raise HTTPException(status_code=404, detail="Template not found")
        return {"message": "Template deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/templates/{template_id}/test", response_model=TemplateTestResponse)
async def test_template(
    template_id: int,
    test_request: TemplateTestRequest,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Test a communication template with sample data"""
    template_service = TemplateService(db)
    
    try:
        rendered = template_service.render_template(template_id, test_request.test_variables)
        
        return TemplateTestResponse(
            rendered_subject=rendered.get('subject'),
            rendered_body=rendered['body'],
            rendered_html=rendered.get('html_body'),
            validation_errors=[],
            missing_variables=[]
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# Provider Management Endpoints
@router.post("/providers", response_model=CommunicationProvider)
async def create_provider(
    provider_data: CommunicationProviderCreate,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Create a new communication provider"""
    provider_service = ProviderService(db)
    return provider_service.create_provider(provider_data)


@router.get("/providers", response_model=PaginatedProviders)
async def get_providers(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    provider_type: Optional[CommunicationType] = None,
    is_active: Optional[bool] = None,
    search_term: Optional[str] = None,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Get communication providers with filtering and pagination"""
    provider_service = ProviderService(db)
    skip = (page - 1) * size
    
    providers, total = provider_service.get_providers(
        skip=skip,
        limit=size,
        provider_type=provider_type,
        is_active=is_active,
        search_term=search_term
    )
    
    return PaginatedProviders(
        items=providers,
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size
    )


@router.get("/providers/{provider_id}", response_model=CommunicationProvider)
async def get_provider(
    provider_id: int,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Get a specific communication provider"""
    provider_service = ProviderService(db)
    provider = provider_service.get_provider(provider_id)
    
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    
    return provider


@router.put("/providers/{provider_id}", response_model=CommunicationProvider)
async def update_provider(
    provider_id: int,
    provider_data: CommunicationProviderUpdate,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Update a communication provider"""
    provider_service = ProviderService(db)
    
    provider = provider_service.update_provider(provider_id, provider_data)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    
    return provider


@router.delete("/providers/{provider_id}")
async def delete_provider(
    provider_id: int,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Delete a communication provider"""
    provider_service = ProviderService(db)
    
    try:
        success = provider_service.delete_provider(provider_id)
        if not success:
            raise HTTPException(status_code=404, detail="Provider not found")
        return {"message": "Provider deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# Communication Sending Endpoints
@router.post("/send", response_model=SendCommunicationResponse)
async def send_communication(
    request: SendCommunicationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Send a single communication"""
    communication_service = CommunicationService(db)
    
    try:
        comm_log = communication_service.send_communication(request, current_admin.id)
        
        return SendCommunicationResponse(
            communication_id=comm_log.id,
            status=comm_log.status,
            message="Communication sent successfully",
            provider_message_id=comm_log.provider_message_id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/send-bulk", response_model=BulkCommunicationResponse)
async def send_bulk_communication(
    request: BulkCommunicationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Send bulk communications"""
    communication_service = CommunicationService(db)
    
    try:
        queue = communication_service.send_bulk_communication(request, current_admin.id)
        
        return BulkCommunicationResponse(
            queue_id=queue.id,
            total_recipients=queue.total_recipients,
            status=queue.status,
            message="Bulk communication queued successfully"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# Communication Logs and Tracking
@router.get("/logs", response_model=PaginatedCommunicationLogs)
async def get_communication_logs(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    communication_type: Optional[CommunicationType] = None,
    status: Optional[CommunicationStatus] = None,
    customer_id: Optional[int] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Get communication logs with filtering and pagination"""
    communication_service = CommunicationService(db)
    skip = (page - 1) * size
    
    logs, total = communication_service.get_communication_logs(
        skip=skip,
        limit=size,
        communication_type=communication_type,
        status=status,
        customer_id=customer_id,
        date_from=date_from,
        date_to=date_to
    )
    
    return PaginatedCommunicationLogs(
        items=logs,
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size
    )


@router.get("/logs/{log_id}", response_model=CommunicationLog)
async def get_communication_log(
    log_id: int,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Get a specific communication log"""
    communication_service = CommunicationService(db)
    log = communication_service.get_communication_log(log_id)
    
    if not log:
        raise HTTPException(status_code=404, detail="Communication log not found")
    
    return log


@router.post("/logs/{log_id}/retry")
async def retry_communication(
    log_id: int,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Retry a failed communication"""
    communication_service = CommunicationService(db)
    
    success = communication_service.retry_failed_communication(log_id)
    if not success:
        raise HTTPException(
            status_code=400,
            detail="Communication cannot be retried (not found, not failed, or max retries reached)"
        )
    
    return {"message": "Communication retry initiated"}


# Statistics and Analytics
@router.get("/stats", response_model=CommunicationStatsResponse)
async def get_communication_stats(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Get communication statistics"""
    communication_service = CommunicationService(db)
    stats = communication_service.get_communication_stats(days)
    
    return CommunicationStatsResponse(**stats)


# Queue Management
@router.get("/queues", response_model=PaginatedQueues)
async def get_communication_queues(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Get communication queues with filtering and pagination"""
    from app.models.communications import CommunicationQueue
    
    query = db.query(CommunicationQueue)
    
    if status:
        query = query.filter(CommunicationQueue.status == status)
    
    total = query.count()
    skip = (page - 1) * size
    queues = query.order_by(CommunicationQueue.created_at.desc()).offset(skip).limit(size).all()
    
    return PaginatedQueues(
        items=queues,
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size
    )


@router.get("/queues/{queue_id}", response_model=CommunicationQueue)
async def get_communication_queue(
    queue_id: int,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Get a specific communication queue"""
    from app.models.communications import CommunicationQueue
    
    queue = db.query(CommunicationQueue).filter(CommunicationQueue.id == queue_id).first()
    
    if not queue:
        raise HTTPException(status_code=404, detail="Communication queue not found")
    
    return queue


# Customer Preferences Management
@router.get("/preferences/{customer_id}", response_model=CommunicationPreference)
async def get_customer_preferences(
    customer_id: int,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Get customer communication preferences"""
    preference_service = PreferenceService(db)
    preferences = preference_service.get_customer_preferences(customer_id)
    
    if not preferences:
        raise HTTPException(status_code=404, detail="Customer preferences not found")
    
    return preferences


@router.put("/preferences/{customer_id}", response_model=CommunicationPreference)
async def update_customer_preferences(
    customer_id: int,
    preferences_data: CommunicationPreferenceUpdate,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Update customer communication preferences"""
    preference_service = PreferenceService(db)
    
    preferences = preference_service.create_or_update_preferences(customer_id, preferences_data)
    return preferences


# System Templates Management
@router.get("/system-templates")
async def get_system_templates(
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Get available system templates"""
    template_service = TemplateService(db)
    
    templates, _ = template_service.get_templates(
        skip=0,
        limit=1000,
        is_active=True
    )
    
    # Group by category
    by_category = {}
    for template in templates:
        category = template.category.value
        if category not in by_category:
            by_category[category] = []
        
        by_category[category].append({
            "id": template.id,
            "name": template.name,
            "communication_type": template.communication_type.value,
            "description": template.description,
            "required_variables": template.required_variables,
            "optional_variables": template.optional_variables
        })
    
    return by_category


# Health Check
@router.get("/health", include_in_schema=False)
async def health_check(
    db: Session = Depends(get_db)
):
    """Health check for communications module"""
    try:
        # Check database connectivity
        db.execute("SELECT 1")
        
        # Check provider availability
        provider_service = ProviderService(db)
        email_provider = provider_service.get_default_provider(CommunicationType.EMAIL)
        sms_provider = provider_service.get_default_provider(CommunicationType.SMS)
        
        return {
            "status": "healthy",
            "database": "connected",
            "providers": {
                "email": "available" if email_provider else "not_configured",
                "sms": "available" if sms_provider else "not_configured"
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")


# Dashboard Summary
@router.get("/dashboard")
async def get_communications_dashboard(
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Get communications dashboard summary"""
    communication_service = CommunicationService(db)
    template_service = TemplateService(db)
    provider_service = ProviderService(db)
    
    # Get basic stats
    stats = communication_service.get_communication_stats(days=7)
    
    # Get template counts
    templates, template_total = template_service.get_templates(skip=0, limit=1)
    active_templates, _ = template_service.get_templates(skip=0, limit=1, is_active=True)
    
    # Get provider counts
    providers, provider_total = provider_service.get_providers(skip=0, limit=1)
    active_providers, _ = provider_service.get_providers(skip=0, limit=1, is_active=True)
    
    # Get pending communications
    from app.models.communications import CommunicationLog
    pending_count = db.query(CommunicationLog).filter(
        CommunicationLog.status.in_([
            CommunicationStatus.PENDING,
            CommunicationStatus.QUEUED,
            CommunicationStatus.SENDING
        ])
    ).count()
    
    return {
        "stats": stats,
        "templates": {
            "total": template_total,
            "active": len(active_templates)
        },
        "providers": {
            "total": provider_total,
            "active": len(active_providers)
        },
        "pending_communications": pending_count,
        "last_updated": datetime.now().isoformat()
    }
