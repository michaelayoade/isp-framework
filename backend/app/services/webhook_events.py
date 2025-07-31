"""
Webhook Event Catalog

Predefined ISP events for webhook system with comprehensive event definitions,
payload schemas, and automatic event registration.
"""

from typing import Any, Dict

from app.models.webhooks.enums import EventCategory

# ISP Event Catalog
ISP_WEBHOOK_EVENTS = {
    # Customer Events
    "customer.created": {
        "category": EventCategory.CUSTOMER,
        "description": "Triggered when a new customer is created",
        "payload_schema": {
            "type": "object",
            "properties": {
                "customer_id": {"type": "integer"},
                "customer_number": {"type": "string"},
                "name": {"type": "string"},
                "email": {"type": "string"},
                "phone": {"type": "string"},
                "status": {"type": "string"},
                "created_at": {"type": "string", "format": "date-time"},
                "created_by": {"type": "integer"},
            },
            "required": [
                "customer_id",
                "customer_number",
                "name",
                "status",
                "created_at",
            ],
        },
        "sample_payload": {
            "customer_id": 123,
            "customer_number": "CUST-2024-001",
            "name": "John Doe",
            "email": "john.doe@example.com",
            "phone": "+1234567890",
            "status": "active",
            "created_at": "2024-01-15T10:30:00Z",
            "created_by": 1,
        },
    },
    "customer.updated": {
        "category": EventCategory.CUSTOMER,
        "description": "Triggered when customer information is updated",
        "payload_schema": {
            "type": "object",
            "properties": {
                "customer_id": {"type": "integer"},
                "customer_number": {"type": "string"},
                "changes": {"type": "object"},
                "updated_at": {"type": "string", "format": "date-time"},
                "updated_by": {"type": "integer"},
            },
            "required": ["customer_id", "changes", "updated_at"],
        },
        "sample_payload": {
            "customer_id": 123,
            "customer_number": "CUST-2024-001",
            "changes": {
                "email": {"old": "old@example.com", "new": "new@example.com"},
                "phone": {"old": "+1111111111", "new": "+2222222222"},
            },
            "updated_at": "2024-01-15T11:30:00Z",
            "updated_by": 1,
        },
    },
    "customer.status_changed": {
        "category": EventCategory.CUSTOMER,
        "description": "Triggered when customer status changes",
        "payload_schema": {
            "type": "object",
            "properties": {
                "customer_id": {"type": "integer"},
                "customer_number": {"type": "string"},
                "old_status": {"type": "string"},
                "new_status": {"type": "string"},
                "reason": {"type": "string"},
                "changed_at": {"type": "string", "format": "date-time"},
                "changed_by": {"type": "integer"},
            },
            "required": ["customer_id", "old_status", "new_status", "changed_at"],
        },
        "sample_payload": {
            "customer_id": 123,
            "customer_number": "CUST-2024-001",
            "old_status": "active",
            "new_status": "suspended",
            "reason": "Non-payment",
            "changed_at": "2024-01-15T12:00:00Z",
            "changed_by": 1,
        },
    },
    "customer.deleted": {
        "category": EventCategory.CUSTOMER,
        "description": "Triggered when a customer is deleted",
        "payload_schema": {
            "type": "object",
            "properties": {
                "customer_id": {"type": "integer"},
                "customer_number": {"type": "string"},
                "name": {"type": "string"},
                "deleted_at": {"type": "string", "format": "date-time"},
                "deleted_by": {"type": "integer"},
            },
            "required": ["customer_id", "customer_number", "deleted_at"],
        },
        "sample_payload": {
            "customer_id": 123,
            "customer_number": "CUST-2024-001",
            "name": "John Doe",
            "deleted_at": "2024-01-15T13:00:00Z",
            "deleted_by": 1,
        },
    },
    # Billing Events
    "invoice.created": {
        "category": EventCategory.BILLING,
        "description": "Triggered when a new invoice is created",
        "payload_schema": {
            "type": "object",
            "properties": {
                "invoice_id": {"type": "integer"},
                "invoice_number": {"type": "string"},
                "customer_id": {"type": "integer"},
                "amount": {"type": "number"},
                "currency": {"type": "string"},
                "due_date": {"type": "string", "format": "date"},
                "status": {"type": "string"},
                "created_at": {"type": "string", "format": "date-time"},
            },
            "required": [
                "invoice_id",
                "invoice_number",
                "customer_id",
                "amount",
                "due_date",
                "status",
            ],
        },
        "sample_payload": {
            "invoice_id": 456,
            "invoice_number": "INV-2024-001",
            "customer_id": 123,
            "amount": 99.99,
            "currency": "USD",
            "due_date": "2024-02-15",
            "status": "pending",
            "created_at": "2024-01-15T10:00:00Z",
        },
    },
    "invoice.paid": {
        "category": EventCategory.BILLING,
        "description": "Triggered when an invoice is paid",
        "payload_schema": {
            "type": "object",
            "properties": {
                "invoice_id": {"type": "integer"},
                "invoice_number": {"type": "string"},
                "customer_id": {"type": "integer"},
                "amount_paid": {"type": "number"},
                "payment_method": {"type": "string"},
                "payment_id": {"type": "integer"},
                "paid_at": {"type": "string", "format": "date-time"},
            },
            "required": ["invoice_id", "customer_id", "amount_paid", "paid_at"],
        },
        "sample_payload": {
            "invoice_id": 456,
            "invoice_number": "INV-2024-001",
            "customer_id": 123,
            "amount_paid": 99.99,
            "payment_method": "credit_card",
            "payment_id": 789,
            "paid_at": "2024-01-20T14:30:00Z",
        },
    },
    "invoice.overdue": {
        "category": EventCategory.BILLING,
        "description": "Triggered when an invoice becomes overdue",
        "payload_schema": {
            "type": "object",
            "properties": {
                "invoice_id": {"type": "integer"},
                "invoice_number": {"type": "string"},
                "customer_id": {"type": "integer"},
                "amount": {"type": "number"},
                "due_date": {"type": "string", "format": "date"},
                "days_overdue": {"type": "integer"},
                "overdue_at": {"type": "string", "format": "date-time"},
            },
            "required": [
                "invoice_id",
                "customer_id",
                "amount",
                "due_date",
                "days_overdue",
            ],
        },
        "sample_payload": {
            "invoice_id": 456,
            "invoice_number": "INV-2024-001",
            "customer_id": 123,
            "amount": 99.99,
            "due_date": "2024-02-15",
            "days_overdue": 5,
            "overdue_at": "2024-02-20T00:00:00Z",
        },
    },
    # Service Events
    "service.activated": {
        "category": EventCategory.SERVICE,
        "description": "Triggered when a service is activated for a customer",
        "payload_schema": {
            "type": "object",
            "properties": {
                "service_id": {"type": "integer"},
                "customer_id": {"type": "integer"},
                "service_type": {"type": "string"},
                "service_name": {"type": "string"},
                "tariff_id": {"type": "integer"},
                "activation_date": {"type": "string", "format": "date-time"},
                "monthly_cost": {"type": "number"},
            },
            "required": [
                "service_id",
                "customer_id",
                "service_type",
                "activation_date",
            ],
        },
        "sample_payload": {
            "service_id": 789,
            "customer_id": 123,
            "service_type": "internet",
            "service_name": "Fiber 100Mbps",
            "tariff_id": 10,
            "activation_date": "2024-01-15T09:00:00Z",
            "monthly_cost": 49.99,
        },
    },
    "service.suspended": {
        "category": EventCategory.SERVICE,
        "description": "Triggered when a service is suspended",
        "payload_schema": {
            "type": "object",
            "properties": {
                "service_id": {"type": "integer"},
                "customer_id": {"type": "integer"},
                "service_type": {"type": "string"},
                "suspension_reason": {"type": "string"},
                "suspended_at": {"type": "string", "format": "date-time"},
                "suspended_by": {"type": "integer"},
            },
            "required": [
                "service_id",
                "customer_id",
                "suspension_reason",
                "suspended_at",
            ],
        },
        "sample_payload": {
            "service_id": 789,
            "customer_id": 123,
            "service_type": "internet",
            "suspension_reason": "Non-payment",
            "suspended_at": "2024-01-20T16:00:00Z",
            "suspended_by": 1,
        },
    },
    "service.terminated": {
        "category": EventCategory.SERVICE,
        "description": "Triggered when a service is terminated",
        "payload_schema": {
            "type": "object",
            "properties": {
                "service_id": {"type": "integer"},
                "customer_id": {"type": "integer"},
                "service_type": {"type": "string"},
                "termination_reason": {"type": "string"},
                "terminated_at": {"type": "string", "format": "date-time"},
                "final_bill_amount": {"type": "number"},
            },
            "required": [
                "service_id",
                "customer_id",
                "termination_reason",
                "terminated_at",
            ],
        },
        "sample_payload": {
            "service_id": 789,
            "customer_id": 123,
            "service_type": "internet",
            "termination_reason": "Customer request",
            "terminated_at": "2024-02-01T10:00:00Z",
            "final_bill_amount": 25.50,
        },
    },
    # Network Events
    "device.online": {
        "category": EventCategory.NETWORK,
        "description": "Triggered when a network device comes online",
        "payload_schema": {
            "type": "object",
            "properties": {
                "device_id": {"type": "integer"},
                "device_name": {"type": "string"},
                "device_type": {"type": "string"},
                "ip_address": {"type": "string"},
                "location": {"type": "string"},
                "online_at": {"type": "string", "format": "date-time"},
            },
            "required": ["device_id", "device_name", "ip_address", "online_at"],
        },
        "sample_payload": {
            "device_id": 101,
            "device_name": "Router-Main-01",
            "device_type": "router",
            "ip_address": "192.168.1.1",
            "location": "Main Office",
            "online_at": "2024-01-15T08:00:00Z",
        },
    },
    "device.offline": {
        "category": EventCategory.NETWORK,
        "description": "Triggered when a network device goes offline",
        "payload_schema": {
            "type": "object",
            "properties": {
                "device_id": {"type": "integer"},
                "device_name": {"type": "string"},
                "device_type": {"type": "string"},
                "ip_address": {"type": "string"},
                "location": {"type": "string"},
                "offline_at": {"type": "string", "format": "date-time"},
                "last_seen": {"type": "string", "format": "date-time"},
            },
            "required": ["device_id", "device_name", "ip_address", "offline_at"],
        },
        "sample_payload": {
            "device_id": 101,
            "device_name": "Router-Main-01",
            "device_type": "router",
            "ip_address": "192.168.1.1",
            "location": "Main Office",
            "offline_at": "2024-01-15T18:00:00Z",
            "last_seen": "2024-01-15T17:59:30Z",
        },
    },
    "customer.connected": {
        "category": EventCategory.NETWORK,
        "description": "Triggered when a customer connects to the network",
        "payload_schema": {
            "type": "object",
            "properties": {
                "customer_id": {"type": "integer"},
                "username": {"type": "string"},
                "session_id": {"type": "string"},
                "ip_address": {"type": "string"},
                "nas_device": {"type": "string"},
                "connected_at": {"type": "string", "format": "date-time"},
            },
            "required": ["customer_id", "username", "session_id", "connected_at"],
        },
        "sample_payload": {
            "customer_id": 123,
            "username": "john.doe",
            "session_id": "sess_abc123",
            "ip_address": "10.0.1.100",
            "nas_device": "Router-Main-01",
            "connected_at": "2024-01-15T09:30:00Z",
        },
    },
    "customer.disconnected": {
        "category": EventCategory.NETWORK,
        "description": "Triggered when a customer disconnects from the network",
        "payload_schema": {
            "type": "object",
            "properties": {
                "customer_id": {"type": "integer"},
                "username": {"type": "string"},
                "session_id": {"type": "string"},
                "session_duration": {"type": "integer"},
                "bytes_uploaded": {"type": "integer"},
                "bytes_downloaded": {"type": "integer"},
                "disconnected_at": {"type": "string", "format": "date-time"},
                "disconnect_reason": {"type": "string"},
            },
            "required": ["customer_id", "username", "session_id", "disconnected_at"],
        },
        "sample_payload": {
            "customer_id": 123,
            "username": "john.doe",
            "session_id": "sess_abc123",
            "session_duration": 3600,
            "bytes_uploaded": 1048576,
            "bytes_downloaded": 10485760,
            "disconnected_at": "2024-01-15T10:30:00Z",
            "disconnect_reason": "User request",
        },
    },
    # Ticketing Events
    "ticket.created": {
        "category": EventCategory.TICKETING,
        "description": "Triggered when a new support ticket is created",
        "payload_schema": {
            "type": "object",
            "properties": {
                "ticket_id": {"type": "integer"},
                "ticket_number": {"type": "string"},
                "customer_id": {"type": "integer"},
                "subject": {"type": "string"},
                "priority": {"type": "string"},
                "category": {"type": "string"},
                "status": {"type": "string"},
                "created_at": {"type": "string", "format": "date-time"},
                "created_by": {"type": "string"},
            },
            "required": [
                "ticket_id",
                "ticket_number",
                "customer_id",
                "subject",
                "priority",
                "status",
            ],
        },
        "sample_payload": {
            "ticket_id": 301,
            "ticket_number": "TKT-2024-001",
            "customer_id": 123,
            "subject": "Internet connection issues",
            "priority": "high",
            "category": "technical",
            "status": "open",
            "created_at": "2024-01-15T11:00:00Z",
            "created_by": "customer",
        },
    },
    "ticket.assigned": {
        "category": EventCategory.TICKETING,
        "description": "Triggered when a ticket is assigned to an agent",
        "payload_schema": {
            "type": "object",
            "properties": {
                "ticket_id": {"type": "integer"},
                "ticket_number": {"type": "string"},
                "assigned_to": {"type": "integer"},
                "assigned_by": {"type": "integer"},
                "assigned_at": {"type": "string", "format": "date-time"},
            },
            "required": ["ticket_id", "assigned_to", "assigned_at"],
        },
        "sample_payload": {
            "ticket_id": 301,
            "ticket_number": "TKT-2024-001",
            "assigned_to": 5,
            "assigned_by": 1,
            "assigned_at": "2024-01-15T11:15:00Z",
        },
    },
    "ticket.resolved": {
        "category": EventCategory.TICKETING,
        "description": "Triggered when a ticket is resolved",
        "payload_schema": {
            "type": "object",
            "properties": {
                "ticket_id": {"type": "integer"},
                "ticket_number": {"type": "string"},
                "customer_id": {"type": "integer"},
                "resolution": {"type": "string"},
                "resolved_by": {"type": "integer"},
                "resolved_at": {"type": "string", "format": "date-time"},
                "resolution_time_hours": {"type": "number"},
            },
            "required": ["ticket_id", "customer_id", "resolved_by", "resolved_at"],
        },
        "sample_payload": {
            "ticket_id": 301,
            "ticket_number": "TKT-2024-001",
            "customer_id": 123,
            "resolution": "Replaced faulty cable",
            "resolved_by": 5,
            "resolved_at": "2024-01-15T14:30:00Z",
            "resolution_time_hours": 3.5,
        },
    },
    # Authentication Events
    "user.login": {
        "category": EventCategory.AUTHENTICATION,
        "description": "Triggered when a user logs in",
        "payload_schema": {
            "type": "object",
            "properties": {
                "user_id": {"type": "integer"},
                "username": {"type": "string"},
                "user_type": {"type": "string"},
                "ip_address": {"type": "string"},
                "user_agent": {"type": "string"},
                "login_at": {"type": "string", "format": "date-time"},
                "login_method": {"type": "string"},
            },
            "required": ["user_id", "username", "user_type", "login_at"],
        },
        "sample_payload": {
            "user_id": 1,
            "username": "admin",
            "user_type": "administrator",
            "ip_address": "192.168.1.100",
            "user_agent": "Mozilla/5.0...",
            "login_at": "2024-01-15T08:00:00Z",
            "login_method": "password",
        },
    },
    "user.logout": {
        "category": EventCategory.AUTHENTICATION,
        "description": "Triggered when a user logs out",
        "payload_schema": {
            "type": "object",
            "properties": {
                "user_id": {"type": "integer"},
                "username": {"type": "string"},
                "user_type": {"type": "string"},
                "session_duration": {"type": "integer"},
                "logout_at": {"type": "string", "format": "date-time"},
            },
            "required": ["user_id", "username", "user_type", "logout_at"],
        },
        "sample_payload": {
            "user_id": 1,
            "username": "admin",
            "user_type": "administrator",
            "session_duration": 3600,
            "logout_at": "2024-01-15T09:00:00Z",
        },
    },
    # System Events
    "system.backup_completed": {
        "category": EventCategory.SYSTEM,
        "description": "Triggered when a system backup is completed",
        "payload_schema": {
            "type": "object",
            "properties": {
                "backup_id": {"type": "string"},
                "backup_type": {"type": "string"},
                "size_bytes": {"type": "integer"},
                "duration_seconds": {"type": "integer"},
                "completed_at": {"type": "string", "format": "date-time"},
                "status": {"type": "string"},
            },
            "required": ["backup_id", "backup_type", "completed_at", "status"],
        },
        "sample_payload": {
            "backup_id": "backup_20240115_080000",
            "backup_type": "full",
            "size_bytes": 1073741824,
            "duration_seconds": 300,
            "completed_at": "2024-01-15T08:05:00Z",
            "status": "success",
        },
    },
    "system.maintenance_started": {
        "category": EventCategory.SYSTEM,
        "description": "Triggered when system maintenance begins",
        "payload_schema": {
            "type": "object",
            "properties": {
                "maintenance_id": {"type": "string"},
                "maintenance_type": {"type": "string"},
                "description": {"type": "string"},
                "estimated_duration": {"type": "integer"},
                "started_at": {"type": "string", "format": "date-time"},
                "started_by": {"type": "integer"},
            },
            "required": ["maintenance_id", "maintenance_type", "started_at"],
        },
        "sample_payload": {
            "maintenance_id": "maint_20240115_020000",
            "maintenance_type": "scheduled",
            "description": "Database optimization",
            "estimated_duration": 7200,
            "started_at": "2024-01-15T02:00:00Z",
            "started_by": 1,
        },
    },
    # Reseller Events
    "reseller.created": {
        "category": EventCategory.RESELLER,
        "description": "Triggered when a new reseller is created",
        "payload_schema": {
            "type": "object",
            "properties": {
                "reseller_id": {"type": "integer"},
                "company_name": {"type": "string"},
                "contact_person": {"type": "string"},
                "email": {"type": "string"},
                "commission_percentage": {"type": "number"},
                "created_at": {"type": "string", "format": "date-time"},
                "created_by": {"type": "integer"},
            },
            "required": [
                "reseller_id",
                "company_name",
                "commission_percentage",
                "created_at",
            ],
        },
        "sample_payload": {
            "reseller_id": 10,
            "company_name": "TechCorp Reseller",
            "contact_person": "Jane Smith",
            "email": "jane@techcorp.com",
            "commission_percentage": 15.0,
            "created_at": "2024-01-15T10:00:00Z",
            "created_by": 1,
        },
    },
    "reseller.commission_earned": {
        "category": EventCategory.RESELLER,
        "description": "Triggered when a reseller earns commission",
        "payload_schema": {
            "type": "object",
            "properties": {
                "reseller_id": {"type": "integer"},
                "customer_id": {"type": "integer"},
                "invoice_id": {"type": "integer"},
                "commission_amount": {"type": "number"},
                "commission_percentage": {"type": "number"},
                "earned_at": {"type": "string", "format": "date-time"},
            },
            "required": [
                "reseller_id",
                "customer_id",
                "commission_amount",
                "earned_at",
            ],
        },
        "sample_payload": {
            "reseller_id": 10,
            "customer_id": 123,
            "invoice_id": 456,
            "commission_amount": 14.99,
            "commission_percentage": 15.0,
            "earned_at": "2024-01-20T14:30:00Z",
        },
    },
}


