"""
Webhook API Endpoints

Complete REST API for webhook system management including endpoints, events,
deliveries, and testing functionality.
"""

import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_admin_user
from app.models.webhooks.enums import DeliveryStatus, EventCategory, WebhookStatus
from app.schemas.webhooks import (  # Event Types; Endpoints; Events; Deliveries; Filters; Testing; Statistics
    PaginatedWebhookDeliveries,
    PaginatedWebhookEndpoints,
    PaginatedWebhookEvents,
    WebhookDeliveryAttemptResponse,
    WebhookDeliveryResponse,
    WebhookDeliverySearch,
    WebhookEndpointCreate,
    WebhookEndpointResponse,
    WebhookEndpointSearch,
    WebhookEndpointStats,
    WebhookEndpointUpdate,
    WebhookEventCreate,
    WebhookEventResponse,
    WebhookEventSearch,
    WebhookEventTypeCreate,
    WebhookEventTypeResponse,
    WebhookEventTypeUpdate,
    WebhookFilterCreate,
    WebhookFilterResponse,
    WebhookSystemStats,
    WebhookTestRequest,
    WebhookTestResponse,
)
from app.services.webhook_service import (
    WebhookDeliveryEngine,
    WebhookDeliveryService,
    WebhookEndpointService,
    WebhookEventService,
    WebhookEventTypeService,
    WebhookFilterService,
    WebhookTestService,
)

logger = logging.getLogger(__name__)
router = APIRouter()


# Event Type Management
@router.post("/event-types", response_model=WebhookEventTypeResponse)
async def create_event_type(
    event_type_data: WebhookEventTypeCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_admin_user),
):
    """Create a new webhook event type"""
    service = WebhookEventTypeService(db)

    # Check if event type already exists
    existing = service.get_event_type_by_name(event_type_data.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Event type '{event_type_data.name}' already exists",
        )

    return service.create_event_type(event_type_data.dict())


@router.get("/event-types", response_model=List[WebhookEventTypeResponse])
async def list_event_types(
    category: Optional[EventCategory] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_admin_user),
):
    """List all webhook event types"""
    service = WebhookEventTypeService(db)
    return service.list_event_types(category=category, is_active=is_active)


@router.get("/event-types/{event_type_id}", response_model=WebhookEventTypeResponse)
async def get_event_type(
    event_type_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_admin_user),
):
    """Get webhook event type by ID"""
    service = WebhookEventTypeService(db)
    event_type = service.get_event_type(event_type_id)

    if not event_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Event type not found"
        )

    return event_type


@router.put("/event-types/{event_type_id}", response_model=WebhookEventTypeResponse)
async def update_event_type(
    event_type_id: int,
    updates: WebhookEventTypeUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_admin_user),
):
    """Update webhook event type"""
    service = WebhookEventTypeService(db)

    event_type = service.update_event_type(
        event_type_id, updates.dict(exclude_unset=True)
    )
    if not event_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Event type not found"
        )

    return event_type


@router.delete("/event-types/{event_type_id}")
async def delete_event_type(
    event_type_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_admin_user),
):
    """Delete webhook event type"""
    service = WebhookEventTypeService(db)

    if not service.delete_event_type(event_type_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Event type not found"
        )

    return {"message": "Event type deleted successfully"}


# Webhook Endpoint Management
@router.post("/endpoints", response_model=WebhookEndpointResponse)
async def create_webhook_endpoint(
    endpoint_data: WebhookEndpointCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_admin_user),
):
    """Create a new webhook endpoint"""
    service = WebhookEndpointService(db)
    return service.create_endpoint(endpoint_data, current_user["user_id"])


