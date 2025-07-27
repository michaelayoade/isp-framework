"""
Consolidated Alert Management API Endpoints.

Unified alerting system combining Grafana webhooks, alert rule management,
dashboard creation, and alert processing into a single cohesive API.
"""
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Header, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
import structlog

from app.core.database import get_db
from app.api.dependencies import get_current_admin_user
from app.models.auth.base import Administrator
from app.services.communications_service import CommunicationService
from app.services.grafana_alert_integration import GrafanaAlertIntegrationService
from app.core.config import settings

router = APIRouter()
logger = structlog.get_logger("isp.api.alerts")


# ============================================================================
# Schemas
# ============================================================================

class GrafanaAlert(BaseModel):
    """Individual Grafana alert structure."""
    summary: str
    description: str
    runbook_url: str = ""
    labels: Dict[str, str]
    starts_at: str
    ends_at: str = ""
    generator_url: str = ""


class GrafanaAlertPayload(BaseModel):
    """Grafana alert webhook payload structure."""
    alert_name: str
    severity: str
    service: str
    category: str = "system"
    status: str
    alerts_firing: int
    alerts_resolved: int
    alerts: List[GrafanaAlert]


class AlertProcessingRequest(BaseModel):
    """Request schema for processing system alerts."""
    alert_type: str
    severity: str
    title: str
    message: str
    source: str = "grafana"
    metadata: Dict[str, Any] = {}


class AlertRuleRequest(BaseModel):
    """Request schema for creating alert rules."""
    name: str
    description: str
    severity: str
    conditions: Dict[str, Any]
    notifications: List[str]


# ============================================================================
# Webhook Endpoints (from grafana_alerts.py)
# ============================================================================

@router.post("/webhooks/grafana")
async def receive_grafana_webhook(
    request: Request,
    db: Session = Depends(get_db),
    x_alert_source: str = Header(None, alias="X-Alert-Source"),
    x_alert_type: str = Header(None, alias="X-Alert-Type")
):
    """
    Handle incoming Grafana alert webhooks and route through communications module.
    
    This endpoint receives alerts from Grafana and processes them through the
    communications system for email, SMS, and webhook notifications.
    """
    try:
        # Parse the incoming payload
        payload = await request.json()
        
        logger.info("Received Grafana alert webhook", extra={
            "alert_source": x_alert_source,
            "alert_type": x_alert_type,
            "payload_keys": list(payload.keys()) if payload else []
        })
        
        # Initialize communication service
        comm_service = CommunicationService(db)
        
        # Route alert based on type
        if x_alert_type == "email" or not x_alert_type:
            await _handle_email_alert(comm_service, payload)
        elif x_alert_type == "webhook":
            await _handle_webhook_alert(comm_service, payload)
        elif x_alert_type == "sms":
            await _handle_sms_alert(comm_service, payload)
        else:
            logger.warning("Unknown alert type", extra={"alert_type": x_alert_type})
        
        return {"status": "success", "message": "Alert processed successfully"}
        
    except Exception as e:
        logger.error("Failed to process Grafana alert", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail=f"Alert processing failed: {str(e)}")


@router.get("/webhooks/test")
async def test_grafana_webhook():
    """Test endpoint for Grafana webhook configuration."""
    return {
        "status": "success",
        "message": "Grafana webhook endpoint is accessible",
        "timestamp": "2025-01-26T10:00:00Z",
        "endpoint": "/api/v1/alerts/webhooks/grafana"
    }


# ============================================================================
# Alert Rule Management (from enhanced_grafana_alerts.py)
# ============================================================================

@router.post("/rules/error-handling")
async def create_error_handling_rules(
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin_user)
):
    """Create comprehensive error handling alert rules."""
    try:
        service = GrafanaAlertIntegrationService(db)
        result = await service.create_error_handling_alert_rules()
        
        logger.info("Created error handling alert rules", extra={
            "admin_id": current_admin.id,
            "rules_created": len(result.get("rules", []))
        })
        
        return {
            "status": "success",
            "message": "Error handling alert rules created successfully",
            "rules": result
        }
    except Exception as e:
        logger.error("Failed to create error handling rules", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail=f"Failed to create alert rules: {str(e)}")


