"""
Webhook Integration Service

Central service for triggering webhook events throughout the ISP Framework.
Provides easy-to-use methods for triggering events from any part of the system.
"""

import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from fastapi import BackgroundTasks

from app.models.webhooks.models import WebhookEvent, WebhookEventType
from app.services.webhook_service import WebhookEventService, WebhookDeliveryEngine
from app.core.database import SessionLocal, get_db


class WebhookIntegrationService:
    """Service for triggering webhook events across the ISP Framework"""
    
    def __init__(self, db: Session = None):
        self.db = db or SessionLocal()
        self.event_service = WebhookEventService(self.db)
        self.delivery_engine = WebhookDeliveryEngine(self.db)
    
    def trigger_event(
        self,
        event_type: str,
        payload: Dict[str, Any],
        triggered_by_user_id: Optional[int] = None,
        triggered_by_customer_id: Optional[int] = None,
        background_tasks: Optional[BackgroundTasks] = None
    ) -> WebhookEvent:
        """Trigger a webhook event"""
        
        # Create webhook event
        event_data = {
            'event_type_id': self._get_event_type_id(event_type),
            'payload': payload,
            'triggered_by_user_id': triggered_by_user_id,
            'triggered_by_customer_id': triggered_by_customer_id,
            'occurred_at': datetime.now(timezone.utc)
        }
        
        event = self.event_service.create_event(event_data)
        
        # Process in background if provided, otherwise process immediately
        if background_tasks:
            background_tasks.add_task(self._process_event_async, event.id)
        else:
            # Process synchronously
            asyncio.create_task(self._process_event_async(event.id))
        
        return event
    
    async def _process_event_async(self, event_id: int):
        """Process webhook event asynchronously"""
        try:
            # Get fresh session for async processing
            db = next(get_db())
            try:
                delivery_engine = WebhookDeliveryEngine(db)
                event = db.query(WebhookEvent).filter(WebhookEvent.id == event_id).first()
                if event:
                    delivery_engine.process_event(event)
            finally:
                db.close()
        except Exception as e:
            # Log error but don't raise - webhook failures shouldn't break main flow
            print(f"Webhook processing error: {e}")
    
    def _get_event_type_id(self, event_type_name: str) -> int:
        """Get event type ID by name"""
        event_type = self.db.query(WebhookEventType).filter(
            WebhookEventType.name == event_type_name
        ).first()
        
        if not event_type:
            # Fallback to customer.created if event type not found
            event_type = self.db.query(WebhookEventType).filter(
                WebhookEventType.name == 'customer.created'
            ).first()
        
        return event_type.id if event_type else 1


