"""
Payment Dashboard Endpoints

FastAPI endpoints for payment system analytics and reporting.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ....core.database import get_db
from ....core.rbac_decorators import require_permission
from ....services.payment_dashboard_service import PaymentDashboardService


logger = logging.getLogger(__name__)
router = APIRouter()


def get_payment_dashboard_service(db: Session = Depends(get_db)) -> PaymentDashboardService:
    """Get payment dashboard service instance."""
    return PaymentDashboardService(db)


@router.get("/overview")
@require_permission("billing.view")
async def get_payment_overview(
    start_date: Optional[datetime] = Query(None, description="Start date for filtering"),
    end_date: Optional[datetime] = Query(None, description="End date for filtering"),
    tenant_id: Optional[int] = Query(None, description="Tenant ID for scoping"),
    service: PaymentDashboardService = Depends(get_payment_dashboard_service)
):
    """
    Get comprehensive payment system overview.
    
    Requires: billing.view permission
    """
    try:
        overview = service.get_payment_overview(start_date, end_date, tenant_id)
        return overview
    except Exception as e:
        logger.error(f"Error getting payment overview: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/bank-accounts/metrics")
@require_permission("billing.view")
async def get_bank_account_metrics(
    service: PaymentDashboardService = Depends(get_payment_dashboard_service)
):
    """
    Get bank account metrics.
    
    Requires: billing.view permission
    """
    try:
        metrics = service.get_bank_account_metrics()
        return metrics
    except Exception as e:
        logger.error(f"Error getting bank account metrics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/payments/metrics")
@require_permission("billing.view")
async def get_payment_metrics(
    start_date: Optional[datetime] = Query(None, description="Start date for filtering"),
    end_date: Optional[datetime] = Query(None, description="End date for filtering"),
    tenant_id: Optional[int] = Query(None, description="Tenant ID for scoping"),
    service: PaymentDashboardService = Depends(get_payment_dashboard_service)
):
    """
    Get payment transaction metrics.
    
    Requires: billing.view permission
    """
    try:
        if not start_date:
            start_date = datetime.now(timezone.utc) - timedelta(days=30)
        if not end_date:
            end_date = datetime.now(timezone.utc)
        
        metrics = service.get_payment_metrics(start_date, end_date, tenant_id)
        return metrics
    except Exception as e:
        logger.error(f"Error getting payment metrics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/gateways/metrics")
@require_permission("billing.view")
async def get_gateway_metrics(
    start_date: Optional[datetime] = Query(None, description="Start date for filtering"),
    end_date: Optional[datetime] = Query(None, description="End date for filtering"),
    tenant_id: Optional[int] = Query(None, description="Tenant ID for scoping"),
    service: PaymentDashboardService = Depends(get_payment_dashboard_service)
):
    """
    Get payment gateway metrics.
    
    Requires: billing.view permission
    """
    try:
        if not start_date:
            start_date = datetime.now(timezone.utc) - timedelta(days=30)
        if not end_date:
            end_date = datetime.now(timezone.utc)
        
        metrics = service.get_gateway_metrics(start_date, end_date, tenant_id)
        return metrics
    except Exception as e:
        logger.error(f"Error getting gateway metrics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/trends")
@require_permission("billing.view")
async def get_payment_trends(
    start_date: Optional[datetime] = Query(None, description="Start date for filtering"),
    end_date: Optional[datetime] = Query(None, description="End date for filtering"),
    tenant_id: Optional[int] = Query(None, description="Tenant ID for scoping"),
    service: PaymentDashboardService = Depends(get_payment_dashboard_service)
):
    """
    Get payment trends over time.
    
    Requires: billing.view permission
    """
    try:
        if not start_date:
            start_date = datetime.now(timezone.utc) - timedelta(days=30)
        if not end_date:
            end_date = datetime.now(timezone.utc)
        
        trends = service.get_payment_trends(start_date, end_date, tenant_id)
        return trends
    except Exception as e:
        logger.error(f"Error getting payment trends: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/alerts")
@require_permission("billing.view")
async def get_payment_alerts(
    service: PaymentDashboardService = Depends(get_payment_dashboard_service)
):
    """
    Get payment system alerts.
    
    Requires: billing.view permission
    """
    try:
        alerts = service.get_payment_alerts()
        return {"alerts": alerts, "count": len(alerts)}
    except Exception as e:
        logger.error(f"Error getting payment alerts: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/reports/analytics")
@require_permission("billing.view")
async def get_analytics_report(
    start_date: Optional[datetime] = Query(None, description="Start date for filtering"),
    end_date: Optional[datetime] = Query(None, description="End date for filtering"),
    tenant_id: Optional[int] = Query(None, description="Tenant ID for scoping"),
    service: PaymentDashboardService = Depends(get_payment_dashboard_service)
):
    """
    Generate comprehensive analytics report.
    
    Requires: billing.view permission
    """
    try:
        if not start_date:
            start_date = datetime.now(timezone.utc) - timedelta(days=30)
        if not end_date:
            end_date = datetime.now(timezone.utc)
        
        report = service.get_analytics_report(start_date, end_date, tenant_id)
        return report
    except Exception as e:
        logger.error(f"Error generating analytics report: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/recommendations")
@require_permission("billing.view")
async def get_recommendations(
    start_date: Optional[datetime] = Query(None, description="Start date for filtering"),
    end_date: Optional[datetime] = Query(None, description="End date for filtering"),
    tenant_id: Optional[int] = Query(None, description="Tenant ID for scoping"),
    service: PaymentDashboardService = Depends(get_payment_dashboard_service)
):
    """
    Get payment system recommendations.
    
    Requires: billing.view permission
    """
    try:
        if not start_date:
            start_date = datetime.now(timezone.utc) - timedelta(days=30)
        if not end_date:
            end_date = datetime.now(timezone.utc)
        
        overview = service.get_payment_overview(start_date, end_date, tenant_id)
        recommendations = service.get_recommendations(overview)
        return {"recommendations": recommendations, "count": len(recommendations)}
    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Individual KPI endpoints for dashboard integration
@router.get("/kpis/payment-success-rate")
@require_permission("billing.view")
async def get_payment_success_rate_kpi(
    start_date: Optional[datetime] = Query(None, description="Start date for filtering"),
    end_date: Optional[datetime] = Query(None, description="End date for filtering"),
    tenant_id: Optional[int] = Query(None, description="Tenant ID for scoping"),
    service: PaymentDashboardService = Depends(get_payment_dashboard_service)
):
    """
    Get payment success rate KPI.
    
    Requires: billing.view permission
    """
    try:
        if not start_date:
            start_date = datetime.now(timezone.utc) - timedelta(days=30)
        if not end_date:
            end_date = datetime.now(timezone.utc)
        
        metrics = service.get_payment_metrics(start_date, end_date, tenant_id)
        return {
            "key": "payment_success_rate",
            "value": metrics["success_rate"],
            "unit": "percentage",
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            }
        }
    except Exception as e:
        logger.error(f"Error getting payment success rate KPI: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/kpis/total-payment-amount")
@require_permission("billing.view")
async def get_total_payment_amount_kpi(
    start_date: Optional[datetime] = Query(None, description="Start date for filtering"),
    end_date: Optional[datetime] = Query(None, description="End date for filtering"),
    tenant_id: Optional[int] = Query(None, description="Tenant ID for scoping"),
    service: PaymentDashboardService = Depends(get_payment_dashboard_service)
):
    """
    Get total payment amount KPI.
    
    Requires: billing.view permission
    """
    try:
        if not start_date:
            start_date = datetime.now(timezone.utc) - timedelta(days=30)
        if not end_date:
            end_date = datetime.now(timezone.utc)
        
        metrics = service.get_payment_metrics(start_date, end_date, tenant_id)
        return {
            "key": "total_payment_amount",
            "value": metrics["total_amount"],
            "unit": "currency",
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            }
        }
    except Exception as e:
        logger.error(f"Error getting total payment amount KPI: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/kpis/bank-account-verification-rate")
@require_permission("billing.view")
async def get_bank_account_verification_rate_kpi(
    service: PaymentDashboardService = Depends(get_payment_dashboard_service)
):
    """
    Get bank account verification rate KPI.
    
    Requires: billing.view permission
    """
    try:
        metrics = service.get_bank_account_metrics()
        return {
            "key": "bank_account_verification_rate",
            "value": metrics["verification_rate"],
            "unit": "percentage",
            "period": {
                "start_date": None,
                "end_date": None
            }
        }
    except Exception as e:
        logger.error(f"Error getting bank account verification rate KPI: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
