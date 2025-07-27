from typing import Optional, List
from sqlalchemy.orm import Session
from app.repositories.base import BaseRepository
from app.models.services import ServiceTemplate
import logging

logger = logging.getLogger(__name__)


class ServicePlanRepository(BaseRepository[ServiceTemplate]):
    """Repository for service plan-specific database operations."""
    
    def __init__(self, db: Session):
        super().__init__(ServiceTemplate, db)
    
    def get_by_name(self, name: str) -> Optional[ServiceTemplate]:
        """Get service plan by name."""
        return self.db.query(ServiceTemplate).filter(ServiceTemplate.name == name).first()
    
    def get_active_plans(self) -> List[ServiceTemplate]:
        """Get all active service plans."""
        return self.get_all(filters={"is_active": True})
    
    def get_by_service_type(self, service_type: str, active_only: bool = True) -> List[ServiceTemplate]:
        """Get service plans by type."""
        filters = {"service_type": service_type}
        if active_only:
            filters["is_active"] = True
        return self.get_all(filters=filters)
    
    def get_internet_plans(self, active_only: bool = True) -> List[ServiceTemplate]:
        """Get internet service plans."""
        return self.get_by_service_type("internet", active_only)
    
    def get_voice_plans(self, active_only: bool = True) -> List[ServiceTemplate]:
        """Get voice service plans."""
        return self.get_by_service_type("voice", active_only)
    
    def get_bundle_plans(self, active_only: bool = True) -> List[ServiceTemplate]:
        """Get bundle service plans."""
        return self.get_by_service_type("bundle", active_only)
    
    def deactivate_plan(self, plan_id: int) -> ServiceTemplate:
        """Deactivate a service plan."""
        return self.update(plan_id, {"is_active": False})
    
    def activate_plan(self, plan_id: int) -> ServiceTemplate:
        """Activate a service plan."""
        return self.update(plan_id, {"is_active": True})
    
    def name_exists(self, name: str, exclude_id: Optional[int] = None) -> bool:
        """Check if service plan name already exists."""
        query = self.db.query(ServicePlan).filter(ServicePlan.name == name)
        if exclude_id:
            query = query.filter(ServicePlan.id != exclude_id)
        return query.first() is not None
