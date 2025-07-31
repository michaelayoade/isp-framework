"""
ISP Framework - Complete Customer Portal Module
Full self-service portal for ISP customers with billing, payments, and service management
Single-tenant system with reseller support, comprehensive customer self-service
"""

import secrets
from datetime import datetime

from sqlalchemy import (
    ARRAY,
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
from sqlalchemy.dialects.postgresql import INET, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class CustomerPortalSession(Base):
    """Customer portal authentication sessions"""

    __tablename__ = "customer_portal_sessions"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(
        Integer,
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Session Information
    session_token = Column(String(255), unique=True, nullable=False, index=True)
    session_type = Column(String(50), default="web")  # web, mobile, api
    device_info = Column(JSONB, default={})  # Browser, OS, device details

    # Security
    ip_address = Column(INET)
    user_agent = Column(Text)
    two_factor_verified = Column(Boolean, default=False)

    # Session Status
    is_active = Column(Boolean, default=True)
    last_activity = Column(DateTime(timezone=True), server_default=func.now())
    login_method = Column(String(50))  # password, oauth, api_key

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    logged_out_at = Column(DateTime(timezone=True))

    # Relationships
    customer = relationship("Customer")

    @classmethod
    def generate_session_token(cls):
        """Generate secure session token"""
        return secrets.token_urlsafe(32)


class CustomerPortalPreferences(Base):
    """Customer portal preferences and settings"""

    __tablename__ = "customer_portal_preferences"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(
        Integer,
        ForeignKey("customers.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )

    # Portal Appearance
    theme = Column(String(50), default="default")  # default, dark, light
    language = Column(String(10), default="en")  # en, fr, es, etc.
    timezone = Column(String(50), default="UTC")
    date_format = Column(String(20), default="YYYY-MM-DD")

    # Dashboard Configuration
    dashboard_widgets = Column(JSONB, default=[])  # Enabled dashboard widgets
    default_page = Column(String(100), default="dashboard")

    # Notification Preferences
    email_notifications = Column(Boolean, default=True)
    sms_notifications = Column(Boolean, default=False)

    # Specific Notification Types
    ticket_updates = Column(Boolean, default=True)
    service_alerts = Column(Boolean, default=True)
    billing_notifications = Column(Boolean, default=True)
    payment_reminders = Column(Boolean, default=True)
    invoice_ready = Column(Boolean, default=True)
    maintenance_notices = Column(Boolean, default=True)
    promotional_emails = Column(Boolean, default=False)

    # Communication Preferences
    preferred_contact_method = Column(String(50), default="email")
    contact_hours_start = Column(String(10), default="09:00")
    contact_hours_end = Column(String(10), default="18:00")

    # Security Settings
    session_timeout_minutes = Column(Integer, default=60)
    require_2fa = Column(Boolean, default=False)
    login_notifications = Column(Boolean, default=True)

    # Data & Privacy
    data_usage_alerts = Column(Boolean, default=True)
    usage_alert_threshold = Column(Integer, default=80)  # Percentage
    auto_pay_enabled = Column(Boolean, default=False)
    paperless_billing = Column(Boolean, default=False)

    # Framework Integration
    custom_preferences = Column(JSONB, default={})

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    customer = relationship("Customer")


class CustomerPortalPayment(Base):
    """Customer payment processing through portal"""

    __tablename__ = "customer_portal_payments"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(
        Integer,
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Payment Information
    payment_amount = Column(DECIMAL(10, 2), nullable=False)
    currency = Column(String(3), default="USD")
    payment_method = Column(
        String(100), nullable=False
    )  # credit_card, bank_transfer, mobile_money

    # Payment Details
    payment_reference = Column(String(255), unique=True, nullable=False)
    external_payment_id = Column(String(255))  # Payment gateway reference
    payment_gateway = Column(String(100))  # stripe, paystack, flutterwave

    # Payment Status
    status = Column(
        String(50), default="pending"
    )  # pending, processing, completed, failed, cancelled
    failure_reason = Column(Text)
    gateway_response = Column(JSONB, default={})

    # Related Records
    invoice_ids = Column(ARRAY(Integer), default=[])  # Invoices being paid
    credit_applied = Column(DECIMAL(10, 2), default=0)  # Account credit used

    # Payment Method Details (encrypted/tokenized)
    payment_method_token = Column(String(255))  # Tokenized payment method
    last_four_digits = Column(String(4))  # For display purposes
    card_brand = Column(String(50))  # visa, mastercard, etc.

    # Customer Information
    billing_name = Column(String(255))
    billing_email = Column(String(255))
    billing_address = Column(JSONB, default={})

    # Processing Information
    processed_at = Column(DateTime(timezone=True))
    processor_fee = Column(DECIMAL(10, 2), default=0)
    net_amount = Column(DECIMAL(10, 2))  # Amount after fees

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    customer = relationship("Customer")

    @property
    def is_successful(self):
        """Check if payment was successful"""
        return self.status == "completed"


class CustomerPortalAutoPayment(Base):
    """Customer auto-payment configuration"""

    __tablename__ = "customer_portal_autopay"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(
        Integer,
        ForeignKey("customers.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )

    # Auto-payment Configuration
    is_enabled = Column(Boolean, default=False)
    payment_method_token = Column(String(255), nullable=False)
    payment_method_type = Column(String(100), nullable=False)
    last_four_digits = Column(String(4))
    card_brand = Column(String(50))

    # Payment Settings
    auto_pay_amount_type = Column(
        String(50), default="full_balance"
    )  # full_balance, minimum_due, fixed_amount
    fixed_amount = Column(DECIMAL(10, 2))  # If amount_type is fixed_amount

    # Timing
    auto_pay_day = Column(Integer, default=5)  # Day of month (1-28)
    advance_notice_days = Column(Integer, default=5)  # Days before auto-pay to notify

    # Limits & Controls
    max_payment_amount = Column(DECIMAL(10, 2))  # Maximum auto-payment amount
    require_confirmation = Column(
        Boolean, default=False
    )  # Require customer confirmation

    # Status
    last_payment_id = Column(Integer, ForeignKey("customer_portal_payments.id"))
    last_payment_date = Column(DateTime(timezone=True))
    next_payment_date = Column(DateTime(timezone=True))
    failure_count = Column(Integer, default=0)
    suspended_until = Column(DateTime(timezone=True))  # If suspended due to failures

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    customer = relationship("Customer")
    last_payment = relationship("CustomerPortalPayment")


class CustomerPortalServiceRequest(Base):
    """Customer service change requests through portal"""

    __tablename__ = "customer_portal_service_requests"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(
        Integer,
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Request Information
    request_type = Column(
        String(100), nullable=False
    )  # upgrade, downgrade, add_service, cancel_service, suspend_service
    request_title = Column(String(255), nullable=False)
    request_description = Column(Text)

    # Service Context
    current_service_id = Column(Integer, ForeignKey("customer_services.id"))
    requested_tariff_id = Column(Integer, ForeignKey("tariffs.id"))
    requested_add_ons = Column(JSONB, default=[])  # Additional services/features

    # Request Details
    preferred_date = Column(DateTime(timezone=True))  # When customer wants change
    urgency = Column(String(50), default="normal")  # low, normal, high
    reason = Column(Text)  # Why they want the change

    # Pricing Information
    estimated_monthly_change = Column(DECIMAL(10, 2))  # Estimated monthly cost change
    one_time_fees = Column(DECIMAL(10, 2), default=0)  # Setup/change fees
    requires_technician = Column(Boolean, default=False)

    # Status
    status = Column(
        String(100), default="submitted"
    )  # submitted, reviewing, approved, rejected, scheduled, completed
    admin_notes = Column(Text)  # Internal admin notes
    customer_notes = Column(Text)  # Additional customer info

    # Processing
    assigned_to = Column(Integer, ForeignKey("administrators.id"))
    reviewed_at = Column(DateTime(timezone=True))
    review_notes = Column(Text)

    # Related Records
    created_ticket_id = Column(Integer)
    generated_quote_id = Column(Integer)  # If quote generated

    # Approval Workflow
    requires_approval = Column(Boolean, default=True)
    approved_by = Column(Integer, ForeignKey("administrators.id"))
    approved_at = Column(DateTime(timezone=True))
    rejection_reason = Column(Text)

    # Scheduling
    scheduled_date = Column(DateTime(timezone=True))
    technician_assigned = Column(Integer, ForeignKey("administrators.id"))
    installation_notes = Column(Text)

    # Customer Communication
    customer_notified = Column(Boolean, default=False)
    notification_sent_at = Column(DateTime(timezone=True))

    # Framework Integration
    custom_fields = Column(JSONB, default={})

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True))

    # Relationships
    customer = relationship("Customer")
    current_service = relationship("CustomerService")
    requested_tariff = relationship("Tariff")
    assigned_admin = relationship("Administrator", foreign_keys=[assigned_to])
    approver = relationship("Administrator", foreign_keys=[approved_by])
    technician = relationship("Administrator", foreign_keys=[technician_assigned])


class CustomerPortalInvoiceView(Base):
    """Customer view of invoices with portal-specific data"""

    __tablename__ = "customer_portal_invoice_views"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(
        Integer,
        ForeignKey("invoices.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    customer_id = Column(
        Integer, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False
    )

    # Customer View Settings
    is_viewed = Column(Boolean, default=False)
    first_viewed_at = Column(DateTime(timezone=True))
    view_count = Column(Integer, default=0)

    # Payment Tracking
    payment_reminded = Column(Boolean, default=False)
    last_reminder_sent = Column(DateTime(timezone=True))
    reminder_count = Column(Integer, default=0)

    # Dispute/Question Tracking
    has_customer_questions = Column(Boolean, default=False)
    customer_notes = Column(Text)
    dispute_raised = Column(Boolean, default=False)
    dispute_reason = Column(Text)

    # Download Tracking
    pdf_downloaded = Column(Boolean, default=False)
    download_count = Column(Integer, default=0)
    last_downloaded = Column(DateTime(timezone=True))

    # Framework Integration
    custom_fields = Column(JSONB, default={})

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    invoice = relationship("Invoice")
    customer = relationship("Customer")

    def mark_as_viewed(self):
        """Mark invoice as viewed by customer"""
        if not self.is_viewed:
            self.is_viewed = True
            self.first_viewed_at = datetime.now()
        self.view_count += 1


class CustomerPortalUsageView(Base):
    """Customer usage data views and summaries"""

    __tablename__ = "customer_portal_usage_views"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(
        Integer,
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    service_id = Column(
        Integer,
        ForeignKey("customer_services.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Usage Period
    usage_period = Column(
        String(50), nullable=False
    )  # daily, weekly, monthly, billing_cycle
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)

    # Data Usage
    data_uploaded_mb = Column(DECIMAL(15, 2), default=0)
    data_downloaded_mb = Column(DECIMAL(15, 2), default=0)
    total_data_usage_mb = Column(DECIMAL(15, 2), default=0)

    # Usage Metrics
    peak_usage_time = Column(DateTime(timezone=True))
    peak_usage_mb = Column(DECIMAL(10, 2), default=0)
    average_daily_usage_mb = Column(DECIMAL(10, 2), default=0)

    # Service Limits
    data_quota_mb = Column(DECIMAL(15, 2))  # Data allowance for period
    quota_used_percentage = Column(DECIMAL(5, 2), default=0)
    quota_remaining_mb = Column(DECIMAL(15, 2), default=0)

    # Speed Metrics
    average_download_speed_mbps = Column(DECIMAL(10, 2))
    average_upload_speed_mbps = Column(DECIMAL(10, 2))
    peak_download_speed_mbps = Column(DECIMAL(10, 2))
    peak_upload_speed_mbps = Column(DECIMAL(10, 2))

    # Connection Quality
    uptime_percentage = Column(DECIMAL(5, 2), default=100)
    connection_drops = Column(Integer, default=0)
    average_latency_ms = Column(DECIMAL(10, 2))

    # Top Usage Categories (if available)
    top_categories = Column(
        JSONB, default=[]
    )  # [{"category": "streaming", "usage_mb": 1500}, ...]

    # Alerts & Warnings
    exceeded_quota = Column(Boolean, default=False)
    quota_warning_sent = Column(Boolean, default=False)
    throttling_applied = Column(Boolean, default=False)

    # Framework Integration
    additional_metrics = Column(JSONB, default={})

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    customer = relationship("Customer")
    service = relationship("CustomerService")

    @property
    def is_over_quota(self):
        """Check if usage exceeds quota"""
        return self.quota_used_percentage > 100

    @property
    def days_remaining_in_period(self):
        """Calculate days remaining in period"""
        if self.period_end > datetime.now():
            delta = self.period_end - datetime.now()
            return delta.days
        return 0


class CustomerPortalNotification(Base):
    """In-portal notifications for customers"""

    __tablename__ = "customer_portal_notifications"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(
        Integer,
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Notification Content
    notification_type = Column(
        String(100), nullable=False
    )  # ticket_update, payment_due, service_alert, etc.
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)

    # Notification Properties
    priority = Column(String(20), default="normal")  # low, normal, high, urgent
    category = Column(String(100))  # support, billing, technical, account

    # Related Objects
    related_service_id = Column(Integer, ForeignKey("customer_services.id"))
    related_invoice_id = Column(Integer, ForeignKey("invoices.id"))
    related_payment_id = Column(Integer, ForeignKey("customer_portal_payments.id"))

    # Action Information
    action_required = Column(Boolean, default=False)
    action_url = Column(String(500))
    action_text = Column(String(100))

    # Status
    is_read = Column(Boolean, default=False)
    is_dismissed = Column(Boolean, default=False)
    auto_dismiss_at = Column(DateTime(timezone=True))

    # Delivery Tracking
    email_sent = Column(Boolean, default=False)
    sms_sent = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    read_at = Column(DateTime(timezone=True))
    dismissed_at = Column(DateTime(timezone=True))

    # Relationships
    customer = relationship("Customer")
    related_service = relationship("CustomerService")
    related_invoice = relationship("Invoice")
    related_payment = relationship("CustomerPortalPayment")


class CustomerPortalFAQ(Base):
    """Customer portal FAQ system"""

    __tablename__ = "customer_portal_faqs"

    id = Column(Integer, primary_key=True, index=True)

    # FAQ Content
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    answer_format = Column(String(20), default="html")

    # Organization
    category = Column(String(100), index=True)  # billing, technical, account, general
    subcategory = Column(String(100))
    tags = Column(ARRAY(String), default=[])

    # Display
    display_order = Column(Integer, default=0)
    is_featured = Column(Boolean, default=False)

    # Content Management
    author_id = Column(Integer, ForeignKey("administrators.id"))

    # Status
    status = Column(String(50), default="published")
    is_public = Column(Boolean, default=True)

    # Usage Statistics
    view_count = Column(Integer, default=0)
    helpful_votes = Column(Integer, default=0)
    not_helpful_votes = Column(Integer, default=0)

    # Search Optimization
    keywords = Column(ARRAY(String), default=[])
    search_terms = Column(Text)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    author = relationship("Administrator")


class CustomerPortalActivity(Base):
    """Track customer portal activity"""

    __tablename__ = "customer_portal_activity"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(
        Integer,
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    session_id = Column(Integer, ForeignKey("customer_portal_sessions.id"))

    # Activity Information
    activity_type = Column(String(100), nullable=False)
    page_url = Column(String(500))
    action_description = Column(Text)

    # Request Information
    ip_address = Column(INET)
    user_agent = Column(Text)
    request_method = Column(String(10))

    # Context Data
    related_object_type = Column(String(100))
    related_object_id = Column(Integer)
    additional_data = Column(JSONB, default={})

    # Performance
    response_time_ms = Column(Integer)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships
    customer = relationship("Customer")
    session = relationship("CustomerPortalSession")


# Performance indexes
Index(
    "idx_portal_sessions_customer",
    CustomerPortalSession.customer_id,
    CustomerPortalSession.is_active,
)
Index("idx_portal_sessions_token", CustomerPortalSession.session_token)
Index(
    "idx_portal_payments_customer",
    CustomerPortalPayment.customer_id,
    CustomerPortalPayment.status,
)
Index("idx_portal_payments_reference", CustomerPortalPayment.payment_reference)
Index(
    "idx_portal_payments_status",
    CustomerPortalPayment.status,
    CustomerPortalPayment.created_at,
)
Index(
    "idx_portal_service_requests_customer",
    CustomerPortalServiceRequest.customer_id,
    CustomerPortalServiceRequest.status,
)
Index(
    "idx_portal_service_requests_status",
    CustomerPortalServiceRequest.status,
    CustomerPortalServiceRequest.created_at,
)
Index("idx_portal_invoice_views_customer", CustomerPortalInvoiceView.customer_id)
Index("idx_portal_invoice_views_invoice", CustomerPortalInvoiceView.invoice_id)
Index(
    "idx_portal_usage_customer_period",
    CustomerPortalUsageView.customer_id,
    CustomerPortalUsageView.usage_period,
)
Index(
    "idx_portal_usage_service_period",
    CustomerPortalUsageView.service_id,
    CustomerPortalUsageView.period_start,
)
Index(
    "idx_portal_notifications_customer",
    CustomerPortalNotification.customer_id,
    CustomerPortalNotification.is_read,
)
Index(
    "idx_portal_notifications_type",
    CustomerPortalNotification.notification_type,
    CustomerPortalNotification.created_at,
)
