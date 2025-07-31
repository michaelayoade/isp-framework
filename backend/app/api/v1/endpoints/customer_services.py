import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status as http_status
from sqlalchemy.orm import Session

from app.api.v1.dependencies import get_current_admin
from app.core.database import get_db
from app.models.auth import Administrator
from app.schemas.customer_service import (
    CustomerServiceCreate,
    CustomerServiceResponse,
    CustomerServiceSearch,
    CustomerServiceSearchResponse,
    CustomerServicesOverview,
    CustomerServiceUpdate,
    ServicePlanAssignments,
    ServiceProvisioningRequest,
    ServiceProvisioningResponse,
)
from app.services.customer_service import CustomerServiceService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=CustomerServiceSearchResponse)
async def search_customer_services(
    customer_id: Optional[int] = Query(None, description="Filter by customer ID"),
    service_plan_id: Optional[int] = Query(
        None, description="Filter by service plan ID"
    ),
    status: Optional[str] = Query(None, description="Filter by status"),
    service_type: Optional[str] = Query(
        None, description="Filter by service plan type"
    ),
    active_only: bool = Query(True, description="Show only active services"),
    include_expired: bool = Query(False, description="Include expired services"),
    limit: int = Query(50, ge=1, le=100, description="Results per page"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    current_admin: Administrator = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Search customer services with comprehensive filtering."""
    customer_service_service = CustomerServiceService(db)

    try:
        search_params = CustomerServiceSearch(
            customer_id=customer_id,
            service_plan_id=service_plan_id,
            status=status,
            service_type=service_type,
            active_only=active_only,
            include_expired=include_expired,
            limit=limit,
            offset=offset,
        )

        result = customer_service_service.search_customer_services(search_params)
        return CustomerServiceSearchResponse(**result)

    except Exception as e:
        logger.error(f"Error searching customer services: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error searching customer services",
        )


@router.post(
    "/",
    response_model=CustomerServiceResponse,
    status_code=http_status.HTTP_201_CREATED,
)
async def create_customer_service(
    service_data: CustomerServiceCreate,
    current_admin: Administrator = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Create a new customer service assignment."""
    customer_service_service = CustomerServiceService(db)

    try:
        customer_service = customer_service_service.create_customer_service(
            service_data, current_admin.id
        )
        return customer_service

    except ValueError as e:
        logger.warning(f"Validation error creating customer service: {e}")
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating customer service: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating customer service",
        )


@router.get("/{service_id}", response_model=CustomerServiceResponse)
async def get_customer_service(
    service_id: int,
    current_admin: Administrator = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Get a specific customer service assignment by ID."""
    customer_service_service = CustomerServiceService(db)

    try:
        customer_service = customer_service_service.get_customer_service(service_id)
        return customer_service

    except ValueError as e:
        logger.info(f"Customer service not found: {service_id}")
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error retrieving customer service {service_id}: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving customer service",
        )


@router.put("/{service_id}", response_model=CustomerServiceResponse)
async def update_customer_service(
    service_id: int,
    service_data: CustomerServiceUpdate,
    current_admin: Administrator = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Update an existing customer service assignment."""
    customer_service_service = CustomerServiceService(db)

    try:
        customer_service = customer_service_service.update_customer_service(
            service_id, service_data, current_admin.id
        )
        return customer_service

    except ValueError as e:
        logger.info(f"Customer service not found for update: {service_id}")
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating customer service {service_id}: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating customer service",
        )


@router.patch("/{service_id}/activate", response_model=CustomerServiceResponse)
async def activate_customer_service(
    service_id: int,
    current_admin: Administrator = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Activate a customer service."""
    customer_service_service = CustomerServiceService(db)

    try:
        customer_service = customer_service_service.activate_service(
            service_id, current_admin.id
        )
        return customer_service

    except ValueError as e:
        logger.info(f"Customer service not found for activation: {service_id}")
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error activating customer service {service_id}: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error activating customer service",
        )


@router.patch("/{service_id}/suspend", response_model=CustomerServiceResponse)
async def suspend_customer_service(
    service_id: int,
    current_admin: Administrator = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Suspend a customer service."""
    customer_service_service = CustomerServiceService(db)

    try:
        customer_service = customer_service_service.suspend_service(
            service_id, current_admin.id
        )
        return customer_service

    except ValueError as e:
        logger.info(f"Customer service not found for suspension: {service_id}")
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error suspending customer service {service_id}: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error suspending customer service",
        )


@router.patch("/{service_id}/terminate", response_model=CustomerServiceResponse)
async def terminate_customer_service(
    service_id: int,
    current_admin: Administrator = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Terminate a customer service."""
    customer_service_service = CustomerServiceService(db)

    try:
        customer_service = customer_service_service.terminate_service(
            service_id, current_admin.id
        )
        return customer_service

    except ValueError as e:
        logger.info(f"Customer service not found for termination: {service_id}")
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error terminating customer service {service_id}: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error terminating customer service",
        )


@router.post(
    "/provision",
    response_model=ServiceProvisioningResponse,
    status_code=http_status.HTTP_201_CREATED,
)
async def provision_service(
    provision_request: ServiceProvisioningRequest,
    current_admin: Administrator = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Provision a new service for a customer with advanced workflow."""
    customer_service_service = CustomerServiceService(db)

    try:
        result = customer_service_service.provision_service(
            provision_request, current_admin.id
        )
        return ServiceProvisioningResponse(**result)

    except ValueError as e:
        logger.warning(f"Validation error provisioning service: {e}")
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error provisioning service: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error provisioning service",
        )


# Customer-specific endpoints
@router.get("/customer/{customer_id}/overview", response_model=CustomerServicesOverview)
async def get_customer_services_overview(
    customer_id: int,
    current_admin: Administrator = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Get comprehensive overview of all customer's services."""
    customer_service_service = CustomerServiceService(db)

    try:
        overview = customer_service_service.get_customer_services_overview(customer_id)
        return overview

    except ValueError as e:
        logger.info(f"Customer not found: {customer_id}")
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting customer services overview for {customer_id}: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving customer services overview",
        )


@router.get(
    "/customer/{customer_id}/services", response_model=List[CustomerServiceResponse]
)
async def get_customer_services(
    customer_id: int,
    active_only: bool = Query(True, description="Show only active services"),
    current_admin: Administrator = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Get all services for a specific customer."""
    customer_service_service = CustomerServiceService(db)

    try:
        search_params = CustomerServiceSearch(
            customer_id=customer_id,
            active_only=active_only,
            limit=100,  # Higher limit for single customer
        )

        result = customer_service_service.search_customer_services(search_params)
        return result["services"]

    except Exception as e:
        logger.error(f"Error getting customer services for {customer_id}: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving customer services",
        )


# Service plan-specific endpoints
@router.get(
    "/service-plan/{service_plan_id}/assignments", response_model=ServicePlanAssignments
)
async def get_service_plan_assignments(
    service_plan_id: int,
    current_admin: Administrator = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Get all customer assignments for a specific service plan."""
    customer_service_service = CustomerServiceService(db)

    try:
        assignments = customer_service_service.get_service_plan_assignments(
            service_plan_id
        )
        return assignments

    except ValueError as e:
        logger.info(f"Service plan not found: {service_plan_id}")
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(
            f"Error getting service plan assignments for {service_plan_id}: {e}"
        )
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving service plan assignments",
        )


# Analytics and reporting endpoints
@router.get("/analytics/expiring", response_model=List[CustomerServiceResponse])
async def get_expiring_services(
    days_ahead: int = Query(
        30, ge=1, le=365, description="Days ahead to check for expiring services"
    ),
    current_admin: Administrator = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Get services that will expire within specified days."""
    customer_service_service = CustomerServiceService(db)

    try:
        services = customer_service_service.get_expiring_services(days_ahead)
        return services

    except Exception as e:
        logger.error(f"Error getting expiring services: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving expiring services",
        )


@router.get("/analytics/revenue")
async def get_revenue_analytics(
    service_plan_id: Optional[int] = Query(
        None, description="Filter by specific service plan"
    ),
    current_admin: Administrator = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Get revenue analytics by service plan."""
    customer_service_service = CustomerServiceService(db)

    try:
        revenue_data = customer_service_service.get_revenue_analytics(service_plan_id)
        return {
            "revenue_by_service_plan": revenue_data,
            "total_plans": len(revenue_data),
            "total_customers": sum(plan["active_customers"] for plan in revenue_data),
            "total_revenue": sum(plan["total_revenue"] for plan in revenue_data),
        }

    except Exception as e:
        logger.error(f"Error getting revenue analytics: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving revenue analytics",
        )


# Bulk operations
@router.patch("/bulk/status")
async def bulk_update_service_status(
    service_ids: List[int],
    new_status: str,
    current_admin: Administrator = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Update status for multiple customer services."""
    customer_service_service = CustomerServiceService(db)

    try:
        if new_status not in ["active", "suspended", "terminated"]:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="Invalid status. Must be one of: active, suspended, terminated",
            )

        updated_services = customer_service_service.bulk_status_update(
            service_ids, new_status, current_admin.id
        )

        return {
            "message": f"Successfully updated {len(updated_services)} services to {new_status}",
            "updated_services": len(updated_services),
            "service_ids": [s.id for s in updated_services],
        }

    except ValueError as e:
        logger.warning(f"Validation error in bulk status update: {e}")
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error in bulk status update: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating service statuses",
        )
