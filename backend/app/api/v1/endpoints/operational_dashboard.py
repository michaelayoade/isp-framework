"""
Operational Dashboard API Endpoints.

Provides comprehensive operational metrics, health monitoring, and dashboard data
for ISP Framework operations including error handling and system health.
"""

from typing import Any, Dict

import structlog
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_admin_user
from app.core.database import get_db
from app.models.auth.base import Administrator
from app.services.operational_dashboard import OperationalDashboardService

logger = structlog.get_logger("isp.api.operational_dashboard")

router = APIRouter()


@router.get("/health-overview")
async def get_system_health_overview(
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin_user),
) -> Dict[str, Any]:
    """Get comprehensive system health overview."""
    try:
        dashboard_service = OperationalDashboardService(db)
        health_overview = await dashboard_service.get_system_health_overview()

        logger.info(
            "System health overview retrieved",
            admin_id=current_admin.id,
            health_score=health_overview.get("health_score"),
            status=health_overview.get("status"),
        )

        return {"success": True, "data": health_overview}

    except Exception as e:
        logger.error("Failed to get system health overview", error=str(e))
        raise HTTPException(
            status_code=500, detail="Failed to retrieve system health overview"
        )


@router.get("/error-metrics")
async def get_error_metrics_dashboard(
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin_user),
) -> Dict[str, Any]:
    """Get comprehensive error metrics and trends."""
    try:
        dashboard_service = OperationalDashboardService(db)
        error_metrics = await dashboard_service.get_error_metrics_dashboard()

        logger.info(
            "Error metrics dashboard retrieved",
            admin_id=current_admin.id,
            total_errors_24h=error_metrics.get("summary", {}).get("total_errors_24h"),
            total_errors_7d=error_metrics.get("summary", {}).get("total_errors_7d"),
        )

        return {"success": True, "data": error_metrics}

    except Exception as e:
        logger.error("Failed to get error metrics dashboard", error=str(e))
        raise HTTPException(
            status_code=500, detail="Failed to retrieve error metrics dashboard"
        )


@router.get("/operational-kpis")
async def get_operational_kpis(
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin_user),
) -> Dict[str, Any]:
    """Get key operational performance indicators."""
    try:
        dashboard_service = OperationalDashboardService(db)
        kpis = await dashboard_service.get_operational_kpis()

        logger.info(
            "Operational KPIs retrieved",
            admin_id=current_admin.id,
            availability_24h=kpis.get("availability", {}).get("availability_24h"),
            availability_7d=kpis.get("availability", {}).get("availability_7d"),
        )

        return {"success": True, "data": kpis}

    except Exception as e:
        logger.error("Failed to get operational KPIs", error=str(e))
        raise HTTPException(
            status_code=500, detail="Failed to retrieve operational KPIs"
        )


@router.get("/complete-dashboard")
async def get_complete_operational_dashboard(
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin_user),
) -> Dict[str, Any]:
    """Get complete operational dashboard with all metrics."""
    try:
        dashboard_service = OperationalDashboardService(db)

        # Get all dashboard components
        health_overview = await dashboard_service.get_system_health_overview()
        error_metrics = await dashboard_service.get_error_metrics_dashboard()
        kpis = await dashboard_service.get_operational_kpis()

        complete_dashboard = {
            "health_overview": health_overview,
            "error_metrics": error_metrics,
            "operational_kpis": kpis,
            "generated_at": health_overview.get("timestamp"),
        }

        logger.info(
            "Complete operational dashboard retrieved",
            admin_id=current_admin.id,
            overall_health_score=health_overview.get("health_score"),
            total_errors_24h=error_metrics.get("summary", {}).get("total_errors_24h"),
        )

        return {"success": True, "data": complete_dashboard}

    except Exception as e:
        logger.error("Failed to get complete operational dashboard", error=str(e))
        raise HTTPException(
            status_code=500, detail="Failed to retrieve complete operational dashboard"
        )


@router.get("/alerts/active")
async def get_active_system_alerts(
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin_user),
) -> Dict[str, Any]:
    """Get currently active system alerts."""
    try:
        dashboard_service = OperationalDashboardService(db)
        alerts = await dashboard_service._get_active_alerts()

        logger.info(
            "Active system alerts retrieved",
            admin_id=current_admin.id,
            alert_count=len(alerts),
        )

        return {
            "success": True,
            "data": {
                "alerts": alerts,
                "count": len(alerts),
                "has_critical": any(
                    alert.get("severity") == "critical" for alert in alerts
                ),
                "has_high": any(alert.get("severity") == "high" for alert in alerts),
            },
        }

    except Exception as e:
        logger.error("Failed to get active system alerts", error=str(e))
        raise HTTPException(
            status_code=500, detail="Failed to retrieve active system alerts"
        )


@router.get("/health-check", include_in_schema=False)
async def health_check_endpoint(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Simple health check endpoint for monitoring systems."""
    try:
        dashboard_service = OperationalDashboardService(db)

        # Get basic health metrics
        dlq_health = await dashboard_service._get_dead_letter_queue_health()

        # Determine overall status
        if dlq_health.get("health_score", 0) >= 90:
            status = "healthy"
            http_status = 200
        elif dlq_health.get("health_score", 0) >= 70:
            status = "degraded"
            http_status = 200
        else:
            status = "unhealthy"
            http_status = 503

        response = {
            "status": status,
            "health_score": dlq_health.get("health_score", 0),
            "timestamp": dlq_health.get("timestamp"),
            "components": {"dead_letter_queue": dlq_health.get("status", "unknown")},
        }

        if http_status == 503:
            raise HTTPException(status_code=503, detail=response)

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        raise HTTPException(
            status_code=503,
            detail={
                "status": "unhealthy",
                "error": "Health check failed",
                "timestamp": None,
            },
        )


# ============================================================================
# Backward Compatibility Redirects (Temporary - Remove after 6 months)
# ============================================================================

from fastapi.responses import RedirectResponse


# Redirect old /dashboard/* paths to new /monitoring/dashboard/* paths
@router.get("/{path:path}")
async def redirect_old_dashboard_get(path: str):
    """Temporary redirect for old /dashboard/* paths"""
    new_path = f"/api/v1/monitoring/dashboard/{path}"
    return RedirectResponse(url=new_path, status_code=307)


@router.post("/{path:path}")
async def redirect_old_dashboard_post(path: str):
    """Temporary redirect for old /dashboard/* paths"""
    new_path = f"/api/v1/monitoring/dashboard/{path}"
    return RedirectResponse(url=new_path, status_code=307)


@router.put("/{path:path}")
async def redirect_old_dashboard_put(path: str):
    """Temporary redirect for old /dashboard/* paths"""
    new_path = f"/api/v1/monitoring/dashboard/{path}"
    return RedirectResponse(url=new_path, status_code=307)


@router.delete("/{path:path}")
async def redirect_old_dashboard_delete(path: str):
    """Temporary redirect for old /dashboard/* paths"""
    new_path = f"/api/v1/monitoring/dashboard/{path}"
    return RedirectResponse(url=new_path, status_code=307)
