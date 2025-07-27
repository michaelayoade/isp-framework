"""
Webhook Service Layer

Business logic for webhook system including event processing, delivery management,
and endpoint configuration.
"""

import asyncio
import hashlib
import hmac
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc, func
import httpx
import uuid

from app.models.webhooks.models import (
    WebhookEndpoint, WebhookEvent, WebhookDelivery, WebhookEventType,
    WebhookFilter, WebhookSecret, WebhookDeliveryAttempt
)
from app.models.webhooks.enums import (
    WebhookStatus, DeliveryStatus, FilterOperator, RetryStrategy,
    SignatureAlgorithm
)
from app.schemas.webhooks import (
    WebhookEndpointCreate, WebhookEndpointUpdate, WebhookEndpointSearch,
    WebhookEventCreate, WebhookEventSearch, WebhookDeliverySearch,
    WebhookFilterCreate, WebhookFilterUpdate, WebhookTestRequest
)

logger = logging.getLogger(__name__)


class WebhookEventTypeService:
    """Service for managing webhook event types"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_event_type(self, event_type_data: dict) -> WebhookEventType:
        """Create a new webhook event type"""
        event_type = WebhookEventType(**event_type_data)
        self.db.add(event_type)
        self.db.commit()
        self.db.refresh(event_type)
        return event_type
    
    def get_event_type(self, event_type_id: int) -> Optional[WebhookEventType]:
        """Get webhook event type by ID"""
        return self.db.query(WebhookEventType).filter(
            WebhookEventType.id == event_type_id
        ).first()
    
    def get_event_type_by_name(self, name: str) -> Optional[WebhookEventType]:
        """Get webhook event type by name"""
        return self.db.query(WebhookEventType).filter(
            WebhookEventType.name == name
        ).first()
    
    def list_event_types(self, category: Optional[str] = None, is_active: Optional[bool] = None) -> List[WebhookEventType]:
        """List webhook event types with optional filtering"""
        query = self.db.query(WebhookEventType)
        
        if category:
            query = query.filter(WebhookEventType.category == category)
        if is_active is not None:
            query = query.filter(WebhookEventType.is_active == is_active)
        
        return query.order_by(WebhookEventType.category, WebhookEventType.name).all()
    
    def update_event_type(self, event_type_id: int, updates: dict) -> Optional[WebhookEventType]:
        """Update webhook event type"""
        event_type = self.get_event_type(event_type_id)
        if not event_type:
            return None
        
        for key, value in updates.items():
            if hasattr(event_type, key):
                setattr(event_type, key, value)
        
        self.db.commit()
        self.db.refresh(event_type)
        return event_type
    
    def delete_event_type(self, event_type_id: int) -> bool:
        """Delete webhook event type"""
        event_type = self.get_event_type(event_type_id)
        if not event_type:
            return False
        
        self.db.delete(event_type)
        self.db.commit()
        return True


class WebhookEndpointService:
    """Service for managing webhook endpoints"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_endpoint(self, endpoint_data: WebhookEndpointCreate, created_by: int) -> WebhookEndpoint:
        """Create a new webhook endpoint"""
        endpoint_dict = endpoint_data.dict(exclude={'subscribed_event_ids'})
        endpoint_dict['created_by'] = created_by
        
        endpoint = WebhookEndpoint(**endpoint_dict)
        self.db.add(endpoint)
        self.db.flush()  # Get the ID
        
        # Subscribe to events
        if endpoint_data.subscribed_event_ids:
            for event_type_id in endpoint_data.subscribed_event_ids:
                from app.models.webhooks.models import WebhookEndpointEvent
                subscription = WebhookEndpointEvent(
                    endpoint_id=endpoint.id,
                    event_type_id=event_type_id
                )
                self.db.add(subscription)
        
        self.db.commit()
        self.db.refresh(endpoint)
        return endpoint
    
    def get_endpoint(self, endpoint_id: int) -> Optional[WebhookEndpoint]:
        """Get webhook endpoint by ID"""
        return self.db.query(WebhookEndpoint).filter(
            WebhookEndpoint.id == endpoint_id
        ).first()
    
    def search_endpoints(self, search: WebhookEndpointSearch, skip: int = 0, limit: int = 100) -> Tuple[List[WebhookEndpoint], int]:
        """Search webhook endpoints with pagination"""
        query = self.db.query(WebhookEndpoint)
        
        # Apply filters
        if search.name:
            query = query.filter(WebhookEndpoint.name.ilike(f"%{search.name}%"))
        if search.status:
            query = query.filter(WebhookEndpoint.status == search.status)
        if search.is_active is not None:
            query = query.filter(WebhookEndpoint.is_active == search.is_active)
        if search.url_contains:
            query = query.filter(WebhookEndpoint.url.ilike(f"%{search.url_contains}%"))
        if search.created_after:
            query = query.filter(WebhookEndpoint.created_at >= search.created_after)
        if search.created_before:
            query = query.filter(WebhookEndpoint.created_at <= search.created_before)
        if search.last_delivery_after:
            query = query.filter(WebhookEndpoint.last_delivery_at >= search.last_delivery_after)
        if search.last_delivery_before:
            query = query.filter(WebhookEndpoint.last_delivery_at <= search.last_delivery_before)
        
        total = query.count()
        endpoints = query.order_by(desc(WebhookEndpoint.created_at)).offset(skip).limit(limit).all()
        
        return endpoints, total
    
    def update_endpoint(self, endpoint_id: int, updates: WebhookEndpointUpdate) -> Optional[WebhookEndpoint]:
        """Update webhook endpoint"""
        endpoint = self.get_endpoint(endpoint_id)
        if not endpoint:
            return None
        
        update_data = updates.dict(exclude_unset=True)
        for key, value in update_data.items():
            if hasattr(endpoint, key):
                setattr(endpoint, key, value)
        
        self.db.commit()
        self.db.refresh(endpoint)
        return endpoint
    
    def delete_endpoint(self, endpoint_id: int) -> bool:
        """Delete webhook endpoint"""
        endpoint = self.get_endpoint(endpoint_id)
        if not endpoint:
            return False
        
        self.db.delete(endpoint)
        self.db.commit()
        return True
    
    def get_endpoints_for_event(self, event_type_id: int) -> List[WebhookEndpoint]:
        """Get all active endpoints subscribed to an event type"""
        from app.models.webhooks.models import WebhookEndpointEvent
        
        return self.db.query(WebhookEndpoint).join(
            WebhookEndpointEvent,
            WebhookEndpoint.id == WebhookEndpointEvent.endpoint_id
        ).filter(
            and_(
                WebhookEndpointEvent.event_type_id == event_type_id,
                WebhookEndpointEvent.is_active == True,
                WebhookEndpoint.is_active == True,
                WebhookEndpoint.status == WebhookStatus.ACTIVE
            )
        ).all()


