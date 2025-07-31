"""
Portal ID Authentication Endpoints

Provides API endpoints for customer authentication using portal IDs
for both customer portal login and PPPoE/RADIUS authentication.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.v1.dependencies import get_current_admin
from app.core.database import get_db
from app.core.exceptions import ValidationError
from app.models.auth import Administrator
from app.services.customer import CustomerService

router = APIRouter()
security = HTTPBearer()


# Pydantic Models
class PortalAuthRequest(BaseModel):
    """Portal ID authentication request"""

    portal_id: str = Field(..., description="Customer portal ID", example="10003456")
    password: str = Field(..., description="Customer password", min_length=1)


class PortalAuthResponse(BaseModel):
    """Portal ID authentication response"""

    success: bool
    customer_id: int
    portal_id: str
    customer_name: str
    customer_status: str
    message: str


class PortalIDRegenerateRequest(BaseModel):
    """Portal ID regeneration request"""

    customer_id: int = Field(..., description="Customer ID to regenerate portal ID for")


class PortalIDRegenerateResponse(BaseModel):
    """Portal ID regeneration response"""

    success: bool
    customer_id: int
    old_portal_id: str
    new_portal_id: str
    message: str


class PortalIDValidationRequest(BaseModel):
    """Portal ID validation request"""

    portal_id: str = Field(..., description="Portal ID to validate")
    exclude_customer_id: int = Field(
        None, description="Customer ID to exclude from uniqueness check"
    )


class PortalIDValidationResponse(BaseModel):
    """Portal ID validation response"""

    valid_format: bool
    available: bool
    portal_id: str
    message: str


class MigrationResponse(BaseModel):
    """Portal ID migration response"""

    success: bool
    total_customers: int
    successful_migrations: int
    failed_migrations: int
    errors: list
    message: str


class PortalConfigCreate(BaseModel):
    """Portal configuration creation request"""

    partner_id: int = Field(default=1, description="Partner ID")
    prefix: str = Field(..., description="Portal ID prefix", max_length=20)
    description: str = Field(None, description="Configuration description")
    service_type: str = Field(default="internet", description="Service type")
    is_default: bool = Field(default=False, description="Is default configuration")


class PortalConfigUpdate(BaseModel):
    """Portal configuration update request"""

    prefix: str = Field(None, description="Portal ID prefix", max_length=20)
    description: str = Field(None, description="Configuration description")
    service_type: str = Field(None, description="Service type")
    is_default: bool = Field(None, description="Is default configuration")
    is_active: bool = Field(None, description="Is configuration active")


class PortalConfigResponse(BaseModel):
    """Portal configuration response"""

    id: int
    partner_id: int
    prefix: str
    description: str
    service_type: str
    is_default: bool
    is_active: bool
    created_at: str
    updated_at: str


@router.post("/authenticate", response_model=PortalAuthResponse)
async def authenticate_customer_portal_id(
    auth_request: PortalAuthRequest, db: Session = Depends(get_db)
):
    """
    Authenticate customer using portal ID and password.

    This endpoint is used for:
    - Customer portal login
    - PPPoE/RADIUS authentication
    - General customer authentication
    """
    try:
        customer_service = CustomerService(db)

        customer = customer_service.authenticate_by_portal_id(
            auth_request.portal_id, auth_request.password
        )

        if not customer:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid portal ID or password",
            )

        return PortalAuthResponse(
            success=True,
            customer_id=customer.id,
            portal_id=customer.portal_id,
            customer_name=customer.name,
            customer_status=customer.status,
            message="Authentication successful",
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication error: {str(e)}",
        )


@router.get("/customer/{portal_id}")
async def get_customer_by_portal_id(
    portal_id: str,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin),
):
    """
    Get customer information by portal ID.

    Requires admin authentication.
    """
    try:
        customer_service = CustomerService(db)
        customer = customer_service.get_customer_by_portal_id(portal_id)

        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Customer not found for portal ID: {portal_id}",
            )

        # Return basic customer info (without sensitive data)
        return {
            "customer_id": customer.id,
            "portal_id": customer.login,
            "name": customer.name,
            "email": customer.email,
            "status": customer.status,
            "category": customer.category,
            "partner_id": customer.partner_id,
            "created_at": customer.created_at,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving customer: {str(e)}",
        )


@router.post("/regenerate", response_model=PortalIDRegenerateResponse)
async def regenerate_customer_portal_id(
    request: PortalIDRegenerateRequest,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin),
):
    """
    Regenerate portal ID for an existing customer.

    Requires admin authentication.
    """
    try:
        customer_service = CustomerService(db)

        # Get current customer info
        customer = customer_service.customer_repo.get(request.customer_id)
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Customer with ID {request.customer_id} not found",
            )

        old_portal_id = customer.login

        # Regenerate portal ID
        new_portal_id = customer_service.regenerate_customer_portal_id(
            request.customer_id, current_admin.id
        )

        return PortalIDRegenerateResponse(
            success=True,
            customer_id=request.customer_id,
            old_portal_id=old_portal_id,
            new_portal_id=new_portal_id,
            message="Portal ID regenerated successfully",
        )

    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error regenerating portal ID: {str(e)}",
        )


@router.post("/validate", response_model=PortalIDValidationResponse)
async def validate_portal_id(
    request: PortalIDValidationRequest,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin),
):
    """
    Validate portal ID format and availability.

    Requires admin authentication.
    """
    try:
        from app.core.portal_id import PortalIDGenerator

        customer_service = CustomerService(db)

        # Check format
        valid_format = PortalIDGenerator.validate_portal_id_format(request.portal_id)

        # Check availability
        available = False
        if valid_format:
            available = customer_service.validate_portal_id_availability(
                request.portal_id, request.exclude_customer_id
            )

        message = "Portal ID is valid and available"
        if not valid_format:
            message = "Invalid portal ID format"
        elif not available:
            message = "Portal ID is already in use"

        return PortalIDValidationResponse(
            valid_format=valid_format,
            available=available,
            portal_id=request.portal_id,
            message=message,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error validating portal ID: {str(e)}",
        )


@router.post("/migrate", response_model=MigrationResponse)
async def migrate_customers_to_portal_ids(
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin),
):
    """
    Migrate existing customers to use portal ID system.

    This endpoint should be run once when implementing the portal ID system
    to migrate existing customers who don't have proper portal IDs.

    Requires admin authentication.
    """
    try:
        customer_service = CustomerService(db)

        results = customer_service.migrate_existing_customers_to_portal_ids(
            current_admin.id
        )

        success = results["failed_migrations"] == 0
        message = f"Migration completed: {results['successful_migrations']} successful, {results['failed_migrations']} failed"

        return MigrationResponse(
            success=success,
            total_customers=results["total_customers"],
            successful_migrations=results["successful_migrations"],
            failed_migrations=results["failed_migrations"],
            errors=results["errors"],
            message=message,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error during migration: {str(e)}",
        )


@router.get("/config")
async def get_portal_id_config(
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin),
):
    """
    Get current portal ID configuration.

    Requires admin authentication.
    """
    try:
        from app.core.portal_id import PortalIDService

        portal_service = PortalIDService(db)
        config = portal_service.get_portal_config()

        return {
            "success": True,
            "config": config,
            "message": "Portal ID configuration retrieved successfully",
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving configuration: {str(e)}",
        )


@router.get("/config/all")
async def get_all_portal_configs(
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin),
):
    """
    Get all portal configurations.

    Requires admin authentication.
    """
    try:
        from app.core.portal_id import PortalIDService

        portal_service = PortalIDService(db)
        configs = portal_service.get_all_portal_configs()

        return {
            "success": True,
            "configs": configs,
            "count": len(configs),
            "message": "Portal configurations retrieved successfully",
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving configurations: {str(e)}",
        )


@router.post("/config", response_model=PortalConfigResponse)
async def create_portal_config(
    config_data: PortalConfigCreate,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin),
):
    """
    Create new portal configuration.

    Requires admin authentication.
    """
    try:
        from app.core.portal_id import PortalIDService

        portal_service = PortalIDService(db)
        config = portal_service.create_portal_config(config_data.dict())

        return PortalConfigResponse(**config)

    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating configuration: {str(e)}",
        )


@router.put("/config/{config_id}", response_model=PortalConfigResponse)
async def update_portal_config(
    config_id: int,
    update_data: PortalConfigUpdate,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin),
):
    """
    Update portal configuration.

    Requires admin authentication.
    """
    try:
        from app.core.portal_id import PortalIDService

        portal_service = PortalIDService(db)
        config = portal_service.update_portal_config(
            config_id, {k: v for k, v in update_data.dict().items() if v is not None}
        )

        return PortalConfigResponse(**config)

    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating configuration: {str(e)}",
        )


@router.get("/history")
async def get_portal_id_history(
    customer_id: int = None,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin),
):
    """
    Get portal ID change history.

    Requires admin authentication.
    """
    try:
        from app.core.portal_id import PortalIDService

        portal_service = PortalIDService(db)
        history = portal_service.get_portal_id_history(customer_id, limit)

        return {
            "success": True,
            "history": history,
            "count": len(history),
            "message": "Portal ID history retrieved successfully",
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving history: {str(e)}",
        )
