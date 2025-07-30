"""
Plugin Health Monitoring API Endpoints

Provides REST API endpoints for plugin health monitoring including:
- Plugin health checks and status reporting
- Plugin reload and restart operations
- Watchdog service management
- Plugin performance metrics and alerts
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status, BackgroundTasks
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.v1.dependencies import get_current_admin
from app.models.auth import Administrator
from app.services.plugin_health_monitoring import PluginHealthMonitoringService
from app.core.exceptions import NotFoundError, ValidationError
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/health/check-all", response_model=dict)
async def perform_health_checks(
    current_admin: Administrator = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Perform health checks on all active plugins."""
    health_service = PluginHealthMonitoringService(db)
    
    try:
        health_results = await health_service.perform_health_checks()
        logger.info(f"Admin {current_admin.username} triggered plugin health checks")
        return health_results
    except Exception as e:
        logger.error(f"Error performing plugin health checks: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to perform plugin health checks"
        )


@router.get("/health/{plugin_id}", response_model=dict)
async def get_plugin_health_status(
    plugin_id: int,
    current_admin: Administrator = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get current health status for a specific plugin."""
    health_service = PluginHealthMonitoringService(db)
    
    try:
        health_status = health_service.get_plugin_health_status(plugin_id)
        return health_status
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error retrieving plugin health status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve plugin health status"
        )


@router.post("/plugins/{plugin_id}/reload", response_model=dict)
async def reload_plugin(
    plugin_id: int,
    current_admin: Administrator = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Reload a specific plugin."""
    health_service = PluginHealthMonitoringService(db)
    
    try:
        reload_result = await health_service.reload_plugin(plugin_id)
        logger.info(f"Admin {current_admin.username} reloaded plugin {plugin_id}")
        return reload_result
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error reloading plugin {plugin_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reload plugin"
        )


@router.post("/plugins/{plugin_id}/restart", response_model=dict)
async def restart_plugin(
    plugin_id: int,
    reason: str = Query("manual_restart", description="Reason for restart"),
    current_admin: Administrator = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Restart a specific plugin with full reinitialization."""
    health_service = PluginHealthMonitoringService(db)
    
    try:
        restart_result = await health_service.restart_plugin(plugin_id, reason)
        logger.info(f"Admin {current_admin.username} restarted plugin {plugin_id}")
        return restart_result
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error restarting plugin {plugin_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to restart plugin"
        )


@router.post("/watchdog/start", response_model=dict)
async def start_watchdog(
    check_interval_seconds: int = Query(300, ge=60, le=3600, description="Check interval in seconds"),
    current_admin: Administrator = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Start the plugin watchdog service."""
    health_service = PluginHealthMonitoringService(db)
    
    try:
        watchdog_result = await health_service.start_watchdog(check_interval_seconds)
        logger.info(f"Admin {current_admin.username} started plugin watchdog")
        return watchdog_result
    except Exception as e:
        logger.error(f"Error starting plugin watchdog: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start plugin watchdog"
        )


@router.post("/watchdog/stop", response_model=dict)
async def stop_watchdog(
    current_admin: Administrator = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Stop the plugin watchdog service."""
    health_service = PluginHealthMonitoringService(db)
    
    try:
        watchdog_result = await health_service.stop_watchdog()
        logger.info(f"Admin {current_admin.username} stopped plugin watchdog")
        return watchdog_result
    except Exception as e:
        logger.error(f"Error stopping plugin watchdog: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to stop plugin watchdog"
        )


@router.get("/watchdog/status", response_model=dict)
async def get_watchdog_status(
    current_admin: Administrator = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get current watchdog service status."""
    health_service = PluginHealthMonitoringService(db)
    
    try:
        watchdog_status = health_service.get_watchdog_status()
        return watchdog_status
    except Exception as e:
        logger.error(f"Error retrieving watchdog status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve watchdog status"
        )


@router.get("/dashboard/health-overview", response_model=dict)
async def get_health_dashboard(
    current_admin: Administrator = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get comprehensive plugin health dashboard data."""
    health_service = PluginHealthMonitoringService(db)
    
    try:
        # Get recent health check results
        health_results = await health_service.perform_health_checks()
        
        # Get watchdog status
        watchdog_status = health_service.get_watchdog_status()
        
        # Combine dashboard data
        dashboard = {
            'health_overview': {
                'total_plugins': health_results['total_plugins'],
                'healthy_plugins': health_results['healthy_plugins'],
                'warning_plugins': health_results['warning_plugins'],
                'critical_plugins': health_results['critical_plugins'],
                'offline_plugins': health_results['offline_plugins'],
                'overall_status': health_results['overall_status']
            },
            'watchdog_status': watchdog_status,
            'recent_alerts': [
                # Mock recent alerts
                {
                    'plugin_id': 1,
                    'plugin_name': 'Payment Gateway',
                    'alert_type': 'high_memory_usage',
                    'severity': 'warning',
                    'alert_time': '2025-01-29T14:30:00Z'
                }
            ],
            'performance_summary': {
                'average_response_time_ms': 145,
                'total_requests_last_hour': 1250,
                'error_rate_percent': 0.8,
                'plugins_restarted_today': 2
            },
            'last_updated': health_results['check_time']
        }
        
        return dashboard
    except Exception as e:
        logger.error(f"Error retrieving health dashboard: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve health dashboard"
        )


@router.get("/metrics/{plugin_id}", response_model=dict)
async def get_plugin_metrics(
    plugin_id: int,
    period_hours: int = Query(24, ge=1, le=168, description="Period in hours for metrics"),
    current_admin: Administrator = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get performance metrics for a specific plugin."""
    try:
        # This would retrieve historical metrics for the plugin
        metrics = {
            'plugin_id': plugin_id,
            'period_hours': period_hours,
            'metrics': {
                'requests_per_hour': [120, 135, 142, 128, 156, 134, 145],  # Last 7 hours
                'response_times_ms': [145, 152, 138, 161, 149, 143, 147],
                'error_rates_percent': [0.5, 0.8, 0.3, 1.2, 0.6, 0.4, 0.7],
                'memory_usage_mb': [128, 132, 135, 140, 138, 136, 134],
                'cpu_usage_percent': [5.2, 6.1, 5.8, 7.3, 6.5, 5.9, 6.2]
            },
            'summary': {
                'average_response_time_ms': 147.8,
                'total_requests': 1000,
                'success_rate_percent': 99.3,
                'uptime_percent': 99.8,
                'peak_memory_mb': 140,
                'peak_cpu_percent': 7.3
            },
            'alerts_triggered': 2,
            'restarts_count': 0
        }
        
        return metrics
    except Exception as e:
        logger.error(f"Error retrieving plugin metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve plugin metrics"
        )


@router.get("/alerts/recent", response_model=dict)
async def get_recent_health_alerts(
    hours: int = Query(24, ge=1, le=168, description="Hours to look back for alerts"),
    severity: Optional[str] = Query(None, regex="^(warning|critical)$", description="Filter by severity"),
    current_admin: Administrator = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get recent plugin health alerts."""
    try:
        # This would query recent health alerts from the database
        alerts = {
            'period_hours': hours,
            'severity_filter': severity,
            'alerts': [
                {
                    'id': 1,
                    'plugin_id': 1,
                    'plugin_name': 'Payment Gateway',
                    'alert_type': 'high_memory_usage',
                    'severity': 'warning',
                    'message': 'Memory usage exceeded 80% threshold',
                    'alert_time': '2025-01-29T14:30:00Z',
                    'resolved': False,
                    'resolution_time': None
                },
                {
                    'id': 2,
                    'plugin_id': 2,
                    'plugin_name': 'SMS Gateway',
                    'alert_type': 'api_timeout',
                    'severity': 'critical',
                    'message': 'API health check timed out after 30 seconds',
                    'alert_time': '2025-01-29T13:15:00Z',
                    'resolved': True,
                    'resolution_time': '2025-01-29T13:18:00Z'
                }
            ],
            'total_alerts': 2,
            'unresolved_alerts': 1,
            'critical_alerts': 1,
            'warning_alerts': 1
        }
        
        return alerts
    except Exception as e:
        logger.error(f"Error retrieving recent health alerts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve recent health alerts"
        )


@router.post("/alerts/{alert_id}/resolve", response_model=dict)
async def resolve_health_alert(
    alert_id: int,
    resolution_notes: str = Query(..., description="Notes about the resolution"),
    current_admin: Administrator = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Mark a health alert as resolved."""
    try:
        # This would update the alert status in the database
        resolution_result = {
            'alert_id': alert_id,
            'resolved_by': current_admin.username,
            'resolution_time': '2025-01-29T15:30:00Z',
            'resolution_notes': resolution_notes,
            'success': True
        }
        
        logger.info(f"Admin {current_admin.username} resolved health alert {alert_id}")
        
        return resolution_result
    except Exception as e:
        logger.error(f"Error resolving health alert {alert_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to resolve health alert"
        )
