"""
Dunning Management System

Automated dunning process for overdue accounts with escalation workflows,
communication tracking, and comprehensive collection management.
"""

from datetime import datetime, timedelta, timezone

from sqlalchemy import (
    DECIMAL,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..base import Base
from .enums import DeliveryStatus, DunningActionType, DunningStatus, EscalationLevel


class DunningCase(Base):
    """Dunning cases for overdue account management"""

    __tablename__ = "dunning_cases"

    id = Column(Integer, primary_key=True, index=True)
    case_number = Column(String(50), unique=True, nullable=False, index=True)
    billing_account_id = Column(
        Integer, ForeignKey("customer_billing_accounts.id"), nullable=False
    )

    # Case details
    total_overdue_amount = Column(DECIMAL(12, 2), nullable=False)
    oldest_overdue_date = Column(DateTime(timezone=True), nullable=False)
    days_overdue = Column(Integer, nullable=False)

    # Status and workflow
    status = Column(
        SQLEnum(DunningStatus), nullable=False, default=DunningStatus.ACTIVE, index=True
    )
    current_stage = Column(Integer, default=1)  # Dunning stage (1, 2, 3, etc.)
    escalation_level = Column(
        SQLEnum(EscalationLevel), default=EscalationLevel.LOW, index=True
    )

    # Dates
    created_date = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    last_action_date = Column(DateTime(timezone=True))
    next_action_date = Column(DateTime(timezone=True))
    resolved_date = Column(DateTime(timezone=True))

    # Assignment
    assigned_to = Column(Integer, ForeignKey("administrators.id"))

    # Automation settings
    auto_escalate = Column(Boolean, default=True)
    auto_suspend = Column(Boolean, default=True)
    auto_terminate = Column(Boolean, default=False)

    # Thresholds
    suspension_threshold = Column(DECIMAL(12, 2))
    termination_threshold = Column(DECIMAL(12, 2))

    # Communication preferences
    preferred_contact_method = Column(
        String(20), default="email"
    )  # email, sms, phone, letter
    contact_frequency_days = Column(Integer, default=7)

    # Metadata
    notes = Column(Text)
    additional_data = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    billing_account = relationship(
        "CustomerBillingAccount", back_populates="dunning_cases"
    )
    assigned_user = relationship("Administrator", foreign_keys=[assigned_to])
    actions = relationship(
        "DunningAction", back_populates="dunning_case", cascade="all, delete-orphan"
    )

    # Indexes
    __table_args__ = (
        Index("idx_dunning_cases_account_status", "billing_account_id", "status"),
        Index("idx_dunning_cases_stage_date", "current_stage", "next_action_date"),
    )

    def __repr__(self):
        return f"<DunningCase(id={self.id}, number='{self.case_number}', overdue={self.total_overdue_amount})>"

    @property
    def is_active(self):
        """Check if dunning case is active"""
        return self.status == DunningStatus.ACTIVE

    @property
    def is_resolved(self):
        """Check if dunning case is resolved"""
        return self.status == DunningStatus.COMPLETED

    def should_escalate(self):
        """Check if case should be escalated to next stage"""
        if not self.auto_escalate or not self.is_active:
            return False

        if not self.next_action_date:
            return True

        return datetime.now(timezone.utc) >= self.next_action_date

    def calculate_escalation_level(self):
        """Calculate escalation level based on amount and days overdue"""
        if self.total_overdue_amount >= 1000 or self.days_overdue >= 60:
            return EscalationLevel.CRITICAL
        elif self.total_overdue_amount >= 500 or self.days_overdue >= 30:
            return EscalationLevel.HIGH
        elif self.total_overdue_amount >= 100 or self.days_overdue >= 14:
            return EscalationLevel.MEDIUM
        else:
            return EscalationLevel.LOW

    def escalate_to_next_stage(self):
        """Escalate case to next stage"""
        self.current_stage += 1
        self.escalation_level = self.calculate_escalation_level()
        self.last_action_date = datetime.now(timezone.utc)

        # Set next action date based on escalation level
        if self.escalation_level == EscalationLevel.CRITICAL:
            self.next_action_date = datetime.now(timezone.utc) + timedelta(days=1)
        elif self.escalation_level == EscalationLevel.HIGH:
            self.next_action_date = datetime.now(timezone.utc) + timedelta(days=3)
        else:
            self.next_action_date = datetime.now(timezone.utc) + timedelta(
                days=self.contact_frequency_days
            )

    def resolve_case(self, resolution_notes=None):
        """Resolve the dunning case"""
        self.status = DunningStatus.COMPLETED
        self.resolved_date = datetime.now(timezone.utc)
        if resolution_notes:
            self.notes = (
                f"{self.notes}\nResolved: {resolution_notes}"
                if self.notes
                else f"Resolved: {resolution_notes}"
            )

    def pause_case(self, reason=None):
        """Pause the dunning case"""
        self.status = DunningStatus.PAUSED
        if reason:
            self.notes = (
                f"{self.notes}\nPaused: {reason}" if self.notes else f"Paused: {reason}"
            )

    def resume_case(self):
        """Resume the dunning case"""
        self.status = DunningStatus.ACTIVE
        self.next_action_date = datetime.now(timezone.utc) + timedelta(days=1)

    def get_case_summary(self):
        """Get comprehensive dunning case summary"""
        return {
            "case_number": self.case_number,
            "status": self.status.value,
            "current_stage": self.current_stage,
            "escalation_level": self.escalation_level.value,
            "total_overdue_amount": float(self.total_overdue_amount),
            "days_overdue": self.days_overdue,
            "oldest_overdue_date": self.oldest_overdue_date.isoformat(),
            "created_date": self.created_date.isoformat(),
            "last_action_date": (
                self.last_action_date.isoformat() if self.last_action_date else None
            ),
            "next_action_date": (
                self.next_action_date.isoformat() if self.next_action_date else None
            ),
            "resolved_date": (
                self.resolved_date.isoformat() if self.resolved_date else None
            ),
            "preferred_contact_method": self.preferred_contact_method,
            "contact_frequency_days": self.contact_frequency_days,
            "auto_escalate": self.auto_escalate,
            "auto_suspend": self.auto_suspend,
            "auto_terminate": self.auto_terminate,
            "is_active": self.is_active,
            "is_resolved": self.is_resolved,
            "should_escalate": self.should_escalate(),
        }


class DunningAction(Base):
    """Individual dunning actions taken"""

    __tablename__ = "dunning_actions"

    id = Column(Integer, primary_key=True, index=True)
    dunning_case_id = Column(Integer, ForeignKey("dunning_cases.id"), nullable=False)

    # Action details
    action_type = Column(SQLEnum(DunningActionType), nullable=False, index=True)
    action_date = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    stage = Column(Integer, nullable=False)

    # Content
    subject = Column(String(200))
    message = Column(Text)
    template_used = Column(String(100))

    # Delivery
    delivery_method = Column(String(50))  # email, sms, postal, phone
    delivery_address = Column(String(200))
    delivery_status = Column(
        SQLEnum(DeliveryStatus), default=DeliveryStatus.PENDING, index=True
    )
    delivery_date = Column(DateTime(timezone=True))

    # Response tracking
    customer_response = Column(Text)
    response_date = Column(DateTime(timezone=True))

    # Automation
    is_automated = Column(Boolean, default=False)

    # Staff
    performed_by = Column(Integer, ForeignKey("administrators.id"))

    # Metadata
    additional_data = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    dunning_case = relationship("DunningCase", back_populates="actions")
    performer = relationship("Administrator", foreign_keys=[performed_by])

    def __repr__(self):
        return f"<DunningAction(id={self.id}, type='{self.action_type}', stage={self.stage})>"

    @property
    def is_delivered(self):
        """Check if action was delivered"""
        return self.delivery_status == DeliveryStatus.DELIVERED

    @property
    def is_failed(self):
        """Check if action delivery failed"""
        return self.delivery_status in [DeliveryStatus.FAILED, DeliveryStatus.BOUNCED]

    def mark_as_delivered(self):
        """Mark action as delivered"""
        self.delivery_status = DeliveryStatus.DELIVERED
        self.delivery_date = datetime.now(timezone.utc)

    def mark_as_failed(self, failure_reason=None):
        """Mark action as failed"""
        self.delivery_status = DeliveryStatus.FAILED
        if failure_reason:
            self.additional_data = self.additional_data or {}
            self.additional_data["failure_reason"] = failure_reason

    def record_customer_response(self, response):
        """Record customer response to action"""
        self.customer_response = response
        self.response_date = datetime.now(timezone.utc)

    def get_action_summary(self):
        """Get action summary"""
        return {
            "action_type": self.action_type.value,
            "action_date": self.action_date.isoformat(),
            "stage": self.stage,
            "subject": self.subject,
            "delivery_method": self.delivery_method,
            "delivery_status": self.delivery_status.value,
            "delivery_date": (
                self.delivery_date.isoformat() if self.delivery_date else None
            ),
            "is_delivered": self.is_delivered,
            "is_failed": self.is_failed,
            "is_automated": self.is_automated,
            "customer_response": self.customer_response,
            "response_date": (
                self.response_date.isoformat() if self.response_date else None
            ),
        }


class DunningTemplate(Base):
    """Templates for dunning communications"""

    __tablename__ = "dunning_templates"

    id = Column(Integer, primary_key=True, index=True)
    template_name = Column(String(100), nullable=False, unique=True)
    action_type = Column(SQLEnum(DunningActionType), nullable=False)
    stage = Column(Integer, nullable=False)

    # Template configuration
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)

    # Content
    subject_template = Column(String(200), nullable=False)
    message_template = Column(Text, nullable=False)

    # Delivery settings
    delivery_method = Column(String(50), nullable=False)
    priority = Column(String(20), default="normal")  # low, normal, high, urgent

    # Automation
    auto_send = Column(Boolean, default=False)
    send_delay_hours = Column(Integer, default=0)

    # Conditions
    minimum_amount = Column(DECIMAL(12, 2))
    maximum_amount = Column(DECIMAL(12, 2))
    minimum_days_overdue = Column(Integer)

    # Metadata
    description = Column(Text)
    created_by = Column(Integer, ForeignKey("administrators.id"))
    additional_data = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    creator = relationship("Administrator", foreign_keys=[created_by])

    def __repr__(self):
        return f"<DunningTemplate(id={self.id}, name='{self.template_name}', stage={self.stage})>"

    def is_applicable(self, overdue_amount, days_overdue):
        """Check if template is applicable for given conditions"""
        if self.minimum_amount and overdue_amount < self.minimum_amount:
            return False
        if self.maximum_amount and overdue_amount > self.maximum_amount:
            return False
        if self.minimum_days_overdue and days_overdue < self.minimum_days_overdue:
            return False
        return True

    def generate_content(self, **kwargs):
        """Generate content from template"""
        try:
            subject = self.subject_template.format(**kwargs)
            message = self.message_template.format(**kwargs)
            return subject, message
        except KeyError as e:
            raise ValueError(f"Missing template variable: {e}")

    def get_template_summary(self):
        """Get template configuration summary"""
        return {
            "template_name": self.template_name,
            "action_type": self.action_type.value,
            "stage": self.stage,
            "is_active": self.is_active,
            "is_default": self.is_default,
            "delivery_method": self.delivery_method,
            "priority": self.priority,
            "auto_send": self.auto_send,
            "send_delay_hours": self.send_delay_hours,
            "conditions": {
                "minimum_amount": (
                    float(self.minimum_amount) if self.minimum_amount else None
                ),
                "maximum_amount": (
                    float(self.maximum_amount) if self.maximum_amount else None
                ),
                "minimum_days_overdue": self.minimum_days_overdue,
            },
        }


