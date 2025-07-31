"""
ISP Service Management System - Service Provisioning

Service provisioning workflow and status tracking for automated service deployment.
"""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base
from app.models.services.enums import ProvisioningStatus


class ServiceProvisioning(Base):
    """Service provisioning workflow and status"""

    __tablename__ = "service_provisioning"

    id = Column(Integer, primary_key=True, index=True)
    customer_service_id = Column(
        Integer, ForeignKey("customer_services.id", ondelete="CASCADE"), nullable=False
    )

    # Provisioning Status
    status = Column(
        Enum(ProvisioningStatus), default=ProvisioningStatus.NOT_STARTED, index=True
    )

    # Provisioning Steps
    router_config_applied = Column(Boolean, default=False)
    radius_user_created = Column(Boolean, default=False)
    ip_address_assigned = Column(Boolean, default=False)
    speed_profile_applied = Column(Boolean, default=False)
    billing_activated = Column(Boolean, default=False)
    customer_notified = Column(Boolean, default=False)

    # Network Provisioning
    router_api_response = Column(JSONB, default=dict)
    radius_response = Column(JSONB, default=dict)
    provisioning_errors = Column(JSONB, default=list)
    provisioning_log = Column(JSONB, default=list)

    # Scheduling
    scheduled_activation = Column(DateTime(timezone=True))
    actual_activation = Column(DateTime(timezone=True))
    estimated_completion = Column(DateTime(timezone=True))

    # Staff Assignment
    assigned_technician = Column(Integer, ForeignKey("administrators.id"))
    provisioned_by = Column(Integer, ForeignKey("administrators.id"))

    # Progress Tracking
    provisioning_started = Column(DateTime(timezone=True))
    provisioning_completed = Column(DateTime(timezone=True))

    # Rollback Information
    rollback_data = Column(JSONB, default=dict)
    can_rollback = Column(Boolean, default=True)
    rollback_reason = Column(Text)

    # Quality Assurance
    qa_checked = Column(Boolean, default=False)
    qa_passed = Column(Boolean, default=False)
    qa_notes = Column(Text)
    qa_checked_by = Column(Integer, ForeignKey("administrators.id"))
    qa_checked_at = Column(DateTime(timezone=True))

    # Customer Communication
    customer_notification_sent = Column(Boolean, default=False)
    customer_notification_method = Column(String(50))  # email, sms, call
    customer_confirmation_received = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    customer_service = relationship("CustomerService", back_populates="provisioning")
    technician = relationship("Administrator", foreign_keys=[assigned_technician])
    provisioner = relationship("Administrator", foreign_keys=[provisioned_by])
    qa_checker = relationship("Administrator", foreign_keys=[qa_checked_by])

    def __repr__(self):
        return f"<ServiceProvisioning {self.customer_service_id}: {self.status.value}>"

    @property
    def provisioning_progress_percent(self):
        """Calculate provisioning completion percentage"""
        steps = [
            self.router_config_applied,
            self.radius_user_created,
            self.ip_address_assigned,
            self.speed_profile_applied,
            self.billing_activated,
            self.customer_notified,
        ]
        completed = sum(steps)
        return round((completed / len(steps)) * 100, 1)

    @property
    def is_fully_provisioned(self):
        """Check if all provisioning steps completed"""
        return all(
            [
                self.router_config_applied,
                self.radius_user_created,
                self.ip_address_assigned,
                self.speed_profile_applied,
                self.billing_activated,
                self.customer_notified,
            ]
        )

    @property
    def provisioning_duration_hours(self):
        """Calculate provisioning duration in hours"""
        if not self.provisioning_started:
            return 0

        end_time = self.provisioning_completed or datetime.now(
            self.provisioning_started.tzinfo
        )
        return round((end_time - self.provisioning_started).total_seconds() / 3600, 2)

    @property
    def next_pending_step(self):
        """Get the next step that needs to be completed"""
        steps = [
            ("router_config_applied", "Configure Router"),
            ("radius_user_created", "Create RADIUS User"),
            ("ip_address_assigned", "Assign IP Address"),
            ("speed_profile_applied", "Apply Speed Profile"),
            ("billing_activated", "Activate Billing"),
            ("customer_notified", "Notify Customer"),
        ]

        for step_field, step_name in steps:
            if not getattr(self, step_field):
                return step_name

        return None

    def add_log_entry(self, message: str, level: str = "INFO", details: dict = None):
        """Add entry to provisioning log"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "message": message,
            "details": details or {},
        }

        if not self.provisioning_log:
            self.provisioning_log = []

        self.provisioning_log.append(log_entry)

    def add_error(
        self, error_message: str, error_code: str = None, details: dict = None
    ):
        """Add error to provisioning errors"""
        error_entry = {
            "timestamp": datetime.now().isoformat(),
            "error_code": error_code,
            "message": error_message,
            "details": details or {},
        }

        if not self.provisioning_errors:
            self.provisioning_errors = []

        self.provisioning_errors.append(error_entry)


class ProvisioningTemplate(Base):
    """Templates for automated provisioning workflows"""

    __tablename__ = "provisioning_templates"

    id = Column(Integer, primary_key=True, index=True)

    # Template Information
    name = Column(String(255), nullable=False)
    description = Column(Text)
    service_type = Column(String(50), nullable=False)  # internet, voice, bundle

    # Workflow Configuration
    workflow_steps = Column(JSONB, nullable=False)  # Ordered list of steps
    automation_level = Column(String(20), default="semi")  # manual, semi, full

    # Prerequisites
    required_equipment = Column(JSONB, default=list)
    required_network_resources = Column(JSONB, default=list)

    # Timing
    estimated_duration_minutes = Column(Integer, default=60)
    sla_completion_hours = Column(Integer, default=24)

    # Quality Assurance
    requires_qa = Column(Boolean, default=True)
    qa_checklist = Column(JSONB, default=list)

    # Rollback Configuration
    supports_rollback = Column(Boolean, default=True)
    rollback_steps = Column(JSONB, default=list)

    # Status
    is_active = Column(Boolean, default=True)
    version = Column(String(20), default="1.0")

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<ProvisioningTemplate {self.name}: {self.service_type}>"


class ProvisioningQueue(Base):
    """Queue for managing provisioning tasks"""

    __tablename__ = "provisioning_queue"

    id = Column(Integer, primary_key=True, index=True)
    service_provisioning_id = Column(
        Integer,
        ForeignKey("service_provisioning.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Queue Information
    priority = Column(Integer, default=5)  # 1-10, higher = more urgent
    queue_position = Column(Integer)

    # Scheduling
    scheduled_for = Column(DateTime(timezone=True))
    estimated_start = Column(DateTime(timezone=True))
    estimated_completion = Column(DateTime(timezone=True))

    # Dependencies
    depends_on_provisioning_ids = Column(JSONB, default=list)  # Other provisioning IDs
    blocks_provisioning_ids = Column(
        JSONB, default=list
    )  # Provisioning IDs blocked by this

    # Resource Requirements
    required_technician_skills = Column(JSONB, default=list)
    required_equipment = Column(JSONB, default=list)
    estimated_duration_minutes = Column(Integer)

    # Status
    is_active = Column(Boolean, default=True, index=True)
    is_urgent = Column(Boolean, default=False)
    customer_waiting = Column(Boolean, default=False)

    # Processing
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    service_provisioning = relationship("ServiceProvisioning")

    def __repr__(self):
        return f"<ProvisioningQueue {self.service_provisioning_id}: Priority {self.priority}>"

    @property
    def wait_time_hours(self):
        """Calculate how long item has been waiting in queue"""
        if self.started_at:
            return 0  # Already started

        now = datetime.now(self.created_at.tzinfo)
        return round((now - self.created_at).total_seconds() / 3600, 2)

    @property
    def is_overdue(self):
        """Check if provisioning is overdue based on SLA"""
        if not self.estimated_completion:
            return False

        now = datetime.now(self.estimated_completion.tzinfo)
        return now > self.estimated_completion and not self.completed_at


# Performance indexes
# Index already imported at the top of the file

# Service provisioning indexes
Index("idx_provisioning_status", ServiceProvisioning.status)
Index("idx_provisioning_scheduled", ServiceProvisioning.scheduled_activation)
Index("idx_provisioning_technician", ServiceProvisioning.assigned_technician)
Index(
    "idx_provisioning_progress",
    ServiceProvisioning.status,
    ServiceProvisioning.provisioning_started,
)

# Provisioning queue indexes
Index(
    "idx_queue_active_priority", ProvisioningQueue.is_active, ProvisioningQueue.priority
)
Index("idx_queue_scheduled", ProvisioningQueue.scheduled_for)
Index("idx_queue_urgent", ProvisioningQueue.is_urgent, ProvisioningQueue.priority)
