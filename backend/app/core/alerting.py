"""
Alerting Integration System for ISP Framework.

Provides Grafana-based alerting with communications module integration.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

import structlog
from prometheus_client import Counter, Gauge, Histogram
from pydantic import BaseModel

from app.core.config import settings
from app.core.error_handling import (
    ErrorCategory,
    ErrorDetail,
    ErrorImpact,
    ErrorSeverity,
)

# Prometheus metrics for error tracking and Grafana alerting
error_counter = Counter(
    "isp_errors_total",
    "Total number of errors by category and severity",
    ["category", "severity", "impact"],
)

error_duration = Histogram(
    "isp_error_resolution_duration_seconds",
    "Time to resolve errors by category",
    ["category", "severity"],
)

active_alerts = Gauge(
    "isp_active_alerts_total", "Number of active alerts by severity", ["severity"]
)

customer_impact_errors = Counter(
    "isp_customer_impact_errors_total",
    "Errors with customer impact by category",
    ["category", "customer_id"],
)

network_device_errors = Counter(
    "isp_network_device_errors_total",
    "Network device specific errors",
    ["device_type", "device_id", "error_type"],
)

billing_errors = Counter(
    "isp_billing_errors_total", "Billing system errors", ["error_type", "customer_id"]
)

service_provisioning_errors = Counter(
    "isp_service_provisioning_errors_total",
    "Service provisioning failures",
    ["service_type", "provisioning_step", "customer_id"],
)


class AlertChannel(str, Enum):
    """Available alerting channels via communications module."""

    EMAIL = "email"
    WEBHOOK = "webhook"
    SMS = "sms"


class AlertRule(BaseModel):
    """Alert rule configuration for Grafana integration."""

    name: str
    description: str
    enabled: bool = True
    channels: List[AlertChannel]
    severity_threshold: ErrorSeverity = ErrorSeverity.HIGH
    categories: Optional[List[ErrorCategory]] = None
    impacts: Optional[List[ErrorImpact]] = None
    cooldown_minutes: int = 15  # Prevent alert spam
    escalation_minutes: int = 60  # Escalate if not acknowledged
    grafana_rule_id: Optional[str] = None  # Grafana alert rule ID


class CommunicationAlert(BaseModel):
    """Alert message structure for communications module."""

    title: str
    message: str
    severity: ErrorSeverity
    category: ErrorCategory
    channel: AlertChannel
    recipients: List[str]
    metadata: Dict[str, Any] = {}


class GrafanaAlertManager:
    """Manages Grafana-based alerting with communications module integration."""

    def __init__(self):
        self.logger = structlog.get_logger("isp.alerting")
        self.alert_cache = {}  # For cooldown management
        self.setup_default_rules()

    def setup_default_rules(self):
        """Setup default alerting rules for ISP operations."""
        self.rules = [
            AlertRule(
                name="critical_system_errors",
                description="Critical system errors requiring immediate attention",
                channels=[AlertChannel.EMAIL, AlertChannel.WEBHOOK],
                severity_threshold=ErrorSeverity.CRITICAL,
                impacts=[ErrorImpact.CUSTOMER_FACING],
                cooldown_minutes=5,
                escalation_minutes=30,
            ),
            AlertRule(
                name="network_infrastructure_alerts",
                description="Network device and infrastructure failures",
                channels=[AlertChannel.EMAIL, AlertChannel.SMS],
                severity_threshold=ErrorSeverity.HIGH,
                categories=[ErrorCategory.NETWORK, ErrorCategory.RADIUS],
                impacts=[ErrorImpact.CUSTOMER_FACING],
                cooldown_minutes=10,
                escalation_minutes=45,
            ),
            AlertRule(
                name="billing_system_alerts",
                description="Billing and payment processing errors",
                channels=[AlertChannel.EMAIL],
                severity_threshold=ErrorSeverity.HIGH,
                categories=[ErrorCategory.BILLING],
                impacts=[ErrorImpact.CUSTOMER_FACING],
                cooldown_minutes=15,
                escalation_minutes=60,
            ),
            AlertRule(
                name="authentication_security_alerts",
                description="Authentication and security-related errors",
                channels=[AlertChannel.EMAIL, AlertChannel.WEBHOOK],
                severity_threshold=ErrorSeverity.HIGH,
                categories=[ErrorCategory.AUTHENTICATION],
                cooldown_minutes=10,
                escalation_minutes=45,
            ),
            AlertRule(
                name="service_provisioning_alerts",
                description="Service provisioning and management failures",
                channels=[AlertChannel.EMAIL],
                severity_threshold=ErrorSeverity.HIGH,
                categories=[ErrorCategory.SERVICE],
                impacts=[ErrorImpact.CUSTOMER_FACING],
                cooldown_minutes=20,
                escalation_minutes=60,
            ),
        ]

    async def process_error(self, error_detail: ErrorDetail):
        """Process error, update metrics, and trigger appropriate alerts."""
        # Update Prometheus metrics for Grafana monitoring
        self._update_metrics(error_detail)

        # Find matching alert rules
        matching_rules = self._find_matching_rules(error_detail)

        # Send alerts via communications module
        for rule in matching_rules:
            if self._should_alert(rule, error_detail):
                await self._send_communication_alerts(rule, error_detail)
                self._update_alert_cache(rule, error_detail)

    def _update_metrics(self, error_detail: ErrorDetail):
        """Update Prometheus metrics for Grafana dashboards and alerting."""
        # Update general error counter
        error_counter.labels(
            category=error_detail.category.value,
            severity=error_detail.severity.value,
            impact=error_detail.impact.value,
        ).inc()

        # Update customer impact errors if customer is affected
        if error_detail.customer_id:
            customer_impact_errors.labels(
                category=error_detail.category.value,
                customer_id=str(error_detail.customer_id),
            ).inc()

        # Update active alerts gauge
        if error_detail.severity in [ErrorSeverity.CRITICAL, ErrorSeverity.HIGH]:
            active_alerts.labels(severity=error_detail.severity.value).inc()

        # Update category-specific metrics
        if error_detail.category == ErrorCategory.NETWORK:
            device_id = error_detail.context.get("device_id", "unknown")
            device_type = error_detail.context.get("device_type", "unknown")
            network_device_errors.labels(
                device_type=device_type,
                device_id=str(device_id),
                error_type=error_detail.title,
            ).inc()

        elif error_detail.category == ErrorCategory.BILLING:
            billing_errors.labels(
                error_type=error_detail.title,
                customer_id=(
                    str(error_detail.customer_id)
                    if error_detail.customer_id
                    else "unknown"
                ),
            ).inc()

        elif error_detail.category == ErrorCategory.SERVICE:
            service_type = error_detail.context.get("service_type", "unknown")
            provisioning_step = error_detail.context.get("provisioning_step", "unknown")
            service_provisioning_errors.labels(
                service_type=service_type,
                provisioning_step=provisioning_step,
                customer_id=(
                    str(error_detail.customer_id)
                    if error_detail.customer_id
                    else "unknown"
                ),
            ).inc()

    def _find_matching_rules(self, error_detail: ErrorDetail) -> List[AlertRule]:
        """Find alert rules that match the error criteria."""
        matching_rules = []

        for rule in self.rules:
            if not rule.enabled:
                continue

            # Check severity threshold
            severity_levels = [
                ErrorSeverity.LOW,
                ErrorSeverity.MEDIUM,
                ErrorSeverity.HIGH,
                ErrorSeverity.CRITICAL,
            ]
            if severity_levels.index(error_detail.severity) < severity_levels.index(
                rule.severity_threshold
            ):
                continue

            # Check category filter
            if rule.categories and error_detail.category not in rule.categories:
                continue

            # Check impact filter
            if rule.impacts and error_detail.impact not in rule.impacts:
                continue

            matching_rules.append(rule)

        return matching_rules

    def _should_alert(self, rule: AlertRule, error_detail: ErrorDetail) -> bool:
        """Check if alert should be sent based on cooldown and other criteria."""
        cache_key = (
            f"{rule.name}:{error_detail.category.value}:{error_detail.impact.value}"
        )

        if cache_key in self.alert_cache:
            last_alert_time = self.alert_cache[cache_key]["last_sent"]
            cooldown_seconds = rule.cooldown_minutes * 60

            if (
                datetime.now(timezone.utc) - last_alert_time
            ).total_seconds() < cooldown_seconds:
                self.logger.debug(
                    "Alert suppressed due to cooldown",
                    rule=rule.name,
                    error_id=error_detail.error_id,
                    cooldown_minutes=rule.cooldown_minutes,
                )
                return False

        return True

    def _update_alert_cache(self, rule: AlertRule, error_detail: ErrorDetail):
        """Update alert cache to track cooldowns."""
        cache_key = (
            f"{rule.name}:{error_detail.category.value}:{error_detail.impact.value}"
        )
        self.alert_cache[cache_key] = {
            "last_sent": datetime.now(timezone.utc),
            "error_id": error_detail.error_id,
            "count": self.alert_cache.get(cache_key, {}).get("count", 0) + 1,
        }

    async def _send_communication_alerts(
        self, rule: AlertRule, error_detail: ErrorDetail
    ):
        """Send alerts via communications module."""
        try:
            # Import communications service
            from app.core.database import get_db
            from app.services.communications_service import CommunicationsService

            # Get database session
            db = next(get_db())
            comm_service = CommunicationsService(db)

            # Create alert message
            alert_title = f"🚨 ISP Framework Alert: {error_detail.title}"
            alert_message = self._create_alert_message(error_detail)

            # Send alerts to each configured channel
            for channel in rule.channels:
                recipients = self._get_alert_recipients(channel, error_detail)

                if channel == AlertChannel.EMAIL:
                    await self._send_email_alert(
                        comm_service,
                        alert_title,
                        alert_message,
                        recipients,
                        error_detail,
                    )
                elif channel == AlertChannel.WEBHOOK:
                    await self._send_webhook_alert(
                        comm_service, alert_title, alert_message, error_detail
                    )
                elif channel == AlertChannel.SMS:
                    await self._send_sms_alert(
                        comm_service,
                        alert_title,
                        alert_message,
                        recipients,
                        error_detail,
                    )

            self.logger.info(
                "Communication alerts sent successfully",
                rule=rule.name,
                error_id=error_detail.error_id,
                channels=[c.value for c in rule.channels],
            )

        except Exception as e:
            self.logger.error(
                "Failed to send communication alerts",
                rule=rule.name,
                error_id=error_detail.error_id,
                error=str(e),
            )

    def _create_alert_message(self, error_detail: ErrorDetail) -> str:
        """Create formatted alert message."""
        message_parts = [
            "**Error Details:**",
            f"• **Severity:** {error_detail.severity.value.upper()}",
            f"• **Category:** {error_detail.category.value.title()}",
            f"• **Impact:** {error_detail.impact.value.replace('_', ' ').title()}",
            f"• **Error ID:** {error_detail.error_id}",
            f"• **Timestamp:** {error_detail.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}",
            "",
            "**Description:**",
            f"{error_detail.detail}",
        ]

        if error_detail.customer_id:
            message_parts.insert(-3, f"• **Customer ID:** {error_detail.customer_id}")

        if error_detail.context:
            message_parts.extend(["", "**Additional Context:**"])
            for key, value in error_detail.context.items():
                message_parts.append(f"• **{key.replace('_', ' ').title()}:** {value}")

        return "\n".join(message_parts)

    def _get_alert_recipients(
        self, channel: AlertChannel, error_detail: ErrorDetail
    ) -> List[str]:
        """Get alert recipients based on channel and error details."""
        # This would typically come from configuration or database
        # For now, return default recipients based on channel

        if channel == AlertChannel.EMAIL:
            recipients = getattr(
                settings, "ALERT_EMAIL_RECIPIENTS", ["admin@ispframework.com"]
            )

            # Add customer-specific recipients for customer-facing errors
            if (
                error_detail.impact == ErrorImpact.CUSTOMER_FACING
                and error_detail.customer_id
            ):
                # Could add customer support team email here
                pass

        elif channel == AlertChannel.SMS:
            recipients = getattr(settings, "ALERT_SMS_RECIPIENTS", ["+1234567890"])

        else:
            recipients = []

        return recipients

    async def _send_email_alert(
        self,
        comm_service,
        title: str,
        message: str,
        recipients: List[str],
        error_detail: ErrorDetail,
    ):
        """Send email alert via communications module."""
        try:
            await comm_service.send_email(
                recipients=recipients,
                subject=title,
                body=message,
                template_name="alert_notification",
                template_data={
                    "error_detail": error_detail.dict(),
                    "severity_color": self._get_severity_color(error_detail.severity),
                },
            )
        except Exception as e:
            self.logger.error(f"Failed to send email alert: {e}")

    async def _send_webhook_alert(
        self, comm_service, title: str, message: str, error_detail: ErrorDetail
    ):
        """Send webhook alert via communications module."""
        try:
            webhook_payload = {
                "alert_type": "error_notification",
                "title": title,
                "message": message,
                "error_detail": error_detail.dict(),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            webhook_urls = getattr(settings, "ALERT_WEBHOOK_URLS", [])
            for url in webhook_urls:
                await comm_service.send_webhook(
                    url=url,
                    payload=webhook_payload,
                    headers={"Content-Type": "application/json"},
                )
        except Exception as e:
            self.logger.error(f"Failed to send webhook alert: {e}")

    async def _send_sms_alert(
        self,
        comm_service,
        title: str,
        message: str,
        recipients: List[str],
        error_detail: ErrorDetail,
    ):
        """Send SMS alert via communications module."""
        try:
            # Create shorter message for SMS
            sms_message = f"{title}\n{error_detail.detail[:100]}...\nError ID: {error_detail.error_id}"

            for recipient in recipients:
                await comm_service.send_sms(phone_number=recipient, message=sms_message)
        except Exception as e:
            self.logger.error(f"Failed to send SMS alert: {e}")

    def _get_severity_color(self, severity: ErrorSeverity) -> str:
        """Get color code for severity level."""
        color_map = {
            ErrorSeverity.CRITICAL: "#FF0000",  # Red
            ErrorSeverity.HIGH: "#FF8C00",  # Orange
            ErrorSeverity.MEDIUM: "#FFD700",  # Yellow
            ErrorSeverity.LOW: "#32CD32",  # Green
        }
        return color_map.get(severity, "#FF0000")


# Global Grafana alert manager instance
grafana_alert_manager = GrafanaAlertManager()
