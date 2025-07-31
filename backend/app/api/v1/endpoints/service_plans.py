import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.v1.dependencies import get_current_admin
from app.core.database import get_db
from app.models.auth import Administrator
from app.schemas.service_plan import ServicePlan, ServicePlanCreate, ServicePlanUpdate
from app.services.service_plan import ServicePlanService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=list[ServicePlan])
async def list_service_plans(
    service_type: Optional[str] = Query(None, description="Filter by service type"),
    active_only: bool = Query(True, description="Show only active plans"),
    current_admin: Administrator = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """List service plans with optional filtering."""
    service_plan_service = ServicePlanService(db)

    try:
        plans = service_plan_service.list_service_plans(
            service_type=service_type, active_only=active_only
        )
        return plans
    except Exception as e:
        logger.error(f"Error listing service plans: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving service plans",
        )


@router.post("/", response_model=ServicePlan, status_code=status.HTTP_201_CREATED)
async def create_service_plan(
    plan_data: ServicePlanCreate,
    current_admin: Administrator = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Create a new service plan."""
    service_plan_service = ServicePlanService(db)

    try:
        plan = service_plan_service.create_service_plan(plan_data)
        logger.info(f"Admin {current_admin.username} created service plan {plan.id}")
        return plan
    except Exception as e:
        logger.error(f"Error creating service plan: {e}")
        if "already exists" in str(e):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
        elif "Invalid" in str(e):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{plan_id}", response_model=ServicePlan)
async def get_service_plan(
    plan_id: int,
    current_admin: Administrator = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Get a specific service plan by ID."""
    service_plan_service = ServicePlanService(db)

    try:
        plan = service_plan_service.get_service_plan(plan_id)
        return plan
    except Exception as e:
        logger.error(f"Error getting service plan {plan_id}: {e}")
        if "not found" in str(e):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving service plan",
        )


@router.put("/{plan_id}", response_model=ServicePlan)
async def update_service_plan(
    plan_id: int,
    plan_data: ServicePlanUpdate,
    current_admin: Administrator = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Update an existing service plan."""
    service_plan_service = ServicePlanService(db)

    try:
        plan = service_plan_service.update_service_plan(plan_id, plan_data)
        logger.info(f"Admin {current_admin.username} updated service plan {plan_id}")
        return plan
    except Exception as e:
        logger.error(f"Error updating service plan {plan_id}: {e}")
        if "not found" in str(e):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        elif "already exists" in str(e):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
        elif "Invalid" in str(e):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_service_plan(
    plan_id: int,
    current_admin: Administrator = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Delete a service plan."""
    service_plan_service = ServicePlanService(db)

    try:
        service_plan_service.delete_service_plan(plan_id)
        logger.info(f"Admin {current_admin.username} deleted service plan {plan_id}")
        return None
    except Exception as e:
        logger.error(f"Error deleting service plan {plan_id}: {e}")
        if "not found" in str(e):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting service plan",
        )


@router.patch("/{plan_id}/activate", response_model=ServicePlan)
async def activate_service_plan(
    plan_id: int,
    current_admin: Administrator = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Activate a service plan."""
    service_plan_service = ServicePlanService(db)

    try:
        plan = service_plan_service.activate_service_plan(plan_id)
        logger.info(f"Admin {current_admin.username} activated service plan {plan_id}")
        return plan
    except Exception as e:
        logger.error(f"Error activating service plan {plan_id}: {e}")
        if "not found" in str(e):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error activating service plan",
        )


@router.patch("/{plan_id}/deactivate", response_model=ServicePlan)
async def deactivate_service_plan(
    plan_id: int,
    current_admin: Administrator = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Deactivate a service plan."""
    service_plan_service = ServicePlanService(db)

    try:
        plan = service_plan_service.deactivate_service_plan(plan_id)
        logger.info(
            f"Admin {current_admin.username} deactivated service plan {plan_id}"
        )
        return plan
    except Exception as e:
        logger.error(f"Error deactivating service plan {plan_id}: {e}")
        if "not found" in str(e):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deactivating service plan",
        )


# Specialized endpoints for different service types
@router.get("/internet/", response_model=list[ServicePlan])
async def list_internet_plans(
    active_only: bool = Query(True, description="Show only active plans"),
    current_admin: Administrator = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """List internet service plans."""
    service_plan_service = ServicePlanService(db)

    try:
        plans = service_plan_service.get_internet_plans(active_only)
        return plans
    except Exception as e:
        logger.error(f"Error listing internet plans: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving internet plans",
        )


@router.get("/voice/", response_model=list[ServicePlan])
async def list_voice_plans(
    active_only: bool = Query(True, description="Show only active plans"),
    current_admin: Administrator = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """List voice service plans."""
    service_plan_service = ServicePlanService(db)

    try:
        plans = service_plan_service.get_voice_plans(active_only)
        return plans
    except Exception as e:
        logger.error(f"Error listing voice plans: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving voice plans",
        )


@router.get("/bundle/", response_model=list[ServicePlan])
async def list_bundle_plans(
    active_only: bool = Query(True, description="Show only active plans"),
    current_admin: Administrator = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """List bundle service plans."""
    service_plan_service = ServicePlanService(db)

    try:
        plans = service_plan_service.get_bundle_plans(active_only)
        return plans
    except Exception as e:
        logger.error(f"Error listing bundle plans: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving bundle plans",
        )
