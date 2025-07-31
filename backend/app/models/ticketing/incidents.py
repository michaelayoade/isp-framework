"""
Network Incident Models
Network-wide incidents affecting multiple customers
"""

from datetime import datetime

from sqlalchemy import (
    DECIMAL,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base


class NetworkIncident(Base):
    """Network-wide incidents affecting multiple customers"""

    __tablename__ = "network_incidents"

    id = Column(Integer, primary_key=True, index=True)
    incident_number = Column(String(50), unique=True, nullable=False, index=True)

    # Incident Details
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    incident_type = Column(String(100))  # outage, degradation, maintenance
    severity = Column(String(50))  # low, medium, high, critical

    # Affected Infrastructure
    affected_devices = Column(JSONB, default=[])  # List of device IDs
    affected_networks = Column(JSONB, default=[])  # Network segments
    affected_services = Column(JSONB, default=[])  # Service types affected

    # Geographic Impact
    affected_locations = Column(JSONB, default=[])  # Location IDs
    impact_radius_km = Column(DECIMAL(8, 2))

    # Customer Impact
    estimated_customers_affected = Column(Integer, default=0)
    confirmed_customers_affected = Column(Integer, default=0)
    business_customers_affected = Column(Integer, default=0)
    residential_customers_affected = Column(Integer, default=0)

    # Incident Timeline
    detected_at = Column(DateTime(timezone=True), nullable=False, index=True)
    reported_at = Column(DateTime(timezone=True))
    acknowledged_at = Column(DateTime(timezone=True))
    resolved_at = Column(DateTime(timezone=True))

    # Status
    status = Column(
        String(50), default="investigating", index=True
    )  # investigating, identified, monitoring, resolved

    # Response Team
    incident_commander = Column(Integer, ForeignKey("administrators.id"))
    response_team = Column(JSONB, default=[])  # List of admin IDs

    # Root Cause Analysis
    root_cause = Column(Text)
    corrective_actions = Column(Text)
    preventive_actions = Column(Text)

    # Communication
    customer_notification_sent = Column(Boolean, default=False)
    status_page_updated = Column(Boolean, default=False)

    # External References
    vendor_ticket_numbers = Column(JSONB, default=[])  # Vendor support tickets
    monitoring_alert_ids = Column(JSONB, default=[])

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    commander = relationship("Administrator")
    related_tickets = relationship("Ticket")

    @property
    def total_downtime_minutes(self):
        """Calculate total incident duration"""
        if not self.resolved_at:
            end_time = datetime.now(self.detected_at.tzinfo)
        else:
            end_time = self.resolved_at

        delta = end_time - self.detected_at
        return round(delta.total_seconds() / 60, 2)