@router.get("/endpoints", response_model=PaginatedWebhookEndpoints)
async def search_webhook_endpoints(
    name: Optional[str] = None,
    status: Optional[WebhookStatus] = None,
    is_active: Optional[bool] = None,
    url_contains: Optional[str] = None,
    created_after: Optional[datetime] = None,
    created_before: Optional[datetime] = None,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_admin_user),
):
    """Search webhook endpoints with pagination"""
    service = WebhookEndpointService(db)

    search_params = WebhookEndpointSearch(
        name=name,
        status=status,
        is_active=is_active,
        url_contains=url_contains,
        created_after=created_after,
        created_before=created_before,
    )

    skip = (page - 1) * size
    endpoints, total = service.search_endpoints(search_params, skip=skip, limit=size)

    return PaginatedWebhookEndpoints(
        items=endpoints,
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size,
    )


@router.get("/endpoints/{endpoint_id}", response_model=WebhookEndpointResponse)
async def get_webhook_endpoint(
    endpoint_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_admin_user),
):
    """Get webhook endpoint by ID"""
    service = WebhookEndpointService(db)
    endpoint = service.get_endpoint(endpoint_id)

    if not endpoint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Webhook endpoint not found"
        )

    return endpoint


@router.put("/endpoints/{endpoint_id}", response_model=WebhookEndpointResponse)
async def update_webhook_endpoint(
    endpoint_id: int,
    updates: WebhookEndpointUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_admin_user),
):
    """Update webhook endpoint"""
    service = WebhookEndpointService(db)

    endpoint = service.update_endpoint(endpoint_id, updates)
    if not endpoint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Webhook endpoint not found"
        )

    return endpoint


@router.delete("/endpoints/{endpoint_id}")
async def delete_webhook_endpoint(
    endpoint_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_admin_user),
):
    """Delete webhook endpoint"""
    service = WebhookEndpointService(db)

    if not service.delete_endpoint(endpoint_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Webhook endpoint not found"
        )

    return {"message": "Webhook endpoint deleted successfully"}


# Webhook Event Management
@router.post("/events", response_model=WebhookEventResponse)
async def create_webhook_event(
    event_data: WebhookEventCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_admin_user),
):
    """Create a new webhook event and trigger deliveries"""
    service = WebhookEventService(db)
    event = service.create_event(event_data)

    # Process event in background
    background_tasks.add_task(process_webhook_event, event.id, db)

    return event


@router.get("/events", response_model=PaginatedWebhookEvents)
async def search_webhook_events(
    event_type_id: Optional[int] = None,
    category: Optional[EventCategory] = None,
    is_processed: Optional[bool] = None,
    occurred_after: Optional[datetime] = None,
    occurred_before: Optional[datetime] = None,
    triggered_by_user_id: Optional[int] = None,
    triggered_by_customer_id: Optional[int] = None,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_admin_user),
):
    """Search webhook events with pagination"""
    service = WebhookEventService(db)

    search_params = WebhookEventSearch(
        event_type_id=event_type_id,
        category=category,
        is_processed=is_processed,
        occurred_after=occurred_after,
        occurred_before=occurred_before,
        triggered_by_user_id=triggered_by_user_id,
        triggered_by_customer_id=triggered_by_customer_id,
    )

    skip = (page - 1) * size
    events, total = service.search_events(search_params, skip=skip, limit=size)

    return PaginatedWebhookEvents(
        items=events,
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size,
    )


@router.get("/events/{event_id}", response_model=WebhookEventResponse)
async def get_webhook_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_admin_user),
):
    """Get webhook event by ID"""
    service = WebhookEventService(db)
    event = service.get_event(event_id)

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Webhook event not found"
        )

    return event


# Webhook Delivery Management
@router.get("/deliveries", response_model=PaginatedWebhookDeliveries)
async def search_webhook_deliveries(
    endpoint_id: Optional[int] = None,
    event_id: Optional[int] = None,
    status: Optional[DeliveryStatus] = None,
    scheduled_after: Optional[datetime] = None,
    scheduled_before: Optional[datetime] = None,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_admin_user),
):
    """Search webhook deliveries with pagination"""
    service = WebhookDeliveryService(db)

    search_params = WebhookDeliverySearch(
        endpoint_id=endpoint_id,
        event_id=event_id,
        status=status,
        scheduled_after=scheduled_after,
        scheduled_before=scheduled_before,
    )

    skip = (page - 1) * size
    deliveries, total = service.search_deliveries(search_params, skip=skip, limit=size)

    return PaginatedWebhookDeliveries(
        items=deliveries,
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size,
    )