def get_all_event_definitions() -> Dict[str, Dict[str, Any]]:
    """Get all predefined webhook event definitions"""
    return ISP_WEBHOOK_EVENTS


def get_events_by_category(category: EventCategory) -> Dict[str, Dict[str, Any]]:
    """Get webhook events filtered by category"""
    return {
        name: definition
        for name, definition in ISP_WEBHOOK_EVENTS.items()
        if definition["category"] == category
    }


def get_event_definition(event_name: str) -> Dict[str, Any]:
    """Get specific event definition by name"""
    return ISP_WEBHOOK_EVENTS.get(event_name)


def validate_event_payload(event_name: str, payload: Dict[str, Any]) -> bool:
    """Validate payload against event schema (basic validation)"""
    definition = get_event_definition(event_name)
    if not definition:
        return False

    schema = definition.get("payload_schema", {})
    required_fields = schema.get("required", [])

    # Check required fields are present
    for field in required_fields:
        if field not in payload:
            return False

    return True


async def initialize_webhook_events(db):
    """Initialize webhook event types in database"""
    from app.services.webhook_service import WebhookEventTypeService

    service = WebhookEventTypeService(db)

    for event_name, definition in ISP_WEBHOOK_EVENTS.items():
        # Check if event type already exists
        existing = service.get_event_type_by_name(event_name)
        if not existing:
            # Create new event type
            event_data = {
                "name": event_name,
                "category": definition["category"],
                "description": definition["description"],
                "payload_schema": definition["payload_schema"],
                "sample_payload": definition["sample_payload"],
                "is_active": True,
                "requires_authentication": True,
                "max_retry_attempts": 5,
            }
            service.create_event_type(event_data)
            print(f"Created webhook event type: {event_name}")
        else:
            # Update existing event type with new schema/sample
            updates = {
                "description": definition["description"],
                "payload_schema": definition["payload_schema"],
                "sample_payload": definition["sample_payload"],
            }
            service.update_event_type(existing.id, updates)
            print(f"Updated webhook event type: {event_name}")


