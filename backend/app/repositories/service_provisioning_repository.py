"""
Service Provisioning Repository - ISP Service Management System

Repository layer for service provisioning management including:
- Service provisioning workflows (automated deployment processes)
- Provisioning templates (reusable workflow definitions)
- Provisioning queue (task queue management)

Provides database operations for complex provisioning workflows with status tracking,
rollback capabilities, and comprehensive audit trails.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload

from app.models.customer import Customer
from app.models.services import (
    ProvisioningQueue,
    ProvisioningStatus,
    ProvisioningTemplate,
    ServiceProvisioning,
    ServiceType,
)
from app.models.services.instances import CustomerService
from app.repositories.base import BaseRepository


class ServiceProvisioningRepository(BaseRepository[ServiceProvisioning]):
    """Repository for service provisioning operations"""

    def __init__(self, db: Session):
        super().__init__(ServiceProvisioning, db)

    def get_by_service(self, service_id: int) -> List[ServiceProvisioning]:
        """Get all provisioning records for a service"""
        return (
            self.db.query(ServiceProvisioning)
            .filter(ServiceProvisioning.service_id == service_id)
            .options(
                joinedload(ServiceProvisioning.template),
                joinedload(ServiceProvisioning.initiated_by),
            )
            .order_by(ServiceProvisioning.created_at.desc())
            .all()
        )

    def get_active_provisioning(
        self, service_id: Optional[int] = None
    ) -> List[ServiceProvisioning]:
        """Get all active provisioning workflows"""
        query = self.db.query(ServiceProvisioning).filter(
            ServiceProvisioning.status.in_(
                [
                    ProvisioningStatus.PENDING,
                    ProvisioningStatus.IN_PROGRESS,
                    ProvisioningStatus.WAITING_QA,
                    ProvisioningStatus.PAUSED,
                ]
            )
        )

        if service_id:
            query = query.filter(ServiceProvisioning.service_id == service_id)

        return (
            query.options(
                joinedload(ServiceProvisioning.service).joinedload(
                    CustomerService.customer
                ),
                joinedload(ServiceProvisioning.template),
            )
            .order_by(
                ServiceProvisioning.priority.desc(), ServiceProvisioning.created_at
            )
            .all()
        )

    def get_failed_provisioning(
        self, hours_back: int = 24, include_retryable: bool = True
    ) -> List[ServiceProvisioning]:
        """Get failed provisioning workflows within specified timeframe"""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours_back)

        query = self.db.query(ServiceProvisioning).filter(
            ServiceProvisioning.status == ProvisioningStatus.FAILED,
            ServiceProvisioning.updated_at >= cutoff_time,
        )

        if not include_retryable:
            query = query.filter(ServiceProvisioning.can_retry is False)

        return (
            query.options(
                joinedload(ServiceProvisioning.service).joinedload(
                    CustomerService.customer
                ),
                joinedload(ServiceProvisioning.template),
            )
            .order_by(ServiceProvisioning.updated_at.desc())
            .all()
        )

    def get_provisioning_by_status(
        self, status: ProvisioningStatus, limit: int = 50, offset: int = 0
    ) -> Tuple[List[ServiceProvisioning], int]:
        """Get provisioning workflows by status with pagination"""
        query = self.db.query(ServiceProvisioning).filter(
            ServiceProvisioning.status == status
        )

        # Get total count
        total = query.count()

        # Apply pagination and ordering
        provisioning = (
            query.options(
                joinedload(ServiceProvisioning.service).joinedload(
                    CustomerService.customer
                ),
                joinedload(ServiceProvisioning.template),
            )
            .order_by(
                ServiceProvisioning.priority.desc(), ServiceProvisioning.created_at
            )
            .offset(offset)
            .limit(limit)
            .all()
        )

        return provisioning, total

    def get_provisioning_queue(
        self,
        template_id: Optional[int] = None,
        service_type: Optional[ServiceType] = None,
        priority_min: Optional[int] = None,
    ) -> List[ServiceProvisioning]:
        """Get provisioning queue with filtering options"""
        query = self.db.query(ServiceProvisioning).filter(
            ServiceProvisioning.status.in_(
                [ProvisioningStatus.PENDING, ProvisioningStatus.IN_PROGRESS]
            )
        )

        if template_id:
            query = query.filter(ServiceProvisioning.template_id == template_id)

        if service_type:
            query = query.join(CustomerService).filter(
                CustomerService.service_type == service_type
            )

        if priority_min:
            query = query.filter(ServiceProvisioning.priority >= priority_min)

        return (
            query.options(
                joinedload(ServiceProvisioning.service).joinedload(
                    CustomerService.customer
                ),
                joinedload(ServiceProvisioning.template),
            )
            .order_by(
                ServiceProvisioning.priority.desc(),
                ServiceProvisioning.scheduled_at.asc().nullsfirst(),
                ServiceProvisioning.created_at,
            )
            .all()
        )

    def get_overdue_provisioning(self) -> List[ServiceProvisioning]:
        """Get provisioning workflows that are overdue"""
        now = datetime.now(timezone.utc)

        return (
            self.db.query(ServiceProvisioning)
            .filter(
                ServiceProvisioning.status.in_(
                    [ProvisioningStatus.PENDING, ProvisioningStatus.IN_PROGRESS]
                ),
                ServiceProvisioning.scheduled_at.isnot(None),
                ServiceProvisioning.scheduled_at < now,
            )
            .options(
                joinedload(ServiceProvisioning.service).joinedload(
                    CustomerService.customer
                ),
                joinedload(ServiceProvisioning.template),
            )
            .order_by(ServiceProvisioning.scheduled_at)
            .all()
        )

    def search_provisioning(
        self,
        search_term: Optional[str] = None,
        status: Optional[ProvisioningStatus] = None,
        template_id: Optional[int] = None,
        service_type: Optional[ServiceType] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[ServiceProvisioning], int]:
        """Search provisioning workflows with comprehensive filtering"""
        query = self.db.query(ServiceProvisioning)

        # Text search across customer and service details
        if search_term:
            query = (
                query.join(CustomerService)
                .join(Customer)
                .filter(
                    or_(
                        Customer.first_name.ilike(f"%{search_term}%"),
                        Customer.last_name.ilike(f"%{search_term}%"),
                        Customer.login.ilike(f"%{search_term}%"),
                        ServiceProvisioning.workflow_id.ilike(f"%{search_term}%"),
                    )
                )
            )

        # Filter by status
        if status:
            query = query.filter(ServiceProvisioning.status == status)

        # Filter by template
        if template_id:
            query = query.filter(ServiceProvisioning.template_id == template_id)

        # Filter by service type
        if service_type:
            if not search_term:  # Avoid double join
                query = query.join(CustomerService)
            query = query.filter(CustomerService.service_type == service_type)

        # Filter by date range
        if date_from:
            query = query.filter(ServiceProvisioning.created_at >= date_from)

        if date_to:
            query = query.filter(ServiceProvisioning.created_at <= date_to)

        # Get total count
        total = query.count()

        # Apply pagination and ordering
        provisioning = (
            query.options(
                joinedload(ServiceProvisioning.service).joinedload(
                    CustomerService.customer
                ),
                joinedload(ServiceProvisioning.template),
            )
            .order_by(ServiceProvisioning.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        return provisioning, total

    def get_provisioning_statistics(self) -> Dict[str, Any]:
        """Get comprehensive provisioning statistics"""
        stats = {}

        # Total provisioning workflows
        stats["total_provisioning"] = self.db.query(ServiceProvisioning).count()

        # Provisioning by status
        status_stats = (
            self.db.query(
                ServiceProvisioning.status,
                func.count(ServiceProvisioning.id).label("count"),
            )
            .group_by(ServiceProvisioning.status)
            .all()
        )

        stats["by_status"] = {str(status[0]): status[1] for status in status_stats}

        # Success rate (completed vs failed)
        completed = (
            self.db.query(ServiceProvisioning)
            .filter(ServiceProvisioning.status == ProvisioningStatus.COMPLETED)
            .count()
        )

        failed = (
            self.db.query(ServiceProvisioning)
            .filter(ServiceProvisioning.status == ProvisioningStatus.FAILED)
            .count()
        )

        total_finished = completed + failed
        stats["success_rate"] = (
            (completed / total_finished * 100) if total_finished > 0 else 0.0
        )

        # Average provisioning time for completed workflows
        avg_duration = (
            self.db.query(
                func.avg(
                    func.extract(
                        "epoch",
                        ServiceProvisioning.completed_at
                        - ServiceProvisioning.started_at,
                    )
                    / 60
                )
            )
            .filter(
                ServiceProvisioning.status == ProvisioningStatus.COMPLETED,
                ServiceProvisioning.started_at.isnot(None),
                ServiceProvisioning.completed_at.isnot(None),
            )
            .scalar()
        )

        stats["average_provisioning_time_minutes"] = (
            float(avg_duration) if avg_duration else 0.0
        )

        # Active workflows
        stats["active_workflows"] = (
            self.db.query(ServiceProvisioning)
            .filter(
                ServiceProvisioning.status.in_(
                    [ProvisioningStatus.PENDING, ProvisioningStatus.IN_PROGRESS]
                )
            )
            .count()
        )

        # Workflows requiring attention
        stats["requiring_attention"] = (
            self.db.query(ServiceProvisioning)
            .filter(
                ServiceProvisioning.status.in_(
                    [
                        ProvisioningStatus.FAILED,
                        ProvisioningStatus.WAITING_QA,
                        ProvisioningStatus.PAUSED,
                    ]
                )
            )
            .count()
        )

        return stats


class ProvisioningTemplateRepository(BaseRepository[ProvisioningTemplate]):
    """Repository for provisioning template operations"""

    def __init__(self, db: Session):
        super().__init__(ProvisioningTemplate, db)

    def get_by_service_type(
        self, service_type: ServiceType
    ) -> List[ProvisioningTemplate]:
        """Get provisioning templates for a specific service type"""
        return (
            self.db.query(ProvisioningTemplate)
            .filter(
                ProvisioningTemplate.service_type == service_type,
                ProvisioningTemplate.is_active is True,
            )
            .order_by(ProvisioningTemplate.name)
            .all()
        )

    def get_default_template(
        self, service_type: ServiceType
    ) -> Optional[ProvisioningTemplate]:
        """Get default provisioning template for a service type"""
        return (
            self.db.query(ProvisioningTemplate)
            .filter(
                ProvisioningTemplate.service_type == service_type,
                ProvisioningTemplate.is_default is True,
                ProvisioningTemplate.is_active is True,
            )
            .first()
        )

    def get_automated_templates(self) -> List[ProvisioningTemplate]:
        """Get templates with full automation enabled"""
        return (
            self.db.query(ProvisioningTemplate)
            .filter(
                ProvisioningTemplate.is_active is True,
                ProvisioningTemplate.automation_level == "full",
            )
            .order_by(ProvisioningTemplate.service_type, ProvisioningTemplate.name)
            .all()
        )

    def get_templates_requiring_qa(self) -> List[ProvisioningTemplate]:
        """Get templates that require QA approval"""
        return (
            self.db.query(ProvisioningTemplate)
            .filter(
                ProvisioningTemplate.is_active is True,
                ProvisioningTemplate.requires_qa is True,
            )
            .order_by(ProvisioningTemplate.service_type, ProvisioningTemplate.name)
            .all()
        )

    def get_template_usage_stats(
        self, template_id: int, days: int = 30
    ) -> Dict[str, Any]:
        """Get usage statistics for a specific template"""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

        stats = {}

        # Total usage
        stats["total_usage"] = (
            self.db.query(ServiceProvisioning)
            .filter(
                ServiceProvisioning.template_id == template_id,
                ServiceProvisioning.created_at >= cutoff_date,
            )
            .count()
        )

        # Success rate
        completed = (
            self.db.query(ServiceProvisioning)
            .filter(
                ServiceProvisioning.template_id == template_id,
                ServiceProvisioning.status == ProvisioningStatus.COMPLETED,
                ServiceProvisioning.created_at >= cutoff_date,
            )
            .count()
        )

        failed = (
            self.db.query(ServiceProvisioning)
            .filter(
                ServiceProvisioning.template_id == template_id,
                ServiceProvisioning.status == ProvisioningStatus.FAILED,
                ServiceProvisioning.created_at >= cutoff_date,
            )
            .count()
        )

        total_finished = completed + failed
        stats["success_rate"] = (
            (completed / total_finished * 100) if total_finished > 0 else 0.0
        )

        # Average execution time
        avg_time = (
            self.db.query(
                func.avg(
                    func.extract(
                        "epoch",
                        ServiceProvisioning.completed_at
                        - ServiceProvisioning.started_at,
                    )
                    / 60
                )
            )
            .filter(
                ServiceProvisioning.template_id == template_id,
                ServiceProvisioning.status == ProvisioningStatus.COMPLETED,
                ServiceProvisioning.started_at.isnot(None),
                ServiceProvisioning.completed_at.isnot(None),
                ServiceProvisioning.created_at >= cutoff_date,
            )
            .scalar()
        )

        stats["average_execution_time_minutes"] = float(avg_time) if avg_time else 0.0

        return stats


class ProvisioningQueueRepository(BaseRepository[ProvisioningQueue]):
    """Repository for provisioning queue operations"""

    def __init__(self, db: Session):
        super().__init__(ProvisioningQueue, db)

    def get_pending_tasks(
        self, resource_type: Optional[str] = None, priority_min: Optional[int] = None
    ) -> List[ProvisioningQueue]:
        """Get pending tasks from the provisioning queue"""
        query = self.db.query(ProvisioningQueue).filter(
            ProvisioningQueue.status == "pending",
            or_(
                ProvisioningQueue.scheduled_at.is_(None),
                ProvisioningQueue.scheduled_at <= datetime.now(timezone.utc),
            ),
        )

        if resource_type:
            query = query.filter(
                ProvisioningQueue.required_resources.contains([resource_type])
            )

        if priority_min:
            query = query.filter(ProvisioningQueue.priority >= priority_min)

        return (
            query.options(joinedload(ProvisioningQueue.provisioning))
            .order_by(ProvisioningQueue.priority.desc(), ProvisioningQueue.created_at)
            .all()
        )

    def get_tasks_by_provisioning(
        self, provisioning_id: int
    ) -> List[ProvisioningQueue]:
        """Get all queue tasks for a specific provisioning workflow"""
        return (
            self.db.query(ProvisioningQueue)
            .filter(ProvisioningQueue.provisioning_id == provisioning_id)
            .order_by(ProvisioningQueue.step_order)
            .all()
        )

    def get_failed_tasks(self, hours_back: int = 24) -> List[ProvisioningQueue]:
        """Get failed tasks within specified timeframe"""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours_back)

        return (
            self.db.query(ProvisioningQueue)
            .filter(
                ProvisioningQueue.status == "failed",
                ProvisioningQueue.updated_at >= cutoff_time,
            )
            .options(joinedload(ProvisioningQueue.provisioning))
            .order_by(ProvisioningQueue.updated_at.desc())
            .all()
        )

    def get_queue_statistics(self) -> Dict[str, Any]:
        """Get provisioning queue statistics"""
        stats = {}

        # Total tasks
        stats["total_tasks"] = self.db.query(ProvisioningQueue).count()

        # Tasks by status
        status_stats = (
            self.db.query(
                ProvisioningQueue.status,
                func.count(ProvisioningQueue.id).label("count"),
            )
            .group_by(ProvisioningQueue.status)
            .all()
        )

        stats["by_status"] = {status[0]: status[1] for status in status_stats}

        # Pending tasks
        stats["pending_tasks"] = (
            self.db.query(ProvisioningQueue)
            .filter(ProvisioningQueue.status == "pending")
            .count()
        )

        # Average task execution time
        avg_time = (
            self.db.query(
                func.avg(
                    func.extract(
                        "epoch",
                        ProvisioningQueue.completed_at - ProvisioningQueue.started_at,
                    )
                    / 60
                )
            )
            .filter(
                ProvisioningQueue.status == "completed",
                ProvisioningQueue.started_at.isnot(None),
                ProvisioningQueue.completed_at.isnot(None),
            )
            .scalar()
        )

        stats["average_task_time_minutes"] = float(avg_time) if avg_time else 0.0

        return stats


# Repository factory for service provisioning
class ServiceProvisioningRepositoryFactory:
    """Factory for creating service provisioning repositories"""

    @staticmethod
    def create_provisioning_repo(db: Session) -> ServiceProvisioningRepository:
        return ServiceProvisioningRepository(db)

    @staticmethod
    def create_template_repo(db: Session) -> ProvisioningTemplateRepository:
        return ProvisioningTemplateRepository(db)

    @staticmethod
    def create_queue_repo(db: Session) -> ProvisioningQueueRepository:
        return ProvisioningQueueRepository(db)

    @staticmethod
    def create_all_repos(db: Session) -> Dict[str, Any]:
        """Create all service provisioning repositories"""
        return {
            "provisioning": ServiceProvisioningRepository(db),
            "template": ProvisioningTemplateRepository(db),
            "queue": ProvisioningQueueRepository(db),
        }


# Utility functions for provisioning operations
class ProvisioningUtils:
    """Utility functions for provisioning operations"""

    @staticmethod
    def generate_workflow_id(service_type: ServiceType, customer_id: int) -> str:
        """Generate unique workflow identifier"""
        timestamp = int(datetime.now(timezone.utc).timestamp())
        return f"PROV-{service_type.value.upper()}-{customer_id:06d}-{timestamp}"

    @staticmethod
    def calculate_estimated_completion(
        template: ProvisioningTemplate, queue_length: int = 0
    ) -> datetime:
        """Calculate estimated completion time for provisioning"""
        base_time = datetime.now(timezone.utc)

        # Add queue wait time (assuming 5 minutes per queued item)
        queue_wait = timedelta(minutes=queue_length * 5)

        # Add template estimated duration
        template_duration = timedelta(minutes=template.estimated_duration_minutes or 30)

        return base_time + queue_wait + template_duration

    @staticmethod
    def get_next_step_order(provisioning_id: int, db: Session) -> int:
        """Get the next step order for a provisioning workflow"""
        max_order = (
            db.query(func.max(ProvisioningQueue.step_order))
            .filter(ProvisioningQueue.provisioning_id == provisioning_id)
            .scalar()
        )

        return (max_order or 0) + 1

    @staticmethod
    def validate_dependencies(
        task_dependencies: List[str], completed_tasks: List[str]
    ) -> bool:
        """Validate if all task dependencies are completed"""
        return all(dep in completed_tasks for dep in task_dependencies)
