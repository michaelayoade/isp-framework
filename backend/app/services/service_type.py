from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from app.models.service.service_type import ServiceType
from app.schemas.service_type import ServiceTypeCreate, ServiceTypeUpdate
from app.core.exceptions import NotFoundError, DuplicateError, ValidationError
import logging

logger = logging.getLogger(__name__)


class ServiceTypeService:
    """Service layer for service type management."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def list_service_types(self, active_only: bool = True) -> List[ServiceType]:
        """List all service types, optionally filtering by active status."""
        query = self.db.query(ServiceType)
        
        if active_only:
            query = query.filter(ServiceType.is_active is True)
        
        service_types = query.order_by(ServiceType.sort_order, ServiceType.name).all()
        return service_types
    
    def get_service_type(self, service_type_id: int) -> ServiceType:
        """Get a service type by ID."""
        service_type = self.db.query(ServiceType).filter(ServiceType.id == service_type_id).first()
        if not service_type:
            raise NotFoundError(f"Service type with ID {service_type_id} not found")
        return service_type
    
    def get_service_type_by_code(self, code: str) -> Optional[ServiceType]:
        """Get a service type by code."""
        return self.db.query(ServiceType).filter(ServiceType.code == code).first()
    
    def create_service_type(self, service_type_data: ServiceTypeCreate) -> ServiceType:
        """Create a new service type."""
        # Check if code already exists
        existing = self.get_service_type_by_code(service_type_data.code)
        if existing:
            raise DuplicateError(f"Service type with code '{service_type_data.code}' already exists")
        
        # Create service type
        service_type_dict = service_type_data.model_dump()
        service_type_dict['is_system'] = False  # User-created service types are not system types
        
        service_type = ServiceType(**service_type_dict)
        self.db.add(service_type)
        self.db.commit()
        self.db.refresh(service_type)
        
        logger.info(f"Created service type: {service_type.code}")
        return service_type
    
    def update_service_type(self, service_type_id: int, service_type_data: ServiceTypeUpdate) -> ServiceType:
        """Update an existing service type."""
        service_type = self.get_service_type(service_type_id)
        
        # Check if code is being changed and if it conflicts
        if service_type_data.code and service_type_data.code != service_type.code:
            existing = self.get_service_type_by_code(service_type_data.code)
            if existing:
                raise DuplicateError(f"Service type with code '{service_type_data.code}' already exists")
        
        # Update fields
        update_data = service_type_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(service_type, field, value)
        
        service_type.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(service_type)
        
        logger.info(f"Updated service type {service_type_id}")
        return service_type
    
    def delete_service_type(self, service_type_id: int):
        """Delete a service type (only non-system service types)."""
        service_type = self.get_service_type(service_type_id)
        
        # Check if it's a system service type
        if service_type.is_system:
            raise ValidationError(f"System service type '{service_type.code}' cannot be deleted")
        
        # Check if it's in use by service plans
        from app.models.service.plan import ServicePlan
        plans_using_type = self.db.query(ServicePlan).filter(
            ServicePlan.service_type_id == service_type_id
        ).count()
        
        if plans_using_type > 0:
            raise ValidationError(f"Service type '{service_type.code}' is in use by {plans_using_type} service plans and cannot be deleted")
        
        # Check if it's in use by customer services
        try:
            from app.models.customer.service import CustomerService
            services_using_type = self.db.query(CustomerService).filter(
                CustomerService.service_type_id == service_type_id
            ).count()
            
            if services_using_type > 0:
                raise ValidationError(f"Service type '{service_type.code}' is in use by {services_using_type} customer services and cannot be deleted")
        except ImportError:
            # CustomerService model doesn't exist yet, skip this check
            pass
        
        self.db.delete(service_type)
        self.db.commit()
        
        logger.info(f"Deleted service type {service_type_id}")
    
    def get_default_service_type(self) -> ServiceType:
        """Get the default service type (internet)."""
        default_type = self.get_service_type_by_code('internet')
        if not default_type:
            # Fallback to first active service type
            default_type = self.db.query(ServiceType).filter(
                ServiceType.is_active is True
            ).order_by(ServiceType.sort_order).first()
            
            if not default_type:
                raise ValidationError("No active service types found")
        
        return default_type
    
    def get_recurring_service_types(self) -> List[ServiceType]:
        """Get all recurring service types."""
        return self.db.query(ServiceType).filter(
            ServiceType.is_active is True,
            ServiceType.is_recurring is True
        ).order_by(ServiceType.sort_order).all()
    
    def get_one_time_service_types(self) -> List[ServiceType]:
        """Get all one-time service types."""
        return self.db.query(ServiceType).filter(
            ServiceType.is_active is True,
            ServiceType.is_recurring is False
        ).order_by(ServiceType.sort_order).all()
    
    def supports_bandwidth_limits(self, service_type_id: int) -> bool:
        """Check if service type supports bandwidth limits."""
        service_type = self.get_service_type(service_type_id)
        return service_type.supports_bandwidth_limits
    
    def requires_installation(self, service_type_id: int) -> bool:
        """Check if service type requires installation."""
        service_type = self.get_service_type(service_type_id)
        return service_type.requires_installation