@router.post("/dashboards/operational")
async def create_operational_dashboards(
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin_user)
):
    """Create comprehensive operational dashboards."""
    try:
        service = GrafanaAlertIntegrationService(db)
        result = await service.create_operational_dashboards()
        
        logger.info("Created operational dashboards", extra={
            "admin_id": current_admin.id,
            "dashboards_created": len(result.get("dashboards", []))
        })
        
        return {
            "status": "success",
            "message": "Operational dashboards created successfully",
            "dashboards": result
        }
    except Exception as e:
        logger.error("Failed to create operational dashboards", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail=f"Failed to create dashboards: {str(e)}")


@router.post("/process")
async def process_system_alert(
    request: AlertProcessingRequest,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin_user)
):
    """Process incoming system alert and trigger appropriate actions."""
    try:
        service = GrafanaAlertIntegrationService(db)
        result = await service.process_system_alert(
            alert_type=request.alert_type,
            severity=request.severity,
            title=request.title,
            message=request.message,
            source=request.source,
            metadata=request.metadata
        )
        
        logger.info("Processed system alert", extra={
            "admin_id": current_admin.id,
            "alert_type": request.alert_type,
            "severity": request.severity
        })
        
        return {
            "status": "success",
            "message": "System alert processed successfully",
            "result": result
        }
    except Exception as e:
        logger.error("Failed to process system alert", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail=f"Failed to process alert: {str(e)}")


# ============================================================================
# Metrics & Monitoring
# ============================================================================

@router.get("/metrics")
async def get_alert_metrics(
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin_user)
):
    """Get comprehensive alert metrics and statistics."""
    try:
        service = GrafanaAlertIntegrationService(db)
        metrics = await service.get_comprehensive_alert_metrics()
        
        return {
            "status": "success",
            "metrics": metrics,
            "timestamp": "2025-01-26T10:00:00Z"
        }
    except Exception as e:
        logger.error("Failed to get alert metrics", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")


@router.get("/effectiveness")
async def get_alert_effectiveness(
    days: int = Query(7, description="Number of days to analyze"),
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin_user)
):
    """Get alert effectiveness and performance report."""
    try:
        service = GrafanaAlertIntegrationService(db)
        report = await service.get_alert_effectiveness_report(days=days)
        
        return {
            "status": "success",
            "report": report,
            "analysis_period_days": days,
            "timestamp": "2025-01-26T10:00:00Z"
        }
    except Exception as e:
        logger.error("Failed to get effectiveness report", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail=f"Failed to get report: {str(e)}")


@router.get("/status")
async def get_alert_system_status(
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin_user)
):
    """Get comprehensive alert system status."""
    try:
        service = GrafanaAlertIntegrationService(db)
        status = await service.get_alert_system_status()
        
        return {
            "status": "success",
            "system_status": status,
            "timestamp": "2025-01-26T10:00:00Z"
        }
    except Exception as e:
        logger.error("Failed to get system status", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")


@router.post("/test")
async def test_alert_integration(
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin_user)
):
    """Test the alert integration system with a sample alert."""
    try:
        service = GrafanaAlertIntegrationService(db)
        result = await service.test_alert_integration()
        
        logger.info("Tested alert integration", extra={
            "admin_id": current_admin.id,
            "test_result": result.get("status")
        })
        
        return {
            "status": "success",
            "message": "Alert integration test completed",
            "test_result": result
        }
    except Exception as e:
        logger.error("Failed to test alert integration", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail=f"Test failed: {str(e)}")


# ============================================================================
# Helper Functions
# ============================================================================

async def _handle_email_alert(comm_service: CommunicationService, payload: Dict[str, Any]):
    """Handle email alert routing."""
    try:
        recipients = _get_email_recipients(payload)
        
        # Send email notification
        await comm_service.send_email(
            to_addresses=recipients,
            subject=f"Alert: {payload.get('alert_name', 'System Alert')}",
            template_name="grafana_alert",
            template_data={
                "alert_name": payload.get("alert_name"),
                "severity": payload.get("severity"),
                "status": payload.get("status"),
                "alerts": payload.get("alerts", [])
            }
        )
        
        logger.info("Email alert sent", extra={
            "recipients": len(recipients),
            "alert_name": payload.get("alert_name")
        })
        
    except Exception as e:
        logger.error("Failed to send email alert", extra={"error": str(e)})


