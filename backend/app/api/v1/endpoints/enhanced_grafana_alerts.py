"""
Enhanced Grafana Alert Integration API Endpoints.

Provides comprehensive alert integration endpoints for Grafana including
alert rule creation, dashboard management, and alert processing.
"""
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.api.dependencies import get_current_admin_user
from app.models.auth.base import Administrator
from app.services.grafana_alert_integration import GrafanaAlertIntegrationService
import structlog

logger = structlog.get_logger("isp.api.enhanced_grafana_alerts")

router = APIRouter()


class AlertProcessingRequest(BaseModel):
    """Request schema for processing system alerts."""
    alert_type: str
    severity: str
    title: str
    message: str
    source: str = "grafana"
    metadata: Dict[str, Any] = {}


@router.post("/create-alert-rules")
async def create_error_handling_alert_rules(
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin_user)
) -> Dict[str, Any]:
    """Create comprehensive error handling alert rules."""
    try:
        alert_service = GrafanaAlertIntegrationService(db)
        result = await alert_service.create_error_handling_alerts()
        
        logger.info(
            "Error handling alert rules created",
            admin_id=current_admin.id,
            rules_created=result.get('alert_rules_created')
        )
        
        return {
            'success': True,
            'message': 'Error handling alert rules created successfully',
            'data': result
        }
        
    except Exception as e:
        logger.error("Failed to create error handling alert rules", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to create error handling alert rules")


@router.post("/create-dashboards")
async def create_operational_dashboards(
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin_user)
) -> Dict[str, Any]:
    """Create comprehensive operational dashboards."""
    try:
        alert_service = GrafanaAlertIntegrationService(db)
        result = await alert_service.create_operational_dashboards()
        
        logger.info(
            "Operational dashboards created",
            admin_id=current_admin.id,
            dashboards_created=result.get('dashboards_created')
        )
        
        return {
            'success': True,
            'message': 'Operational dashboards created successfully',
            'data': result
        }
        
    except Exception as e:
        logger.error("Failed to create operational dashboards", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to create operational dashboards")


@router.post("/process-alert")
async def process_system_alert(
    request: AlertProcessingRequest,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin_user)
) -> Dict[str, Any]:
    """Process incoming system alert and trigger appropriate actions."""
    try:
        alert_service = GrafanaAlertIntegrationService(db)
        
        alert_data = {
            'alert_type': request.alert_type,
            'severity': request.severity,
            'title': request.title,
            'message': request.message,
            'source': request.source,
            'metadata': request.metadata,
            'processed_by': current_admin.id
        }
        
        result = await alert_service.process_system_alert(alert_data)
        
        logger.info(
            "System alert processed",
            admin_id=current_admin.id,
            alert_type=request.alert_type,
            severity=request.severity,
            actions_taken=len(result.get('actions_taken', []))
        )
        
        return {
            'success': True,
            'message': 'System alert processed successfully',
            'data': result
        }
        
    except Exception as e:
        logger.error("Failed to process system alert", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to process system alert")


@router.get("/alert-metrics")
async def get_comprehensive_alert_metrics(
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin_user)
) -> Dict[str, Any]:
    """Get comprehensive alert metrics and statistics."""
    try:
        alert_service = GrafanaAlertIntegrationService(db)
        metrics = await alert_service.get_alert_metrics()
        
        logger.info(
            "Alert metrics retrieved",
            admin_id=current_admin.id,
            system_health_score=metrics.get('system_health', {}).get('health_score')
        )
        
        return {
            'success': True,
            'data': metrics
        }
        
    except Exception as e:
        logger.error("Failed to get alert metrics", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve alert metrics")


@router.get("/alert-effectiveness")
async def get_alert_effectiveness_report(
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin_user)
) -> Dict[str, Any]:
    """Get alert effectiveness and performance report."""
    try:
        alert_service = GrafanaAlertIntegrationService(db)
        metrics = await alert_service.get_alert_metrics()
        
        effectiveness = metrics.get('alert_effectiveness', {})
        
        report = {
            'effectiveness_score': effectiveness.get('alert_accuracy', 0),
            'true_positive_rate': effectiveness.get('true_positive_rate', 0),
            'false_positive_rate': effectiveness.get('false_positive_rate', 0),
            'actionable_alerts_percentage': effectiveness.get('actionable_alerts_percentage', 0),
            'noise_reduction': effectiveness.get('noise_reduction', 0),
            'recommendations': []
        }
        
        # Add recommendations based on metrics
        if effectiveness.get('false_positive_rate', 0) > 10:
            report['recommendations'].append("Consider tuning alert thresholds to reduce false positives")
        
        if effectiveness.get('actionable_alerts_percentage', 0) < 80:
            report['recommendations'].append("Review alert rules to ensure they trigger actionable alerts")
        
        if effectiveness.get('alert_accuracy', 0) < 90:
            report['recommendations'].append("Improve alert rule precision and context")
        
        logger.info(
            "Alert effectiveness report generated",
            admin_id=current_admin.id,
            effectiveness_score=report['effectiveness_score']
        )
        
        return {
            'success': True,
            'data': report
        }
        
    except Exception as e:
        logger.error("Failed to get alert effectiveness report", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve alert effectiveness report")


@router.post("/test-alert-integration")
async def test_alert_integration(
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin_user)
) -> Dict[str, Any]:
    """Test the alert integration system with a sample alert."""
    try:
        alert_service = GrafanaAlertIntegrationService(db)
        
        # Create test alert
        test_alert = {
            'alert_type': 'system',
            'severity': 'medium',
            'title': 'Test Alert Integration',
            'message': 'This is a test alert to verify the integration system is working correctly',
            'source': 'api_test',
            'metadata': {
                'test': True,
                'initiated_by': current_admin.id
            }
        }
        
        result = await alert_service.process_system_alert(test_alert)
        
        logger.info(
            "Alert integration test completed",
            admin_id=current_admin.id,
            test_successful=result.get('success', False)
        )
        
        return {
            'success': True,
            'message': 'Alert integration test completed successfully',
            'data': {
                'test_result': result,
                'integration_status': 'working',
                'test_timestamp': result.get('processed_at')
            }
        }
        
    except Exception as e:
        logger.error("Alert integration test failed", error=str(e))
        raise HTTPException(status_code=500, detail="Alert integration test failed")


