"""Dashboard API endpoints for dynamic metrics and KPI reporting."""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.dependencies import get_current_admin_user
from app.core.permissions import require_permission
from app.models.auth.base import Administrator
from app.services.dashboard_service import DashboardService
from app.schemas.dashboard import (
    KPIResponse,
    MetricResponse,
    FinancialReportResponse,
    NetworkReportResponse,
    DashboardWidgetResponse
)

router = APIRouter()


@router.get("/kpis", response_model=dict)
@require_permission("dashboard.view")
async def get_dashboard_kpis(
    categories: Optional[List[str]] = Query(None, description="Filter by metric categories"),
    metrics: Optional[List[str]] = Query(None, description="Specific metric keys to retrieve"),
    period: str = Query("month", description="Time period: day, week, month, quarter, year"),
    start_date: Optional[datetime] = Query(None, description="Custom start date"),
    end_date: Optional[datetime] = Query(None, description="Custom end date"),
    segments: Optional[List[str]] = Query(None, description="Apply segmentation filters"),
    db: Session = Depends(get_db),
    current_user: Administrator = Depends(get_current_admin_user)
):
    """
    Get dashboard KPIs with flexible filtering and segmentation.
    
    This endpoint dynamically calculates metrics based on database configuration,
    allowing new metrics to be added without code changes.
    """
    # Validate period parameter
    valid_periods = ["day", "week", "month", "quarter", "year"]
    if period not in valid_periods:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid period '{period}'. Must be one of: {', '.join(valid_periods)}"
        )
    
    try:
        dashboard_service = DashboardService(db)
        
        # Get user roles for RBAC filtering
        user_roles = ["admin"] if current_user.is_superuser else ["manager"]  # Simplified role mapping
        
        result = dashboard_service.get_kpis(
            categories=categories,
            metrics=metrics,
            period=period,
            start_date=start_date,
            end_date=end_date,
            segments=segments,
            tenant_scope="reseller",  # TODO: Get from user context
            user_roles=user_roles
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate KPIs: {str(e)}")


@router.get("/metrics/{metric_key}", response_model=dict)
@require_permission("dashboard.view")
async def get_single_metric(
    metric_key: str,
    period: str = Query("month", description="Time period: day, week, month, quarter, year"),
    start_date: Optional[datetime] = Query(None, description="Custom start date"),
    end_date: Optional[datetime] = Query(None, description="Custom end date"),
    db: Session = Depends(get_db),
    current_user: Administrator = Depends(get_current_admin_user)
):
    """
    Get a single metric by key with detailed calculation information.
    """
    try:
        dashboard_service = DashboardService(db)
        
        # Get metric definition
        user_roles = ["admin"] if current_user.is_superuser else ["manager"]
        metric_configs = dashboard_service.get_metric_definitions(
            metric_keys=[metric_key],
            tenant_scope="reseller",
            user_roles=user_roles
        )
        
        if not metric_configs:
            raise HTTPException(status_code=404, detail=f"Metric '{metric_key}' not found or not accessible")
        
        config = metric_configs[0]
        result = dashboard_service.calculate_metric(
            config=config,
            period=period,
            start_date=start_date,
            end_date=end_date
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate metric: {str(e)}")


@router.get("/reports/financial", response_model=dict)
@require_permission("dashboard.financial")
async def get_financial_report(
    period: str = Query("month", description="Time period: day, week, month, quarter, year"),
    start_date: Optional[datetime] = Query(None, description="Custom start date"),
    end_date: Optional[datetime] = Query(None, description="Custom end date"),
    breakdown_by: Optional[str] = Query(None, description="Breakdown dimension: plan, region, customer_type"),
    db: Session = Depends(get_db),
    current_user: Administrator = Depends(get_current_admin_user)
):
    """
    Generate comprehensive financial report with optional breakdowns.
    """
    try:
        dashboard_service = DashboardService(db)
        
        result = dashboard_service.get_financial_report(
            period=period,
            start_date=start_date,
            end_date=end_date,
            breakdown_by=breakdown_by
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate financial report: {str(e)}")


@router.get("/reports/network", response_model=dict)
@require_permission("dashboard.network")
async def get_network_report(
    period: str = Query("month", description="Time period: day, week, month, quarter, year"),
    start_date: Optional[datetime] = Query(None, description="Custom start date"),
    end_date: Optional[datetime] = Query(None, description="Custom end date"),
    db: Session = Depends(get_db),
    current_user: Administrator = Depends(get_current_admin_user)
):
    """
    Generate network performance report with key metrics.
    """
    try:
        dashboard_service = DashboardService(db)
        
        result = dashboard_service.get_network_report(
            period=period,
            start_date=start_date,
            end_date=end_date
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate network report: {str(e)}")


@router.get("/reports/customer", response_model=dict)
@require_permission("dashboard.view")
async def get_customer_report(
    period: str = Query("month", description="Time period: day, week, month, quarter, year"),
    start_date: Optional[datetime] = Query(None, description="Custom start date"),
    end_date: Optional[datetime] = Query(None, description="Custom end date"),
    db: Session = Depends(get_db),
    current_user: Administrator = Depends(get_current_admin_user)
):
    """
    Generate customer metrics report.
    """
    try:
        dashboard_service = DashboardService(db)
        
        # Get customer metrics
        user_roles = ["admin"] if current_user.is_superuser else ["manager"]
        result = dashboard_service.get_kpis(
            categories=["customer"],
            period=period,
            start_date=start_date,
            end_date=end_date,
            tenant_scope="reseller",
            user_roles=user_roles
        )
        
        return {
            "report_type": "customer",
            "summary": result["kpis"],
            "period": period,
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate customer report: {str(e)}")


@router.get("/reports/operational", response_model=dict)
@require_permission("dashboard.view")
async def get_operational_report(
    period: str = Query("month", description="Time period: day, week, month, quarter, year"),
    start_date: Optional[datetime] = Query(None, description="Custom start date"),
    end_date: Optional[datetime] = Query(None, description="Custom end date"),
    db: Session = Depends(get_db),
    current_user: Administrator = Depends(get_current_admin_user)
):
    """
    Generate operational metrics report.
    """
    try:
        dashboard_service = DashboardService(db)
        
        # Get operational metrics
        user_roles = ["admin"] if current_user.is_superuser else ["manager"]
        result = dashboard_service.get_kpis(
            categories=["operational"],
            period=period,
            start_date=start_date,
            end_date=end_date,
            tenant_scope="reseller",
            user_roles=user_roles
        )
        
        return {
            "report_type": "operational",
            "summary": result["kpis"],
            "period": period,
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate operational report: {str(e)}")


@router.get("/widgets", response_model=List[dict])
@require_permission("dashboard.view")
async def get_dashboard_widgets(
    categories: Optional[List[str]] = Query(None, description="Filter by widget categories"),
    db: Session = Depends(get_db),
    current_user: Administrator = Depends(get_current_admin_user)
):
    """
    Get dashboard widget configurations for UI rendering.
    """
    try:
        dashboard_service = DashboardService(db)
        
        user_roles = ["admin"] if current_user.is_superuser else ["manager"]
        widgets = dashboard_service.get_dashboard_widgets(
            categories=categories,
            user_roles=user_roles,
            tenant_scope="reseller"
        )
        
        # Convert to dict format for JSON response
        result = []
        for widget in widgets:
            widget_data = {
                "widget_key": widget.widget_key,
                "title": widget.title,
                "description": widget.description,
                "category": widget.category,
                "widget_type": widget.widget_type,
                "chart_type": widget.chart_type,
                "metrics": widget.metrics,
                "display_config": widget.display_config,
                "position": widget.position,
                "refresh_interval_seconds": widget.refresh_interval_seconds,
                "auto_refresh": widget.auto_refresh
            }
            result.append(widget_data)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard widgets: {str(e)}")


@router.get("/metrics", response_model=List[dict])
@require_permission("dashboard.view")
async def get_available_metrics(
    categories: Optional[List[str]] = Query(None, description="Filter by metric categories"),
    db: Session = Depends(get_db),
    current_user: Administrator = Depends(get_current_admin_user)
):
    """
    Get list of available metrics with their definitions.
    """
    try:
        dashboard_service = DashboardService(db)
        
        user_roles = ["admin"] if current_user.is_superuser else ["manager"]
        metrics = dashboard_service.get_metric_definitions(
            categories=categories,
            tenant_scope="reseller",
            user_roles=user_roles
        )
        
        # Convert to dict format for JSON response
        result = []
        for metric in metrics:
            metric_data = {
                "metric_key": metric.metric_key,
                "metric_name": metric.metric_name,
                "description": metric.description,
                "category": metric.category,
                "calculation_method": metric.calculation_method,
                "display_format": metric.display_format,
                "unit": metric.unit,
                "is_real_time": metric.is_real_time,
                "cache_ttl_seconds": metric.cache_ttl_seconds
            }
            result.append(metric_data)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get available metrics: {str(e)}")


@router.get("/segments", response_model=List[dict])
@require_permission("dashboard.view")
async def get_available_segments(
    segment_types: Optional[List[str]] = Query(None, description="Filter by segment types"),
    db: Session = Depends(get_db),
    current_user: Administrator = Depends(get_current_admin_user)
):
    """
    Get list of available segments for filtering.
    """
    try:
        from app.models.dashboard import SegmentDefinition
        
        query = db.query(SegmentDefinition).filter(SegmentDefinition.is_active == True)
        
        if segment_types:
            query = query.filter(SegmentDefinition.segment_type.in_(segment_types))
        
        segments = query.all()
        
        # Convert to dict format for JSON response
        result = []
        for segment in segments:
            segment_data = {
                "segment_key": segment.segment_key,
                "segment_name": segment.segment_name,
                "description": segment.description,
                "segment_type": segment.segment_type,
                "criteria": segment.criteria
            }
            result.append(segment_data)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get available segments: {str(e)}")


@router.post("/cache/clear")
@require_permission("dashboard.admin")
async def clear_dashboard_cache(
    db: Session = Depends(get_db),
    current_user: Administrator = Depends(get_current_admin_user)
):
    """
    Clear dashboard metrics cache (admin only).
    """
    try:
        dashboard_service = DashboardService(db)
        dashboard_service.clear_cache()
        
        return {
            "message": "Dashboard cache cleared successfully",
            "cleared_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")


@router.get("/cache/stats")
@require_permission("dashboard.admin")
async def get_cache_stats(
    db: Session = Depends(get_db),
    current_user: Administrator = Depends(get_current_admin_user)
):
    """
    Get dashboard cache statistics (admin only).
    """
    try:
        dashboard_service = DashboardService(db)
        stats = dashboard_service.get_cache_stats()
        
        return {
            "cache_stats": stats,
            "retrieved_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get cache stats: {str(e)}")