# Helper functions for triggering events
class WebhookEventTrigger:
    """Helper class for triggering webhook events from application code"""

    def __init__(self, db):
        self.db = db

    async def trigger_event(
        self,
        event_name: str,
        payload: Dict[str, Any],
        triggered_by_user_id: int = None,
        triggered_by_customer_id: int = None,
        source_ip: str = None,
        user_agent: str = None,
    ):
        """Trigger a webhook event"""
        from datetime import datetime, timezone

        from app.schemas.webhooks import WebhookEventCreate
        from app.services.webhook_service import (
            WebhookEventService,
            WebhookEventTypeService,
        )

        # Get event type
        event_type_service = WebhookEventTypeService(self.db)
        event_type = event_type_service.get_event_type_by_name(event_name)

        if not event_type or not event_type.is_active:
            return None

        # Validate payload
        if not validate_event_payload(event_name, payload):
            raise ValueError(f"Invalid payload for event {event_name}")

        # Create event
        event_service = WebhookEventService(self.db)
        event_data = WebhookEventCreate(
            event_type_id=event_type.id,
            payload=payload,
            metadata={
                "event_name": event_name,
                "triggered_at": datetime.now(timezone.utc).isoformat(),
            },
            occurred_at=datetime.now(timezone.utc),
            source_ip=source_ip,
            user_agent=user_agent,
            triggered_by_user_id=triggered_by_user_id,
            triggered_by_customer_id=triggered_by_customer_id,
        )

        event = event_service.create_event(event_data)

        # Process event asynchronously
        from app.services.webhook_service import WebhookDeliveryEngine

        engine = WebhookDeliveryEngine(self.db)
        await engine.process_event(event)

        return event
