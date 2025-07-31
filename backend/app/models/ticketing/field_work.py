"""
Field Work Order Models
Field technician dispatch and work order management
"""

import enum
from datetime import datetime

from sqlalchemy import (
    DECIMAL,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base


class FieldWorkStatus(enum.Enum):
    SCHEDULED = "scheduled"
    DISPATCHED = "dispatched"
    EN_ROUTE = "en_route"
    ON_SITE = "on_site"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    RESCHEDULED = "rescheduled"


class FieldWorkOrder(Base):
    """Field work orders for on-site technician dispatch"""

    __tablename__ = "field_work_orders"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(
        Integer, ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False
    )
    work_order_number = Column(String(50), unique=True, nullable=False, index=True)

    # Work Details
    work_type = Column(
        String(100), nullable=False
    )  # installation, repair, maintenance, survey
    work_description = Column(Text, nullable=False)
    special_instructions = Column(Text)

    # Location
    work_address = Column(Text, nullable=False)
    gps_latitude = Column(String(20))
    gps_longitude = Column(String(20))
    location_contact_name = Column(String(255))
    location_contact_phone = Column(String(50))

    # Scheduling
    status = Column(
        Enum(FieldWorkStatus), default=FieldWorkStatus.SCHEDULED, index=True
    )
    priority = Column(
        String(20), default="normal"
    )  # Using String to avoid circular import
    scheduled_date = Column(DateTime(timezone=True), index=True)
    estimated_duration_hours = Column(DECIMAL(5, 2))

    # Assignment
    assigned_technician = Column(Integer, ForeignKey("administrators.id"))
    technician_team = Column(String(100))
    backup_technician = Column(Integer, ForeignKey("administrators.id"))

    # Equipment & Materials
    required_equipment = Column(JSONB, default=[])  # List of required equipment
    required_materials = Column(JSONB, default=[])  # List of materials needed
    equipment_assigned = Column(JSONB, default=[])  # Actually assigned equipment

    # Customer Interaction
    customer_availability = Column(Text)  # When customer is available
    access_requirements = Column(Text)  # Gate codes, keys, etc.
    safety_requirements = Column(Text)  # Safety considerations

    # Work Execution
    actual_start_time = Column(DateTime(timezone=True))
    actual_end_time = Column(DateTime(timezone=True))
    work_performed = Column(Text)
    findings = Column(Text)

    # Results
    work_completed = Column(Boolean, default=False)
    customer_signature_required = Column(Boolean, default=False)
    customer_signature_obtained = Column(Boolean, default=False)
    customer_satisfaction_score = Column(Integer)  # 1-5 rating

    # Photos & Documentation
    before_photos = Column(JSONB, default=[])  # Photo file paths
    after_photos = Column(JSONB, default=[])
    work_photos = Column(JSONB, default=[])

    # Follow-up
    follow_up_required = Column(Boolean, default=False)
    follow_up_date = Column(DateTime(timezone=True))
    follow_up_reason = Column(String(255))

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True))

    # Relationships
    ticket = relationship("Ticket", back_populates="field_work")
    technician = relationship("Administrator", foreign_keys=[assigned_technician])
    backup_tech = relationship("Administrator", foreign_keys=[backup_technician])

    @property
    def is_overdue(self):
        """Check if field work is overdue"""
        if not self.scheduled_date or self.status in [
            FieldWorkStatus.COMPLETED,
            FieldWorkStatus.CANCELLED,
        ]:
            return False
        return datetime.now(self.scheduled_date.tzinfo) > self.scheduled_date

    @property
    def actual_duration_hours(self):
        """Calculate actual work duration"""
        if not self.actual_start_time or not self.actual_end_time:
            return None

        delta = self.actual_end_time - self.actual_start_time
        return round(delta.total_seconds() / 3600, 2)
