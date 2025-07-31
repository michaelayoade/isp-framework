"""
Reseller Service

Business logic for reseller management in single-tenant ISP Framework.
"""

import logging
from datetime import datetime, timezone
from typing import List

from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.core.exceptions import DuplicateError, NotFoundError, ValidationError
from app.models.customer import Customer
from app.repositories.reseller import ResellerRepository
from app.schemas.reseller import (
    ResellerCommissionReport,
    ResellerCreate,
    ResellerCustomerSummary,
    ResellerDashboard,
    ResellerResponse,
    ResellerStats,
    ResellerUpdate,
)
from app.services.reseller_helpers import (
    get_customer_last_payment_date,
    get_customer_monthly_revenue,
    get_customer_services_count,
)

logger = logging.getLogger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class ResellerService:
    """Service for reseller management operations"""

    def __init__(self, db: Session):
        self.db = db
        self.repository = ResellerRepository(db)

    def create_reseller(self, reseller_data: ResellerCreate) -> ResellerResponse:
        """Create a new reseller"""
        logger.info(f"Creating new reseller: {reseller_data.name}")

        # Check if code already exists
        existing_reseller = self.repository.get_by_code(reseller_data.code)
        if existing_reseller:
            raise DuplicateError(
                f"Reseller with code '{reseller_data.code}' already exists"
            )

        # Check if email already exists
        existing_email = self.repository.get_by_email(reseller_data.email)
        if existing_email:
            raise DuplicateError(
                f"Reseller with email '{reseller_data.email}' already exists"
            )

        # Create reseller data dictionary
        reseller_dict = reseller_data.model_dump()

        # Hash the password before storing
        if "password" in reseller_dict:
            reseller_dict["password_hash"] = pwd_context.hash(reseller_dict["password"])
            del reseller_dict["password"]  # Remove plain text password

        reseller_dict["created_at"] = datetime.now(timezone.utc)
        reseller_dict["updated_at"] = datetime.now(timezone.utc)

        created_reseller = self.repository.create(reseller_dict)
        logger.info(f"Reseller created successfully: ID {created_reseller.id}")

        return ResellerResponse.model_validate(created_reseller)

    def get_reseller(self, reseller_id: int) -> ResellerResponse:
        """Get reseller by ID with customer count"""
        logger.info(f"Retrieving reseller: {reseller_id}")

        result = self.repository.get_reseller_with_customer_count(reseller_id)
        if not result:
            raise NotFoundError(f"Reseller with ID {reseller_id} not found")

        reseller_data = result["reseller"].__dict__.copy()
        reseller_data["customer_count"] = result["customer_count"]

        return ResellerResponse.model_validate(reseller_data)

    def update_reseller(
        self, reseller_id: int, update_data: ResellerUpdate
    ) -> ResellerResponse:
        """Update reseller information"""
        logger.info(f"Updating reseller: {reseller_id}")

        reseller = self.repository.get_by_id(reseller_id)
        if not reseller:
            raise NotFoundError(f"Reseller with ID {reseller_id} not found")

        # Check for email conflicts if email is being updated
        if update_data.email and update_data.email != reseller.email:
            existing_email = self.repository.get_by_email(update_data.email)
            if existing_email:
                raise DuplicateError(
                    f"Reseller with email '{update_data.email}' already exists"
                )

        # Update fields
        update_dict = update_data.model_dump(exclude_unset=True)
        update_dict["updated_at"] = datetime.now(timezone.utc)

        updated_reseller = self.repository.update(reseller.id, update_dict)

        logger.info(f"Reseller updated successfully: {reseller_id}")
        return ResellerResponse.model_validate(updated_reseller)

    def delete_reseller(self, reseller_id: int) -> bool:
        """Delete reseller (soft delete by deactivating)"""
        logger.info(f"Deleting reseller: {reseller_id}")

        reseller = self.repository.get_by_id(reseller_id)
        if not reseller:
            raise NotFoundError(f"Reseller with ID {reseller_id} not found")

        # Check if reseller has customers
        customer_count = self.repository.get_reseller_customer_count(reseller_id)
        if customer_count > 0:
            raise ValidationError(
                f"Cannot delete reseller with {customer_count} assigned customers"
            )

        # Soft delete by deactivating
        update_data = {"is_active": False, "updated_at": datetime.now(timezone.utc)}
        self.repository.update(reseller.id, update_data)

        logger.info(f"Reseller deactivated successfully: {reseller_id}")
        return True

    def get_resellers(
        self, limit: int = 50, offset: int = 0, active_only: bool = True
    ) -> List[ResellerResponse]:
        """Get list of resellers with customer counts"""
        logger.info(
            f"Retrieving resellers: limit={limit}, offset={offset}, active_only={active_only}"
        )

        filters = {"is_active": True} if active_only else {}
        resellers = self.repository.get_all(filters=filters, limit=limit, skip=offset)

        results = []
        for reseller in resellers:
            customer_count = self.repository.get_reseller_customer_count(reseller.id)
            reseller_data = reseller.__dict__.copy()
            reseller_data["customer_count"] = customer_count
            results.append(ResellerResponse.model_validate(reseller_data))

        return results

    def search_resellers(
        self, query: str, limit: int = 50, offset: int = 0
    ) -> List[ResellerResponse]:
        """Search resellers by name, code, or email"""
        logger.info(f"Searching resellers: query='{query}'")

        resellers = self.repository.search_resellers(query, limit, offset)

        results = []
        for reseller in resellers:
            customer_count = self.repository.get_reseller_customer_count(reseller.id)
            reseller_data = reseller.__dict__.copy()
            reseller_data["customer_count"] = customer_count
            results.append(ResellerResponse.model_validate(reseller_data))

        return results

    def get_reseller_stats(self, reseller_id: int) -> ResellerStats:
        """Get comprehensive reseller statistics"""
        logger.info(f"Retrieving reseller stats: {reseller_id}")

        reseller = self.repository.get_by_id(reseller_id)
        if not reseller:
            raise NotFoundError(f"Reseller with ID {reseller_id} not found")

        stats_data = self.repository.get_reseller_stats(reseller_id)
        return ResellerStats.model_validate(stats_data)

    def get_reseller_customers(
        self, reseller_id: int, limit: int = 50, offset: int = 0
    ) -> List[ResellerCustomerSummary]:
        """Get customers assigned to a reseller"""
        logger.info(f"Retrieving reseller customers: reseller_id={reseller_id}")

        reseller = self.repository.get_by_id(reseller_id)
        if not reseller:
            raise NotFoundError(f"Reseller with ID {reseller_id} not found")

        customers = self.repository.get_reseller_customers(reseller_id, limit, offset)

        results = []
        for customer in customers:
            # Get customer service count and revenue (simplified for now)
            customer_data = {
                "customer_id": customer.id,
                "portal_id": customer.portal_id,
                "name": customer.name,
                "email": customer.email,
                "status": customer.status,
                "services_count": get_customer_services_count(self.db, customer.id),
                "monthly_revenue": get_customer_monthly_revenue(self.db, customer.id),
                "last_payment": get_customer_last_payment_date(self.db, customer.id),
                "created_at": customer.created_at,
            }
            results.append(ResellerCustomerSummary.model_validate(customer_data))

        return results

    def get_reseller_commission_report(
        self, reseller_id: int, start_date: datetime, end_date: datetime
    ) -> ResellerCommissionReport:
        """Generate commission report for reseller"""
        logger.info(
            f"Generating commission report: reseller_id={reseller_id}, period={start_date} to {end_date}"
        )

        reseller = self.repository.get_by_id(reseller_id)
        if not reseller:
            raise NotFoundError(f"Reseller with ID {reseller_id} not found")

        commission_data = self.repository.get_reseller_commission_data(
            reseller_id, start_date, end_date
        )

        total_payments = commission_data["total_payments"]
        commission_amount = total_payments * (reseller.commission_percentage / 100)

        report_data = {
            "reseller_id": reseller_id,
            "reseller_name": reseller.name,
            "period_start": start_date,
            "period_end": end_date,
            "total_customer_payments": total_payments,
            "commission_rate": reseller.commission_percentage,
            "commission_amount": commission_amount,
            "payment_count": commission_data["payment_count"],
            "customer_count": commission_data["unique_customers"],
        }

        return ResellerCommissionReport.model_validate(report_data)

    def get_reseller_dashboard(self, reseller_id: int) -> ResellerDashboard:
        """Get comprehensive dashboard data for reseller"""
        logger.info(f"Retrieving reseller dashboard: {reseller_id}")

        # Get reseller info
        reseller_info = self.get_reseller(reseller_id)

        # Get stats
        stats = self.get_reseller_stats(reseller_id)

        # Get recent customers (last 10)
        recent_customers = self.get_reseller_customers(reseller_id, limit=10, offset=0)

        # Get commission summary for current month
        now = datetime.now(timezone.utc)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        commission_summary = self.get_reseller_commission_report(
            reseller_id, month_start, now
        )

        return ResellerDashboard(
            reseller=reseller_info,
            stats=stats,
            recent_customers=recent_customers,
            commission_summary=commission_summary,
        )

    def assign_customer_to_reseller(self, customer_id: int, reseller_id: int) -> bool:
        """Assign a customer to a reseller"""
        logger.info(f"Assigning customer {customer_id} to reseller {reseller_id}")

        reseller = self.repository.get_by_id(reseller_id)
        if not reseller:
            raise NotFoundError(f"Reseller with ID {reseller_id} not found")

        if not reseller.is_active:
            raise ValidationError("Cannot assign customers to inactive reseller")

        success = self.repository.assign_customer_to_reseller(customer_id, reseller_id)
        if not success:
            raise ValidationError(
                "Failed to assign customer to reseller (customer limit reached or customer not found)"
            )

        logger.info(
            f"Customer {customer_id} assigned to reseller {reseller_id} successfully"
        )
        return True

    def unassign_customer_from_reseller(self, customer_id: int) -> bool:
        """Remove customer assignment from reseller"""
        logger.info(f"Unassigning customer {customer_id} from reseller")

        # Find the customer and remove reseller assignment
        customer = self.db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            raise NotFoundError(f"Customer with ID {customer_id} not found")

        if not customer.reseller_id:
            logger.warning(f"Customer {customer_id} is not assigned to any reseller")
            return False

        # Remove reseller assignment
        customer.reseller_id = None
        customer.updated_at = datetime.now(timezone.utc)
        self.db.commit()

        logger.info(f"Customer {customer_id} unassigned from reseller successfully")
        return True


# Duplicate function implementations removed to fix F811 redefinition errors
# All functions are already implemented above in the ResellerService class
