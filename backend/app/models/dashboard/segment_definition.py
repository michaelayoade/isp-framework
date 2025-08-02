"""Segment definition model for dynamic data filtering and grouping."""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from app.models.base import Base


class SegmentDefinition(Base):
    """
    Dynamic segment definitions for filtering and grouping metrics.
    Enables flexible customer, service, geographic, and custom segmentation.
    """
    __tablename__ = "segment_definitions"

    id = Column(Integer, primary_key=True, index=True)
    
    # Segment identification
    segment_key = Column(String(100), unique=True, nullable=False, index=True)
    segment_name = Column(String(200), nullable=False)
    description = Column(Text)
    segment_type = Column(String(50), nullable=False)  # 'customer', 'service', 'geographic', 'device', 'custom'
    
    # Filtering criteria (dynamic JSON configuration)
    criteria = Column(JSONB, nullable=False)
    # Examples:
    # Customer: {"arpu": {"operator": ">", "value": 50}, "status": {"operator": "=", "value": "active"}}
    # Geographic: {"location.city": {"operator": "in", "value": ["Lagos", "Abuja"]}}
    # Service: {"service_type": {"operator": "=", "value": "fiber"}, "bandwidth": {"operator": ">=", "value": 100}}
    # Device: {"device_type": {"operator": "=", "value": "router"}, "vendor": {"operator": "=", "value": "Cisco"}}
    
    # SQL generation configuration
    base_table = Column(String(100))  # Primary table for filtering
    join_tables = Column(JSONB)  # Additional tables to join
    # Example: [{"table": "customers", "on": "customer_id", "type": "inner"}]
    
    # Access control
    visibility_roles = Column(JSONB)  # ["admin", "manager", "viewer"]
    tenant_scope = Column(String(50))  # 'global', 'reseller', 'customer'
    
    # Metadata
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    created_by = Column(String(100))
    
    def __repr__(self):
        return f"<SegmentDefinition(key='{self.segment_key}', type='{self.segment_type}')>"
