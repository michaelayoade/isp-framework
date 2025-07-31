import logging
from typing import List, Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class CustomerRepository(BaseRepository[Customer]):
    """Repository for customer-specific database operations."""

    def __init__(self, db: Session):
        super().__init__(Customer, db)

    def get_by_email(self, email: str) -> Optional[Customer]:
        """Get customer by email address."""
        return self.get_by_field("email", email)

    def get_by_login(self, login: str) -> Optional[Customer]:
        """Get customer by login."""
        return self.get_by_field("login", login)

    def search(
        self,
        query: str,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        category: Optional[str] = None,
        location_id: Optional[int] = None,
    ) -> List[Customer]:
        """Search customers by name, email, or phone with additional filters."""
        try:
            db_query = self.db.query(self.model)

            # Text search across multiple fields
            if query:
                search_filter = or_(
                    Customer.name.ilike(f"%{query}%"),
                    Customer.email.ilike(f"%{query}%"),
                    Customer.phone.ilike(f"%{query}%"),
                )
                db_query = db_query.filter(search_filter)

            # Additional filters
            if status:
                db_query = db_query.filter(Customer.status == status)

            if category:
                db_query = db_query.filter(Customer.category == category)

            if location_id:
                db_query = db_query.filter(Customer.location_id == location_id)

            return db_query.offset(skip).limit(limit).all()

        except Exception as e:
            logger.error(f"Error searching customers: {e}")
            raise

    def count_search(
        self,
        query: str,
        status: Optional[str] = None,
        category: Optional[str] = None,
        location_id: Optional[int] = None,
    ) -> int:
        """Count customers matching search criteria."""
        try:
            db_query = self.db.query(self.model)

            # Text search across multiple fields
            if query:
                search_filter = or_(
                    Customer.name.ilike(f"%{query}%"),
                    Customer.email.ilike(f"%{query}%"),
                    Customer.phone.ilike(f"%{query}%"),
                )
                db_query = db_query.filter(search_filter)

            # Additional filters
            if status:
                db_query = db_query.filter(Customer.status == status)

            if category:
                db_query = db_query.filter(Customer.category == category)

            if location_id:
                db_query = db_query.filter(Customer.location_id == location_id)

            return db_query.count()

        except Exception as e:
            logger.error(f"Error counting search results: {e}")
            raise

    def get_by_status(self, status: str) -> List[Customer]:
        """Get all customers with a specific status."""
        return self.get_all(filters={"status": status})

    def get_by_category(self, category: str) -> List[Customer]:
        """Get all customers with a specific category."""
        return self.get_all(filters={"category": category})

    def get_active_customers(self) -> List[Customer]:
        """Get all active customers."""
        return self.get_by_status("active")

    def update_status(self, customer_id: int, status: str) -> Customer:
        """Update customer status."""
        return self.update(customer_id, {"status": status})

    def email_exists(self, email: str, exclude_id: Optional[int] = None) -> bool:
        """Check if email already exists, optionally excluding a specific customer."""
        query = self.db.query(Customer).filter(Customer.email == email)
        if exclude_id:
            query = query.filter(Customer.id != exclude_id)
        return query.first() is not None

    def login_exists(self, login: str, exclude_id: Optional[int] = None) -> bool:
        """Check if login already exists, optionally excluding a specific customer."""
        query = self.db.query(Customer).filter(Customer.login == login)
        if exclude_id:
            query = query.filter(Customer.id != exclude_id)
        return query.first() is not None