@router.get("/deliveries/{delivery_id}", response_model=WebhookDeliveryResponse)
async def get_webhook_delivery(
    delivery_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_admin_user),
):
    """Get webhook delivery by ID"""
    service = WebhookDeliveryService(db)
    delivery = service.get_delivery(delivery_id)

    if not delivery:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Webhook delivery not found"
        )

    return delivery


@router.get(
    "/deliveries/{delivery_id}/attempts",
    response_model=List[WebhookDeliveryAttemptResponse],
)
async def get_delivery_attempts(
    delivery_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_admin_user),
):
    """Get all delivery attempts for a delivery"""
    service = WebhookDeliveryService(db)
    delivery = service.get_delivery(delivery_id)

    if not delivery:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Webhook delivery not found"
        )

    return delivery.attempts


@router.post("/deliveries/{delivery_id}/retry")
async def retry_webhook_delivery(
    delivery_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_admin_user),
):
    """Manually retry a failed webhook delivery"""
    service = WebhookDeliveryService(db)
    delivery = service.get_delivery(delivery_id)

    if not delivery:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Webhook delivery not found"
        )

    if delivery.status not in [DeliveryStatus.FAILED, DeliveryStatus.ABANDONED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only retry failed or abandoned deliveries",
        )

    # Reset delivery for retry
    delivery.status = DeliveryStatus.PENDING
    delivery.next_retry_at = None
    db.commit()

    # Process delivery in background
    background_tasks.add_task(process_single_delivery, delivery_id, db)

    return {"message": "Delivery retry initiated"}


# Webhook Filter Management
@router.post("/endpoints/{endpoint_id}/filters", response_model=WebhookFilterResponse)
async def create_webhook_filter(
    endpoint_id: int,
    filter_data: WebhookFilterCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_admin_user),
):
    """Create a new webhook filter for an endpoint"""
    # Verify endpoint exists
    endpoint_service = WebhookEndpointService(db)
    if not endpoint_service.get_endpoint(endpoint_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Webhook endpoint not found"
        )

    filter_service = WebhookFilterService(db)
    return filter_service.create_filter(endpoint_id, filter_data)


@router.get(
    "/endpoints/{endpoint_id}/filters", response_model=List[WebhookFilterResponse]
)
async def get_endpoint_filters(
    endpoint_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_admin_user),
):
    """Get all filters for an endpoint"""
    filter_service = WebhookFilterService(db)
    return filter_service.get_filters_for_endpoint(endpoint_id)


# Webhook Testing
@router.post("/test", response_model=WebhookTestResponse)
async def test_webhook_endpoint(
    test_request: WebhookTestRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_admin_user),
):
    """Test a webhook endpoint with sample payload"""
    service = WebhookTestService(db)
    result = await service.test_endpoint(test_request)
    return WebhookTestResponse(**result)


