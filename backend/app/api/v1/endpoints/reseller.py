"""
Reseller Management API Endpoints

REST API endpoints for reseller management in single-tenant ISP Framework.
"""
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.v1.dependencies import get_current_admin
from app.services.reseller import ResellerService
from app.schemas.reseller import (
    ResellerCreate, ResellerUpdate, ResellerResponse, ResellerListResponse,
    ResellerStats, ResellerCommissionReport, ResellerCustomerSummary,
    ResellerDashboard
)
from app.core.exceptions import ValidationError, NotFoundError, DuplicateError
from app.core.security import get_current_reseller
from app.models.foundation.base import Reseller

router = APIRouter(tags=["resellers"])


@router.post("/", response_model=ResellerResponse, status_code=201)
async def create_reseller(
    reseller_data: ResellerCreate,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Create a new reseller"""
    try:
        service = ResellerService(db)
        return service.create_reseller(reseller_data)
    except DuplicateError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=List[ResellerResponse])
async def get_resellers(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    active_only: bool = Query(True),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Get list of resellers with optional search"""
    service = ResellerService(db)
    
    if search:
        return service.search_resellers(search, limit, offset)
    else:
        return service.get_resellers(limit, offset, active_only)


@router.get("/{reseller_id}", response_model=ResellerResponse)
async def get_reseller(
    reseller_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Get reseller by ID"""
    try:
        service = ResellerService(db)
        return service.get_reseller(reseller_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/{reseller_id}", response_model=ResellerResponse)
async def update_reseller(
    reseller_id: int = Path(..., gt=0),
    update_data: ResellerUpdate = ...,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Update reseller information"""
    try:
        service = ResellerService(db)
        return service.update_reseller(reseller_id, update_data)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DuplicateError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{reseller_id}", status_code=204)
async def delete_reseller(
    reseller_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Delete reseller (soft delete by deactivating)"""
    try:
        service = ResellerService(db)
        service.delete_reseller(reseller_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{reseller_id}/stats", response_model=ResellerStats)
async def get_reseller_stats(
    reseller_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Get comprehensive reseller statistics"""
    try:
        service = ResellerService(db)
        return service.get_reseller_stats(reseller_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{reseller_id}/customers", response_model=List[ResellerCustomerSummary])
async def get_reseller_customers(
    reseller_id: int = Path(..., gt=0),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Get customers assigned to a reseller"""
    try:
        service = ResellerService(db)
        return service.get_reseller_customers(reseller_id, limit, offset)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{reseller_id}/commission-report", response_model=ResellerCommissionReport)
async def get_reseller_commission_report(
    reseller_id: int = Path(..., gt=0),
    start_date: datetime = Query(..., description="Start date for commission report"),
    end_date: datetime = Query(..., description="End date for commission report"),
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Generate commission report for reseller"""
    try:
        service = ResellerService(db)
        return service.get_reseller_commission_report(reseller_id, start_date, end_date)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{reseller_id}/dashboard", response_model=ResellerDashboard)
async def get_reseller_dashboard(
    reseller_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Get comprehensive dashboard data for reseller"""
    try:
        service = ResellerService(db)
        return service.get_reseller_dashboard(reseller_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{reseller_id}/assign-customer/{customer_id}", status_code=200)
async def assign_customer_to_reseller(
    reseller_id: int = Path(..., gt=0),
    customer_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Assign a customer to a reseller"""
    try:
        service = ResellerService(db)
        success = service.assign_customer_to_reseller(customer_id, reseller_id)
        return {"success": success, "message": f"Customer {customer_id} assigned to reseller {reseller_id}"}
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/unassign-customer/{customer_id}", status_code=200)
async def unassign_customer_from_reseller(
    customer_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Remove customer assignment from reseller"""
    try:
        service = ResellerService(db)
        success = service.unassign_customer_from_reseller(customer_id)
        return {"success": success, "message": f"Customer {customer_id} unassigned from reseller"}
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{reseller_id}/customer-limit", response_model=dict)
async def check_reseller_customer_limit(
    reseller_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Check reseller customer limit status"""
    try:
        service = ResellerService(db)
        return service.check_customer_limit(reseller_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


# Reseller-specific endpoints (for reseller login access)
@router.get("/me/dashboard", response_model=ResellerDashboard)
async def get_my_dashboard(
    db: Session = Depends(get_db),
    current_reseller: Reseller = Depends(get_current_reseller)
):
    """Get dashboard data for authenticated reseller"""
    try:
        service = ResellerService(db)
        dashboard_data = await service.get_reseller_dashboard(current_reseller.id)
        return dashboard_data
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/me/customers", response_model=List[ResellerCustomerSummary])
async def get_my_customers(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_reseller: Reseller = Depends(get_current_reseller)
):
    """Get customers for authenticated reseller"""
    try:
        service = ResellerService(db)
        customers = await service.get_reseller_customers(
            reseller_id=current_reseller.id,
            limit=limit,
            offset=offset
        )
        return customers
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/me/commission-report", response_model=ResellerCommissionReport)
async def get_my_commission_report(
    start_date: datetime = Query(..., description="Start date for commission report"),
    end_date: datetime = Query(..., description="End date for commission report"),
    db: Session = Depends(get_db),
    current_reseller: Reseller = Depends(get_current_reseller)
):
    """Get commission report for authenticated reseller"""
    try:
        service = ResellerService(db)
        commission_report = await service.get_commission_report(
            reseller_id=current_reseller.id,
            start_date=start_date,
            end_date=end_date
        )
        return commission_report
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
