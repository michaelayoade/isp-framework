"""
Customer Portal Service Layer
Comprehensive business logic for customer self-service portal operations
"""

import logging
import secrets
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.customer.base import Customer
from app.models.customer.portal_complete import (
    CustomerPortalNotification,
    CustomerPortalPayment,
    CustomerPortalServiceRequest,
    CustomerPortalSession,
)
from app.models.services.instances import CustomerService

logger = logging.getLogger(__name__)


class CustomerPortalSessionService:
    """Manage customer portal authentication sessions"""

    def __init__(self, db: Session = None):
        self.db = db or SessionLocal()

    def create_session(
        self, customer_id: int, session_data: Dict[str, Any]
    ) -> CustomerPortalSession:
        """Create new customer portal session"""
        try:
            session_token = CustomerPortalSession.generate_session_token()
            expires_at = datetime.now() + timedelta(hours=24)

            session = CustomerPortalSession(
                customer_id=customer_id,
                session_token=session_token,
                session_type=session_data.get("session_type", "web"),
                device_info=session_data.get("device_info", {}),
                ip_address=session_data.get("ip_address"),
                user_agent=session_data.get("user_agent"),
                login_method=session_data.get("login_method", "password"),
                expires_at=expires_at,
            )

            self.db.add(session)
            self.db.commit()

            logger.info(f"Created portal session for customer {customer_id}")
            return session

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating portal session: {e}")
            raise

    def validate_session(self, session_token: str) -> Optional[CustomerPortalSession]:
        """Validate and return active session"""
        try:
            session = (
                self.db.query(CustomerPortalSession)
                .filter(
                    CustomerPortalSession.session_token == session_token,
                    CustomerPortalSession.is_active is True,
                    CustomerPortalSession.expires_at > datetime.now(),
                )
                .first()
            )

            if session:
                session.last_activity = datetime.now()
                self.db.commit()

            return session

        except Exception as e:
            logger.error(f"Error validating session: {e}")
            return None


class CustomerPortalPaymentService:
    """Handle customer portal payment operations"""

    def __init__(self, db: Session = None):
        self.db = db or SessionLocal()

    def process_payment(
        self, customer_id: int, payment_data: Dict[str, Any]
    ) -> CustomerPortalPayment:
        """Process customer payment through portal"""
        try:
            payment_reference = f"PRT-{datetime.now().strftime('%Y%m%d')}-{secrets.token_hex(4).upper()}"

            payment = CustomerPortalPayment(
                customer_id=customer_id,
                payment_amount=payment_data["amount"],
                currency=payment_data.get("currency", "USD"),
                payment_method=payment_data["payment_method"],
                payment_reference=payment_reference,
                payment_gateway=payment_data.get("gateway"),
                invoice_ids=payment_data.get("invoice_ids", []),
                payment_method_token=payment_data.get("payment_method_token"),
                billing_name=payment_data.get("billing_name"),
                billing_email=payment_data.get("billing_email"),
            )

            self.db.add(payment)
            self.db.flush()

            # Mock gateway processing
            gateway_response = {
                "success": True,
                "transaction_id": f"TXN_{secrets.token_hex(8).upper()}",
                "fee": float(payment.payment_amount) * 0.029,
            }

            if gateway_response.get("success"):
                payment.status = "completed"
                payment.external_payment_id = gateway_response.get("transaction_id")
                payment.processed_at = datetime.now()
                payment.processor_fee = gateway_response.get("fee", 0)
                payment.net_amount = payment.payment_amount - payment.processor_fee
            else:
                payment.status = "failed"
                payment.failure_reason = gateway_response.get("error_message")

            payment.gateway_response = gateway_response
            self.db.commit()

            logger.info(
                f"Processed payment {payment.id} for customer {customer_id}: {payment.status}"
            )
            return payment

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error processing payment: {e}")
            raise