# Statistics and Monitoring
@router.get("/stats", response_model=WebhookSystemStats)
async def get_webhook_system_stats(
    db: Session = Depends(get_db), current_user: dict = Depends(get_current_admin_user)
):
    """Get overall webhook system statistics"""
    from datetime import date

    from sqlalchemy import and_, func

    from app.models.webhooks.models import (
        WebhookDelivery,
        WebhookEndpoint,
        WebhookEvent,
        WebhookEventType,
    )

    today = date.today()

    # Basic counts
    total_endpoints = db.query(func.count(WebhookEndpoint.id)).scalar()
    active_endpoints = (
        db.query(func.count(WebhookEndpoint.id))
        .filter(
            and_(
                WebhookEndpoint.is_active is True,
                WebhookEndpoint.status == WebhookStatus.ACTIVE,
            )
        )
        .scalar()
    )
    total_event_types = db.query(func.count(WebhookEventType.id)).scalar()

    # Today's stats
    total_events_today = (
        db.query(func.count(WebhookEvent.id))
        .filter(func.date(WebhookEvent.occurred_at) == today)
        .scalar()
    )

    total_deliveries_today = (
        db.query(func.count(WebhookDelivery.id))
        .filter(func.date(WebhookDelivery.scheduled_at) == today)
        .scalar()
    )

    successful_deliveries_today = (
        db.query(func.count(WebhookDelivery.id))
        .filter(
            and_(
                func.date(WebhookDelivery.scheduled_at) == today,
                WebhookDelivery.status == DeliveryStatus.DELIVERED,
            )
        )
        .scalar()
    )

    failed_deliveries_today = (
        db.query(func.count(WebhookDelivery.id))
        .filter(
            and_(
                func.date(WebhookDelivery.scheduled_at) == today,
                WebhookDelivery.status == DeliveryStatus.FAILED,
            )
        )
        .scalar()
    )

    # Success rate
    total_all_deliveries = db.query(func.count(WebhookDelivery.id)).scalar()
    successful_all_deliveries = (
        db.query(func.count(WebhookDelivery.id))
        .filter(WebhookDelivery.status == DeliveryStatus.DELIVERED)
        .scalar()
    )

    average_success_rate = (
        (successful_all_deliveries / total_all_deliveries * 100)
        if total_all_deliveries > 0
        else 0
    )

    # Events by category
    events_by_category = {}
    category_stats = (
        db.query(WebhookEventType.category, func.count(WebhookEvent.id))
        .join(WebhookEvent)
        .group_by(WebhookEventType.category)
        .all()
    )

    for category, count in category_stats:
        events_by_category[category.value] = count

    # Top endpoints
    top_endpoints_query = (
        db.query(WebhookEndpoint)
        .order_by(desc(WebhookEndpoint.total_deliveries))
        .limit(5)
        .all()
    )

    top_endpoints = []
    for endpoint in top_endpoints_query:
        success_rate = (
            (endpoint.successful_deliveries / endpoint.total_deliveries * 100)
            if endpoint.total_deliveries > 0
            else 0
        )
        top_endpoints.append(
            WebhookEndpointStats(
                endpoint_id=endpoint.id,
                endpoint_name=endpoint.name,
                total_deliveries=endpoint.total_deliveries,
                successful_deliveries=endpoint.successful_deliveries,
                failed_deliveries=endpoint.failed_deliveries,
                success_rate=success_rate,
                last_delivery_at=endpoint.last_delivery_at,
                last_success_at=endpoint.last_success_at,
                last_failure_at=endpoint.last_failure_at,
            )
        )

    return WebhookSystemStats(
        total_endpoints=total_endpoints,
        active_endpoints=active_endpoints,
        total_event_types=total_event_types,
        total_events_today=total_events_today,
        total_deliveries_today=total_deliveries_today,
        successful_deliveries_today=successful_deliveries_today,
        failed_deliveries_today=failed_deliveries_today,
        average_success_rate=average_success_rate,
        events_by_category=events_by_category,
        top_endpoints=top_endpoints,
    )


