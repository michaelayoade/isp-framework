import logging
from typing import List, Optional

from sqlalchemy.orm import Session

from app.core.exceptions import DuplicateError, NotFoundError, ValidationError
from app.repositories.service_plan import ServicePlanRepository
from app.schemas.service_plan import ServicePlanCreate, ServicePlanUpdate

logger = logging.getLogger(__name__)


class ServicePlanService:
    """Service layer for service plan business logic."""

    def __init__(self, db: Session):
        self.db = db
        self.service_plan_repo = ServicePlanRepository(db)

    def get_service_plan(self, plan_id: int):
        """Get a service plan by ID."""
        plan = self.service_plan_repo.get(plan_id)
        if not plan:
            raise NotFoundError(f"Service plan with id {plan_id} not found")
        return plan

    def list_service_plans(
        self, service_type: Optional[str] = None, active_only: bool = True
    ) -> List:
        """List service plans with optional filtering."""
        if service_type:
            return self.service_plan_repo.get_by_service_type(service_type, active_only)
        else:
            filters = {}
            if active_only:
                filters["is_active"] = True
            return self.service_plan_repo.get_all(filters=filters)

    def create_service_plan(self, plan_data: ServicePlanCreate):
        """Create a new service plan."""
        # Validate unique name
        if self.service_plan_repo.name_exists(plan_data.name):
            raise DuplicateError(
                f"Service plan with name '{plan_data.name}' already exists"
            )

        # Validate service type
        valid_types = ["internet", "voice", "bundle", "recurring", "onetime"]
        if plan_data.service_type not in valid_types:
            raise ValidationError(
                f"Invalid service type. Must be one of: {valid_types}"
            )

        # Validate pricing
        if plan_data.price <= 0:
            raise ValidationError("Price must be greater than 0")

        # Create plan data dict
        plan_dict = plan_data.model_dump()
        plan_dict["is_active"] = True  # Default to active

        try:
            plan = self.service_plan_repo.create(plan_dict)
            logger.info(f"Created service plan {plan.id} with name '{plan.name}'")
            return plan
        except Exception as e:
            logger.error(f"Error creating service plan: {e}")
            raise

    def update_service_plan(self, plan_id: int, plan_data: ServicePlanUpdate):
        """Update an existing service plan."""
        # Check if plan exists
        existing_plan = self.get_service_plan(plan_id)

        # Validate unique name if being updated
        if plan_data.name and plan_data.name != existing_plan.name:
            if self.service_plan_repo.name_exists(plan_data.name, exclude_id=plan_id):
                raise DuplicateError(
                    f"Service plan with name '{plan_data.name}' already exists"
                )

        # Validate pricing if being updated
        if plan_data.price is not None and plan_data.price <= 0:
            raise ValidationError("Price must be greater than 0")

        # Update plan
        update_dict = plan_data.model_dump(exclude_unset=True)
        try:
            plan = self.service_plan_repo.update(plan_id, update_dict)
            logger.info(f"Updated service plan {plan.id}")
            return plan
        except Exception as e:
            logger.error(f"Error updating service plan {plan_id}: {e}")
            raise

    def delete_service_plan(self, plan_id: int) -> bool:
        """Delete a service plan."""
        # Check if plan exists
        self.get_service_plan(plan_id)

        # Check if plan is in use by any services before deletion
        if self._is_plan_in_use(plan_id):
            raise ValidationError(
                f"Cannot delete service plan {plan_id}: it is currently in use by active services"
            )

        try:
            result = self.service_plan_repo.delete(plan_id)
            logger.info(f"Deleted service plan {plan_id}")
            return result
        except Exception as e:
            logger.error(f"Error deleting service plan {plan_id}: {e}")
            raise

    def activate_service_plan(self, plan_id: int):
        """Activate a service plan."""
        try:
            plan = self.service_plan_repo.activate_plan(plan_id)
            logger.info(f"Activated service plan {plan_id}")
            return plan
        except Exception as e:
            logger.error(f"Error activating service plan {plan_id}: {e}")
            raise

    def deactivate_service_plan(self, plan_id: int):
        """Deactivate a service plan."""
        try:
            plan = self.service_plan_repo.deactivate_plan(plan_id)
            logger.info(f"Deactivated service plan {plan_id}")
            return plan
        except Exception as e:
            logger.error(f"Error deactivating service plan {plan_id}: {e}")
            raise

    def get_internet_plans(self, active_only: bool = True):
        """Get internet service plans."""
        return self.service_plan_repo.get_internet_plans(active_only)

    def get_voice_plans(self, active_only: bool = True):
        """Get voice service plans."""
        return self.service_plan_repo.get_voice_plans(active_only)

    def get_bundle_plans(self, active_only: bool = True):
        """Get bundle service plans."""
        return self.service_plan_repo.get_bundle_plans(active_only)

    def _is_plan_in_use(self, plan_id: int) -> bool:
        """Check if a service plan is currently in use by any active services."""
        from app.models.service.base import Service

        # Check if any active services are using this plan
        active_services = (
            self.db.query(Service)
            .filter(
                Service.service_plan_id == plan_id,
                Service.status.in_(
                    ["active", "suspended"]
                ),  # Consider both active and suspended as "in use"
            )
            .count()
        )

        return active_services > 0
