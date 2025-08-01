"""
Template Repository Layer

Comprehensive repository layer for communication template management including:
- Email/SMS template management
- Template rendering and validation
- Communication provider management
- Template versioning and deployment
- Communication queue management
"""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional

from jinja2 import Environment, Template, TemplateSyntaxError
from sqlalchemy import and_, desc, func, or_
from sqlalchemy.orm import Session, joinedload

from app.models.communications import (
    CommunicationLog,
    CommunicationPreference,
    CommunicationProvider,
    CommunicationQueue,
    CommunicationRule,
    CommunicationStatus,
    CommunicationType,
    TemplateCategory,
    CommunicationTemplate,
)
from app.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class TemplateRepository(BaseRepository[CommunicationTemplate]):
    """Repository for communication template management"""

    def __init__(self, db: Session):
        super().__init__(db, CommunicationTemplate)
        self.jinja_env = Environment()

    def create_template(
        self,
        name: str,
        category: TemplateCategory,
        communication_type: CommunicationType,
        body_template: str,
        subject_template: Optional[str] = None,
        html_template: Optional[str] = None,
        created_by: Optional[int] = None,
        language: str = "en",
        required_variables: List[str] = None,
        optional_variables: List[str] = None,
        description: Optional[str] = None,
        is_system: bool = False,
    ) -> CommunicationTemplate:
        """Create a new communication template"""
        
        # Validate template syntax
        self._validate_template_syntax(body_template, "body")
        if subject_template:
            self._validate_template_syntax(subject_template, "subject")
        if html_template:
            self._validate_template_syntax(html_template, "html")
        
        template = CommunicationTemplate(
            name=name,
            category=category,
            communication_type=communication_type,
            body_template=body_template,
            subject_template=subject_template,
            html_template=html_template,
            created_by=created_by,
            language=language,
            required_variables=required_variables or [],
            optional_variables=optional_variables or [],
            description=description,
            is_system=is_system,
        )
        
        self.db.add(template)
        self.db.commit()
        self.db.refresh(template)
        
        logger.info(f"Created template: {name} ({category.value})")
        return template

    def get_templates_by_category(
        self,
        category: TemplateCategory,
        communication_type: Optional[CommunicationType] = None,
        language: str = "en",
        active_only: bool = True,
    ) -> List[CommunicationTemplate]:
        """Get templates by category and type"""
        
        query = self.db.query(CommunicationTemplate).filter(
            CommunicationTemplate.category == category,
            CommunicationTemplate.language == language,
        )
        
        if communication_type:
            query = query.filter(CommunicationTemplate.communication_type == communication_type)
        
        if active_only:
            query = query.filter(CommunicationTemplate.is_active == True)
        
        return query.order_by(CommunicationTemplate.name).all()

    def get_template_by_name(
        self,
        name: str,
        language: str = "en",
    ) -> Optional[CommunicationTemplate]:
        """Get template by name and language"""
        
        return (
            self.db.query(CommunicationTemplate)
            .filter(
                CommunicationTemplate.name == name,
                CommunicationTemplate.language == language,
                CommunicationTemplate.is_active == True,
            )
            .first()
        )

    def render_template(
        self,
        template_id: int,
        variables: Dict,
        validate_required: bool = True,
    ) -> Dict[str, str]:
        """Render template with provided variables"""
        
        template = self.get_by_id(template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found")
        
        if not template.is_active:
            raise ValueError(f"Template {template_id} is not active")
        
        # Validate required variables
        if validate_required and template.required_variables:
            missing_vars = set(template.required_variables) - set(variables.keys())
            if missing_vars:
                raise ValueError(f"Missing required variables: {', '.join(missing_vars)}")
        
        result = {}
        
        # Render subject if present
        if template.subject_template:
            subject_tmpl = self.jinja_env.from_string(template.subject_template)
            result["subject"] = subject_tmpl.render(**variables)
        
        # Render body
        body_tmpl = self.jinja_env.from_string(template.body_template)
        result["body"] = body_tmpl.render(**variables)
        
        # Render HTML if present
        if template.html_template:
            html_tmpl = self.jinja_env.from_string(template.html_template)
            result["html_body"] = html_tmpl.render(**variables)
        
        return result

    def clone_template(
        self,
        template_id: int,
        new_name: str,
        created_by: Optional[int] = None,
    ) -> CommunicationTemplate:
        """Clone an existing template"""
        
        original = self.get_by_id(template_id)
        if not original:
            raise ValueError(f"Template {template_id} not found")
        
        cloned = CommunicationTemplate(
            name=new_name,
            category=original.category,
            communication_type=original.communication_type,
            subject_template=original.subject_template,
            body_template=original.body_template,
            html_template=original.html_template,
            language=original.language,
            required_variables=original.required_variables.copy(),
            optional_variables=original.optional_variables.copy(),
            description=f"Cloned from: {original.name}",
            created_by=created_by,
            is_system=False,  # Cloned templates are never system templates
        )
        
        self.db.add(cloned)
        self.db.commit()
        self.db.refresh(cloned)
        
        logger.info(f"Cloned template {original.name} to {new_name}")
        return cloned

    def get_template_usage_stats(
        self,
        template_id: int,
        days_back: int = 30,
    ) -> Dict:
        """Get usage statistics for a template"""
        
        start_date = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        ) - timedelta(days=days_back)
        
        # Total usage count
        total_usage = (
            self.db.query(func.count(CommunicationLog.id))
            .filter(
                CommunicationLog.template_id == template_id,
                CommunicationLog.created_at >= start_date,
            )
            .scalar()
        )
        
        # Success rate
        success_count = (
            self.db.query(func.count(CommunicationLog.id))
            .filter(
                CommunicationLog.template_id == template_id,
                CommunicationLog.created_at >= start_date,
                CommunicationLog.status.in_([
                    CommunicationStatus.SENT,
                    CommunicationStatus.DELIVERED,
                ])
            )
            .scalar()
        )
        
        success_rate = (success_count / total_usage * 100) if total_usage > 0 else 0
        
        # Usage by communication type
        usage_by_type = (
            self.db.query(
                CommunicationLog.communication_type,
                func.count(CommunicationLog.id).label('count')
            )
            .filter(
                CommunicationLog.template_id == template_id,
                CommunicationLog.created_at >= start_date,
            )
            .group_by(CommunicationLog.communication_type)
            .all()
        )
        
        return {
            "template_id": template_id,
            "total_usage": total_usage,
            "success_count": success_count,
            "success_rate": round(success_rate, 2),
            "usage_by_type": {
                usage.communication_type.value: usage.count
                for usage in usage_by_type
            },
        }

    def _validate_template_syntax(self, template_content: str, template_type: str):
        """Validate Jinja2 template syntax"""
        try:
            self.jinja_env.from_string(template_content)
        except TemplateSyntaxError as e:
            raise ValueError(f"Invalid {template_type} template syntax: {e}")


