from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from app.models.customer.base import ContactType
from app.schemas.customer import ContactTypeCreate, ContactTypeUpdate
from app.core.exceptions import NotFoundError, DuplicateError, ValidationError
import logging

logger = logging.getLogger(__name__)


class ContactTypeService:
    """Service layer for contact type management."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def list_contact_types(self, active_only: bool = True) -> List[ContactType]:
        """List all contact types, optionally filtering by active status."""
        query = self.db.query(ContactType)
        
        if active_only:
            query = query.filter(ContactType.is_active == True)
        
        contact_types = query.order_by(ContactType.sort_order, ContactType.name).all()
        return contact_types
    
    def get_contact_type(self, contact_type_id: int) -> ContactType:
        """Get a contact type by ID."""
        contact_type = self.db.query(ContactType).filter(ContactType.id == contact_type_id).first()
        if not contact_type:
            raise NotFoundError(f"Contact type with ID {contact_type_id} not found")
        return contact_type
    
    def get_contact_type_by_code(self, code: str) -> Optional[ContactType]:
        """Get a contact type by code."""
        return self.db.query(ContactType).filter(ContactType.code == code).first()
    
    def create_contact_type(self, contact_type_data: ContactTypeCreate) -> ContactType:
        """Create a new contact type."""
        # Check if code already exists
        existing = self.get_contact_type_by_code(contact_type_data.code)
        if existing:
            raise DuplicateError(f"Contact type with code '{contact_type_data.code}' already exists")
        
        # Create contact type
        contact_type_dict = contact_type_data.model_dump()
        contact_type_dict['is_system'] = False  # User-created types are not system types
        
        contact_type = ContactType(**contact_type_dict)
        self.db.add(contact_type)
        self.db.commit()
        self.db.refresh(contact_type)
        
        logger.info(f"Created contact type: {contact_type.code}")
        return contact_type
    
    def update_contact_type(self, contact_type_id: int, contact_type_data: ContactTypeUpdate) -> ContactType:
        """Update an existing contact type."""
        contact_type = self.get_contact_type(contact_type_id)
        
        # Check if code is being changed and if it conflicts
        if contact_type_data.code and contact_type_data.code != contact_type.code:
            existing = self.get_contact_type_by_code(contact_type_data.code)
            if existing:
                raise DuplicateError(f"Contact type with code '{contact_type_data.code}' already exists")
        
        # Update fields
        update_data = contact_type_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(contact_type, field, value)
        
        contact_type.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(contact_type)
        
        logger.info(f"Updated contact type {contact_type_id}")
        return contact_type
    
    def delete_contact_type(self, contact_type_id: int):
        """Delete a contact type (only non-system types)."""
        contact_type = self.get_contact_type(contact_type_id)
        
        # Check if it's a system type
        if contact_type.is_system:
            raise ValidationError(f"System contact type '{contact_type.code}' cannot be deleted")
        
        # Check if it's in use
        from app.models.customer.base import CustomerContact
        contacts_using_type = self.db.query(CustomerContact).filter(
            CustomerContact.contact_type_id == contact_type_id
        ).count()
        
        if contacts_using_type > 0:
            raise ValidationError(f"Contact type '{contact_type.code}' is in use by {contacts_using_type} contacts and cannot be deleted")
        
        self.db.delete(contact_type)
        self.db.commit()
        
        logger.info(f"Deleted contact type {contact_type_id}")
    
    def get_default_contact_type(self) -> ContactType:
        """Get the default contact type (primary)."""
        default_type = self.get_contact_type_by_code('primary')
        if not default_type:
            # Fallback to first active contact type
            default_type = self.db.query(ContactType).filter(
                ContactType.is_active == True
            ).order_by(ContactType.sort_order).first()
            
            if not default_type:
                raise ValidationError("No active contact types found")
        
        return default_type
