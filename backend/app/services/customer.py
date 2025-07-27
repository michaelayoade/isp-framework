from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from passlib.context import CryptContext
from app.repositories.customer import CustomerRepository
from app.schemas.customer import CustomerCreate, CustomerUpdate, CustomerList
from app.core.exceptions import NotFoundError, DuplicateError, ValidationError
from app.core.config import settings
from app.services.portal_id import PortalIDService
from app.services.webhook_integration_service import WebhookTriggers
import logging

logger = logging.getLogger(__name__)


class CustomerService:
    """Service layer for customer business logic with ISP Framework features."""
    
    def __init__(self, db: Session):
        self.db = db
        self.customer_repo = CustomerRepository(db)
        self.portal_id_service = PortalIDService(db)
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.webhook_triggers = WebhookTriggers(db)
    
    def get_customer(self, customer_id: int):
        """Get a customer by ID."""
        customer = self.customer_repo.get(customer_id)
        if not customer:
            raise NotFoundError(f"Customer with id {customer_id} not found")
        return customer
    
    def list_customers(
        self,
        page: int = 1,
        per_page: int = None,
        search: Optional[str] = None,
        status: Optional[str] = None,
        category: Optional[str] = None,
        location_id: Optional[int] = None
    ) -> CustomerList:
        """List customers with pagination and filtering."""
        if per_page is None:
            per_page = settings.default_page_size
        
        # Validate pagination parameters
        if page < 1:
            page = 1
        if per_page > settings.max_page_size:
            per_page = settings.max_page_size
        
        skip = (page - 1) * per_page
        
        # Get customers and total count
        if search:
            customers = self.customer_repo.search(
                query=search,
                skip=skip,
                limit=per_page,
                status=status,
                category=category,
                location_id=location_id
            )
            total = self.customer_repo.count_search(
                query=search,
                status=status,
                category=category,
                location_id=location_id
            )
        else:
            filters = {}
            if status:
                filters["status"] = status
            if category:
                filters["category"] = category
            if location_id:
                filters["location_id"] = location_id
            
            customers = self.customer_repo.get_all(
                skip=skip,
                limit=per_page,
                filters=filters
            )
            total = self.customer_repo.count(filters=filters)
        
        return CustomerList(
            customers=customers,
            total=total,
            page=page,
            per_page=per_page,
            pages=((total - 1) // per_page) + 1 if total > 0 else 0
        )
    
    def create_customer(self, customer_data: CustomerCreate) -> Any:
        """Create a new customer."""
        # Validate unique constraints
        if customer_data.email and self.customer_repo.email_exists(customer_data.email):
            raise DuplicateError(f"Customer with email {customer_data.email} already exists")
        
        # Create customer data dict
        customer_dict = customer_data.model_dump()
        customer_dict["status"] = "new"  # Default status
        
        # Handle password hashing (remove password field and add password_hash)
        if "password" in customer_dict and customer_dict["password"]:
            customer_dict["password_hash"] = self.pwd_context.hash(customer_dict["password"])
        del customer_dict["password"]  # Remove password field to avoid model constructor error
        
        # Set required fields with defaults
        customer_dict["partner_id"] = customer_dict.get("partner_id", 1)  # Default partner
        customer_dict["location_id"] = customer_dict.get("location_id", 1)  # Default location
        
        try:
            # We need to handle the portal_id NOT NULL constraint
            # First, let's get the next customer ID to generate the portal_id
            next_id = self._get_next_customer_id()
            
            # Generate portal ID using the predicted next ID
            portal_id = self.portal_id_service.generate_portal_id(next_id, customer_dict["partner_id"])
            
            # Check if portal ID already exists
            existing_customers = self.customer_repo.get_all(filters={"portal_id": portal_id})
            if existing_customers:
                raise DuplicateError(f"Customer with portal ID {portal_id} already exists")
            
            # Add portal_id to customer data before creation
            customer_dict["portal_id"] = portal_id
            
            # Create customer with portal_id included
            customer = self.customer_repo.create(customer_dict)
            
            # Trigger webhook event
            try:
                self.webhook_triggers.customer_created({
                    'id': customer.id,
                    'email': customer.email,
                    'full_name': customer.full_name,
                    'portal_id': customer.portal_id,
                    'created_at': customer.created_at.isoformat(),
                    'customer_type': customer.customer_type or 'individual'
                })
            except Exception as e:
                logger.warning(f"Failed to trigger customer.created webhook: {e}")
            
            logger.info(f"Created customer {customer.id} with portal ID {portal_id}")
            
            return customer
        except Exception as e:
            logger.error(f"Error creating customer: {e}")
            raise
    
    def _get_next_customer_id(self) -> int:
        """Get the next customer ID by querying the database sequence."""
        try:
            from sqlalchemy import text
            # Get the current maximum ID and add 1
            result = self.db.execute(text("SELECT COALESCE(MAX(id), 0) + 1 FROM customers"))
            next_id = result.scalar()
            logger.debug(f"Predicted next customer ID: {next_id}")
            return next_id
        except Exception as e:
            logger.error(f"Error getting next customer ID: {e}")
            # Fallback: get count and add 1
            try:
                count = self.customer_repo.count()
                return count + 1
            except:
                return 999999
    
    def update_customer(self, customer_id: int, customer_data: CustomerUpdate) -> Any:
        """Update an existing customer."""
        # Check if customer exists
        existing_customer = self.get_customer(customer_id)
        
        # Validate unique constraints if email is being updated
        if customer_data.email and customer_data.email != existing_customer.email:
            if self.customer_repo.email_exists(customer_data.email, exclude_id=customer_id):
                raise DuplicateError(f"Customer with email {customer_data.email} already exists")
        
        # Update customer
        update_dict = customer_data.model_dump(exclude_unset=True)
        try:
            customer = self.customer_repo.update(customer_id, update_dict)
            
            # Trigger webhook event
            try:
                self.webhook_triggers.customer_updated({
                    'id': customer.id,
                    'email': customer.email,
                    'full_name': customer.full_name,
                    'portal_id': customer.portal_id,
                    'updated_at': customer.updated_at.isoformat(),
                    'customer_type': customer.customer_type or 'individual'
                })
            except Exception as e:
                logger.warning(f"Failed to trigger customer.updated webhook: {e}")
            
            logger.info(f"Updated customer {customer.id}")
            return customer
        except Exception as e:
            logger.error(f"Error updating customer {customer_id}: {e}")
            raise
    
    def delete_customer(self, customer_id: int) -> bool:
        """Delete a customer."""
        # Check if customer exists
        customer = self.get_customer(customer_id)
        
        try:
            # Get customer data before deletion for webhook
            customer_data = {
                'id': customer.id,
                'email': customer.email,
                'full_name': customer.full_name,
                'portal_id': customer.portal_id
            }
            
            # Delete customer
            self.customer_repo.delete(customer_id)
            
            # Trigger webhook event
            try:
                self.webhook_triggers.customer_deleted(customer_id, customer_data)
            except Exception as e:
                logger.warning(f"Failed to trigger customer.deleted webhook: {e}")
            
            logger.info(f"Customer deleted: {customer_id}")
            return {"message": "Customer deleted successfully"}
        except Exception as e:
            logger.error(f"Error deleting customer {customer_id}: {e}")
            raise
    
    def update_customer_status(self, customer_id: int, status: str) -> Any:
        """Update customer status."""
        valid_statuses = ["new", "active", "blocked", "disabled"]
        if status not in valid_statuses:
            raise ValidationError(f"Invalid status. Must be one of: {valid_statuses}")
        
        try:
            customer = self.customer_repo.update_status(customer_id, status)
            logger.info(f"Updated customer {customer_id} status to {status}")
            return customer
        except Exception as e:
            logger.error(f"Error updating customer {customer_id} status: {e}")
            raise
    
    def get_customers_by_status(self, status: str) -> List[Any]:
        """Get customers by status."""
        return self.customer_repo.get_by_status(status)
    
    def get_active_customers(self) -> List[Any]:
        """Get all active customers."""
        return self.customer_repo.get_active_customers()
    
    def _generate_login(self, name: str, email: str) -> str:
        """Generate a unique login for the customer."""
        # Try email username first
        if email:
            base_login = email.split("@")[0].lower()
        else:
            # Use name as fallback
            base_login = name.lower().replace(" ", "").replace(".", "")
        
        # Ensure uniqueness
        login = base_login
        counter = 1
        while self.customer_repo.login_exists(login):
            login = f"{base_login}{counter}"
            counter += 1
        
        return login
    
    # Portal ID Authentication Methods
    def authenticate_by_portal_id(self, portal_id: str, password: str) -> Optional[Any]:
        """Authenticate customer using portal ID and password."""
        try:
            # Get customer by portal ID (computed from customer ID)
            customer = self.get_customer_by_portal_id(portal_id)
            if not customer:
                logger.warning(f"Authentication failed: Portal ID {portal_id} not found")
                return None
            
            # Verify password
            if not customer.password_hash or not self.pwd_context.verify(password, customer.password_hash):
                logger.warning(f"Authentication failed: Invalid password for portal ID {portal_id}")
                return None
            
            # Update last login
            self.customer_repo.update(customer.id, {
                "last_online": datetime.now(timezone.utc)
            })
            
            logger.info(f"Successful authentication for portal ID {portal_id} (customer {customer.id})")
            return customer
            
        except Exception as e:
            logger.error(f"Error authenticating portal ID {portal_id}: {e}")
            return None
    
    def get_customer_by_portal_id(self, portal_id: str) -> Optional[Any]:
        """Get customer by portal ID (computed from customer ID + prefix)."""
        try:
            # Extract customer ID from portal ID
            customer_id = self.portal_id_service.extract_customer_id_from_portal_id(portal_id)
            if not customer_id:
                return None
            
            # Get customer and verify portal ID matches
            customer = self.customer_repo.get(customer_id)
            if customer:
                expected_portal_id = self.portal_id_service.generate_portal_id(customer.id)
                if expected_portal_id == portal_id:
                    return customer
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting customer by portal ID {portal_id}: {e}")
            return None
    
    def set_customer_password(self, customer_id: int, password: str) -> bool:
        """Set customer password (hashed)."""
        try:
            password_hash = self.pwd_context.hash(password)
            self.customer_repo.update(customer_id, {"password_hash": password_hash})
            logger.info(f"Password updated for customer {customer_id}")
            return True
        except Exception as e:
            logger.error(f"Error setting password for customer {customer_id}: {e}")
            return False
    
    def get_customer_portal_id(self, customer_id: int) -> Optional[str]:
        """Get portal ID for a customer."""
        try:
            customer = self.get_customer(customer_id)
            if customer:
                return self.portal_id_service.generate_portal_id(customer.id)
            return None
        except Exception as e:
            logger.error(f"Error getting portal ID for customer {customer_id}: {e}")
            return None
    
    # Enhanced Customer Management Methods
    def create_customer_with_portal_id(self, customer_data: CustomerCreate, password: Optional[str] = None) -> Any:
        """Create customer with automatic portal ID generation and optional password."""
        # Generate unique login if not provided
        if not hasattr(customer_data, 'login') or not customer_data.login:
            login = self._generate_login(customer_data.name, customer_data.email or "")
        else:
            login = customer_data.login
        
        # Check for duplicate login
        if self.customer_repo.login_exists(login):
            raise DuplicateError(f"Customer with login {login} already exists")
        
        # Create customer data dict
        customer_dict = customer_data.model_dump()
        customer_dict["login"] = login
        customer_dict["status"] = "new"  # Default status
        
        # Hash password if provided
        if password:
            customer_dict["password_hash"] = self.pwd_context.hash(password)
        
        try:
            customer = self.customer_repo.create(customer_dict)
            
            # Generate and log portal ID
            portal_id = self.portal_id_service.generate_portal_id(customer.id)
            logger.info(f"Created customer {customer.id} with login {customer.login} and portal ID {portal_id}")
            
            return customer
        except Exception as e:
            logger.error(f"Error creating customer: {e}")
            raise
    
    def get_customer_with_related_data(self, customer_id: int) -> Dict[str, Any]:
        """Get customer with all related modular data."""
        customer = self.get_customer(customer_id)
        
        # Get portal ID
        portal_id = self.get_customer_portal_id(customer_id)
        
        return {
            "customer": customer,
            "portal_id": portal_id,
            "info": customer.info,
            "billing_config": customer.billing_config,
            "contacts": customer.contacts,
            "labels": [assoc.label for assoc in customer.label_associations],
            "documents": customer.documents,
            "services": customer.services
        }