@router.get("/endpoints/{endpoint_id}/stats", response_model=WebhookEndpointStats)
async def get_endpoint_stats(
    endpoint_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_admin_user),
):
    """Get statistics for a specific endpoint"""
    service = WebhookEndpointService(db)
    endpoint = service.get_endpoint(endpoint_id)

    if not endpoint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Webhook endpoint not found"
        )

    # Calculate average response time
    from sqlalchemy import and_, func

    from app.models.webhooks.models import WebhookDelivery

    avg_response_time = (
        db.query(func.avg(WebhookDelivery.response_time_ms))
        .filter(
            and_(
                WebhookDelivery.endpoint_id == endpoint_id,
                WebhookDelivery.response_time_ms.isnot(None),
            )
        )
        .scalar()
    )

    success_rate = (
        (endpoint.successful_deliveries / endpoint.total_deliveries * 100)
        if endpoint.total_deliveries > 0
        else 0
    )

    return WebhookEndpointStats(
        endpoint_id=endpoint.id,
        endpoint_name=endpoint.name,
        total_deliveries=endpoint.total_deliveries,
        successful_deliveries=endpoint.successful_deliveries,
        failed_deliveries=endpoint.failed_deliveries,
        success_rate=success_rate,
        average_response_time_ms=avg_response_time,
        last_delivery_at=endpoint.last_delivery_at,
        last_success_at=endpoint.last_success_at,
        last_failure_at=endpoint.last_failure_at,
    )


# Background Tasks
async def process_webhook_event(event_id: int, db: Session):
    """Background task to process webhook event"""
    try:
        engine = WebhookDeliveryEngine(db)
        event_service = WebhookEventService(db)

        event = event_service.get_event(event_id)
        if not event:
            return

        # Create deliveries for subscribed endpoints
        deliveries = await engine.process_event(event)

        # Mark event as processed
        event_service.mark_event_processed(event_id)

        # Process deliveries
        for delivery in deliveries:
            await engine.deliver_webhook(delivery)

    except Exception as e:
        logger.error(f"Error processing webhook event {event_id}: {e}")


async def process_single_delivery(delivery_id: int, db: Session):
    """Background task to process single delivery"""
    try:
        engine = WebhookDeliveryEngine(db)
        delivery_service = WebhookDeliveryService(db)

        delivery = delivery_service.get_delivery(delivery_id)
        if not delivery:
            return

        await engine.deliver_webhook(delivery)

    except Exception as e:
        logger.error(f"Error processing webhook delivery {delivery_id}: {e}")


# Periodic cleanup and retry task
@router.post("/admin/process-pending")
async def process_pending_deliveries(
    background_tasks: BackgroundTasks,
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_admin_user),
):
    """Manually trigger processing of pending deliveries"""
    service = WebhookDeliveryService(db)
    pending_deliveries = service.get_pending_deliveries(limit=limit)

    for delivery in pending_deliveries:
        background_tasks.add_task(process_single_delivery, delivery.id, db)

    return {
        "message": f"Processing {len(pending_deliveries)} pending deliveries",
        "count": len(pending_deliveries),
    }


# ============================================================================
# Backward Compatibility Redirects (Temporary - Remove after 6 months)
# ============================================================================


# Redirect old /webhooks/* paths to new /integrations/webhooks/* paths
@router.get("/{path:path}")
async def redirect_old_webhooks_get(path: str):
    """Temporary redirect for old /webhooks/* paths"""
    new_path = f"/api/v1/integrations/webhooks/{path}"
    return RedirectResponse(url=new_path, status_code=307)


@router.post("/{path:path}")
async def redirect_old_webhooks_post(path: str):
    """Temporary redirect for old /webhooks/* paths"""
    new_path = f"/api/v1/integrations/webhooks/{path}"
    return RedirectResponse(url=new_path, status_code=307)


@router.put("/{path:path}")
async def redirect_old_webhooks_put(path: str):
    """Temporary redirect for old /webhooks/* paths"""
    new_path = f"/api/v1/integrations/webhooks/{path}"
    return RedirectResponse(url=new_path, status_code=307)


@router.patch("/{path:path}")
async def redirect_old_webhooks_patch(path: str):
    """Temporary redirect for old /webhooks/* paths"""
    new_path = f"/api/v1/integrations/webhooks/{path}"
    return RedirectResponse(url=new_path, status_code=307)


@router.delete("/{path:path}")
async def redirect_old_webhooks_delete(path: str):
    """Temporary redirect for old /webhooks/* paths"""
    new_path = f"/api/v1/integrations/webhooks/{path}"
    return RedirectResponse(url=new_path, status_code=307)