class CustomerPortalServiceRequestService:
    """Handle customer service change requests"""

    def __init__(self, db: Session = None):
        self.db = db or SessionLocal()

    def create_service_request(
        self, customer_id: int, request_data: Dict[str, Any]
    ) -> CustomerPortalServiceRequest:
        """Create new service change request"""
        try:
            service_request = CustomerPortalServiceRequest(
                customer_id=customer_id,
                request_type=request_data["request_type"],
                request_title=request_data["request_title"],
                request_description=request_data.get("request_description"),
                current_service_id=request_data.get("current_service_id"),
                requested_tariff_id=request_data.get("requested_tariff_id"),
                preferred_date=request_data.get("preferred_date"),
                urgency=request_data.get("urgency", "normal"),
                reason=request_data.get("reason"),
                custom_fields=request_data.get("custom_fields", {}),
            )

            self.db.add(service_request)
            self.db.commit()

            logger.info(
                f"Created service request {service_request.id} for customer {customer_id}"
            )
            return service_request

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating service request: {e}")
            raise

    def suspend_service(self, customer_id: int, service_id: int) -> Dict[str, Any]:
        """Suspend a customer service."""
        try:
            # Get the customer service
            customer_service = (
                self.db.query(CustomerService)
                .filter(
                    CustomerService.customer_id == customer_id,
                    CustomerService.id == service_id
                )
                .first()
            )
            
            if not customer_service:
                raise ValueError("Service not found or access denied")
            
            if customer_service.status == "suspended":
                raise ValueError("Service is already suspended")
            
            # Update service status
            customer_service.status = "suspended"
            customer_service.updated_at = datetime.now()
            
            self.db.commit()
            
            logger.info(f"Service {service_id} suspended for customer {customer_id}")
            return {
                "success": True,
                "effective_date": datetime.now().isoformat(),
                "previous_status": "active"
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error suspending service {service_id}: {e}")
            raise
    
    def resume_service(self, customer_id: int, service_id: int) -> Dict[str, Any]:
        """Resume a suspended customer service."""
        try:
            # Get the customer service
            customer_service = (
                self.db.query(CustomerService)
                .filter(
                    CustomerService.customer_id == customer_id,
                    CustomerService.id == service_id
                )
                .first()
            )
            
            if not customer_service:
                raise ValueError("Service not found or access denied")
            
            if customer_service.status != "suspended":
                raise ValueError("Service is not suspended")
            
            # Update service status
            customer_service.status = "active"
            customer_service.updated_at = datetime.now()
            
            self.db.commit()
            
            logger.info(f"Service {service_id} resumed for customer {customer_id}")
            return {
                "success": True,
                "effective_date": datetime.now().isoformat(),
                "previous_status": "suspended"
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error resuming service {service_id}: {e}")
            raise
    
    def get_service_status(self, customer_id: int, service_id: int) -> Dict[str, Any]:
        """Get the current status of a customer service."""
        try:
            customer_service = (
                self.db.query(CustomerService)
                .filter(
                    CustomerService.customer_id == customer_id,
                    CustomerService.id == service_id
                )
                .first()
            )
            
            if not customer_service:
                raise ValueError("Service not found or access denied")
            
            return {
                "service_id": service_id,
                "status": customer_service.status,
                "service_type": customer_service.service_type,
                "created_at": customer_service.created_at.isoformat() if customer_service.created_at else None,
                "updated_at": customer_service.updated_at.isoformat() if customer_service.updated_at else None,
                "can_suspend": customer_service.status == "active",
                "can_resume": customer_service.status == "suspended"
            }
            
        except Exception as e:
            logger.error(f"Error getting service status {service_id}: {e}")
            raise


class CustomerPortalDashboardService:
    """Generate customer portal dashboard data"""

    def __init__(self, db: Session = None):
        self.db = db or SessionLocal()

    def get_dashboard_data(self, customer_id: int) -> Dict[str, Any]:
        """Get comprehensive dashboard data for customer"""
        try:
            customer = self.db.query(Customer).filter_by(id=customer_id).first()
            if not customer:
                raise ValueError("Customer not found")

            dashboard = {
                "customer_info": {
                    "name": customer.name,
                    "email": customer.email,
                    "account_status": customer.status,
                    "customer_since": customer.created_at.strftime("%B %Y"),
                    "portal_id": customer.portal_id,
                },
                "billing_summary": self._get_billing_summary(customer_id),
                "service_summary": self._get_service_summary(customer_id),
                "notifications": self._get_notifications_summary(customer_id),
                "quick_actions": [
                    {
                        "title": "Pay Bills",
                        "url": "/portal/billing/pay",
                        "icon": "payment",
                    },
                    {
                        "title": "View Usage",
                        "url": "/portal/services/usage",
                        "icon": "chart",
                    },
                    {
                        "title": "Upgrade Service",
                        "url": "/portal/services/upgrade",
                        "icon": "upgrade",
                    },
                    {
                        "title": "Create Support Ticket",
                        "url": "/portal/support/new",
                        "icon": "support",
                    },
                ],
            }

            return dashboard

        except Exception as e:
            logger.error(f"Error getting dashboard data: {e}")
            raise

    def _get_billing_summary(self, customer_id: int) -> Dict[str, Any]:
        """Get billing summary"""
        return {
            "current_balance": 150.00,
            "overdue_amount": 0.00,
            "next_invoice_date": (datetime.now() + timedelta(days=15)).strftime(
                "%Y-%m-%d"
            ),
            "autopay_enabled": False,
        }

    def _get_service_summary(self, customer_id: int) -> Dict[str, Any]:
        """Get service summary"""
        services = (
            self.db.query(CustomerService).filter_by(customer_id=customer_id).all()
        )

        return {
            "total_services": len(services),
            "active_services": len([s for s in services if s.status == "active"]),
            "total_monthly_cost": sum(float(s.tariff.monthly_price) for s in services),
            "services": [
                {
                    "id": service.id,
                    "name": service.service_name,
                    "type": service.service_type,
                    "status": service.status,
                    "monthly_price": float(service.tariff.monthly_price),
                }
                for service in services
            ],
        }

    def _get_notifications_summary(self, customer_id: int) -> Dict[str, Any]:
        """Get notifications summary"""
        unread_count = (
            self.db.query(CustomerPortalNotification)
            .filter_by(customer_id=customer_id, is_read=False)
            .count()
        )

        recent_notifications = (
            self.db.query(CustomerPortalNotification)
            .filter_by(customer_id=customer_id)
            .order_by(desc(CustomerPortalNotification.created_at))
            .limit(5)
            .all()
        )

        return {
            "unread_count": unread_count,
            "recent": [
                {
                    "id": notif.id,
                    "title": notif.title,
                    "message": notif.message,
                    "type": notif.notification_type,
                    "priority": notif.priority,
                    "created_at": notif.created_at.isoformat(),
                    "is_read": notif.is_read,
                }
                for notif in recent_notifications
            ],
        }


class CustomerPortalNotificationService:
    """Manage customer portal notifications"""

    def __init__(self, db: Session = None):
        self.db = db or SessionLocal()

    def create_notification(
        self, customer_id: int, notification_data: Dict[str, Any]
    ) -> CustomerPortalNotification:
        """Create new customer notification"""
        try:
            notification = CustomerPortalNotification(
                customer_id=customer_id,
                notification_type=notification_data["notification_type"],
                title=notification_data["title"],
                message=notification_data["message"],
                priority=notification_data.get("priority", "normal"),
                category=notification_data.get("category"),
                action_required=notification_data.get("action_required", False),
                action_url=notification_data.get("action_url"),
                action_text=notification_data.get("action_text"),
            )

            self.db.add(notification)
            self.db.commit()

            logger.info(
                f"Created notification {notification.id} for customer {customer_id}"
            )
            return notification

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating notification: {e}")
            raise

    def mark_as_read(self, customer_id: int, notification_id: int) -> bool:
        """Mark notification as read"""
        try:
            notification = (
                self.db.query(CustomerPortalNotification)
                .filter_by(id=notification_id, customer_id=customer_id)
                .first()
            )

            if notification and not notification.is_read:
                notification.is_read = True
                notification.read_at = datetime.now()
                self.db.commit()
                return True

            return False

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error marking notification as read: {e}")
            return False
