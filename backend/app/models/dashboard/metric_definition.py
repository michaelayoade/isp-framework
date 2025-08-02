"""Metric definition model for dynamic dashboard metrics."""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, DECIMAL
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from app.models.base import Base


class MetricDefinition(Base):
    """
    Dynamic metric definitions that can be configured without code changes.
    Supports financial, network, customer, and operational metrics.
    """
    __tablename__ = "metric_definitions"

    id = Column(Integer, primary_key=True, index=True)
    
    # Core metric identification
    metric_key = Column(String(100), unique=True, nullable=False, index=True)
    metric_name = Column(String(200), nullable=False)
    description = Column(Text)
    category = Column(String(50), nullable=False, index=True)  # 'financial', 'network', 'customer', 'operational'
    
    # Calculation configuration
    calculation_method = Column(String(50), nullable=False)  # 'sum', 'avg', 'count', 'ratio', 'custom_sql'
    source_table = Column(String(100))  # Primary table for calculation
    source_column = Column(String(100))  # Primary column for calculation
    custom_sql = Column(Text)  # For complex calculations
    
    # Filtering and segmentation
    filters = Column(JSONB)  # Default filters: {"status": "active", "deleted_at": null}
    joins = Column(JSONB)  # Join configuration: [{"table": "customers", "on": "customer_id"}]
    
    # Display and formatting
    display_format = Column(String(20), default='number')  # 'currency', 'percentage', 'number', 'bytes'
    unit = Column(String(20))  # 'USD', '%', 'MB', 'count'
    decimal_places = Column(Integer, default=2)
    
    # Performance and caching
    cache_ttl_seconds = Column(Integer, default=300)  # 5 minutes default
    is_real_time = Column(Boolean, default=False)  # For WebSocket streaming
    
    # Access control
    visibility_roles = Column(JSONB)  # ["admin", "manager", "viewer"]
    tenant_scope = Column(String(50))  # 'global', 'reseller', 'customer'
    
    # Metadata
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    created_by = Column(String(100))
    
    def __repr__(self):
        return f"<MetricDefinition(key='{self.metric_key}', category='{self.category}')>"
