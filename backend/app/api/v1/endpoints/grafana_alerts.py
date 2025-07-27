"""
Grafana Alert Webhook Endpoints for ISP Framework.

Handles incoming alerts from Grafana and routes them through the communications module.
"""
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, Request, Header
from pydantic import BaseModel
from sqlalchemy.orm import Session
import structlog

from app.core.database import get_db
from app.services.communications_service import CommunicationService
from app.core.config import settings


router = APIRouter()
logger = structlog.get_logger("isp.grafana_alerts")


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


@router.post("/webhook/grafana-alerts")
async def handle_grafana_alert(
    request: Request,
    db: Session = Depends(get_db),
    x_alert_source: str = Header(None, alias="X-Alert-Source"),
    x_alert_type: str = Header(None, alias="X-Alert-Type")
):
    """Handle incoming Grafana alert webhooks and route through communications module."""
    try:
        # Parse the incoming payload
        payload = await request.json()
        
        # Log the incoming alert
        logger.info(
            "Received Grafana alert webhook",
            alert_source=x_alert_source,
            alert_type=x_alert_type,
            payload_keys=list(payload.keys()) if isinstance(payload, dict) else "non-dict"
        )
        
        # Initialize communications service
        comm_service = CommunicationService(db)
        
        # Route based on alert type header
        if x_alert_type == "email":
            await _handle_email_alert(comm_service, payload)
        elif x_alert_type == "webhook":
            await _handle_webhook_alert(comm_service, payload)
        elif x_alert_type == "sms":
            await _handle_sms_alert(comm_service, payload)
        else:
            # Default to email if no type specified
            await _handle_email_alert(comm_service, payload)
        
        return {"status": "success", "message": "Alert processed successfully"}
        
    except Exception as e:
        logger.error(
            "Failed to process Grafana alert webhook",
            error=str(e),
            alert_source=x_alert_source,
            alert_type=x_alert_type
        )
        raise HTTPException(status_code=500, detail=f"Failed to process alert: {str(e)}")


async def _handle_email_alert(comm_service: CommunicationService, payload: Dict[str, Any]):
    """Handle email alert routing."""
    try:
        # Extract alert information
        title = payload.get("title", "ISP Framework Alert")
        message = payload.get("text", "Alert notification from Grafana")
        
        # Get email recipients based on severity
        recipients = _get_email_recipients(payload)
        
        # Send email via communications module
        await comm_service.send_email(
            recipients=recipients,
            subject=title,
            body=message,
            template_name="grafana_alert_notification",
            template_data={
                "alert_payload": payload,
                "severity": payload.get("severity", "unknown"),
                "service": payload.get("service", "isp-framework")
            }
        )
        
        logger.info(
            "Email alert sent successfully",
            recipients_count=len(recipients),
            alert_title=title
        )
        
    except Exception as e:
        logger.error(f"Failed to send email alert: {e}")
        raise


async def _handle_webhook_alert(comm_service: CommunicationService, payload: Dict[str, Any]):
    """Handle webhook alert routing."""
    try:
        # Get webhook URLs from configuration
        webhook_urls = getattr(settings, 'GRAFANA_ALERT_WEBHOOK_URLS', [])
        
        if not webhook_urls:
            logger.warning("No webhook URLs configured for Grafana alerts")
            return
        
        # Send to each configured webhook URL
        for url in webhook_urls:
            await comm_service.send_webhook(
                url=url,
                payload=payload,
                headers={
                    "Content-Type": "application/json",
                    "X-Alert-Source": "grafana",
                    "X-ISP-Framework-Alert": "true"
                }
            )
        
        logger.info(
            "Webhook alerts sent successfully",
            webhook_count=len(webhook_urls),
            alert_name=payload.get("alert_name", "unknown")
        )
        
    except Exception as e:
        logger.error(f"Failed to send webhook alert: {e}")
        raise


async def _handle_sms_alert(comm_service: CommunicationService, payload: Dict[str, Any]):
    """Handle SMS alert routing."""
    try:
        # Extract alert information
        title = payload.get("title", "ISP Alert")
        message = payload.get("text", "Alert from ISP Framework")
        
        # Create shorter message for SMS (160 character limit consideration)
        sms_message = f"{title}\n{message[:100]}..."
        
        # Get SMS recipients based on severity
        recipients = _get_sms_recipients(payload)
        
        # Send SMS to each recipient
        for recipient in recipients:
            await comm_service.send_sms(
                phone_number=recipient,
                message=sms_message
            )
        
        logger.info(
            "SMS alerts sent successfully",
            recipients_count=len(recipients),
            alert_title=title
        )
        
    except Exception as e:
        logger.error(f"Failed to send SMS alert: {e}")
        raise


def _get_email_recipients(payload: Dict[str, Any]) -> List[str]:
    """Get email recipients based on alert severity and category."""
    severity = payload.get("severity", "medium").lower()
    category = payload.get("category", "system").lower()
    
    # Base recipients for all alerts
    recipients = getattr(settings, 'GRAFANA_ALERT_EMAIL_RECIPIENTS', ['admin@ispframework.com'])
    
    # Add severity-specific recipients
    if severity == "critical":
        critical_recipients = getattr(settings, 'CRITICAL_ALERT_EMAIL_RECIPIENTS', [])
        recipients.extend(critical_recipients)
    
    # Add category-specific recipients
    if category == "network":
        network_recipients = getattr(settings, 'NETWORK_ALERT_EMAIL_RECIPIENTS', [])
        recipients.extend(network_recipients)
    elif category == "billing":
        billing_recipients = getattr(settings, 'BILLING_ALERT_EMAIL_RECIPIENTS', [])
        recipients.extend(billing_recipients)
    
    # Remove duplicates
    return list(set(recipients))


def _get_sms_recipients(payload: Dict[str, Any]) -> List[str]:
    """Get SMS recipients based on alert severity."""
    severity = payload.get("severity", "medium").lower()
    
    # Only send SMS for critical and high severity alerts
    if severity in ["critical", "high"]:
        return getattr(settings, 'GRAFANA_ALERT_SMS_RECIPIENTS', [])
    
    return []


@router.get("/webhook/test")
async def test_grafana_webhook():
    """Test endpoint for Grafana webhook configuration."""
    return {
        "status": "ok",
        "message": "Grafana webhook endpoint is working",
        "timestamp": "2025-01-26T13:40:00Z"
    }