class DunningRule(Base):
    """Automated dunning rules and workflows"""

    __tablename__ = "dunning_rules"

    id = Column(Integer, primary_key=True, index=True)
    rule_name = Column(String(100), nullable=False, unique=True)

    # Rule configuration
    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=100)  # Lower number = higher priority

    # Trigger conditions
    trigger_days_overdue = Column(Integer, nullable=False)
    trigger_amount_threshold = Column(DECIMAL(12, 2))
    trigger_escalation_level = Column(SQLEnum(EscalationLevel))

    # Actions to take
    action_type = Column(SQLEnum(DunningActionType), nullable=False)
    template_id = Column(Integer, ForeignKey("dunning_templates.id"))

    # Escalation settings
    escalate_after_days = Column(Integer, default=7)
    max_escalation_stage = Column(Integer, default=5)

    # Account actions
    suspend_account = Column(Boolean, default=False)
    terminate_account = Column(Boolean, default=False)
    restrict_services = Column(Boolean, default=False)

    # Automation
    auto_execute = Column(Boolean, default=True)
    execution_delay_hours = Column(Integer, default=0)

    # Metadata
    description = Column(Text)
    created_by = Column(Integer, ForeignKey("administrators.id"))
    additional_data = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    template = relationship("DunningTemplate", foreign_keys=[template_id])
    creator = relationship("Administrator", foreign_keys=[created_by])

    def __repr__(self):
        return f"<DunningRule(id={self.id}, name='{self.rule_name}')>"

    def is_triggered(self, days_overdue, overdue_amount, escalation_level):
        """Check if rule should be triggered"""
        if not self.is_active:
            return False

        # Check days overdue
        if days_overdue < self.trigger_days_overdue:
            return False

        # Check amount threshold
        if (
            self.trigger_amount_threshold
            and overdue_amount < self.trigger_amount_threshold
        ):
            return False

        # Check escalation level
        if (
            self.trigger_escalation_level
            and escalation_level != self.trigger_escalation_level
        ):
            return False

        return True

    def get_rule_summary(self):
        """Get rule configuration summary"""
        return {
            "rule_name": self.rule_name,
            "is_active": self.is_active,
            "priority": self.priority,
            "trigger_conditions": {
                "days_overdue": self.trigger_days_overdue,
                "amount_threshold": (
                    float(self.trigger_amount_threshold)
                    if self.trigger_amount_threshold
                    else None
                ),
                "escalation_level": (
                    self.trigger_escalation_level.value
                    if self.trigger_escalation_level
                    else None
                ),
            },
            "action_type": self.action_type.value,
            "escalation": {
                "escalate_after_days": self.escalate_after_days,
                "max_escalation_stage": self.max_escalation_stage,
            },
            "account_actions": {
                "suspend_account": self.suspend_account,
                "terminate_account": self.terminate_account,
                "restrict_services": self.restrict_services,
            },
            "automation": {
                "auto_execute": self.auto_execute,
                "execution_delay_hours": self.execution_delay_hours,
            },
        }
