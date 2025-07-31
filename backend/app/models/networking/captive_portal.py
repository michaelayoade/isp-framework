"""Captive portal models for customer authentication and payment flows."""

from sqlalchemy import (
    DECIMAL,
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base


class CaptivePortalSettings(Base):
    """Global captive portal configuration settings."""

    __tablename__ = "captive_portal_settings"

    id = Column(Integer, primary_key=True, index=True)

    # Portal Branding
    portal_title = Column(String(255), default="ISP Customer Portal")
    company_name = Column(String(255), nullable=False)
    logo_url = Column(String(500), nullable=True)
    favicon_url = Column(String(500), nullable=True)

    # Theme and Styling
    primary_color = Column(String(7), default="#3B82F6")  # Hex color
    secondary_color = Column(String(7), default="#64748B")
    background_color = Column(String(7), default="#F8FAFC")
    custom_css = Column(Text, nullable=True)

    # Portal URLs
    portal_domain = Column(String(255), nullable=False)
    success_redirect_url = Column(String(500), nullable=True)
    terms_url = Column(String(500), nullable=True)
    privacy_url = Column(String(500), nullable=True)
    support_url = Column(String(500), nullable=True)

    # Session Settings
    session_timeout_minutes = Column(Integer, default=60)
    grace_period_minutes = Column(Integer, default=5)
    max_concurrent_sessions = Column(Integer, default=3)

    # Payment Integration
    payment_gateway = Column(
        String(50), nullable=True
    )  # stripe, paystack, flutterwave, etc.
    payment_config = Column(JSON, default=dict)  # Gateway-specific configuration

    # Content and Messages
    welcome_message = Column(Text, nullable=True)
    payment_instructions = Column(Text, nullable=True)
    maintenance_message = Column(Text, nullable=True)

    # Features
    enable_voucher_payments = Column(Boolean, default=True)
    enable_card_payments = Column(Boolean, default=True)
    enable_bank_transfer = Column(Boolean, default=False)
    enable_mobile_money = Column(Boolean, default=False)
    enable_guest_access = Column(Boolean, default=False)
    guest_access_duration_minutes = Column(Integer, default=30)

    # Status
    is_active = Column(Boolean, default=True)
    maintenance_mode = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return (
            f"<CaptivePortalSettings(id={self.id}, company_name={self.company_name})>"
        )


class CaptivePortalSession(Base):
    """Captive portal user sessions."""

    __tablename__ = "captive_portal_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), nullable=False, unique=True, index=True)

    # Client Information
    client_mac = Column(String(17), nullable=False, index=True)
    client_ip = Column(String(45), nullable=False, index=True)
    user_agent = Column(Text, nullable=True)

    # Customer Information (if authenticated)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True, index=True)
    service_id = Column(
        Integer, ForeignKey("customer_services.id"), nullable=True, index=True
    )

    # Session Status
    status = Column(
        String(20), nullable=False, default="pending"
    )  # pending, authenticated, expired, terminated
    auth_method = Column(
        String(20), nullable=True
    )  # voucher, payment, guest, credentials

    # Network Information
    nas_identifier = Column(String(255), nullable=True)
    nas_port = Column(String(50), nullable=True)
    original_url = Column(String(1000), nullable=True)  # URL user was trying to access

    # Session Timing
    start_time = Column(DateTime(timezone=True), server_default=func.now())
    auth_time = Column(DateTime(timezone=True), nullable=True)
    last_activity = Column(DateTime(timezone=True), server_default=func.now())
    end_time = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)

    # Usage Tracking
    bytes_downloaded = Column(Integer, default=0)
    bytes_uploaded = Column(Integer, default=0)
    pages_visited = Column(Integer, default=0)

    # Payment Information (if applicable)
    payment_id = Column(Integer, ForeignKey("payments.id"), nullable=True)
    amount_paid = Column(DECIMAL(10, 2), nullable=True)

    # Relationships
    customer = relationship("Customer")
    service = relationship("CustomerService")
    # payment = relationship("Payment")  # Uncomment when payment model is available

    # Indexes for performance
    __table_args__ = (
        Index("idx_session_mac_status", "client_mac", "status"),
        Index("idx_session_customer_status", "customer_id", "status"),
        Index("idx_session_start_time", "start_time"),
        Index("idx_session_expires_at", "expires_at"),
    )

    def __repr__(self):
        return f"<CaptivePortalSession(id={self.id}, session_id={self.session_id}, status={self.status})>"

    @property
    def is_active(self) -> bool:
        """Check if session is currently active."""
        return self.status == "authenticated" and (
            self.expires_at is None or self.expires_at > func.now()
        )

    @property
    def duration_minutes(self) -> int:
        """Calculate session duration in minutes."""
        if self.end_time:
            return int((self.end_time - self.start_time).total_seconds() / 60)
        return int((func.now() - self.start_time).total_seconds() / 60)


