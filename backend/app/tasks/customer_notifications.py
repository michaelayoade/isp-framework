"""
Customer Notification Background Tasks.

Handles email, SMS, and other customer communications with comprehensive
error handling and dead-letter queue integration.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List

import structlog
from celery import current_task

from app.core.celery import ISPFrameworkTask, celery_app
from app.core.database import get_db
from app.core.error_handling import (
    ErrorCategory,
    ErrorImpact,
    ErrorSeverity,
    ISPException,
)
from app.models.customer.base import Customer
from app.models.services.instances import CustomerService

logger = structlog.get_logger("isp.tasks.customer_notifications")


@celery_app.task(
    bind=True, base=ISPFrameworkTask, name="app.tasks.customer_notifications.send_email"
)
def send_email(
    self,
    customer_id: int,
    template_name: str,
    context: Dict[str, Any],
    subject: str = None,
    priority: str = "normal",
) -> Dict[str, Any]:
    """
    Send email notification to customer.

    This is a critical task that may fail due to:
    - SMTP server issues
    - Invalid email addresses
    - Template rendering errors
    - Network connectivity issues
    """
    try:
        db = next(get_db())

        # Get customer
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            raise ISPException(
                title="Customer Not Found",
                detail=f"Customer {customer_id} not found for email notification",
                severity=ErrorSeverity.HIGH,
                category=ErrorCategory.BUSINESS_LOGIC,
                impact=ErrorImpact.CUSTOMER_FACING,
            )

        if not customer.email:
            raise ISPException(
                title="No Email Address",
                detail=f"Customer {customer_id} has no email address",
                severity=ErrorSeverity.MEDIUM,
                category=ErrorCategory.BUSINESS_LOGIC,
                impact=ErrorImpact.CUSTOMER_FACING,
            )

        logger.info(
            "Sending email notification",
            customer_id=customer_id,
            email=customer.email,
            template=template_name,
            priority=priority,
            task_id=current_task.request.id,
        )

        # Simulate email sending (in real implementation, would use SMTP)
        if template_name == "test_failure":
            # Simulate a failure for testing dead-letter queue
            raise Exception("Simulated SMTP server connection timeout")

        # Mock successful email sending
        result = {
            "success": True,
            "customer_id": customer_id,
            "email": customer.email,
            "template": template_name,
            "subject": subject or f"ISP Framework Notification - {template_name}",
            "priority": priority,
            "sent_at": datetime.now(timezone.utc).isoformat(),
            "message_id": f"msg_{current_task.request.id}_{customer_id}",
            "task_id": current_task.request.id,
        }

        logger.info("Email notification sent successfully", **result)

        return result

    except Exception as e:
        logger.error(
            "Email notification failed",
            customer_id=customer_id,
            template=template_name,
            error=str(e),
            task_id=current_task.request.id,
        )
        raise
    finally:
        db.close()


@celery_app.task(
    bind=True, base=ISPFrameworkTask, name="app.tasks.customer_notifications.send_sms"
)
def send_sms(
    self, customer_id: int, message: str, priority: str = "normal"
) -> Dict[str, Any]:
    """
    Send SMS notification to customer.

    This task may fail due to:
    - SMS gateway issues
    - Invalid phone numbers
    - Rate limiting
    - Insufficient credits
    """
    try:
        db = next(get_db())

        # Get customer
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            raise ISPException(
                title="Customer Not Found",
                detail=f"Customer {customer_id} not found for SMS notification",
                severity=ErrorSeverity.HIGH,
                category=ErrorCategory.BUSINESS_LOGIC,
                impact=ErrorImpact.CUSTOMER_FACING,
            )

        if not customer.phone:
            raise ISPException(
                title="No Phone Number",
                detail=f"Customer {customer_id} has no phone number",
                severity=ErrorSeverity.MEDIUM,
                category=ErrorCategory.BUSINESS_LOGIC,
                impact=ErrorImpact.CUSTOMER_FACING,
            )

        logger.info(
            "Sending SMS notification",
            customer_id=customer_id,
            phone=customer.phone,
            message_length=len(message),
            priority=priority,
            task_id=current_task.request.id,
        )

        # Simulate SMS sending (in real implementation, would use SMS gateway)
        if "test_failure" in message:
            # Simulate a failure for testing dead-letter queue
            raise Exception("SMS gateway rate limit exceeded")

        # Mock successful SMS sending
        result = {
            "success": True,
            "customer_id": customer_id,
            "phone": customer.phone,
            "message": message[:100] + "..." if len(message) > 100 else message,
            "priority": priority,
            "sent_at": datetime.now(timezone.utc).isoformat(),
            "sms_id": f"sms_{current_task.request.id}_{customer_id}",
            "task_id": current_task.request.id,
        }

        logger.info("SMS notification sent successfully", **result)

        return result

    except Exception as e:
        logger.error(
            "SMS notification failed",
            customer_id=customer_id,
            error=str(e),
            task_id=current_task.request.id,
        )
        raise
    finally:
        db.close()


@celery_app.task(
    bind=True,
    base=ISPFrameworkTask,
    name="app.tasks.customer_notifications.send_service_suspension_notification",
)
def send_service_suspension_notification(
    self,
    customer_id: int,
    customer_service_id: int,
    suspension_reason: str,
    grace_period_hours: int,
) -> Dict[str, Any]:
    """Send notification about service suspension."""
    try:
        db = next(get_db())

        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        customer_service = (
            db.query(CustomerService)
            .filter(CustomerService.id == customer_service_id)
            .first()
        )

        if not customer or not customer_service:
            raise ISPException(
                title="Customer or Service Not Found",
                detail=f"Customer {customer_id} or service {customer_service_id} not found",
                severity=ErrorSeverity.HIGH,
                category=ErrorCategory.BUSINESS_LOGIC,
                impact=ErrorImpact.CUSTOMER_FACING,
            )

        # Send email notification
        email_context = {
            "customer_name": customer.first_name,
            "service_name": customer_service.service_template.name,
            "suspension_reason": suspension_reason,
            "grace_period_hours": grace_period_hours,
            "portal_id": customer.portal_id,
        }

        email_task = send_email.delay(
            customer_id=customer_id,
            template_name="service_suspension",
            context=email_context,
            subject=f"Service Suspension Notice - {customer.portal_id}",
            priority="high",
        )

        # Send SMS notification
        sms_message = (
            f"NOTICE: Your internet service has been suspended due to {suspension_reason}. "
            f"You have {grace_period_hours} hours grace period. Contact support for assistance."
        )

        sms_task = send_sms.delay(
            customer_id=customer_id, message=sms_message, priority="high"
        )

        result = {
            "success": True,
            "customer_id": customer_id,
            "customer_service_id": customer_service_id,
            "suspension_reason": suspension_reason,
            "grace_period_hours": grace_period_hours,
            "email_task_id": email_task.id,
            "sms_task_id": sms_task.id,
            "sent_at": datetime.now(timezone.utc).isoformat(),
        }

        logger.info("Service suspension notifications sent", **result)

        return result

    except Exception as e:
        logger.error(
            "Service suspension notification failed",
            customer_id=customer_id,
            customer_service_id=customer_service_id,
            error=str(e),
        )
        raise
    finally:
        db.close()


@celery_app.task(
    bind=True,
    base=ISPFrameworkTask,
    name="app.tasks.customer_notifications.send_service_restoration_notification",
)
def send_service_restoration_notification(
    self, customer_id: int, customer_service_id: int, restoration_notes: str
) -> Dict[str, Any]:
    """Send notification about service restoration."""
    try:
        db = next(get_db())

        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        customer_service = (
            db.query(CustomerService)
            .filter(CustomerService.id == customer_service_id)
            .first()
        )

        if not customer or not customer_service:
            raise ISPException(
                title="Customer or Service Not Found",
                detail=f"Customer {customer_id} or service {customer_service_id} not found",
                severity=ErrorSeverity.HIGH,
                category=ErrorCategory.BUSINESS_LOGIC,
                impact=ErrorImpact.CUSTOMER_FACING,
            )

        # Send email notification
        email_context = {
            "customer_name": customer.first_name,
            "service_name": customer_service.service_template.name,
            "restoration_notes": restoration_notes,
            "portal_id": customer.portal_id,
        }

        email_task = send_email.delay(
            customer_id=customer_id,
            template_name="service_restoration",
            context=email_context,
            subject=f"Service Restored - {customer.portal_id}",
            priority="high",
        )

        # Send SMS notification
        sms_message = (
            "GOOD NEWS: Your internet service has been restored. "
            "Thank you for your patience. Enjoy your connection!"
        )

        sms_task = send_sms.delay(
            customer_id=customer_id, message=sms_message, priority="high"
        )

        result = {
            "success": True,
            "customer_id": customer_id,
            "customer_service_id": customer_service_id,
            "restoration_notes": restoration_notes,
            "email_task_id": email_task.id,
            "sms_task_id": sms_task.id,
            "sent_at": datetime.now(timezone.utc).isoformat(),
        }

        logger.info("Service restoration notifications sent", **result)

        return result

    except Exception as e:
        logger.error(
            "Service restoration notification failed",
            customer_id=customer_id,
            customer_service_id=customer_service_id,
            error=str(e),
        )
        raise
    finally:
        db.close()


@celery_app.task(
    bind=True,
    base=ISPFrameworkTask,
    name="app.tasks.customer_notifications.send_bulk_notifications",
)
def send_bulk_notifications(
    self,
    customer_ids: List[int],
    template_name: str,
    context: Dict[str, Any],
    notification_type: str = "email",
) -> Dict[str, Any]:
    """
    Send bulk notifications to multiple customers.

    This task demonstrates batch processing with individual task spawning.
    """
    try:
        logger.info(
            "Starting bulk notification sending",
            customer_count=len(customer_ids),
            template=template_name,
            notification_type=notification_type,
            task_id=current_task.request.id,
        )

        task_ids = []
        failed_customers = []

        for customer_id in customer_ids:
            try:
                if notification_type == "email":
                    task = send_email.delay(
                        customer_id=customer_id,
                        template_name=template_name,
                        context=context,
                        priority="bulk",
                    )
                elif notification_type == "sms":
                    # Extract message from context
                    message = context.get(
                        "message", "Bulk notification from ISP Framework"
                    )
                    task = send_sms.delay(
                        customer_id=customer_id, message=message, priority="bulk"
                    )
                else:
                    raise ValueError(
                        f"Unsupported notification type: {notification_type}"
                    )

                task_ids.append({"customer_id": customer_id, "task_id": task.id})

            except Exception as e:
                logger.error(
                    "Failed to queue notification for customer",
                    customer_id=customer_id,
                    error=str(e),
                )
                failed_customers.append({"customer_id": customer_id, "error": str(e)})

        result = {
            "success": True,
            "total_customers": len(customer_ids),
            "queued_tasks": len(task_ids),
            "failed_customers_count": len(failed_customers),
            "task_ids": task_ids,
            "failed_customers": failed_customers,
            "template": template_name,
            "notification_type": notification_type,
            "queued_at": datetime.now(timezone.utc).isoformat(),
        }

        logger.info("Bulk notification queuing completed", **result)

        return result

    except Exception as e:
        logger.error(
            "Bulk notification queuing failed",
            customer_count=len(customer_ids),
            template=template_name,
            error=str(e),
        )
        raise
