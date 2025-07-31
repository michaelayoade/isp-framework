import logging
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy.orm import Session

from app.core.exceptions import DuplicateError, NotFoundError, ValidationError
from app.models.customer.status import CustomerStatus
from app.schemas.customer_status import CustomerStatusCreate, CustomerStatusUpdate

logger = logging.getLogger(__name__)


class CustomerStatusService:
    """Service layer for customer status management."""

    def __init__(self, db: Session):
        self.db = db

    def list_customer_statuses(self, active_only: bool = True) -> List[CustomerStatus]:
        """List all customer statuses, optionally filtering by active status."""
        query = self.db.query(CustomerStatus)

        if active_only:
            query = query.filter(CustomerStatus.is_active is True)

        statuses = query.order_by(CustomerStatus.sort_order, CustomerStatus.name).all()
        return statuses

    def get_customer_status(self, status_id: int) -> CustomerStatus:
        """Get a customer status by ID."""
        status = (
            self.db.query(CustomerStatus).filter(CustomerStatus.id == status_id).first()
        )
        if not status:
            raise NotFoundError(f"Customer status with ID {status_id} not found")
        return status

    def get_customer_status_by_code(self, code: str) -> Optional[CustomerStatus]:
        """Get a customer status by code."""
        return self.db.query(CustomerStatus).filter(CustomerStatus.code == code).first()

    def create_customer_status(
        self, status_data: CustomerStatusCreate
    ) -> CustomerStatus:
        """Create a new customer status."""
        # Check if code already exists
        existing = self.get_customer_status_by_code(status_data.code)
        if existing:
            raise DuplicateError(
                f"Customer status with code '{status_data.code}' already exists"
            )

        # Create status
        status_dict = status_data.model_dump()
        status_dict["is_system"] = (
            False  # User-created statuses are not system statuses
        )

        status = CustomerStatus(**status_dict)
        self.db.add(status)
        self.db.commit()
        self.db.refresh(status)

        logger.info(f"Created customer status: {status.code}")
        return status

    def update_customer_status(
        self, status_id: int, status_data: CustomerStatusUpdate
    ) -> CustomerStatus:
        """Update an existing customer status."""
        status = self.get_customer_status(status_id)

        # Check if code is being changed and if it conflicts
        if status_data.code and status_data.code != status.code:
            existing = self.get_customer_status_by_code(status_data.code)
            if existing:
                raise DuplicateError(
                    f"Customer status with code '{status_data.code}' already exists"
                )

        # Update fields
        update_data = status_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(status, field, value)

        status.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(status)

        logger.info(f"Updated customer status {status_id}")
        return status

    def delete_customer_status(self, status_id: int):
        """Delete a customer status (only non-system statuses)."""
        status = self.get_customer_status(status_id)

        # Check if it's a system status
        if status.is_system:
            raise ValidationError(
                f"System customer status '{status.code}' cannot be deleted"
            )

        # Check if it's in use
        from app.models.customer.base import Customer

        customers_using_status = (
            self.db.query(Customer).filter(Customer.status_id == status_id).count()
        )

        if customers_using_status > 0:
            raise ValidationError(
                f"Customer status '{status.code}' is in use by {customers_using_status} customers and cannot be deleted"
            )

        self.db.delete(status)
        self.db.commit()

        logger.info(f"Deleted customer status {status_id}")

    def get_default_customer_status(self) -> CustomerStatus:
        """Get the default customer status (new)."""
        default_status = self.get_customer_status_by_code("new")
        if not default_status:
            # Fallback to first active status
            default_status = (
                self.db.query(CustomerStatus)
                .filter(CustomerStatus.is_active is True)
                .order_by(CustomerStatus.sort_order)
                .first()
            )

            if not default_status:
                raise ValidationError("No active customer statuses found")

        return default_status

    def get_active_customer_status(self) -> CustomerStatus:
        """Get the active customer status."""
        active_status = self.get_customer_status_by_code("active")
        if not active_status:
            raise ValidationError("Active customer status not found")
        return active_status

    def can_activate_services(self, status_id: int) -> bool:
        """Check if services can be activated for customers with this status."""
        status = self.get_customer_status(status_id)
        return status.allows_service_activation

    def should_continue_billing(self, status_id: int) -> bool:
        """Check if billing should continue for customers with this status."""
        status = self.get_customer_status(status_id)
        return status.allows_billing
