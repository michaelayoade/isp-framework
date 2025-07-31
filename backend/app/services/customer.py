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
            except Exception:
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
    
    # Extended Customer Information Methods
    def get_customer_with_extended(self, customer_id: int):
        """Get customer with extended information and contacts."""
        from app.models.customer.base import CustomerExtended, CustomerContact
        
        customer = self.get_customer(customer_id)
        
        # Get extended info
        extended_info = self.db.query(CustomerExtended).filter(
            CustomerExtended.customer_id == customer_id
        ).first()
        
        # Get contacts
        contacts = self.db.query(CustomerContact).filter(
            CustomerContact.customer_id == customer_id
        ).all()
        
        # Build response
        customer_dict = {
            "id": customer.id,
            "portal_id": customer.portal_id,
            "name": customer.name,
            "email": customer.email,
            "phone": customer.phone,
            "category": customer.category,
            "address": customer.address,
            "city": customer.city,
            "zip_code": customer.zip_code,
            "billing_email": customer.billing_email,
            "gps": customer.gps,
            "custom_fields": customer.custom_fields or {},
            "status": customer.status,
            "created_at": customer.date_add,
            "updated_at": customer.last_update,
            "extended_info": extended_info,
            "contacts": contacts
        }
        
        return customer_dict
    
    def create_customer_extended(self, customer_id: int, extended_data):
        """Create extended information for a customer."""
        from app.models.customer.base import CustomerExtended
        
        # Verify customer exists
        self.get_customer(customer_id)
        
        # Check if extended info already exists
        existing = self.db.query(CustomerExtended).filter(
            CustomerExtended.customer_id == customer_id
        ).first()
        
        if existing:
            raise ValidationError(f"Extended information already exists for customer {customer_id}")
        
        # Create extended info
        extended_dict = extended_data.model_dump()
        extended_dict['customer_id'] = customer_id
        
        extended_info = CustomerExtended(**extended_dict)
        self.db.add(extended_info)
        self.db.commit()
        self.db.refresh(extended_info)
        
        logger.info(f"Created extended info for customer {customer_id}")
        return extended_info
    
    def update_customer_extended(self, customer_id: int, extended_data):
        """Update extended information for a customer."""
        from app.models.customer.base import CustomerExtended
        
        # Verify customer exists
        self.get_customer(customer_id)
        
        # Get existing extended info
        extended_info = self.db.query(CustomerExtended).filter(
            CustomerExtended.customer_id == customer_id
        ).first()
        
        if not extended_info:
            raise NotFoundError(f"Extended information not found for customer {customer_id}")
        
        # Update fields
        update_data = extended_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(extended_info, field, value)
        
        extended_info.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(extended_info)
        
        logger.info(f"Updated extended info for customer {customer_id}")
        return extended_info
    
    # Customer Contacts Methods
    def list_customer_contacts(self, customer_id: int):
        """List all contacts for a customer."""
        from app.models.customer.base import CustomerContact
        from sqlalchemy.orm import joinedload
        
        # Verify customer exists
        self.get_customer(customer_id)
        
        contacts = self.db.query(CustomerContact).options(
            joinedload(CustomerContact.contact_type_ref)
        ).filter(
            CustomerContact.customer_id == customer_id
        ).all()
        
        return contacts
    
    def create_customer_contact(self, customer_id: int, contact_data):
        """Create a new contact for a customer."""
        from app.models.customer.base import CustomerContact, ContactType
        
        # Verify customer exists
        self.get_customer(customer_id)
        
        # Verify contact type exists
        contact_type = self.db.query(ContactType).filter(
            ContactType.id == contact_data.contact_type_id,
            ContactType.is_active is True
        ).first()
        if not contact_type:
            raise ValidationError(f"Contact type with ID {contact_data.contact_type_id} not found or inactive")
        
        # Create contact
        contact_dict = contact_data.model_dump()
        contact_dict['customer_id'] = customer_id
        
        contact = CustomerContact(**contact_dict)
        self.db.add(contact)
        self.db.commit()
        self.db.refresh(contact)
        
        logger.info(f"Created contact for customer {customer_id}")
        return contact
    
    def update_customer_contact(self, customer_id: int, contact_id: int, contact_data):
        """Update a customer contact."""
        from app.models.customer.base import CustomerContact
        
        # Verify customer exists
        self.get_customer(customer_id)
        
        # Get contact
        contact = self.db.query(CustomerContact).filter(
            CustomerContact.id == contact_id,
            CustomerContact.customer_id == customer_id
        ).first()
        
        if not contact:
            raise NotFoundError(f"Contact {contact_id} not found for customer {customer_id}")
        
        # Update fields
        update_data = contact_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(contact, field, value)
        
        contact.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(contact)
        
        logger.info(f"Updated contact {contact_id} for customer {customer_id}")
        return contact
    
    def delete_customer_contact(self, customer_id: int, contact_id: int):
        """Delete a customer contact."""
        from app.models.customer.base import CustomerContact
        
        # Verify customer exists
        self.get_customer(customer_id)
        
        # Get contact
        contact = self.db.query(CustomerContact).filter(
            CustomerContact.id == contact_id,
            CustomerContact.customer_id == customer_id
        ).first()
        
        if not contact:
            raise NotFoundError(f"Contact {contact_id} not found for customer {customer_id}")
        
        self.db.delete(contact)
        self.db.commit()
        
        logger.info(f"Deleted contact {contact_id} for customer {customer_id}")