class WebhookEventService:
    """Service for managing webhook events"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_event(self, event_data: WebhookEventCreate) -> WebhookEvent:
        """Create a new webhook event"""
        event = WebhookEvent(**event_data.dict())
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event
    
    def get_event(self, event_id: int) -> Optional[WebhookEvent]:
        """Get webhook event by ID"""
        return self.db.query(WebhookEvent).filter(
            WebhookEvent.id == event_id
        ).first()
    
    def search_events(self, search: WebhookEventSearch, skip: int = 0, limit: int = 100) -> Tuple[List[WebhookEvent], int]:
        """Search webhook events with pagination"""
        query = self.db.query(WebhookEvent)
        
        # Apply filters
        if search.event_type_id:
            query = query.filter(WebhookEvent.event_type_id == search.event_type_id)
        if search.is_processed is not None:
            query = query.filter(WebhookEvent.is_processed == search.is_processed)
        if search.occurred_after:
            query = query.filter(WebhookEvent.occurred_at >= search.occurred_after)
        if search.occurred_before:
            query = query.filter(WebhookEvent.occurred_at <= search.occurred_before)
        if search.triggered_by_user_id:
            query = query.filter(WebhookEvent.triggered_by_user_id == search.triggered_by_user_id)
        if search.triggered_by_customer_id:
            query = query.filter(WebhookEvent.triggered_by_customer_id == search.triggered_by_customer_id)
        
        total = query.count()
        events = query.order_by(desc(WebhookEvent.occurred_at)).offset(skip).limit(limit).all()
        
        return events, total
    
    def mark_event_processed(self, event_id: int) -> bool:
        """Mark event as processed"""
        event = self.get_event(event_id)
        if not event:
            return False
        
        event.is_processed = True
        event.processed_at = datetime.now(timezone.utc)
        self.db.commit()
        return True


class WebhookDeliveryService:
    """Service for managing webhook deliveries"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_delivery(self, event_id: int, endpoint_id: int) -> WebhookDelivery:
        """Create a new webhook delivery"""
        delivery = WebhookDelivery(
            event_id=event_id,
            endpoint_id=endpoint_id,
            scheduled_at=datetime.now(timezone.utc)
        )
        self.db.add(delivery)
        self.db.commit()
        self.db.refresh(delivery)
        return delivery
    
    def get_delivery(self, delivery_id: int) -> Optional[WebhookDelivery]:
        """Get webhook delivery by ID"""
        return self.db.query(WebhookDelivery).filter(
            WebhookDelivery.id == delivery_id
        ).first()
    
    def search_deliveries(self, search: WebhookDeliverySearch, skip: int = 0, limit: int = 100) -> Tuple[List[WebhookDelivery], int]:
        """Search webhook deliveries with pagination"""
        query = self.db.query(WebhookDelivery)
        
        # Apply filters
        if search.endpoint_id:
            query = query.filter(WebhookDelivery.endpoint_id == search.endpoint_id)
        if search.event_id:
            query = query.filter(WebhookDelivery.event_id == search.event_id)
        if search.status:
            query = query.filter(WebhookDelivery.status == search.status)
        if search.scheduled_after:
            query = query.filter(WebhookDelivery.scheduled_at >= search.scheduled_after)
        if search.scheduled_before:
            query = query.filter(WebhookDelivery.scheduled_at <= search.scheduled_before)
        if search.delivered_after:
            query = query.filter(WebhookDelivery.delivered_at >= search.delivered_after)
        if search.delivered_before:
            query = query.filter(WebhookDelivery.delivered_at <= search.delivered_before)
        if search.min_attempts:
            query = query.filter(WebhookDelivery.attempt_count >= search.min_attempts)
        if search.max_attempts:
            query = query.filter(WebhookDelivery.attempt_count <= search.max_attempts)
        
        total = query.count()
        deliveries = query.order_by(desc(WebhookDelivery.scheduled_at)).offset(skip).limit(limit).all()
        
        return deliveries, total
    
    def get_pending_deliveries(self, limit: int = 100) -> List[WebhookDelivery]:
        """Get pending deliveries ready for processing"""
        now = datetime.now(timezone.utc)
        
        return self.db.query(WebhookDelivery).filter(
            and_(
                WebhookDelivery.status.in_([DeliveryStatus.PENDING, DeliveryStatus.RETRYING]),
                or_(
                    WebhookDelivery.scheduled_at <= now,
                    and_(
                        WebhookDelivery.next_retry_at.isnot(None),
                        WebhookDelivery.next_retry_at <= now
                    )
                ),
                WebhookDelivery.attempt_count < WebhookDelivery.max_attempts
            )
        ).order_by(WebhookDelivery.scheduled_at).limit(limit).all()
    
    def update_delivery_status(self, delivery_id: int, status: DeliveryStatus, 
                             response_data: Optional[Dict[str, Any]] = None) -> bool:
        """Update delivery status and response data"""
        delivery = self.get_delivery(delivery_id)
        if not delivery:
            return False
        
        delivery.status = status
        delivery.attempt_count += 1
        
        if response_data:
            for key, value in response_data.items():
                if hasattr(delivery, key):
                    setattr(delivery, key, value)
        
        if status == DeliveryStatus.DELIVERED:
            delivery.delivered_at = datetime.now(timezone.utc)
        elif status == DeliveryStatus.FAILED and delivery.attempt_count < delivery.max_attempts:
            # Schedule retry
            delivery.status = DeliveryStatus.RETRYING
            delivery.next_retry_at = self._calculate_next_retry(delivery)
        
        self.db.commit()
        return True
    
    def _calculate_next_retry(self, delivery: WebhookDelivery) -> datetime:
        """Calculate next retry time based on retry strategy"""
        endpoint = delivery.endpoint
        base_delay = endpoint.retry_delay_seconds
        
        if endpoint.retry_strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            delay = base_delay * (2 ** (delivery.attempt_count - 1))
        elif endpoint.retry_strategy == RetryStrategy.LINEAR_BACKOFF:
            delay = base_delay * delivery.attempt_count
        elif endpoint.retry_strategy == RetryStrategy.FIXED_INTERVAL:
            delay = base_delay
        else:  # IMMEDIATE
            delay = 0
        
        # Cap maximum delay at 24 hours
        delay = min(delay, 86400)
        
        return datetime.now(timezone.utc) + timedelta(seconds=delay)