class CaptivePortalVoucher(Base):
    """Vouchers for captive portal access."""

    __tablename__ = "captive_portal_vouchers"

    id = Column(Integer, primary_key=True, index=True)
    voucher_code = Column(String(50), nullable=False, unique=True, index=True)

    # Voucher Details
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Access Configuration
    duration_minutes = Column(Integer, nullable=False)  # How long access lasts
    data_limit_mb = Column(Integer, nullable=True)  # Data limit in MB
    speed_limit_kbps = Column(Integer, nullable=True)  # Speed limit in kbps

    # Pricing
    price = Column(DECIMAL(10, 2), nullable=False)
    currency = Column(String(3), default="NGN")

    # Usage Limits
    max_uses = Column(Integer, default=1)  # How many times voucher can be used
    current_uses = Column(Integer, default=0)
    max_concurrent_sessions = Column(Integer, default=1)

    # Validity Period
    valid_from = Column(DateTime(timezone=True), server_default=func.now())
    valid_until = Column(DateTime(timezone=True), nullable=True)

    # Status
    is_active = Column(Boolean, default=True)
    is_reusable = Column(Boolean, default=False)

    # Creation Info
    created_by = Column(Integer, ForeignKey("administrators.id"), nullable=True)
    batch_id = Column(String(100), nullable=True, index=True)  # For bulk generation

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    creator = relationship("Administrator", foreign_keys=[created_by])
    sessions = relationship("CaptivePortalVoucherUsage", back_populates="voucher")

    def __repr__(self):
        return f"<CaptivePortalVoucher(id={self.id}, code={self.voucher_code}, price={self.price})>"

    @property
    def is_valid(self) -> bool:
        """Check if voucher is currently valid."""
        now = func.now()
        return (
            self.is_active
            and self.current_uses < self.max_uses
            and self.valid_from <= now
            and (self.valid_until is None or self.valid_until >= now)
        )

    @property
    def remaining_uses(self) -> int:
        """Calculate remaining uses for the voucher."""
        return max(0, self.max_uses - self.current_uses)


class CaptivePortalVoucherUsage(Base):
    """Track voucher usage in captive portal sessions."""

    __tablename__ = "captive_portal_voucher_usage"

    id = Column(Integer, primary_key=True, index=True)
    voucher_id = Column(
        Integer, ForeignKey("captive_portal_vouchers.id"), nullable=False, index=True
    )
    session_id = Column(
        Integer, ForeignKey("captive_portal_sessions.id"), nullable=False, index=True
    )

    # Usage Details
    used_at = Column(DateTime(timezone=True), server_default=func.now())
    client_mac = Column(String(17), nullable=False)
    client_ip = Column(String(45), nullable=False)

    # Session Results
    duration_minutes = Column(Integer, default=0)
    data_used_mb = Column(Integer, default=0)

    # Relationships
    voucher = relationship("CaptivePortalVoucher", back_populates="sessions")
    session = relationship("CaptivePortalSession")

    def __repr__(self):
        return f"<CaptivePortalVoucherUsage(id={self.id}, voucher_id={self.voucher_id}, session_id={self.session_id})>"


class CaptivePortalPayment(Base):
    """Payment transactions for captive portal access."""

    __tablename__ = "captive_portal_payments"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String(255), nullable=False, unique=True, index=True)

    # Customer Information
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True, index=True)
    session_id = Column(
        Integer, ForeignKey("captive_portal_sessions.id"), nullable=False, index=True
    )

    # Payment Details
    amount = Column(DECIMAL(10, 2), nullable=False)
    currency = Column(String(3), default="NGN")
    payment_method = Column(
        String(50), nullable=False
    )  # card, bank_transfer, mobile_money

    # Gateway Information
    gateway = Column(String(50), nullable=False)  # stripe, paystack, flutterwave
    gateway_transaction_id = Column(String(255), nullable=True)
    gateway_reference = Column(String(255), nullable=True)
    gateway_response = Column(JSON, default=dict)

    # Payment Status
    status = Column(
        String(20), nullable=False, default="pending"
    )  # pending, completed, failed, refunded

    # Service Configuration (what was purchased)
    access_duration_minutes = Column(Integer, nullable=False)
    data_limit_mb = Column(Integer, nullable=True)
    speed_limit_kbps = Column(Integer, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    customer = relationship("Customer")
    session = relationship("CaptivePortalSession")

    def __repr__(self):
        return f"<CaptivePortalPayment(id={self.id}, transaction_id={self.transaction_id}, amount={self.amount}, status={self.status})>"

    @property
    def is_successful(self) -> bool:
        """Check if payment was successful."""
        return self.status == "completed"


class CaptivePortalTemplate(Base):
    """Custom templates for captive portal pages."""

    __tablename__ = "captive_portal_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=True)

    # Template Content
    template_type = Column(
        String(50), nullable=False
    )  # login, payment, success, error, terms
    html_content = Column(Text, nullable=False)
    css_content = Column(Text, nullable=True)
    js_content = Column(Text, nullable=True)

    # Template Variables (JSON schema for dynamic content)
    variables_schema = Column(JSON, default=dict)

    # Status
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)

    # Version Control
    version = Column(String(20), default="1.0")

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<CaptivePortalTemplate(id={self.id}, name={self.name}, type={self.template_type})>"