class CommunicationProviderRepository(BaseRepository[CommunicationProvider]):
    """Repository for communication provider management"""

    def __init__(self, db: Session):
        super().__init__(db, CommunicationProvider)

    def create_provider(
        self,
        name: str,
        provider_type: CommunicationType,
        provider_class: str,
        configuration: Dict,
        credentials: Dict,
        is_default: bool = False,
        rate_limit_per_minute: int = 60,
        rate_limit_per_hour: int = 1000,
        rate_limit_per_day: int = 10000,
        description: Optional[str] = None,
    ) -> CommunicationProvider:
        """Create a new communication provider"""
        
        # If setting as default, unset other defaults of same type
        if is_default:
            self.db.query(CommunicationProvider).filter(
                CommunicationProvider.provider_type == provider_type,
                CommunicationProvider.is_default == True,
            ).update({"is_default": False})
        
        provider = CommunicationProvider(
            name=name,
            provider_type=provider_type,
            provider_class=provider_class,
            configuration=configuration,
            credentials=credentials,
            is_default=is_default,
            rate_limit_per_minute=rate_limit_per_minute,
            rate_limit_per_hour=rate_limit_per_hour,
            rate_limit_per_day=rate_limit_per_day,
            description=description,
        )
        
        self.db.add(provider)
        self.db.commit()
        self.db.refresh(provider)
        
        logger.info(f"Created provider: {name} ({provider_type.value})")
        return provider

    def get_default_provider(
        self,
        provider_type: CommunicationType,
    ) -> Optional[CommunicationProvider]:
        """Get default provider for communication type"""
        
        return (
            self.db.query(CommunicationProvider)
            .filter(
                CommunicationProvider.provider_type == provider_type,
                CommunicationProvider.is_default == True,
                CommunicationProvider.is_active == True,
            )
            .first()
        )

    def get_available_providers(
        self,
        provider_type: CommunicationType,
    ) -> List[CommunicationProvider]:
        """Get all available providers for communication type"""
        
        return (
            self.db.query(CommunicationProvider)
            .filter(
                CommunicationProvider.provider_type == provider_type,
                CommunicationProvider.is_active == True,
            )
            .order_by(
                CommunicationProvider.is_default.desc(),
                CommunicationProvider.priority.asc(),
            )
            .all()
        )

    def update_provider_stats(
        self,
        provider_id: int,
        success: bool,
        delivery_time_seconds: Optional[int] = None,
    ):
        """Update provider success rate and delivery time"""
        
        provider = self.get_by_id(provider_id)
        if not provider:
            return
        
        # Update last used timestamp
        provider.last_used = datetime.now(timezone.utc)
        
        # Simple success rate calculation (could be enhanced with rolling averages)
        if success:
            provider.success_rate = min(100, provider.success_rate + 1)
        else:
            provider.success_rate = max(0, provider.success_rate - 5)
        
        # Update average delivery time
        if delivery_time_seconds is not None and success:
            if provider.average_delivery_time == 0:
                provider.average_delivery_time = delivery_time_seconds
            else:
                # Simple moving average
                provider.average_delivery_time = int(
                    (provider.average_delivery_time + delivery_time_seconds) / 2
                )
        
        self.db.commit()