class WebhookFilterService:
    """Service for managing webhook filters"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_filter(self, endpoint_id: int, filter_data: WebhookFilterCreate) -> WebhookFilter:
        """Create a new webhook filter"""
        filter_dict = filter_data.dict()
        filter_dict['endpoint_id'] = endpoint_id
        
        webhook_filter = WebhookFilter(**filter_dict)
        self.db.add(webhook_filter)
        self.db.commit()
        self.db.refresh(webhook_filter)
        return webhook_filter
    
    def get_filters_for_endpoint(self, endpoint_id: int) -> List[WebhookFilter]:
        """Get all filters for an endpoint"""
        return self.db.query(WebhookFilter).filter(
            and_(
                WebhookFilter.endpoint_id == endpoint_id,
                WebhookFilter.is_active == True
            )
        ).all()
    
    def evaluate_filters(self, endpoint_id: int, payload: Dict[str, Any]) -> bool:
        """Evaluate if payload passes all filters for an endpoint"""
        filters = self.get_filters_for_endpoint(endpoint_id)
        if not filters:
            return True  # No filters = pass
        
        for webhook_filter in filters:
            if not self._evaluate_single_filter(webhook_filter, payload):
                return False
        
        return True
    
    def _evaluate_single_filter(self, webhook_filter: WebhookFilter, payload: Dict[str, Any]) -> bool:
        """Evaluate a single filter against payload"""
        try:
            # Extract value from payload using field path
            field_value = self._extract_field_value(payload, webhook_filter.field_path)
            
            # Apply operator
            result = self._apply_operator(
                field_value, 
                webhook_filter.operator, 
                webhook_filter.value, 
                webhook_filter.values
            )
            
            # Apply include/exclude logic
            return result if webhook_filter.include_on_match else not result
            
        except Exception as e:
            logger.warning(f"Filter evaluation error: {e}")
            return False  # Fail safe
    
    def _extract_field_value(self, payload: Dict[str, Any], field_path: str) -> Any:
        """Extract field value from payload using dot notation"""
        keys = field_path.split('.')
        value = payload
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        
        return value
    
    def _apply_operator(self, field_value: Any, operator: FilterOperator, 
                       expected_value: Optional[str], expected_values: Optional[List[str]]) -> bool:
        """Apply filter operator"""
        if operator == FilterOperator.EXISTS:
            return field_value is not None
        elif operator == FilterOperator.NOT_EXISTS:
            return field_value is None
        
        if field_value is None:
            return False
        
        field_str = str(field_value)
        
        if operator == FilterOperator.EQUALS:
            return field_str == expected_value
        elif operator == FilterOperator.NOT_EQUALS:
            return field_str != expected_value
        elif operator == FilterOperator.CONTAINS:
            return expected_value in field_str
        elif operator == FilterOperator.NOT_CONTAINS:
            return expected_value not in field_str
        elif operator == FilterOperator.IN:
            return field_str in (expected_values or [])
        elif operator == FilterOperator.NOT_IN:
            return field_str not in (expected_values or [])
        elif operator == FilterOperator.GREATER_THAN:
            try:
                return float(field_value) > float(expected_value)
            except (ValueError, TypeError):
                return False
        elif operator == FilterOperator.LESS_THAN:
            try:
                return float(field_value) < float(expected_value)
            except (ValueError, TypeError):
                return False
        elif operator == FilterOperator.GREATER_EQUAL:
            try:
                return float(field_value) >= float(expected_value)
            except (ValueError, TypeError):
                return False
        elif operator == FilterOperator.LESS_EQUAL:
            try:
                return float(field_value) <= float(expected_value)
            except (ValueError, TypeError):
                return False
        elif operator == FilterOperator.REGEX:
            import re
            try:
                return bool(re.search(expected_value, field_str))
            except re.error:
                return False
        
        return False


class WebhookDeliveryEngine:
    """Engine for processing webhook deliveries"""
    
    def __init__(self, db: Session):
        self.db = db
        self.delivery_service = WebhookDeliveryService(db)
        self.filter_service = WebhookFilterService(db)
    
    async def process_event(self, event: WebhookEvent) -> List[WebhookDelivery]:
        """Process an event and create deliveries for subscribed endpoints"""
        endpoint_service = WebhookEndpointService(self.db)
        endpoints = endpoint_service.get_endpoints_for_event(event.event_type_id)
        
        deliveries = []
        for endpoint in endpoints:
            # Check filters
            if endpoint.enable_filtering:
                if not self.filter_service.evaluate_filters(endpoint.id, event.payload):
                    continue
            
            # Create delivery
            delivery = self.delivery_service.create_delivery(event.id, endpoint.id)
            deliveries.append(delivery)
        
        return deliveries
    
    async def deliver_webhook(self, delivery: WebhookDelivery) -> bool:
        """Deliver a single webhook"""
        try:
            # Prepare request
            event = delivery.event
            endpoint = delivery.endpoint
            
            # Build payload
            payload = {
                "event_id": event.event_id,
                "event_type": event.event_type.name,
                "occurred_at": event.occurred_at.isoformat(),
                "data": event.payload,
                "metadata": event.metadata
            }
            
            # Prepare headers
            headers = {
                "Content-Type": endpoint.content_type.value,
                "User-Agent": "ISP-Framework-Webhook/1.0",
                "X-Webhook-Event-ID": event.event_id,
                "X-Webhook-Event-Type": event.event_type.name,
                "X-Webhook-Delivery-ID": delivery.delivery_id
            }
            
            # Add custom headers
            if endpoint.custom_headers:
                headers.update(endpoint.custom_headers)
            
            # Add signature
            if endpoint.secret_token:
                signature = self._generate_signature(
                    json.dumps(payload, sort_keys=True),
                    endpoint.secret_token,
                    endpoint.signature_algorithm
                )
                headers["X-Webhook-Signature"] = signature
            
            # Record attempt
            attempt = WebhookDeliveryAttempt(
                delivery_id=delivery.id,
                attempt_number=delivery.attempt_count + 1,
                attempted_at=datetime.now(timezone.utc),
                request_url=str(endpoint.url),
                request_headers=headers,
                request_body_hash=hashlib.sha256(json.dumps(payload).encode()).hexdigest()
            )
            self.db.add(attempt)
            self.db.flush()
            
            # Make HTTP request
            start_time = datetime.now()
            async with httpx.AsyncClient(
                timeout=endpoint.timeout_seconds,
                verify=endpoint.verify_ssl
            ) as client:
                response = await client.request(
                    method=endpoint.http_method.value,
                    url=str(endpoint.url),
                    headers=headers,
                    json=payload if endpoint.content_type == "application/json" else None,
                    data=payload if endpoint.content_type != "application/json" else None
                )
            
            end_time = datetime.now()
            response_time_ms = int((end_time - start_time).total_seconds() * 1000)
            
            # Update attempt with response
            attempt.response_status_code = response.status_code
            attempt.response_headers = dict(response.headers)
            attempt.response_body = response.text[:10000]  # Limit response body size
            attempt.response_time_ms = response_time_ms
            attempt.is_successful = 200 <= response.status_code < 300
            
            # Update delivery
            response_data = {
                "response_status_code": response.status_code,
                "response_headers": dict(response.headers),
                "response_body": response.text[:1000],
                "response_time_ms": response_time_ms,
                "request_url": str(endpoint.url),
                "request_method": endpoint.http_method.value,
                "request_headers": headers,
                "request_body": json.dumps(payload)[:5000]
            }
            
            if attempt.is_successful:
                self.delivery_service.update_delivery_status(
                    delivery.id, DeliveryStatus.DELIVERED, response_data
                )
                
                # Update endpoint statistics
                endpoint.successful_deliveries += 1
                endpoint.last_success_at = datetime.now(timezone.utc)
            else:
                response_data["error_message"] = f"HTTP {response.status_code}: {response.text[:500]}"
                self.delivery_service.update_delivery_status(
                    delivery.id, DeliveryStatus.FAILED, response_data
                )
                
                # Update endpoint statistics
                endpoint.failed_deliveries += 1
                endpoint.last_failure_at = datetime.now(timezone.utc)
            
            endpoint.total_deliveries += 1
            endpoint.last_delivery_at = datetime.now(timezone.utc)
            self.db.commit()
            
            return attempt.is_successful
            
        except Exception as e:
            logger.error(f"Webhook delivery error: {e}")
            
            # Update attempt with error
            attempt.error_type = type(e).__name__
            attempt.error_message = str(e)
            attempt.is_successful = False
            
            # Update delivery
            error_data = {
                "error_message": str(e),
                "error_details": {"error_type": type(e).__name__}
            }
            self.delivery_service.update_delivery_status(
                delivery.id, DeliveryStatus.FAILED, error_data
            )
            
            # Update endpoint statistics
            endpoint = delivery.endpoint
            endpoint.failed_deliveries += 1
            endpoint.total_deliveries += 1
            endpoint.last_failure_at = datetime.now(timezone.utc)
            endpoint.last_delivery_at = datetime.now(timezone.utc)
            
            self.db.commit()
            return False
    
    def _generate_signature(self, payload: str, secret: str, algorithm: SignatureAlgorithm) -> str:
        """Generate webhook signature"""
        if algorithm == SignatureAlgorithm.HMAC_SHA256:
            signature = hmac.new(
                secret.encode(), 
                payload.encode(), 
                hashlib.sha256
            ).hexdigest()
            return f"sha256={signature}"
        elif algorithm == SignatureAlgorithm.HMAC_SHA512:
            signature = hmac.new(
                secret.encode(), 
                payload.encode(), 
                hashlib.sha512
            ).hexdigest()
            return f"sha512={signature}"
        elif algorithm == SignatureAlgorithm.HMAC_SHA1:
            signature = hmac.new(
                secret.encode(), 
                payload.encode(), 
                hashlib.sha1
            ).hexdigest()
            return f"sha1={signature}"
        
        return ""


class WebhookTestService:
    """Service for testing webhook endpoints"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def test_endpoint(self, test_request: WebhookTestRequest) -> Dict[str, Any]:
        """Test a webhook endpoint with a sample payload"""
        endpoint_service = WebhookEndpointService(self.db)
        endpoint = endpoint_service.get_endpoint(test_request.endpoint_id)
        
        if not endpoint:
            return {
                "success": False,
                "error_message": "Endpoint not found"
            }
        
        try:
            # Use override URL if provided
            url = test_request.override_url or endpoint.url
            
            # Prepare headers
            headers = {
                "Content-Type": endpoint.content_type.value,
                "User-Agent": "ISP-Framework-Webhook-Test/1.0",
                "X-Webhook-Test": "true"
            }
            
            if endpoint.custom_headers:
                headers.update(endpoint.custom_headers)
            
            # Add signature if secret is configured
            if endpoint.secret_token:
                payload_str = json.dumps(test_request.test_payload, sort_keys=True)
                signature = self._generate_test_signature(
                    payload_str, endpoint.secret_token, endpoint.signature_algorithm
                )
                headers["X-Webhook-Signature"] = signature
            
            # Make request
            start_time = datetime.now()
            async with httpx.AsyncClient(
                timeout=endpoint.timeout_seconds,
                verify=endpoint.verify_ssl
            ) as client:
                response = await client.request(
                    method=endpoint.http_method.value,
                    url=str(url),
                    headers=headers,
                    json=test_request.test_payload if endpoint.content_type == "application/json" else None,
                    data=test_request.test_payload if endpoint.content_type != "application/json" else None
                )
            
            end_time = datetime.now()
            response_time_ms = int((end_time - start_time).total_seconds() * 1000)
            
            return {
                "success": 200 <= response.status_code < 300,
                "status_code": response.status_code,
                "response_time_ms": response_time_ms,
                "response_body": response.text[:1000],
                "response_headers": dict(response.headers)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error_message": str(e),
                "error_type": type(e).__name__
            }
    
    def _generate_test_signature(self, payload: str, secret: str, algorithm: SignatureAlgorithm) -> str:
        """Generate test signature (same as delivery engine)"""
        engine = WebhookDeliveryEngine(self.db)
        return engine._generate_signature(payload, secret, algorithm)
