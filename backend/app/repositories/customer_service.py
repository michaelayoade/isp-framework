from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timezone, timedelta
from app.repositories.base import BaseRepository
from app.models.services import (
    ServiceTemplate,
    CustomerService,
)
from app.models.services.enums import ServiceStatus
import logging

logger = logging.getLogger(__name__)

# Default pagination limit for repository queries
DEFAULT_LIMIT = 50


class CustomerServiceRepository(BaseRepository[CustomerService]):
    """Repository for customer service assignment operations."""

    def _query(self) -> "Session.query[CustomerService]":
        """Return base query with soft-delete filtering applied (if column exists)."""
        query = self.db.query(CustomerService)
        if hasattr(CustomerService, "is_deleted"):
            query = query.filter(CustomerService.is_deleted.is_(False))
        return query
    """Repository for customer service assignment operations."""
    
    def __init__(self, db: Session):
        super().__init__(CustomerService, db)
    
    def get_with_details(self, service_id: int) -> Optional[CustomerService]:
        """Get customer service with related service plan and customer details."""
        return self.db.query(CustomerService).options(
            joinedload(CustomerService.service_template),
            joinedload(CustomerService.customer)
        ).filter(CustomerService.id == service_id).first()
    
    def get_customer_services(
        self, 
        customer_id: int, 
        active_only: bool = True,
        include_details: bool = False
    ) -> List[CustomerService]:
        """Get all services for a specific customer."""
        query = self.db.query(CustomerService)
        
        if include_details:
            query = query.options(
                joinedload(CustomerService.service_template),
                joinedload(CustomerService.customer)
            )
        
        query = query.filter(CustomerService.customer_id == customer_id)
        
        if active_only:
            query = query.filter(CustomerService.status == ServiceStatus.ACTIVE.value)
        
        return query.order_by(CustomerService.created_at.desc()).all()
    
    def get_service_plan_assignments(
        self, 
        service_plan_id: int, 
        active_only: bool = True,
        include_details: bool = False
    ) -> List[CustomerService]:
        """Get all customer assignments for a specific service plan."""
        query = self.db.query(CustomerService)
        
        if include_details:
            query = query.options(
                joinedload(CustomerService.service_template),
                joinedload(CustomerService.customer)
            )
        
        query = query.filter(CustomerService.service_template_id == service_plan_id)
        
        if active_only:
            query = query.filter(CustomerService.status == ServiceStatus.ACTIVE.value)
        
        return query.order_by(CustomerService.created_at.desc()).all()
    
    def search_customer_services(self, search_params: Dict[str, Any]) -> Tuple[List[CustomerService], int]:
        """Search customer services with comprehensive filtering."""
        query = self._query().options(
            joinedload(CustomerService.service_template),
            joinedload(CustomerService.customer)
        )
        
        # Apply filters
        if search_params.get("customer_id"):
            query = query.filter(CustomerService.customer_id == search_params["customer_id"])
        
        if search_params.get("service_plan_id"):
            query = query.filter(CustomerService.service_template_id == search_params["service_plan_id"])
        
        if search_params.get("status"):
            query = query.filter(CustomerService.status == search_params["status"])
        
        if search_params.get("service_type"):
            query = query.join(ServiceTemplate).filter(ServiceTemplate.service_type == search_params["service_type"])
        
        if search_params.get("active_only", True):
            query = query.filter(CustomerService.status == ServiceStatus.ACTIVE.value)
        
        if not search_params.get("include_expired", False):
            current_time = datetime.now(timezone.utc)
            query = query.filter(
                or_(
                    CustomerService.end_date.is_(None),
                    CustomerService.end_date > current_time
                )
            )
        
        # Get total count before pagination
        total_count = query.count()
        
        # Apply pagination
        limit = search_params.get("limit", DEFAULT_LIMIT)
        offset = search_params.get("offset", 0)
        
        services = query.order_by(CustomerService.created_at.desc()).offset(offset).limit(limit).all()
        
        return services, total_count
    
    def get_customer_active_service(self, customer_id: int, service_template_id: int) -> Optional[CustomerService]:
        """Check if customer already has an active service for a specific plan."""
        return self.db.query(CustomerService).filter(
            and_(
                CustomerService.customer_id == customer_id,
                CustomerService.service_template_id == service_template_id,
                CustomerService.status == ServiceStatus.ACTIVE.value
            )
        ).first()
    
    def get_customer_services_overview(self, customer_id: int) -> Dict[str, Any]:
        """Get comprehensive overview of customer's services."""
        # Aggregations directly in SQL for performance
        aggregates = self._query().with_entities(
            func.count().label("total"),
            func.sum(func.case([(CustomerService.status == ServiceStatus.ACTIVE.value, 1)], else_=0)).label("active"),
            func.sum(func.case([(CustomerService.status == ServiceStatus.SUSPENDED.value, 1)], else_=0)).label("suspended"),
            func.sum(func.case([(CustomerService.status == ServiceStatus.EXPIRED.value, 1)], else_=0)).label("expired"),
            func.sum(func.case([(CustomerService.status == ServiceStatus.ACTIVE.value, CustomerService.monthly_cost)], else_=0)).label("revenue")
        ).filter(CustomerService.customer_id == customer_id).first()

        total_services = aggregates.total or 0
        active_count = aggregates.active or 0
        suspended_count = aggregates.suspended or 0
        expired_count = aggregates.expired or 0
        total_monthly_cost = aggregates.revenue or 0

        services = self.get_customer_services(customer_id, active_only=False, include_details=True)
        
        
        
        logger.info("Customer %s services overview calculated", customer_id)
        return {
            "total_services": total_services,
            "active_services": active_count,
            "suspended_services": suspended_count,
            "expired_services": expired_count,
            "total_monthly_cost": total_monthly_cost,
            "services": services,
        }
    
    def get_service_template_assignments_overview(
        self, 
        service_template_id: int
    ) -> Dict[str, Any]:
        """Get comprehensive overview of service template assignments."""
        # Fetch aggregate counts via SQL first for performance
        aggregate = self._query().with_entities(
            func.count().label("total"),
            func.sum(func.case([(CustomerService.status == ServiceStatus.ACTIVE.value, 1)], else_=0)).label("active"),
            func.sum(func.case([(CustomerService.status == ServiceStatus.SUSPENDED.value, 1)], else_=0)).label("suspended"),
            func.sum(func.case([(CustomerService.status == ServiceStatus.EXPIRED.value, 1)], else_=0)).label("expired"),
            func.sum(func.case([(CustomerService.status == ServiceStatus.ACTIVE.value, CustomerService.monthly_cost)], else_=0)).label("revenue")
        ).filter(CustomerService.service_template_id == service_template_id).first()

        total_assignments = aggregate.total or 0
        active_count = aggregate.active or 0
        suspended_count = aggregate.suspended or 0
        expired_count = aggregate.expired or 0
        total_revenue = aggregate.revenue or 0

        assignments = self.get_service_plan_assignments(
            service_template_id,
            active_only=False,
            include_details=True,
        )
        
        logger.info("Service template %s assignments overview calculated", service_template_id)
        return {
            "total_assignments": total_assignments,
            "active_count": active_count,
            "suspended_count": suspended_count,
            "expired_count": expired_count,
            "total_revenue": total_revenue,
            "assignments": assignments
        }
    
    def activate_service(self, service_id: int) -> CustomerService:
        """Activate a customer service."""
        service = self.get(service_id)
        if service:
            service.status = ServiceStatus.ACTIVE.value
            logger.info("Activated customer service %s", service_id)
            service.updated_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(service)
        return service
    
    def suspend_service(self, service_id: int) -> CustomerService:
        """Suspend a customer service."""
        service = self.get(service_id)
        if service:
            service.status = ServiceStatus.SUSPENDED.value
            logger.info("Suspended customer service %s", service_id)
            service.updated_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(service)
        return service
    
    def terminate_service(self, service_id: int, end_date: Optional[datetime] = None) -> CustomerService:
        """Terminate a customer service."""
        service = self.get(service_id)
        if service:
            service.status = ServiceStatus.TERMINATED.value
            logger.info("Terminated customer service %s", service_id)
            service.end_date = end_date or datetime.now(timezone.utc)
            service.updated_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(service)
        return service
    
    def get_expiring_services(self, days_ahead: int = 30) -> List[CustomerService]:
        """Get services that will expire within specified days."""
        future_date = datetime.now(timezone.utc) + timedelta(days=days_ahead)
        
        return self.db.query(CustomerService).options(
            joinedload(CustomerService.service_template),
            joinedload(CustomerService.customer)
        ).filter(
            and_(
                CustomerService.status == ServiceStatus.ACTIVE,
                CustomerService.end_date.isnot(None),
                CustomerService.end_date <= future_date
            )
        ).order_by(CustomerService.end_date).all()
    
    def commit_batch(self, objects: List[CustomerService], batch_size: int = 1000) -> int:
        """Insert or update many CustomerService objects in batches with a single commit per batch.

        Args:
            objects: List of CustomerService instances (transient or detached) to be persisted.
            batch_size: Number of rows per flush/commit cycle. Defaults to 1000.

        Returns:
            int: Number of objects successfully committed.
        """
        total = 0
        try:
            for idx, obj in enumerate(objects, start=1):
                self.db.add(obj)
                if idx % batch_size == 0:
                    self.db.flush()
                    self.db.commit()
                    total += batch_size
            # Commit remaining
            self.db.commit()
            total += (len(objects) - total)
            logger.info("Committed %s CustomerService objects in batches of %s", total, batch_size)
            return total
        except SQLAlchemyError as exc:
            self.db.rollback()
            logger.error("Batch commit failed after %s objects: %s", total, exc)
            raise

    def get_revenue_by_service_plan(self, service_plan_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Calculate revenue statistics by service plan."""
        query = self.db.query(
            ServiceTemplate.id,
            ServiceTemplate.name,
            ServiceTemplate.service_type,
            func.count(CustomerService.id).label('total_assignments'),
            func.count(func.case([(CustomerService.status == 'active', CustomerService.id)])).label('active_assignments'),
            func.sum(func.case([(CustomerService.status == 'active', CustomerService.monthly_cost)])).label('total_revenue')
        ).join(CustomerService).filter(CustomerService.status == 'active')
        
        if service_plan_id:
            query = query.filter(ServiceTemplate.id == service_plan_id)
        
        return query.group_by(ServiceTemplate.id, ServiceTemplate.name, ServiceTemplate.service_type).all()