class CommunicationQueueRepository(BaseRepository[CommunicationQueue]):
    """Repository for communication queue management"""

    def __init__(self, db: Session):
        super().__init__(db, CommunicationQueue)

    def create_queue_job(
        self,
        queue_name: str,
        communication_type: CommunicationType,
        recipients: List[Dict],
        template_id: Optional[int] = None,
        subject: Optional[str] = None,
        body: Optional[str] = None,
        html_body: Optional[str] = None,
        template_variables: Dict = None,
        scheduled_at: Optional[datetime] = None,
        created_by: Optional[int] = None,
        batch_size: int = 100,
        delay_between_batches: int = 60,
    ) -> CommunicationQueue:
        """Create a new communication queue job"""
        
        queue_job = CommunicationQueue(
            queue_name=queue_name,
            communication_type=communication_type,
            total_recipients=len(recipients),
            template_id=template_id,
            subject=subject,
            body=body,
            html_body=html_body,
            recipients=recipients,
            template_variables=template_variables or {},
            scheduled_at=scheduled_at or datetime.now(timezone.utc),
            created_by=created_by,
            batch_size=batch_size,
            delay_between_batches=delay_between_batches,
        )
        
        self.db.add(queue_job)
        self.db.commit()
        self.db.refresh(queue_job)
        
        logger.info(f"Created queue job: {queue_name} ({len(recipients)} recipients)")
        return queue_job

    def get_pending_jobs(
        self,
        communication_type: Optional[CommunicationType] = None,
        limit: int = 10,
    ) -> List[CommunicationQueue]:
        """Get pending queue jobs ready for processing"""
        
        query = (
            self.db.query(CommunicationQueue)
            .filter(
                CommunicationQueue.status == "pending",
                CommunicationQueue.scheduled_at <= datetime.now(timezone.utc),
            )
        )
        
        if communication_type:
            query = query.filter(CommunicationQueue.communication_type == communication_type)
        
        return (
            query.order_by(CommunicationQueue.scheduled_at)
            .limit(limit)
            .all()
        )

    def update_job_progress(
        self,
        job_id: int,
        processed_count: int,
        success_count: int,
        failed_count: int,
        status: str = "processing",
    ):
        """Update job processing progress"""
        
        job = self.get_by_id(job_id)
        if not job:
            return
        
        job.processed_count = processed_count
        job.success_count = success_count
        job.failed_count = failed_count
        job.status = status
        
        if status == "processing" and not job.started_at:
            job.started_at = datetime.now(timezone.utc)
        elif status == "completed":
            job.completed_at = datetime.now(timezone.utc)
        
        self.db.commit()

    def get_queue_statistics(
        self,
        days_back: int = 7,
    ) -> Dict:
        """Get queue processing statistics"""
        
        start_date = datetime.now(timezone.utc) - timedelta(days=days_back)
        
        total_jobs = (
            self.db.query(func.count(CommunicationQueue.id))
            .filter(CommunicationQueue.created_at >= start_date)
            .scalar()
        )
        
        completed_jobs = (
            self.db.query(func.count(CommunicationQueue.id))
            .filter(
                CommunicationQueue.created_at >= start_date,
                CommunicationQueue.status == "completed",
            )
            .scalar()
        )
        
        total_recipients = (
            self.db.query(func.sum(CommunicationQueue.total_recipients))
            .filter(CommunicationQueue.created_at >= start_date)
            .scalar() or 0
        )
        
        total_success = (
            self.db.query(func.sum(CommunicationQueue.success_count))
            .filter(CommunicationQueue.created_at >= start_date)
            .scalar() or 0
        )
        
        return {
            "total_jobs": total_jobs,
            "completed_jobs": completed_jobs,
            "completion_rate": (completed_jobs / total_jobs * 100) if total_jobs > 0 else 0,
            "total_recipients": total_recipients,
            "total_success": total_success,
            "success_rate": (total_success / total_recipients * 100) if total_recipients > 0 else 0,
        }
