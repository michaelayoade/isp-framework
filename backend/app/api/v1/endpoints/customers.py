from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.customer import CustomerService
from app.schemas.customer import (
    Customer, CustomerCreate, CustomerUpdate, CustomerList, CustomerWithExtended,
    CustomerContact, CustomerContactCreate, CustomerContactUpdate,
    CustomerExtended, CustomerExtendedCreate, CustomerExtendedUpdate
)
from app.api.dependencies import get_current_active_admin
from app.models import Administrator
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=CustomerList)
async def list_customers(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(25, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by name, email, or phone"),
    status: Optional[str] = Query(None, description="Filter by status"),
    category: Optional[str] = Query(None, description="Filter by category"),
    location_id: Optional[int] = Query(None, description="Filter by location"),
    current_admin: Administrator = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """List customers with pagination and filtering."""
    customer_service = CustomerService(db)
    
    try:
        result = customer_service.list_customers(
            page=page,
            per_page=per_page,
            search=search,
            status=status,
            category=category,
            location_id=location_id
        )
        return result
    except Exception as e:
        logger.error(f"Error listing customers: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving customers"
        )


@router.post("/", response_model=Customer, status_code=status.HTTP_201_CREATED)
async def create_customer(
    customer_data: CustomerCreate,
    current_admin: Administrator = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """Create a new customer."""
    customer_service = CustomerService(db)
    
    try:
        customer = customer_service.create_customer(customer_data)
        logger.info(f"Admin {current_admin.username} created customer {customer.id}")
        return customer
    except Exception as e:
        logger.error(f"Error creating customer: {e}")
        if "already exists" in str(e):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{customer_id}", response_model=Customer)
async def get_customer(
    customer_id: int,
    current_admin: Administrator = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """Get a specific customer by ID."""
    customer_service = CustomerService(db)
    
    try:
        customer = customer_service.get_customer(customer_id)
        return customer
    except Exception as e:
        logger.error(f"Error getting customer {customer_id}: {e}")
        if "not found" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving customer"
        )


@router.put("/{customer_id}", response_model=Customer)
async def update_customer(
    customer_id: int,
    customer_data: CustomerUpdate,
    current_admin: Administrator = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """Update an existing customer."""
    customer_service = CustomerService(db)
    
    try:
        customer = customer_service.update_customer(customer_id, customer_data)
        logger.info(f"Admin {current_admin.username} updated customer {customer_id}")
        return customer
    except Exception as e:
        logger.error(f"Error updating customer {customer_id}: {e}")
        if "not found" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        elif "already exists" in str(e):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_customer(
    customer_id: int,
    current_admin: Administrator = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """Delete a customer."""
    customer_service = CustomerService(db)
    
    try:
        customer_service.delete_customer(customer_id)
        logger.info(f"Admin {current_admin.username} deleted customer {customer_id}")
        return None
    except Exception as e:
        logger.error(f"Error deleting customer {customer_id}: {e}")
        if "not found" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting customer"
        )


@router.patch("/{customer_id}/status")
async def update_customer_status(
    customer_id: int,
    status_data: dict,
    current_admin: Administrator = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """Update customer status."""
    customer_service = CustomerService(db)
    
    new_status = status_data.get("status")
    if not new_status:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Status is required"
        )
    
    try:
        customer = customer_service.update_customer_status(customer_id, new_status)
        logger.info(f"Admin {current_admin.username} updated customer {customer_id} status to {new_status}")
        return customer
    except Exception as e:
        logger.error(f"Error updating customer {customer_id} status: {e}")
        if "not found" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        elif "Invalid status" in str(e):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating customer status"
        )


# Extended Customer Information Endpoints
@router.get("/{customer_id}/extended", response_model=CustomerWithExtended)
async def get_customer_with_extended(
    customer_id: int,
    current_admin: Administrator = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """Get customer with extended information and contacts."""
    customer_service = CustomerService(db)
    
    try:
        customer = customer_service.get_customer_with_extended(customer_id)
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Customer with ID {customer_id} not found"
            )
        return customer
    except Exception as e:
        logger.error(f"Error retrieving extended customer {customer_id}: {e}")
        if "not found" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving customer"
        )


@router.post("/{customer_id}/extended", response_model=CustomerExtended, status_code=status.HTTP_201_CREATED)
async def create_customer_extended(
    customer_id: int,
    extended_data: CustomerExtendedCreate,
    current_admin: Administrator = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """Create extended information for a customer."""
    customer_service = CustomerService(db)
    
    try:
        extended_info = customer_service.create_customer_extended(customer_id, extended_data)
        logger.info(f"Admin {current_admin.username} created extended info for customer {customer_id}")
        return extended_info
    except Exception as e:
        logger.error(f"Error creating extended info for customer {customer_id}: {e}")
        if "not found" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        elif "already exists" in str(e):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating extended customer information"
        )


@router.put("/{customer_id}/extended", response_model=CustomerExtended)
async def update_customer_extended(
    customer_id: int,
    extended_data: CustomerExtendedUpdate,
    current_admin: Administrator = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """Update extended information for a customer."""
    customer_service = CustomerService(db)
    
    try:
        extended_info = customer_service.update_customer_extended(customer_id, extended_data)
        logger.info(f"Admin {current_admin.username} updated extended info for customer {customer_id}")
        return extended_info
    except Exception as e:
        logger.error(f"Error updating extended info for customer {customer_id}: {e}")
        if "not found" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating extended customer information"
        )


# Customer Contacts Endpoints
@router.get("/{customer_id}/contacts", response_model=list[CustomerContact])
async def list_customer_contacts(
    customer_id: int,
    current_admin: Administrator = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """List all contacts for a customer."""
    customer_service = CustomerService(db)
    
    try:
        contacts = customer_service.list_customer_contacts(customer_id)
        return contacts
    except Exception as e:
        logger.error(f"Error listing contacts for customer {customer_id}: {e}")
        if "not found" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving customer contacts"
        )


@router.post("/{customer_id}/contacts", response_model=CustomerContact, status_code=status.HTTP_201_CREATED)
async def create_customer_contact(
    customer_id: int,
    contact_data: CustomerContactCreate,
    current_admin: Administrator = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """Create a new contact for a customer."""
    customer_service = CustomerService(db)
    
    try:
        contact = customer_service.create_customer_contact(customer_id, contact_data)
        logger.info(f"Admin {current_admin.username} created contact for customer {customer_id}")
        return contact
    except Exception as e:
        logger.error(f"Error creating contact for customer {customer_id}: {e}")
        if "not found" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating customer contact"
        )


@router.put("/{customer_id}/contacts/{contact_id}", response_model=CustomerContact)
async def update_customer_contact(
    customer_id: int,
    contact_id: int,
    contact_data: CustomerContactUpdate,
    current_admin: Administrator = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """Update a customer contact."""
    customer_service = CustomerService(db)
    
    try:
        contact = customer_service.update_customer_contact(customer_id, contact_id, contact_data)
        logger.info(f"Admin {current_admin.username} updated contact {contact_id} for customer {customer_id}")
        return contact
    except Exception as e:
        logger.error(f"Error updating contact {contact_id} for customer {customer_id}: {e}")
        if "not found" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating customer contact"
        )


@router.delete("/{customer_id}/contacts/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_customer_contact(
    customer_id: int,
    contact_id: int,
    current_admin: Administrator = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """Delete a customer contact."""
    customer_service = CustomerService(db)
    
    try:
        customer_service.delete_customer_contact(customer_id, contact_id)
        logger.info(f"Admin {current_admin.username} deleted contact {contact_id} for customer {customer_id}")
    except Exception as e:
        logger.error(f"Error deleting contact {contact_id} for customer {customer_id}: {e}")
        if "not found" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting customer contact"
        )
