from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.customer import CustomerService
from app.schemas.customer import Customer, CustomerCreate, CustomerUpdate, CustomerList
from app.api.dependencies import get_current_active_admin, validate_pagination
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