async def _handle_webhook_alert(comm_service: CommunicationService, payload: Dict[str, Any]):
    """Handle webhook alert routing."""
    try:
        webhook_url = settings.ALERT_WEBHOOK_URL
        if not webhook_url:
            logger.warning("No webhook URL configured for alerts")
            return
        
        # Send webhook notification
        await comm_service.send_webhook(
            url=webhook_url,
            payload=payload,
            headers={"X-Alert-Source": "grafana"}
        )
        
        logger.info("Webhook alert sent", extra={
            "webhook_url": webhook_url,
            "alert_name": payload.get("alert_name")
        })
        
    except Exception as e:
        logger.error("Failed to send webhook alert", extra={"error": str(e)})


async def _handle_sms_alert(comm_service: CommunicationService, payload: Dict[str, Any]):
    """Handle SMS alert routing."""
    try:
        recipients = _get_sms_recipients(payload)
        
        # Send SMS notification
        message = f"ALERT: {payload.get('alert_name')} - {payload.get('severity')} - {payload.get('status')}"
        
        for recipient in recipients:
            await comm_service.send_sms(
                to_number=recipient,
                message=message
            )
        
        logger.info("SMS alert sent", extra={
            "recipients": len(recipients),
            "alert_name": payload.get("alert_name")
        })
        
    except Exception as e:
        logger.error("Failed to send SMS alert", extra={"error": str(e)})


def _get_email_recipients(payload: Dict[str, Any]) -> List[str]:
    """Get email recipients based on alert severity and category."""
    severity = payload.get("severity", "").lower()
    category = payload.get("category", "system").lower()
    
    # Default recipients
    recipients = ["ops@ispframework.com"]
    
    # Add severity-based recipients
    if severity in ["critical", "high"]:
        recipients.extend(["admin@ispframework.com", "oncall@ispframework.com"])
    elif severity == "medium":
        recipients.append("support@ispframework.com")
    
    # Add category-based recipients
    if category == "billing":
        recipients.append("billing@ispframework.com")
    elif category == "network":
        recipients.append("network@ispframework.com")
    
    return list(set(recipients))  # Remove duplicates


def _get_sms_recipients(payload: Dict[str, Any]) -> List[str]:
    """Get SMS recipients based on alert severity."""
    severity = payload.get("severity", "").lower()
    
    # Only send SMS for critical alerts
    if severity == "critical":
        return ["+1-555-0100", "+1-555-0101"]  # On-call numbers
    
    return []



# ============================================================================
# Backward Compatibility Redirects (Temporary - Remove after 6 months)
# ============================================================================

from fastapi.responses import RedirectResponse

# Redirect old /alerts/* paths to new /monitoring/alerts/* paths
@router.get("/{path:path}")
async def redirect_old_alerts_get(path: str):
    """Temporary redirect for old /alerts/* paths"""
    new_path = f"/api/v1/monitoring/alerts/{path}"
    return RedirectResponse(url=new_path, status_code=307)

@router.post("/{path:path}")
async def redirect_old_alerts_post(path: str):
    """Temporary redirect for old /alerts/* paths"""
    new_path = f"/api/v1/monitoring/alerts/{path}"
    return RedirectResponse(url=new_path, status_code=307)

@router.put("/{path:path}")
async def redirect_old_alerts_put(path: str):
    """Temporary redirect for old /alerts/* paths"""
    new_path = f"/api/v1/monitoring/alerts/{path}"
    return RedirectResponse(url=new_path, status_code=307)

@router.delete("/{path:path}")
async def redirect_old_alerts_delete(path: str):
    """Temporary redirect for old /alerts/* paths"""
    new_path = f"/api/v1/monitoring/alerts/{path}"
    return RedirectResponse(url=new_path, status_code=307)