@router.get("/system-status")
async def get_alert_system_status(
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin_user)
) -> Dict[str, Any]:
    """Get comprehensive alert system status."""
    try:
        alert_service = GrafanaAlertIntegrationService(db)
        metrics = await alert_service.get_alert_metrics()
        
        # Extract key status indicators
        system_health = metrics.get('system_health', {})
        alert_stats = metrics.get('alert_statistics', {})
        
        status = {
            'overall_status': system_health.get('status', 'unknown'),
            'health_score': system_health.get('health_score', 0),
            'active_alerts': len(system_health.get('alerts', [])),
            'critical_alerts': len([a for a in system_health.get('alerts', []) if a.get('severity') == 'critical']),
            'recent_alerts_24h': alert_stats.get('alerts_24h', 0),
            'resolution_rate': metrics.get('resolution_metrics', {}).get('resolution_rate', 0),
            'components': {
                'dead_letter_queue': system_health.get('components', {}).get('dead_letter_queue', {}),
                'task_execution': system_health.get('components', {}).get('task_execution', {}),
                'customer_services': system_health.get('components', {}).get('customer_services', {})
            },
            'last_updated': metrics.get('timestamp')
        }
        
        logger.info(
            "Alert system status retrieved",
            admin_id=current_admin.id,
            overall_status=status['overall_status'],
            health_score=status['health_score']
        )
        
        return {
            'success': True,
            'data': status
        }
        
    except Exception as e:
        logger.error("Failed to get alert system status", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve alert system status")
