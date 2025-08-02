"""Threshold definition model for alerting and monitoring."""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, DECIMAL
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from app.models.base import Base


class ThresholdDefinition(Base):
    """
    Dynamic threshold definitions for alerting and monitoring.
    Enables configurable alerts based on metric values and conditions.
    """
    __tablename__ = "threshold_definitions"

    id = Column(Integer, primary_key=True, index=True)
    
    # Threshold identification
    threshold_key = Column(String(100), unique=True, nullable=False, index=True)
    threshold_name = Column(String(200), nullable=False)
    description = Column(Text)
    
    # Metric association
    metric_key = Column(String(100), nullable=False, index=True)  # References MetricDefinition.metric_key
    
    # Threshold conditions
    operator = Column(String(20), nullable=False)  # '>', '<', '>=', '<=', '=', '!=', 'between'
    value = Column(DECIMAL(15, 4), nullable=False)  # Primary threshold value
    secondary_value = Column(DECIMAL(15, 4))  # For 'between' operator
    
    # Severity and categorization
    severity = Column(String(20), nullable=False)  # 'critical', 'warning', 'info'
    category = Column(String(50), nullable=False)  # 'performance', 'financial', 'security', 'operational'
    
    # Alert configuration
    alert_config = Column(JSONB, nullable=False)
    # Examples:
    # {"email": {"enabled": true, "recipients": ["admin@isp.com"]}}
    # {"webhook": {"enabled": true, "url": "https://alerts.isp.com/webhook", "method": "POST"}}
    # {"sms": {"enabled": true, "numbers": ["+1234567890"]}}
    # {"slack": {"enabled": true, "channel": "#alerts", "webhook_url": "https://hooks.slack.com/..."}}
    
    # Evaluation configuration
    evaluation_interval_seconds = Column(Integer, default=300)  # 5 minutes
    consecutive_breaches_required = Column(Integer, default=1)  # How many consecutive breaches before alerting
    cooldown_seconds = Column(Integer, default=1800)  # 30 minutes before re-alerting
    
    # Filtering and segmentation
    filters = Column(JSONB)  # Additional filters for threshold evaluation
    segments = Column(JSONB)  # Apply threshold to specific segments only
    
    # Status tracking
    is_active = Column(Boolean, default=True, nullable=False)
    last_evaluation = Column(DateTime(timezone=True))
    last_breach = Column(DateTime(timezone=True))
    last_alert_sent = Column(DateTime(timezone=True))
    consecutive_breaches = Column(Integer, default=0)
    
    # Access control
    visibility_roles = Column(JSONB)  # ["admin", "manager", "viewer"]
    tenant_scope = Column(String(50))  # 'global', 'reseller', 'customer'
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    created_by = Column(String(100))
    
    def __repr__(self):
        return f"<ThresholdDefinition(key='{self.threshold_key}', metric='{self.metric_key}', severity='{self.severity}')>"
