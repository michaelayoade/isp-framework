"""Alerting Integration System for ISP Framework.

Provides Grafana-based alerting with communications module integration.
"""
import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Optional
from enum import Enum

import aiohttp
import structlog
from pydantic import BaseModel
from prometheus_client import Counter, Histogram, Gauge

from app.core.config import settings
from app.core.error_handling import ErrorDetail, ErrorSeverity, ErrorCategory, ErrorImpact


# Prometheus metrics for error tracking
error_counter = Counter(
    'isp_errors_total',
    'Total number of errors by category and severity',
    ['category', 'severity', 'impact']
)

error_duration = Histogram(
    'isp_error_resolution_duration_seconds',
    'Time to resolve errors by category',
    ['category', 'severity']
)

active_alerts = Gauge(
    'isp_active_alerts_total',
    'Number of active alerts by severity',
    ['severity']
)

customer_impact_errors = Counter(
    'isp_customer_impact_errors_total',
    'Errors with customer impact by category',
    ['category', 'customer_id']
)


class AlertChannel(str, Enum):
    """Available alerting channels via communications module."""
    EMAIL = "email"
    WEBHOOK = "webhook"
    SMS = "sms"


class AlertRule(BaseModel):
    """Alert rule configuration."""
    name: str
    description: str
    enabled: bool = True
    channels: List[AlertChannel]
    severity_threshold: ErrorSeverity = ErrorSeverity.HIGH
    categories: Optional[List[ErrorCategory]] = None
    impacts: Optional[List[ErrorImpact]] = None
    cooldown_minutes: int = 15  # Prevent alert spam
    escalation_minutes: int = 60  # Escalate if not acknowledged


class SlackAlert(BaseModel):
    """Slack alert message structure."""
    text: str
    channel: str
    username: str = "ISP Framework Alert"
    icon_emoji: str = ":warning:"
    attachments: List[Dict] = []


class PagerDutyAlert(BaseModel):
    """PagerDuty alert structure."""
    routing_key: str
    event_action: str = "trigger"
    dedup_key: Optional[str] = None
    payload: Dict
    client: str = "ISP Framework"
    client_url: Optional[str] = None


