"""
ISP Tariff Models
Comprehensive tariff system for ISP operations with data caps, FUP, SLA, and flexible pricing
"""

import enum

from sqlalchemy import (
    DECIMAL,
    BigInteger,
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

from ..services.enums import ServiceType


class BillingType(enum.Enum):
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"
    PREPAID = "prepaid"
    USAGE_BASED = "usage_based"


class FUPResetPeriod(enum.Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    NEVER = "never"


class ServiceClass(enum.Enum):
    ECONOMY = "economy"
    STANDARD = "standard"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


class Tariff(Base):
    """Base tariff model for all service types"""

    __tablename__ = "tariffs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    display_name = Column(String(255))
    description = Column(Text)
    service_type = Column(Enum(ServiceType), nullable=False, index=True)

    # Basic Pricing
    base_price = Column(DECIMAL(10, 4), nullable=False)
    currency = Column(String(3), default="NGN")

    # Tax Configuration
    includes_tax = Column(Boolean, default=True)
    tax_rate = Column(DECIMAL(5, 2), default=0)

    # Service Level
    service_class = Column(Enum(ServiceClass), default=ServiceClass.STANDARD)
    priority_level = Column(Integer, default=5)  # 1-10

    # Contract Terms
    contract_period_months = Column(Integer)  # null for no contract
    early_termination_fee = Column(DECIMAL(10, 4), default=0)
    auto_renewal = Column(Boolean, default=True)

    # Fees
    installation_fee = Column(DECIMAL(10, 4), default=0)
    activation_fee = Column(DECIMAL(10, 4), default=0)
    equipment_rental_monthly = Column(DECIMAL(10, 4), default=0)

    # Availability
    is_active = Column(Boolean, default=True, index=True)
    is_public = Column(Boolean, default=True)  # Visible to customers
    available_from = Column(DateTime(timezone=True))
    available_until = Column(DateTime(timezone=True))

    # Service Level Agreement
    uptime_guarantee = Column(DECIMAL(5, 2))  # 99.9%
    support_response_time = Column(Integer)  # minutes

    # Legacy compatibility fields
    speed_down = Column(Integer)  # Download speed in kbps
    speed_up = Column(Integer)  # Upload speed in kbps
    data_limit = Column(BigInteger)  # Data limit in bytes
    price = Column(DECIMAL(10, 4))  # Maps to base_price

    # Extensibility
    custom_fields = Column(JSONB, default={})

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    billing_options = relationship(
        "TariffBillingOption", back_populates="tariff", cascade="all, delete-orphan"
    )
    internet_config = relationship(
        "InternetTariffConfig",
        back_populates="tariff",
        uselist=False,
        cascade="all, delete-orphan",
    )
    zone_pricing = relationship(
        "TariffZonePricing", back_populates="tariff", cascade="all, delete-orphan"
    )
    # Linked service templates using this tariff
    service_templates = relationship(
        "ServiceTemplate", back_populates="tariff", cascade="all, delete-orphan"
    )
    # Customer service instances referencing this tariff
    customer_services = relationship(
        "CustomerService", back_populates="tariff", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Tariff {self.id}: {self.name} ({self.service_type.value if self.service_type else 'unknown'})>"

    @property
    def effective_price(self):
        """Calculate price including tax if applicable"""
        base = self.base_price or self.price or 0
        if self.includes_tax and self.tax_rate and self.tax_rate > 0:
            return base * (1 + self.tax_rate / 100)
        return base


class InternetTariffConfig(Base):
    """Internet-specific tariff configuration"""

    __tablename__ = "internet_tariff_configs"

    tariff_id = Column(
        Integer, ForeignKey("tariffs.id", ondelete="CASCADE"), primary_key=True
    )

    # Speed Configuration (in kbps)
    speed_download = Column(Integer, nullable=False)
    speed_upload = Column(Integer, nullable=False)
    guaranteed_speed_percent = Column(Integer, default=10)  # Minimum guaranteed speed %

    # Burst Configuration
    burst_enabled = Column(Boolean, default=False)
    burst_download = Column(Integer, default=0)
    burst_upload = Column(Integer, default=0)
    burst_threshold_percent = Column(Integer, default=75)
    burst_time_seconds = Column(Integer, default=8)

    # Data Limits & Fair Usage Policy
    data_limit_bytes = Column(BigInteger)  # null for unlimited
    fup_enabled = Column(Boolean, default=False)
    fup_speed_download = Column(Integer)  # Speed after FUP limit
    fup_speed_upload = Column(Integer)
    fup_reset_period = Column(Enum(FUPResetPeriod), default=FUPResetPeriod.MONTHLY)

    # Overage Billing (for metered plans)
    overage_enabled = Column(Boolean, default=False)
    overage_price_per_gb = Column(DECIMAL(10, 4), default=0)
    overage_free_gb = Column(Integer, default=0)  # Free overage allowance

    # Quality of Service
    traffic_priority = Column(Integer, default=5)  # 1-10
    allowed_protocols = Column(
        JSONB, default=[]
    )  # ['http', 'https', 'ftp'] or [] for all
    blocked_ports = Column(JSONB, default=[])  # [25, 135, 445] blocked ports

    # Time-based Restrictions
    time_restrictions = Column(
        JSONB, default={}
    )  # {'weekday_hours': '08:00-22:00', 'weekend_hours': 'unlimited'}

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    tariff = relationship("Tariff", back_populates="internet_config")

    @property
    def speed_display(self):
        """Human-readable speed format"""

        def format_speed(kbps):
            if kbps >= 1000000:  # >= 1 Gbps
                return f"{kbps/1000000:.1f}Gbps"
            elif kbps >= 1000:  # >= 1 Mbps
                return f"{kbps/1000:.0f}Mbps"
            else:
                return f"{kbps}Kbps"

        return f"{format_speed(self.speed_download)}/{format_speed(self.speed_upload)}"

    @property
    def data_limit_display(self):
        """Human-readable data limit"""
        if not self.data_limit_bytes:
            return "Unlimited"

        gb = self.data_limit_bytes / (1024**3)
        if gb >= 1000:
            return f"{gb/1000:.1f}TB"
        else:
            return f"{gb:.0f}GB"


class TariffBillingOption(Base):
    """Billing options for tariffs (monthly, quarterly, annual, etc.)"""

    __tablename__ = "tariff_billing_options"

    id = Column(Integer, primary_key=True, index=True)
    tariff_id = Column(
        Integer, ForeignKey("tariffs.id", ondelete="CASCADE"), nullable=False
    )

    billing_type = Column(Enum(BillingType), nullable=False)
    billing_cycle_months = Column(Integer, nullable=False)  # 1, 3, 12, etc.

    # Pricing modifiers
    price_modifier_percent = Column(
        DECIMAL(5, 2), default=0
    )  # -10 for discount, +5 for premium
    setup_fee = Column(DECIMAL(10, 4), default=0)

    # Terms
    minimum_commitment_months = Column(Integer, default=0)
    advance_payment_required = Column(Boolean, default=False)

    # Status
    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    tariff = relationship("Tariff", back_populates="billing_options")

    @property
    def effective_price(self):
        """Calculate effective price with modifier"""
        base_price = self.tariff.effective_price
        if self.price_modifier_percent != 0:
            return base_price * (1 + self.price_modifier_percent / 100)
        return base_price

    @property
    def billing_display(self):
        """Human-readable billing description"""
        if self.billing_cycle_months == 1:
            return "Monthly"
        elif self.billing_cycle_months == 3:
            return "Quarterly"
        elif self.billing_cycle_months == 12:
            return "Annual"
        else:
            return f"Every {self.billing_cycle_months} months"


class TariffZonePricing(Base):
    """Location-based pricing for tariffs"""

    __tablename__ = "tariff_zone_pricing"

    id = Column(Integer, primary_key=True, index=True)
    tariff_id = Column(
        Integer, ForeignKey("tariffs.id", ondelete="CASCADE"), nullable=False
    )
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)

    # Pricing adjustments
    price_modifier_percent = Column(DECIMAL(5, 2), default=0)
    installation_fee_override = Column(DECIMAL(10, 4))
    equipment_rental_override = Column(DECIMAL(10, 4))

    # Availability
    is_available = Column(Boolean, default=True)
    max_customers = Column(Integer)  # Capacity limit for this zone
    current_customers = Column(Integer, default=0)

    # Special conditions
    requires_site_survey = Column(Boolean, default=False)
    estimated_install_days = Column(Integer)
    special_requirements = Column(Text)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    tariff = relationship("Tariff", back_populates="zone_pricing")

    @property
    def is_at_capacity(self):
        """Check if zone is at customer capacity"""
        if self.max_customers:
            return self.current_customers >= self.max_customers
        return False


class TariffPromotion(Base):
    """Promotional pricing and discounts"""

    __tablename__ = "tariff_promotions"

    id = Column(Integer, primary_key=True, index=True)
    tariff_id = Column(
        Integer, ForeignKey("tariffs.id", ondelete="CASCADE"), nullable=False
    )

    name = Column(String(255), nullable=False)
    description = Column(Text)

    # Discount Configuration
    discount_type = Column(
        String(20), nullable=False
    )  # percentage, fixed_amount, free_months
    discount_value = Column(DECIMAL(10, 4), nullable=False)

    # Duration
    promotion_months = Column(Integer)  # How long discount applies
    max_uses = Column(Integer)  # Total promotion usage limit
    current_uses = Column(Integer, default=0)

    # Validity
    valid_from = Column(DateTime(timezone=True), nullable=False)
    valid_until = Column(DateTime(timezone=True), nullable=False)

    # Conditions
    new_customers_only = Column(Boolean, default=False)
    requires_contract = Column(Boolean, default=False)
    minimum_contract_months = Column(Integer)

    # Status
    is_active = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    @property
    def is_valid(self):
        """Check if promotion is currently valid"""
        now = func.now()
        return (
            self.is_active
            and self.valid_from <= now <= self.valid_until
            and (not self.max_uses or self.current_uses < self.max_uses)
        )


# Indexes for performance
Index("idx_tariffs_service_type_active", Tariff.service_type, Tariff.is_active)
Index("idx_tariffs_public_active", Tariff.is_public, Tariff.is_active)
Index("idx_internet_config_tariff", InternetTariffConfig.tariff_id)
Index("idx_billing_options_tariff", TariffBillingOption.tariff_id)
Index(
    "idx_zone_pricing_tariff_location",
    TariffZonePricing.tariff_id,
    TariffZonePricing.location_id,
)
Index(
    "idx_promotions_tariff_valid",
    TariffPromotion.tariff_id,
    TariffPromotion.valid_from,
    TariffPromotion.valid_until,
)