# Convenience functions for common events
class WebhookTriggers:
    """Convenience class for triggering common webhook events"""
    
    def __init__(self, db: Session = None):
        self.integration_service = WebhookIntegrationService(db)
    
    # Customer Events
    def customer_created(self, customer_data: Dict[str, Any], user_id: Optional[int] = None):
        """Trigger customer creation event"""
        payload = {
            'customer_id': customer_data.get('id'),
            'email': customer_data.get('email'),
            'full_name': customer_data.get('full_name'),
            'portal_id': customer_data.get('portal_id'),
            'created_at': customer_data.get('created_at'),
            'customer_type': customer_data.get('customer_type', 'individual')
        }
        return self.integration_service.trigger_event(
            'customer.created',
            payload,
            triggered_by_user_id=user_id,
            triggered_by_customer_id=customer_data.get('id')
        )
    
    def customer_updated(self, customer_data: Dict[str, Any], user_id: Optional[int] = None):
        """Trigger customer update event"""
        payload = {
            'customer_id': customer_data.get('id'),
            'email': customer_data.get('email'),
            'full_name': customer_data.get('full_name'),
            'updated_fields': customer_data.get('updated_fields', {}),
            'updated_at': customer_data.get('updated_at')
        }
        return self.integration_service.trigger_event(
            'customer.updated',
            payload,
            triggered_by_user_id=user_id,
            triggered_by_customer_id=customer_data.get('id')
        )
    
    def customer_deleted(self, customer_id: int, customer_data: Dict[str, Any], user_id: Optional[int] = None):
        """Trigger customer deletion event"""
        payload = {
            'customer_id': customer_id,
            'email': customer_data.get('email'),
            'full_name': customer_data.get('full_name'),
            'deleted_at': datetime.now(timezone.utc).isoformat()
        }
        return self.integration_service.trigger_event(
            'customer.deleted',
            payload,
            triggered_by_user_id=user_id
        )
    
    def customer_service_created(self, service_data: Dict[str, Any], user_id: Optional[int] = None):
        """Trigger customer service creation event"""
        return self.integration_service.trigger_event(
            'customer.service.created',
            service_data,
            triggered_by_user_id=user_id
        )

    def customer_service_updated(self, service_data: Dict[str, Any], user_id: Optional[int] = None):
        """Trigger customer service update event"""
        return self.integration_service.trigger_event(
            'customer.service.updated',
            service_data,
            triggered_by_user_id=user_id
        )

    def customer_services_overview(self, overview_data: Dict[str, Any], user_id: Optional[int] = None):
        """Trigger customer services overview event"""
        return self.integration_service.trigger_event(
            'customer.services.overview',
            overview_data,
            triggered_by_user_id=user_id
        )
    
    # Service Events
    def service_activated(self, service_data: Dict[str, Any], user_id: Optional[int] = None):
        """Trigger service activation event"""
        payload = {
            'service_id': service_data.get('id'),
            'customer_id': service_data.get('customer_id'),
            'service_type': service_data.get('service_type'),
            'service_name': service_data.get('service_name'),
            'tariff_name': service_data.get('tariff_name'),
            'activation_date': service_data.get('activation_date'),
            'monthly_fee': service_data.get('monthly_fee'),
            'speed_config': service_data.get('speed_config', {})
        }
        return self.integration_service.trigger_event(
            'service.activated',
            payload,
            triggered_by_user_id=user_id,
            triggered_by_customer_id=service_data.get('customer_id')
        )
    
    def service_suspended(self, service_data: Dict[str, Any], reason: str, user_id: Optional[int] = None):
        """Trigger service suspension event"""
        payload = {
            'service_id': service_data.get('id'),
            'customer_id': service_data.get('customer_id'),
            'service_type': service_data.get('service_type'),
            'service_name': service_data.get('service_name'),
            'suspension_reason': reason,
            'suspended_at': datetime.now(timezone.utc).isoformat()
        }
        return self.integration_service.trigger_event(
            'service.suspended',
            payload,
            triggered_by_user_id=user_id,
            triggered_by_customer_id=service_data.get('customer_id')
        )
    
    def service_terminated(self, service_data: Dict[str, Any], reason: str, user_id: Optional[int] = None):
        """Trigger service termination event"""
        payload = {
            'service_id': service_data.get('id'),
            'customer_id': service_data.get('customer_id'),
            'service_type': service_data.get('service_type'),
            'service_name': service_data.get('service_name'),
            'termination_reason': reason,
            'terminated_at': datetime.now(timezone.utc).isoformat()
        }
        return self.integration_service.trigger_event(
            'service.terminated',
            payload,
            triggered_by_user_id=user_id,
            triggered_by_customer_id=service_data.get('customer_id')
        )
    
    # Billing Events
    def invoice_created(self, invoice_data: Dict[str, Any], user_id: Optional[int] = None):
        """Trigger invoice creation event"""
        payload = {
            'invoice_id': invoice_data.get('id'),
            'customer_id': invoice_data.get('customer_id'),
            'invoice_number': invoice_data.get('invoice_number'),
            'total_amount': invoice_data.get('total_amount'),
            'due_date': invoice_data.get('due_date'),
            'status': invoice_data.get('status'),
            'items': invoice_data.get('items', [])
        }
        return self.integration_service.trigger_event(
            'billing.invoice.created',
            payload,
            triggered_by_user_id=user_id,
            triggered_by_customer_id=invoice_data.get('customer_id')
        )
    
    def invoice_paid(self, invoice_data: Dict[str, Any], payment_data: Dict[str, Any], user_id: Optional[int] = None):
        """Trigger invoice payment event"""
        payload = {
            'invoice_id': invoice_data.get('id'),
            'customer_id': invoice_data.get('customer_id'),
            'invoice_number': invoice_data.get('invoice_number'),
            'total_amount': invoice_data.get('total_amount'),
            'paid_amount': payment_data.get('amount'),
            'payment_method': payment_data.get('payment_method'),
            'paid_at': payment_data.get('paid_at')
        }
        return self.integration_service.trigger_event(
            'billing.invoice.paid',
            payload,
            triggered_by_user_id=user_id,
            triggered_by_customer_id=invoice_data.get('customer_id')
        )
    
    def invoice_overdue(self, invoice_data: Dict[str, Any], days_overdue: int, user_id: Optional[int] = None):
        """Trigger invoice overdue event"""
        payload = {
            'invoice_id': invoice_data.get('id'),
            'customer_id': invoice_data.get('customer_id'),
            'invoice_number': invoice_data.get('invoice_number'),
            'total_amount': invoice_data.get('total_amount'),
            'due_date': invoice_data.get('due_date'),
            'days_overdue': days_overdue,
            'overdue_at': datetime.now(timezone.utc).isoformat()
        }
        return self.integration_service.trigger_event(
            'billing.invoice.overdue',
            payload,
            triggered_by_user_id=user_id,
            triggered_by_customer_id=invoice_data.get('customer_id')
        )
    
    # Authentication Events
    def auth_login(self, user_data: Dict[str, Any], ip_address: str, user_agent: str):
        """Trigger login event"""
        payload = {
            'user_id': user_data.get('id'),
            'email': user_data.get('email'),
            'full_name': user_data.get('full_name'),
            'ip_address': ip_address,
            'user_agent': user_agent,
            'login_at': datetime.now(timezone.utc).isoformat()
        }
        return self.integration_service.trigger_event(
            'auth.login',
            payload,
            triggered_by_user_id=user_data.get('id')
        )
    
    def auth_logout(self, user_data: Dict[str, Any], ip_address: str):
        """Trigger logout event"""
        payload = {
            'user_id': user_data.get('id'),
            'email': user_data.get('email'),
            'full_name': user_data.get('full_name'),
            'ip_address': ip_address,
            'logout_at': datetime.now(timezone.utc).isoformat()
        }
        return self.integration_service.trigger_event(
            'auth.logout',
            payload,
            triggered_by_user_id=user_data.get('id')
        )
    
    # Network Events
    def network_device_down(self, device_data: Dict[str, Any], site_data: Dict[str, Any]):
        """Trigger network device down event"""
        payload = {
            'device_id': device_data.get('id'),
            'device_name': device_data.get('name'),
            'device_type': device_data.get('device_type'),
            'site_id': site_data.get('id'),
            'site_name': site_data.get('name'),
            'down_since': datetime.now(timezone.utc).isoformat()
        }
        return self.integration_service.trigger_event(
            'network.device.down',
            payload
        )
    
    def network_device_up(self, device_data: Dict[str, Any], site_data: Dict[str, Any]):
        """Trigger network device up event"""
        payload = {
            'device': device_data,
            'site': site_data,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        return self.integration_service.trigger_event('network.device.up', payload)

    def network_site_created(self, site_data: Dict[str, Any], user_id: Optional[int] = None):
        """Trigger network site creation event"""
        return self.integration_service.trigger_event(
            'network.site.created',
            site_data,
            triggered_by_user_id=user_id
        )

    def network_device_created(self, device_data: Dict[str, Any], user_id: Optional[int] = None):
        """Trigger network device creation event"""
        return self.integration_service.trigger_event(
            'network.device.created',
            device_data,
            triggered_by_user_id=user_id
        )
    
    # Ticketing Events
    def ticket_created(self, ticket_data: Dict[str, Any], user_id: Optional[int] = None):
        """Trigger ticket creation event"""
        payload = {
            'ticket_id': ticket_data.get('id'),
            'ticket_number': ticket_data.get('ticket_number'),
            'customer_id': ticket_data.get('customer_id'),
            'title': ticket_data.get('title'),
            'priority': ticket_data.get('priority'),
            'category': ticket_data.get('category'),
            'created_at': ticket_data.get('created_at')
        }
        return self.integration_service.trigger_event(
            'ticket.created',
            payload,
            triggered_by_user_id=user_id,
            triggered_by_customer_id=ticket_data.get('customer_id')
        )
    
    def ticket_updated(self, ticket_data: Dict[str, Any], changes: Dict[str, Any], user_id: Optional[int] = None):
        """Trigger ticket update event"""
        payload = {
            'ticket_id': ticket_data.get('id'),
            'ticket_number': ticket_data.get('ticket_number'),
            'customer_id': ticket_data.get('customer_id'),
            'title': ticket_data.get('title'),
            'changes': changes,
            'updated_at': datetime.now(timezone.utc).isoformat()
        }
        return self.integration_service.trigger_event(
            'ticket.updated',
            payload,
            triggered_by_user_id=user_id,
            triggered_by_customer_id=ticket_data.get('customer_id')
        )
    
    def ticket_resolved(self, ticket_data: Dict[str, Any], resolution_notes: str, user_id: Optional[int] = None):
        """Trigger ticket resolution event"""
        payload = {
            **ticket_data,
            'resolution_notes': resolution_notes,
            'resolved_at': datetime.now(timezone.utc).isoformat()
        }
        return self.integration_service.trigger_event(
            'ticket.resolved',
            payload,
            triggered_by_user_id=user_id
        )

    def ticket_status_changed(self, ticket_data: Dict[str, Any], user_id: Optional[int] = None):
        """Trigger ticket status change event"""
        return self.integration_service.trigger_event(
            'ticket.status_changed',
            ticket_data,
            triggered_by_user_id=user_id
        )

    def ticket_assigned(self, ticket_data: Dict[str, Any], user_id: Optional[int] = None):
        """Trigger ticket assignment event"""
        return self.integration_service.trigger_event(
            'ticket.assigned',
            ticket_data,
            triggered_by_user_id=user_id
        )


# Global instance for easy access
webhook_triggers = WebhookTriggers()