class AlertManager:
    """Manages alerting rules and delivery for critical errors."""
    
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
                channels=[AlertChannel.SLACK, AlertChannel.PAGERDUTY],
                severity_threshold=ErrorSeverity.CRITICAL,
                impacts=[ErrorImpact.CUSTOMER_FACING],
                cooldown_minutes=5,
                escalation_minutes=30
            ),
            AlertRule(
                name="network_infrastructure_alerts",
                description="Network device and infrastructure failures",
                channels=[AlertChannel.SLACK, AlertChannel.PAGERDUTY],
                severity_threshold=ErrorSeverity.HIGH,
                categories=[ErrorCategory.NETWORK, ErrorCategory.RADIUS],
                impacts=[ErrorImpact.CUSTOMER_FACING],
                cooldown_minutes=10,
                escalation_minutes=45
            ),
            AlertRule(
                name="billing_system_alerts",
                description="Billing and payment processing errors",
                channels=[AlertChannel.SLACK],
                severity_threshold=ErrorSeverity.HIGH,
                categories=[ErrorCategory.BILLING],
                impacts=[ErrorImpact.CUSTOMER_FACING],
                cooldown_minutes=15,
                escalation_minutes=60
            ),
            AlertRule(
                name="authentication_security_alerts",
                description="Authentication and security-related errors",
                channels=[AlertChannel.SLACK],
                severity_threshold=ErrorSeverity.HIGH,
                categories=[ErrorCategory.AUTHENTICATION],
                cooldown_minutes=10,
                escalation_minutes=45
            ),
            AlertRule(
                name="service_provisioning_alerts",
                description="Service provisioning and management failures",
                channels=[AlertChannel.SLACK],
                severity_threshold=ErrorSeverity.HIGH,
                categories=[ErrorCategory.SERVICE],
                impacts=[ErrorImpact.CUSTOMER_FACING],
                cooldown_minutes=20,
                escalation_minutes=60
            )
        ]
    
    async def process_error(self, error_detail: ErrorDetail):
        """Process error and trigger appropriate alerts."""
        matching_rules = self._find_matching_rules(error_detail)
        
        for rule in matching_rules:
            if self._should_alert(rule, error_detail):
                await self._send_alerts(rule, error_detail)
                self._update_alert_cache(rule, error_detail)
    
    def _find_matching_rules(self, error_detail: ErrorDetail) -> List[AlertRule]:
        """Find alert rules that match the error criteria."""
        matching_rules = []
        
        for rule in self.rules:
            if not rule.enabled:
                continue
            
            # Check severity threshold
            severity_levels = [ErrorSeverity.LOW, ErrorSeverity.MEDIUM, ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]
            if severity_levels.index(error_detail.severity) < severity_levels.index(rule.severity_threshold):
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
        cache_key = f"{rule.name}:{error_detail.category.value}:{error_detail.impact.value}"
        
        if cache_key in self.alert_cache:
            last_alert_time = self.alert_cache[cache_key]['last_sent']
            cooldown_seconds = rule.cooldown_minutes * 60
            
            if (datetime.now(timezone.utc) - last_alert_time).total_seconds() < cooldown_seconds:
                self.logger.debug(
                    "Alert suppressed due to cooldown",
                    rule=rule.name,
                    error_id=error_detail.error_id,
                    cooldown_minutes=rule.cooldown_minutes
                )
                return False
        
        return True
    
    def _update_alert_cache(self, rule: AlertRule, error_detail: ErrorDetail):
        """Update alert cache to track cooldowns."""
        cache_key = f"{rule.name}:{error_detail.category.value}:{error_detail.impact.value}"
        self.alert_cache[cache_key] = {
            'last_sent': datetime.now(timezone.utc),
            'error_id': error_detail.error_id,
            'count': self.alert_cache.get(cache_key, {}).get('count', 0) + 1
        }
    
    async def _send_alerts(self, rule: AlertRule, error_detail: ErrorDetail):
        """Send alerts to configured channels."""
        tasks = []
        
        for channel in rule.channels:
            if channel == AlertChannel.SLACK:
                tasks.append(self._send_slack_alert(rule, error_detail))
            elif channel == AlertChannel.PAGERDUTY:
                tasks.append(self._send_pagerduty_alert(rule, error_detail))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _send_slack_alert(self, rule: AlertRule, error_detail: ErrorDetail):
        """Send alert to Slack channel."""
        if not hasattr(settings, 'SLACK_WEBHOOK_URL') or not settings.SLACK_WEBHOOK_URL:
            self.logger.warning("Slack webhook URL not configured, skipping Slack alert")
            return
        
        # Determine color based on severity
        color_map = {
            ErrorSeverity.CRITICAL: "#FF0000",  # Red
            ErrorSeverity.HIGH: "#FF8C00",      # Orange
            ErrorSeverity.MEDIUM: "#FFD700",    # Yellow
            ErrorSeverity.LOW: "#32CD32"        # Green
        }
        
        # Create Slack message
        alert_message = {
            "text": f"🚨 ISP Framework Alert: {error_detail.title}",
            "channel": getattr(settings, 'SLACK_ALERT_CHANNEL', '#alerts'),
            "username": "ISP Framework",
            "icon_emoji": ":warning:",
            "attachments": [
                {
                    "color": color_map.get(error_detail.severity, "#FF0000"),
                    "title": f"{error_detail.severity.value.upper()} - {error_detail.title}",
                    "text": error_detail.detail,
                    "fields": [
                        {
                            "title": "Error ID",
                            "value": error_detail.error_id,
                            "short": True
                        },
                        {
                            "title": "Category",
                            "value": error_detail.category.value.title(),
                            "short": True
                        },
                        {
                            "title": "Impact",
                            "value": error_detail.impact.value.replace('_', ' ').title(),
                            "short": True
                        },
                        {
                            "title": "Timestamp",
                            "value": error_detail.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC"),
                            "short": True
                        }
                    ],
                    "footer": "ISP Framework Error Handling",
                    "ts": int(error_detail.timestamp.timestamp())
                }
            ]
        }
        
        # Add customer information if available
        if error_detail.customer_id:
            alert_message["attachments"][0]["fields"].append({
                "title": "Customer ID",
                "value": str(error_detail.customer_id),
                "short": True
            })
        
        # Add context information if available
        if error_detail.context:
            context_text = "\n".join([f"• {k}: {v}" for k, v in error_detail.context.items()])
            alert_message["attachments"][0]["fields"].append({
                "title": "Context",
                "value": f"```{context_text}```",
                "short": False
            })
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    settings.SLACK_WEBHOOK_URL,
                    json=alert_message,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        self.logger.info(
                            "Slack alert sent successfully",
                            rule=rule.name,
                            error_id=error_detail.error_id
                        )
                    else:
                        self.logger.error(
                            "Failed to send Slack alert",
                            rule=rule.name,
                            error_id=error_detail.error_id,
                            status_code=response.status,
                            response_text=await response.text()
                        )
        except Exception as e:
            self.logger.error(
                "Error sending Slack alert",
                rule=rule.name,
                error_id=error_detail.error_id,
                error=str(e)
            )
    
    async def _send_pagerduty_alert(self, rule: AlertRule, error_detail: ErrorDetail):
        """Send alert to PagerDuty."""
        if not hasattr(settings, 'PAGERDUTY_INTEGRATION_KEY') or not settings.PAGERDUTY_INTEGRATION_KEY:
            self.logger.warning("PagerDuty integration key not configured, skipping PagerDuty alert")
            return
        
        # Create PagerDuty event
        event_data = {
            "routing_key": settings.PAGERDUTY_INTEGRATION_KEY,
            "event_action": "trigger",
            "dedup_key": f"isp-framework-{error_detail.category.value}-{error_detail.impact.value}",
            "payload": {
                "summary": f"ISP Framework {error_detail.severity.value.upper()}: {error_detail.title}",
                "source": "ISP Framework",
                "severity": error_detail.severity.value,
                "component": error_detail.category.value,
                "group": "ISP Operations",
                "class": error_detail.impact.value,
                "custom_details": {
                    "error_id": error_detail.error_id,
                    "detail": error_detail.detail,
                    "category": error_detail.category.value,
                    "impact": error_detail.impact.value,
                    "timestamp": error_detail.timestamp.isoformat(),
                    "customer_id": error_detail.customer_id,
                    "correlation_id": error_detail.correlation_id,
                    "context": error_detail.context
                }
            },
            "client": "ISP Framework Error Handler",
            "client_url": getattr(settings, 'FRONTEND_URL', 'https://ispframework.com')
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://events.pagerduty.com/v2/enqueue",
                    json=event_data,
                    headers={"Content-Type": "application/json"},
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 202:
                        self.logger.info(
                            "PagerDuty alert sent successfully",
                            rule=rule.name,
                            error_id=error_detail.error_id
                        )
                    else:
                        self.logger.error(
                            "Failed to send PagerDuty alert",
                            rule=rule.name,
                            error_id=error_detail.error_id,
                            status_code=response.status,
                            response_text=await response.text()
                        )
        except Exception as e:
            self.logger.error(
                "Error sending PagerDuty alert",
                rule=rule.name,
                error_id=error_detail.error_id,
                error=str(e)
            )


# Global alert manager instance
alert_manager = AlertManager()
