"""
Communications Service Layer for ISP Framework

Handles email, SMS, and notification management with Jinja2 templating,
provider management, delivery tracking, and automated communication rules.
"""

import logging
import smtplib
import ssl
from datetime import datetime, timedelta, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, List, Optional, Tuple

import requests
from jinja2 import BaseLoader, Environment, TemplateError, select_autoescape
from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from app.models.communications import (
    CommunicationLog,
    CommunicationPreference,
    CommunicationProvider,
    CommunicationQueue,
    CommunicationStatus,
    CommunicationTemplate,
    CommunicationType,
    TemplateCategory,
)
from app.schemas.communications import (
    BulkCommunicationRequest,
    CommunicationPreferenceUpdate,
    CommunicationProviderCreate,
    CommunicationProviderUpdate,
    CommunicationTemplateCreate,
    CommunicationTemplateUpdate,
    SendCommunicationRequest,
)

logger = logging.getLogger(__name__)


class TemplateService:
    """Service for managing communication templates"""

    def __init__(self, db: Session):
        self.db = db
        self.jinja_env = Environment(
            loader=BaseLoader(), autoescape=select_autoescape(["html", "xml"])
        )

    def create_template(
        self, template_data: CommunicationTemplateCreate, created_by: int
    ) -> CommunicationTemplate:
        """Create a new communication template"""
        # Validate template syntax
        self._validate_template_syntax(template_data.body_template)
        if template_data.subject_template:
            self._validate_template_syntax(template_data.subject_template)
        if template_data.html_template:
            self._validate_template_syntax(template_data.html_template)

        template = CommunicationTemplate(**template_data.dict(), created_by=created_by)

        self.db.add(template)
        self.db.commit()
        self.db.refresh(template)

        logger.info(
            f"Created communication template: {template.name} (ID: {template.id})"
        )
        return template

    def get_template(self, template_id: int) -> Optional[CommunicationTemplate]:
        """Get template by ID"""
        return (
            self.db.query(CommunicationTemplate)
            .filter(CommunicationTemplate.id == template_id)
            .first()
        )

    def get_templates(
        self,
        skip: int = 0,
        limit: int = 100,
        category: Optional[TemplateCategory] = None,
        communication_type: Optional[CommunicationType] = None,
        is_active: Optional[bool] = None,
        search_term: Optional[str] = None,
    ) -> Tuple[List[CommunicationTemplate], int]:
        """Get templates with filtering and pagination"""
        query = self.db.query(CommunicationTemplate)

        if category:
            query = query.filter(CommunicationTemplate.category == category)
        if communication_type:
            query = query.filter(
                CommunicationTemplate.communication_type == communication_type
            )
        if is_active is not None:
            query = query.filter(CommunicationTemplate.is_active == is_active)
        if search_term:
            query = query.filter(
                or_(
                    CommunicationTemplate.name.ilike(f"%{search_term}%"),
                    CommunicationTemplate.description.ilike(f"%{search_term}%"),
                )
            )

        total = query.count()
        templates = (
            query.order_by(CommunicationTemplate.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

        return templates, total

    def update_template(
        self, template_id: int, template_data: CommunicationTemplateUpdate
    ) -> Optional[CommunicationTemplate]:
        """Update a communication template"""
        template = self.get_template(template_id)
        if not template:
            return None

        if template.is_system:
            raise ValueError("System templates cannot be modified")

        update_data = template_data.dict(exclude_unset=True)

        # Validate template syntax if templates are being updated
        if "body_template" in update_data:
            self._validate_template_syntax(update_data["body_template"])
        if "subject_template" in update_data and update_data["subject_template"]:
            self._validate_template_syntax(update_data["subject_template"])
        if "html_template" in update_data and update_data["html_template"]:
            self._validate_template_syntax(update_data["html_template"])

        for field, value in update_data.items():
            setattr(template, field, value)

        self.db.commit()
        self.db.refresh(template)

        logger.info(
            f"Updated communication template: {template.name} (ID: {template.id})"
        )
        return template

    def delete_template(self, template_id: int) -> bool:
        """Delete a communication template"""
        template = self.get_template(template_id)
        if not template:
            return False

        if template.is_system:
            raise ValueError("System templates cannot be deleted")

        # Check if template is being used
        usage_count = (
            self.db.query(CommunicationLog)
            .filter(CommunicationLog.template_id == template_id)
            .count()
        )

        if usage_count > 0:
            # Deactivate instead of delete if template has been used
            template.is_active = False
            self.db.commit()
            logger.info(
                f"Deactivated communication template: {template.name} (ID: {template.id})"
            )
        else:
            self.db.delete(template)
            self.db.commit()
            logger.info(
                f"Deleted communication template: {template.name} (ID: {template.id})"
            )

        return True

    def render_template(
        self, template_id: int, variables: Dict[str, Any]
    ) -> Dict[str, str]:
        """Render a template with provided variables"""
        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found")

        if not template.is_active:
            raise ValueError(f"Template {template_id} is not active")

        result = {}

        try:
            # Render body template
            body_template = self.jinja_env.from_string(template.body_template)
            result["body"] = body_template.render(**variables)

            # Render subject template if exists
            if template.subject_template:
                subject_template = self.jinja_env.from_string(template.subject_template)
                result["subject"] = subject_template.render(**variables)

            # Render HTML template if exists
            if template.html_template:
                html_template = self.jinja_env.from_string(template.html_template)
                result["html_body"] = html_template.render(**variables)

        except TemplateError as e:
            logger.error(
                f"Template rendering error for template {template_id}: {str(e)}"
            )
            raise ValueError(f"Template rendering failed: {str(e)}")

        return result

    def _validate_template_syntax(self, template_content: str):
        """Validate Jinja2 template syntax"""
        try:
            self.jinja_env.from_string(template_content)
        except TemplateError as e:
            raise ValueError(f"Invalid template syntax: {str(e)}")


class ProviderService:
    """Service for managing communication providers"""

    def __init__(self, db: Session):
        self.db = db

    def create_provider(
        self, provider_data: CommunicationProviderCreate
    ) -> CommunicationProvider:
        """Create a new communication provider"""
        # If this is set as default, unset other defaults of same type
        if provider_data.is_default:
            self.db.query(CommunicationProvider).filter(
                and_(
                    CommunicationProvider.provider_type == provider_data.provider_type,
                    CommunicationProvider.is_default is True,
                )
            ).update({"is_default": False})

        provider = CommunicationProvider(**provider_data.dict())

        self.db.add(provider)
        self.db.commit()
        self.db.refresh(provider)

        logger.info(
            f"Created communication provider: {provider.name} (ID: {provider.id})"
        )
        return provider

    def get_provider(self, provider_id: int) -> Optional[CommunicationProvider]:
        """Get provider by ID"""
        return (
            self.db.query(CommunicationProvider)
            .filter(CommunicationProvider.id == provider_id)
            .first()
        )

    def get_providers(
        self,
        skip: int = 0,
        limit: int = 100,
        provider_type: Optional[CommunicationType] = None,
        is_active: Optional[bool] = None,
        search_term: Optional[str] = None,
    ) -> Tuple[List[CommunicationProvider], int]:
        """Get providers with filtering and pagination"""
        query = self.db.query(CommunicationProvider)

        if provider_type:
            query = query.filter(CommunicationProvider.provider_type == provider_type)
        if is_active is not None:
            query = query.filter(CommunicationProvider.is_active == is_active)
        if search_term:
            query = query.filter(
                or_(
                    CommunicationProvider.name.ilike(f"%{search_term}%"),
                    CommunicationProvider.description.ilike(f"%{search_term}%"),
                )
            )

        total = query.count()
        providers = (
            query.order_by(CommunicationProvider.priority.asc())
            .offset(skip)
            .limit(limit)
            .all()
        )

        return providers, total

    def get_default_provider(
        self, provider_type: CommunicationType
    ) -> Optional[CommunicationProvider]:
        """Get default provider for a communication type"""
        return (
            self.db.query(CommunicationProvider)
            .filter(
                and_(
                    CommunicationProvider.provider_type == provider_type,
                    CommunicationProvider.is_default is True,
                    CommunicationProvider.is_active is True,
                )
            )
            .first()
        )

    def update_provider(
        self, provider_id: int, provider_data: CommunicationProviderUpdate
    ) -> Optional[CommunicationProvider]:
        """Update a communication provider"""
        provider = self.get_provider(provider_id)
        if not provider:
            return None

        update_data = provider_data.dict(exclude_unset=True)

        # Handle default provider logic
        if update_data.get("is_default"):
            self.db.query(CommunicationProvider).filter(
                and_(
                    CommunicationProvider.provider_type == provider.provider_type,
                    CommunicationProvider.id != provider_id,
                    CommunicationProvider.is_default is True,
                )
            ).update({"is_default": False})

        for field, value in update_data.items():
            setattr(provider, field, value)

        self.db.commit()
        self.db.refresh(provider)

        logger.info(
            f"Updated communication provider: {provider.name} (ID: {provider.id})"
        )
        return provider

    def delete_provider(self, provider_id: int) -> bool:
        """Delete a communication provider"""
        provider = self.get_provider(provider_id)
        if not provider:
            return False

        # Check if provider is being used
        usage_count = (
            self.db.query(CommunicationLog)
            .filter(CommunicationLog.provider_id == provider_id)
            .count()
        )

        if usage_count > 0:
            # Deactivate instead of delete if provider has been used
            provider.is_active = False
            self.db.commit()
            logger.info(
                f"Deactivated communication provider: {provider.name} (ID: {provider.id})"
            )
        else:
            self.db.delete(provider)
            self.db.commit()
            logger.info(
                f"Deleted communication provider: {provider.name} (ID: {provider.id})"
            )

        return True


class CommunicationService:
    """Main service for sending and managing communications"""

    def __init__(self, db: Session):
        self.db = db
        self.template_service = TemplateService(db)
        self.provider_service = ProviderService(db)

    def send_communication(
        self, request: SendCommunicationRequest, admin_id: Optional[int] = None
    ) -> CommunicationLog:
        """Send a single communication"""
        # Prepare communication data
        comm_data = {
            "communication_type": request.communication_type,
            "priority": request.priority,
            "recipient_email": request.recipient_email,
            "recipient_phone": request.recipient_phone,
            "recipient_name": request.recipient_name,
            "subject": request.subject,
            "body": request.body,
            "html_body": request.html_body,
            "template_id": request.template_id,
            "customer_id": request.customer_id,
            "admin_id": admin_id,
            "context_type": request.context_type,
            "context_id": request.context_id,
            "template_variables": request.template_variables,
            "scheduled_at": request.scheduled_at,
        }

        # Render template if template_id is provided
        if request.template_id:
            rendered = self.template_service.render_template(
                request.template_id, request.template_variables
            )
            comm_data.update(rendered)

        # Create communication log entry
        comm_log = CommunicationLog(**comm_data)
        self.db.add(comm_log)
        self.db.commit()
        self.db.refresh(comm_log)

        # Send immediately if not scheduled
        if not request.scheduled_at or request.scheduled_at <= datetime.now(
            timezone.utc
        ):
            self._send_communication_now(comm_log)

        return comm_log

    def send_bulk_communication(
        self, request: BulkCommunicationRequest, admin_id: Optional[int] = None
    ) -> CommunicationQueue:
        """Queue bulk communications for processing"""
        queue_data = {
            **request.dict(),
            "total_recipients": len(request.recipients),
            "created_by": admin_id,
        }

        queue = CommunicationQueue(**queue_data)
        self.db.add(queue)
        self.db.commit()
        self.db.refresh(queue)

        # Process immediately if not scheduled
        if not request.scheduled_at or request.scheduled_at <= datetime.now(
            timezone.utc
        ):
            self._process_communication_queue(queue.id)

        return queue

    def get_communication_log(self, log_id: int) -> Optional[CommunicationLog]:
        """Get communication log by ID"""
        return (
            self.db.query(CommunicationLog)
            .filter(CommunicationLog.id == log_id)
            .first()
        )

    def get_communication_logs(
        self,
        skip: int = 0,
        limit: int = 100,
        communication_type: Optional[CommunicationType] = None,
        status: Optional[CommunicationStatus] = None,
        customer_id: Optional[int] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> Tuple[List[CommunicationLog], int]:
        """Get communication logs with filtering and pagination"""
        query = self.db.query(CommunicationLog)

        if communication_type:
            query = query.filter(
                CommunicationLog.communication_type == communication_type
            )
        if status:
            query = query.filter(CommunicationLog.status == status)
        if customer_id:
            query = query.filter(CommunicationLog.customer_id == customer_id)
        if date_from:
            query = query.filter(CommunicationLog.created_at >= date_from)
        if date_to:
            query = query.filter(CommunicationLog.created_at <= date_to)

        total = query.count()
        logs = (
            query.order_by(CommunicationLog.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

        return logs, total

    def retry_failed_communication(self, log_id: int) -> bool:
        """Retry a failed communication"""
        comm_log = self.get_communication_log(log_id)
        if not comm_log:
            return False

        if comm_log.status not in [
            CommunicationStatus.FAILED,
            CommunicationStatus.BOUNCED,
        ]:
            return False

        if comm_log.retry_count >= comm_log.max_retries:
            return False

        comm_log.retry_count += 1
        comm_log.status = CommunicationStatus.PENDING
        comm_log.error_message = None

        self.db.commit()

        # Attempt to send again
        self._send_communication_now(comm_log)

        return True

    def get_communication_stats(self, days: int = 30) -> Dict[str, Any]:
        """Get communication statistics"""
        date_from = datetime.now(timezone.utc) - timedelta(days=days)

        # Basic stats
        total_sent = (
            self.db.query(CommunicationLog)
            .filter(CommunicationLog.created_at >= date_from)
            .count()
        )

        total_delivered = (
            self.db.query(CommunicationLog)
            .filter(
                and_(
                    CommunicationLog.created_at >= date_from,
                    CommunicationLog.status == CommunicationStatus.DELIVERED,
                )
            )
            .count()
        )

        total_failed = (
            self.db.query(CommunicationLog)
            .filter(
                and_(
                    CommunicationLog.created_at >= date_from,
                    CommunicationLog.status.in_(
                        [CommunicationStatus.FAILED, CommunicationStatus.BOUNCED]
                    ),
                )
            )
            .count()
        )

        # Stats by type
        type_stats = (
            self.db.query(
                CommunicationLog.communication_type,
                CommunicationLog.status,
                func.count(CommunicationLog.id),
            )
            .filter(CommunicationLog.created_at >= date_from)
            .group_by(CommunicationLog.communication_type, CommunicationLog.status)
            .all()
        )

        # Stats by priority
        priority_stats = (
            self.db.query(CommunicationLog.priority, func.count(CommunicationLog.id))
            .filter(CommunicationLog.created_at >= date_from)
            .group_by(CommunicationLog.priority)
            .all()
        )

        # Recent activity
        recent_activity = (
            self.db.query(CommunicationLog)
            .filter(CommunicationLog.created_at >= date_from)
            .order_by(CommunicationLog.created_at.desc())
            .limit(10)
            .all()
        )

        return {
            "total_sent": total_sent,
            "total_delivered": total_delivered,
            "total_failed": total_failed,
            "delivery_rate": (
                (total_delivered / total_sent * 100) if total_sent > 0 else 0
            ),
            "by_type": self._format_type_stats(type_stats),
            "by_priority": {str(priority): count for priority, count in priority_stats},
            "recent_activity": [
                {
                    "id": log.id,
                    "type": log.communication_type.value,
                    "status": log.status.value,
                    "recipient": log.recipient_email or log.recipient_phone,
                    "created_at": log.created_at.isoformat(),
                }
                for log in recent_activity
            ],
        }

    def _send_communication_now(self, comm_log: CommunicationLog):
        """Send communication immediately"""
        try:
            # Get provider
            provider = None
            if comm_log.provider_id:
                provider = self.provider_service.get_provider(comm_log.provider_id)
            else:
                provider = self.provider_service.get_default_provider(
                    comm_log.communication_type
                )

            if not provider:
                raise ValueError(
                    f"No provider available for {comm_log.communication_type.value}"
                )

            # Update status
            comm_log.status = CommunicationStatus.SENDING
            comm_log.provider_id = provider.id
            self.db.commit()

            # Send based on communication type
            if comm_log.communication_type == CommunicationType.EMAIL:
                self._send_email(comm_log, provider)
            elif comm_log.communication_type == CommunicationType.SMS:
                self._send_sms(comm_log, provider)
            else:
                raise ValueError(
                    f"Unsupported communication type: {comm_log.communication_type.value}"
                )

            # Update success status
            comm_log.status = CommunicationStatus.SENT
            comm_log.sent_at = datetime.now(timezone.utc)

        except Exception as e:
            logger.error(f"Failed to send communication {comm_log.id}: {str(e)}")
            comm_log.status = CommunicationStatus.FAILED
            comm_log.error_message = str(e)

        self.db.commit()

    def _send_email(self, comm_log: CommunicationLog, provider: CommunicationProvider):
        """Send email using SMTP"""
        config = provider.configuration
        credentials = provider.credentials

        # Create message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = comm_log.subject or "No Subject"
        msg["From"] = config.get("from_email", credentials.get("username"))
        msg["To"] = comm_log.recipient_email

        # Add text part
        text_part = MIMEText(comm_log.body, "plain")
        msg.attach(text_part)

        # Add HTML part if available
        if comm_log.html_body:
            html_part = MIMEText(comm_log.html_body, "html")
            msg.attach(html_part)

        # Send email
        context = ssl.create_default_context()

        with smtplib.SMTP(config["smtp_host"], config.get("smtp_port", 587)) as server:
            if config.get("use_tls", True):
                server.starttls(context=context)

            server.login(credentials["username"], credentials["password"])
            server.send_message(msg)

        logger.info(f"Email sent successfully to {comm_log.recipient_email}")

    def _send_sms(self, comm_log: CommunicationLog, provider: CommunicationProvider):
        """Send SMS using HTTP API"""
        config = provider.configuration
        credentials = provider.credentials

        # Prepare SMS data
        sms_data = {
            "to": comm_log.recipient_phone,
            "message": comm_log.body,
            **config.get("default_params", {}),
        }

        # Add credentials to request
        if config.get("auth_method") == "header":
            headers = {
                "Authorization": f"Bearer {credentials.get('api_key')}",
                "Content-Type": "application/json",
            }
            response = requests.post(config["api_url"], json=sms_data, headers=headers)
        else:
            sms_data.update(credentials)
            response = requests.post(config["api_url"], json=sms_data)

        response.raise_for_status()

        # Store provider response
        comm_log.provider_response = response.json()
        comm_log.provider_message_id = response.json().get("message_id")

        logger.info(f"SMS sent successfully to {comm_log.recipient_phone}")

    def _process_communication_queue(self, queue_id: int):
        """Process communication queue in background"""
        # This would typically be handled by a background task system like Celery
        # For now, we'll implement a simple synchronous version
        queue = (
            self.db.query(CommunicationQueue)
            .filter(CommunicationQueue.id == queue_id)
            .first()
        )

        if not queue:
            return

        queue.status = "processing"
        queue.started_at = datetime.now(timezone.utc)
        self.db.commit()

        try:
            for recipient in queue.recipients:
                # Create individual communication log
                comm_data = {
                    "communication_type": queue.communication_type,
                    "priority": queue.priority,
                    "recipient_email": recipient.get("email"),
                    "recipient_phone": recipient.get("phone"),
                    "recipient_name": recipient.get("name"),
                    "subject": queue.subject,
                    "body": queue.body,
                    "html_body": queue.html_body,
                    "template_id": queue.template_id,
                    "template_variables": {
                        **queue.template_variables,
                        **recipient.get("variables", {}),
                    },
                    "customer_id": recipient.get("customer_id"),
                }

                # Render template if needed
                if queue.template_id:
                    rendered = self.template_service.render_template(
                        queue.template_id, comm_data["template_variables"]
                    )
                    comm_data.update(rendered)

                # Create and send communication
                comm_log = CommunicationLog(**comm_data)
                self.db.add(comm_log)
                self.db.commit()
                self.db.refresh(comm_log)

                self._send_communication_now(comm_log)

                # Update queue progress
                queue.processed_count += 1
                if comm_log.status == CommunicationStatus.SENT:
                    queue.success_count += 1
                else:
                    queue.failed_count += 1

                self.db.commit()

            queue.status = "completed"
            queue.completed_at = datetime.now(timezone.utc)

        except Exception as e:
            logger.error(f"Failed to process communication queue {queue_id}: {str(e)}")
            queue.status = "failed"

        self.db.commit()

    def _format_type_stats(self, type_stats) -> Dict[str, Dict[str, int]]:
        """Format type statistics for response"""
        result = {}
        for comm_type, status, count in type_stats:
            type_key = comm_type.value
            status_key = status.value

            if type_key not in result:
                result[type_key] = {}

            result[type_key][status_key] = count

        return result


class PreferenceService:
    """Service for managing customer communication preferences"""

    def __init__(self, db: Session):
        self.db = db

    def get_customer_preferences(
        self, customer_id: int
    ) -> Optional[CommunicationPreference]:
        """Get customer communication preferences"""
        return (
            self.db.query(CommunicationPreference)
            .filter(CommunicationPreference.customer_id == customer_id)
            .first()
        )

    def create_or_update_preferences(
        self, customer_id: int, preferences_data: CommunicationPreferenceUpdate
    ) -> CommunicationPreference:
        """Create or update customer communication preferences"""
        existing = self.get_customer_preferences(customer_id)

        if existing:
            # Update existing preferences
            update_data = preferences_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(existing, field, value)

            self.db.commit()
            self.db.refresh(existing)
            return existing
        else:
            # Create new preferences
            preferences = CommunicationPreference(
                customer_id=customer_id, **preferences_data.dict()
            )

            self.db.add(preferences)
            self.db.commit()
            self.db.refresh(preferences)
            return preferences

    def check_communication_allowed(
        self,
        customer_id: int,
        communication_type: CommunicationType,
        category: TemplateCategory,
    ) -> bool:
        """Check if communication is allowed based on customer preferences"""
        preferences = self.get_customer_preferences(customer_id)
        if not preferences:
            return True  # Default to allowed if no preferences set

        # Check if communication type is enabled
        type_enabled_field = f"{communication_type.value}_enabled"
        if not getattr(preferences, type_enabled_field, True):
            return False

        # Check category-specific preferences
        category_field = f"{communication_type.value}_{category.value}"
        return getattr(preferences, category_field, True)


# Factory function for dependency injection
def get_communication_services(db: Session) -> Dict[str, Any]:
    """Get all communication services"""
    return {
        "template_service": TemplateService(db),
        "provider_service": ProviderService(db),
        "communication_service": CommunicationService(db),
        "preference_service": PreferenceService(db),
    }
