"""
Customer-related models following ISP Framework modular architecture
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, ForeignKey, Date, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Customer(Base):
    """Core customer model"""
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    portal_id = Column(String(100), unique=True, nullable=False, index=True)  # Portal ID for RADIUS/portal/PPPoE auth
    password_hash = Column(String(255))
    status = Column(String(20), default="new")  # new, active, blocked, disabled
    reseller_id = Column(Integer, ForeignKey("resellers.id"), nullable=True)  # Optional - customers can be direct or via reseller
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    parent_id = Column(Integer, ForeignKey("customers.id"))  # for sub-accounts
    
    # Personal Information
    name = Column(String(255), nullable=False)
    email = Column(String(255), index=True)
    billing_email = Column(String(255))
    phone = Column(String(50))
    category = Column(String(20), default="person")  # person, company
    
    # Address
    address = Column(String(500))  # Full address in single field
    zip_code = Column(String(20))
    city = Column(String(100))
    subdivision_id = Column(Integer)  # state/province
    
    # Financial
    billing_type = Column(String(20), default="recurring")  # recurring, prepaid_daily, prepaid_monthly
    mrr_total = Column(Integer, default=0)  # Monthly recurring revenue in cents
    daily_prepaid_cost = Column(Integer, default=0)  # Daily cost in cents
    
    # Metadata
    gps = Column(String(100))  # latitude,longitude
    date_add = Column(DateTime(timezone=True), server_default=func.now())
    conversion_date = Column(DateTime(timezone=True))
    added_by = Column(String(20), default="admin")
    added_by_id = Column(Integer)
    last_online = Column(DateTime(timezone=True))
    last_update = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Framework Integration
    custom_fields = Column(JSON, default=dict)  # Dynamic custom fields from framework
    workflow_state = Column(JSON, default=dict)  # Current state in workflows
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    reseller = relationship("Reseller", back_populates="customers")
    services = relationship("CustomerService", back_populates="customer")
    parent = relationship("Customer", remote_side=[id])
    children = relationship("Customer", overlaps="parent")
    extended_info = relationship("CustomerExtended", back_populates="customer", uselist=False)
    info = relationship("CustomerInfo", back_populates="customer", uselist=False)
    billing_config = relationship("CustomerBilling", back_populates="customer", uselist=False)
    contacts = relationship("CustomerContact", back_populates="customer")
    label_associations = relationship("CustomerLabelAssociation", back_populates="customer")
    documents = relationship("CustomerDocument", back_populates="customer")
    billing_account = relationship("CustomerBillingAccount", back_populates="customer", uselist=False)
    payment_methods = relationship("PaymentMethod", back_populates="customer")
    tickets = relationship("Ticket", back_populates="customer")
    communications = relationship("CommunicationLog", back_populates="customer")
    communication_preferences = relationship("CommunicationPreference", back_populates="customer", uselist=False)
    # API keys for customer API access
    api_keys = relationship("APIKey", back_populates="customer", cascade="all, delete-orphan")
    # File storage for customer documents and uploads
    files = relationship("FileMetadata", back_populates="customer", cascade="all, delete-orphan")
    
    # Billing relationships (commented out until billing models are properly integrated)
    # invoices = relationship("Invoice", back_populates="customer")
    # payments = relationship("Payment", back_populates="customer")


class CustomerExtended(Base):
    """Extended customer information and preferences"""
    __tablename__ = "customers_extended"
    
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="CASCADE"), primary_key=True)
    login = Column(String(255), unique=True, index=True)  # Portal login username
    
    # Extended Information
    company_name = Column(String(255))
    tax_number = Column(String(100))
    registration_number = Column(String(100))
    
    # Preferences
    language = Column(String(10), default="en")
    timezone = Column(String(50), default="UTC")
    currency = Column(String(3), default="NGN")
    
    # Communication Preferences
    email_notifications = Column(Boolean, default=True)
    sms_notifications = Column(Boolean, default=False)
    marketing_emails = Column(Boolean, default=False)
    
    # Portal Settings
    portal_theme = Column(String(50), default="default")
    dashboard_layout = Column(JSON, default=dict)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    customer = relationship("Customer", back_populates="extended_info")


class CustomerLabel(Base):
    """Customer labels for categorization"""
    __tablename__ = "customer_labels"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    color = Column(String(7), default="#007bff")  # Hex color code
    description = Column(Text)
    is_system = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    label_associations = relationship("CustomerLabelAssociation", back_populates="label")


class CustomerLabelAssociation(Base):
    """Many-to-many relationship between customers and labels"""
    __tablename__ = "customer_label_associations"

    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="CASCADE"), primary_key=True)
    label_id = Column(Integer, ForeignKey("customer_labels.id", ondelete="CASCADE"), primary_key=True)

    # Relationships
    customer = relationship("Customer", back_populates="label_associations")
    label = relationship("CustomerLabel", back_populates="label_associations")


class CustomerInfo(Base):
    """Additional customer information"""
    __tablename__ = "customer_info"

    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="CASCADE"), primary_key=True)
    birthday = Column(Date)
    passport = Column(String(100))
    company_id = Column(String(100))
    contact_person = Column(String(255))
    vat_id = Column(String(100))
    
    # Timestamps
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    customer = relationship("Customer", back_populates="info")


class CustomerBilling(Base):
    """Customer billing configuration"""
    __tablename__ = "customer_billing"

    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="CASCADE"), primary_key=True)
    
    # Billing preferences
    billing_day = Column(Integer, default=1)  # Day of month for billing
    payment_method = Column(String(50), default="bank_transfer")
    auto_payment = Column(Boolean, default=False)
    
    # Credit and limits
    credit_limit = Column(Integer, default=0)  # In cents
    current_balance = Column(Integer, default=0)  # In cents
    
    # Tax information
    tax_exempt = Column(Boolean, default=False)
    tax_id = Column(String(100))
    
    # Billing address (can override customer address)
    billing_name = Column(String(255))
    billing_street_1 = Column(String(255))
    billing_street_2 = Column(String(255))
    billing_city = Column(String(100))
    billing_zip_code = Column(String(20))
    billing_country = Column(String(100))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    customer = relationship("Customer", back_populates="billing_config")


class CustomerContact(Base):
    """Customer contact information"""
    __tablename__ = "customer_contacts"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    
    # Contact details
    contact_type = Column(String(50), default="primary")  # primary, billing, technical, emergency
    name = Column(String(255), nullable=False)
    email = Column(String(255))
    phone = Column(String(50))
    mobile = Column(String(50))
    position = Column(String(100))  # Job title/position
    
    # Contact preferences
    is_primary = Column(Boolean, default=False)
    receive_notifications = Column(Boolean, default=True)
    receive_billing = Column(Boolean, default=False)
    receive_technical = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    customer = relationship("Customer", back_populates="contacts")


class CustomerDocument(Base):
    """Customer document attachments"""
    __tablename__ = "customer_documents"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    file_id = Column(Integer, ForeignKey("file_storage.id", ondelete="CASCADE"), nullable=False)
    
    # Document metadata
    document_type = Column(String(50), default="general")  # id_card, contract, invoice, etc.
    title = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Access control
    is_public = Column(Boolean, default=False)
    requires_approval = Column(Boolean, default=False)
    approved_by = Column(Integer, ForeignKey("administrators.id"))
    approved_at = Column(DateTime(timezone=True))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    customer = relationship("Customer", back_populates="documents")
    file = relationship("FileStorage", back_populates="customer_documents")
    approved_by_admin = relationship("Administrator")


class CustomerNote(Base):
    """Customer notes and comments"""
    __tablename__ = "customer_notes"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    
    # Note content
    title = Column(String(255))
    content = Column(Text, nullable=False)
    note_type = Column(String(50), default="general")  # general, billing, technical, support
    
    # Metadata
    is_important = Column(Boolean, default=False)
    is_internal = Column(Boolean, default=True)  # Internal notes vs customer-visible
    
    # Author information
    created_by = Column(Integer, ForeignKey("administrators.id"))
    created_by_type = Column(String(20), default="admin")  # admin, system, api
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    customer = relationship("Customer")
    author = relationship("Administrator")


class CustomerTrafficCounter(Base):
    """Customer traffic usage counters"""
    __tablename__ = "customer_traffic_counters"

    service_id = Column(Integer, ForeignKey("customer_internet_service_instances.customer_service_id", ondelete="CASCADE"), primary_key=True)
    
    # Traffic counters (in bytes)
    day_up = Column(Integer, default=0)
    day_down = Column(Integer, default=0)
    week_up = Column(Integer, default=0)
    week_down = Column(Integer, default=0)
    month_up = Column(Integer, default=0)
    month_down = Column(Integer, default=0)
    
    # Time counters (in seconds)
    day_time = Column(Integer, default=0)
    week_time = Column(Integer, default=0)
    month_time = Column(Integer, default=0)
    
    # Reset timestamps
    day_reset = Column(DateTime(timezone=True))
    week_reset = Column(DateTime(timezone=True))
    month_reset = Column(DateTime(timezone=True))
    
    # Timestamps
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    internet_service = relationship("CustomerInternetService", back_populates="traffic_counters", overlaps="customer_service,traffic_counters")


class CustomerBonusTrafficCounter(Base):
    """Customer bonus traffic counters"""
    __tablename__ = "customer_bonus_traffic_counters"

    service_id = Column(Integer, ForeignKey("customer_internet_service_instances.customer_service_id", ondelete="CASCADE"), primary_key=True)
    
    # Bonus traffic counters (in bytes)
    day_up = Column(Integer, default=0)
    day_down = Column(Integer, default=0)
    week_up = Column(Integer, default=0)
    week_down = Column(Integer, default=0)
    month_up = Column(Integer, default=0)
    month_down = Column(Integer, default=0)
    
    # Timestamps
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    internet_service = relationship("CustomerInternetService", back_populates="bonus_traffic_counters", overlaps="customer_service,bonus_traffic_counters")