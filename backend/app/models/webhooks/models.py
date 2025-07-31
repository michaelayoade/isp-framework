"""
Webhook System Models

Complete webhook infrastructure models for event-driven integrations.
"""

import uuid

from sqlalchemy import Boolean, Column, DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import INET, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base

from .enums import (
    ContentType,
    DeliveryStatus,
    EventCategory,
    FilterOperator,
    HttpMethod,
    RetryStrategy,
    SignatureAlgorithm,
    WebhookStatus,
)


class WebhookEventType(Base):
    """Catalog of available webhook events"""

    __tablename__ = "webhook_event_types"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(
        String(100), unique=True, nullable=False, index=True
    )  # e.g., "customer.created"
    category = Column(SQLEnum(EventCategory), nullable=False, index=True)
    description = Column(Text)

    # Event schema and validation
    payload_schema = Column(JSONB)  # JSON schema for payload validation
    sample_payload = Column(JSONB)  # Example payload for documentation

    # Event configuration
    is_active = Column(Boolean, default=True)
    requires_authentication = Column(Boolean, default=True)
    max_retry_attempts = Column(Integer, default=5)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    events = relationship("WebhookEvent", back_populates="event_type")
    endpoint_subscriptions = relationship(
        "WebhookEndpoint",
        secondary="webhook_endpoint_events",
        back_populates="subscribed_events",
    )


class WebhookEndpoint(Base):
    """Webhook endpoint configuration"""

    __tablename__ = "webhook_endpoints"

    id = Column(Integer, primary_key=True, index=True)

    # Endpoint identity
    name = Column(String(255), nullable=False)
    description = Column(Text)
    url = Column(String(2048), nullable=False)

    # HTTP configuration
    http_method = Column(SQLEnum(HttpMethod), default=HttpMethod.POST)
    content_type = Column(SQLEnum(ContentType), default=ContentType.JSON)
    custom_headers = Column(JSONB, default=dict)  # Additional HTTP headers

    # Authentication and security
    secret_token = Column(String(255))  # For signature verification
    signature_algorithm = Column(
        SQLEnum(SignatureAlgorithm), default=SignatureAlgorithm.HMAC_SHA256
    )
    verify_ssl = Column(Boolean, default=True)

    # Delivery configuration
    timeout_seconds = Column(Integer, default=30)
    retry_strategy = Column(
        SQLEnum(RetryStrategy), default=RetryStrategy.EXPONENTIAL_BACKOFF
    )
    max_retry_attempts = Column(Integer, default=5)
    retry_delay_seconds = Column(Integer, default=60)

    # Status and monitoring
    status = Column(SQLEnum(WebhookStatus), default=WebhookStatus.ACTIVE, index=True)
    is_active = Column(Boolean, default=True, index=True)

    # Rate limiting
    rate_limit_per_minute = Column(Integer, default=60)
    rate_limit_per_hour = Column(Integer, default=1000)

    # Filtering
    enable_filtering = Column(Boolean, default=False)

    # Statistics
    total_deliveries = Column(Integer, default=0)
    successful_deliveries = Column(Integer, default=0)
    failed_deliveries = Column(Integer, default=0)
    last_delivery_at = Column(DateTime(timezone=True))
    last_success_at = Column(DateTime(timezone=True))
    last_failure_at = Column(DateTime(timezone=True))

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("administrators.id"))

    # Relationships
    subscribed_events = relationship(
        "WebhookEventType",
        secondary="webhook_endpoint_events",
        back_populates="endpoint_subscriptions",
    )
    deliveries = relationship(
        "WebhookDelivery", back_populates="endpoint", cascade="all, delete-orphan"
    )
    filters = relationship(
        "WebhookFilter", back_populates="endpoint", cascade="all, delete-orphan"
    )
    secrets = relationship(
        "WebhookSecret", back_populates="endpoint", cascade="all, delete-orphan"
    )


# Association table for many-to-many relationship
class WebhookEndpointEvent(Base):
    """Association table for webhook endpoints and event types"""

    __tablename__ = "webhook_endpoint_events"

    endpoint_id = Column(
        Integer,
        ForeignKey("webhook_endpoints.id", ondelete="CASCADE"),
        primary_key=True,
    )
    event_type_id = Column(
        Integer,
        ForeignKey("webhook_event_types.id", ondelete="CASCADE"),
        primary_key=True,
    )

    # Subscription configuration
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class WebhookEvent(Base):
    """Individual webhook events generated by the system"""

    __tablename__ = "webhook_events"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(
        String(36),
        unique=True,
        nullable=False,
        index=True,
        default=lambda: str(uuid.uuid4()),
    )

    # Event identification
    event_type_id = Column(
        Integer, ForeignKey("webhook_event_types.id"), nullable=False
    )

    # Event data
    payload = Column(JSONB, nullable=False)
    event_metadata = Column(JSONB, default=dict)  # Additional event metadata

    # Event context
    source_ip = Column(INET)
    user_agent = Column(String(500))
    triggered_by_user_id = Column(Integer, ForeignKey("administrators.id"))
    triggered_by_customer_id = Column(Integer, ForeignKey("customers.id"))

    # Event timing
    occurred_at = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Processing status
    is_processed = Column(Boolean, default=False, index=True)
    processed_at = Column(DateTime(timezone=True))

    # Relationships
    event_type = relationship("WebhookEventType", back_populates="events")
    deliveries = relationship(
        "WebhookDelivery", back_populates="event", cascade="all, delete-orphan"
    )


class WebhookDelivery(Base):
    """Webhook delivery attempts and status"""

    __tablename__ = "webhook_deliveries"

    id = Column(Integer, primary_key=True, index=True)
    delivery_id = Column(
        String(36),
        unique=True,
        nullable=False,
        index=True,
        default=lambda: str(uuid.uuid4()),
    )

    # Delivery references
    event_id = Column(
        Integer, ForeignKey("webhook_events.id", ondelete="CASCADE"), nullable=False
    )
    endpoint_id = Column(
        Integer, ForeignKey("webhook_endpoints.id", ondelete="CASCADE"), nullable=False
    )

    # Delivery status
    status = Column(SQLEnum(DeliveryStatus), default=DeliveryStatus.PENDING, index=True)
    attempt_count = Column(Integer, default=0)
    max_attempts = Column(Integer, default=5)

    # Delivery timing
    scheduled_at = Column(DateTime(timezone=True), nullable=False, index=True)
    delivered_at = Column(DateTime(timezone=True))
    next_retry_at = Column(DateTime(timezone=True), index=True)

    # HTTP details
    request_url = Column(String(2048))
    request_method = Column(String(10))
    request_headers = Column(JSONB)
    request_body = Column(Text)
    request_signature = Column(String(255))

    # Response details
    response_status_code = Column(Integer)
    response_headers = Column(JSONB)
    response_body = Column(Text)
    response_time_ms = Column(Integer)

    # Error tracking
    error_message = Column(Text)
    error_details = Column(JSONB)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    event = relationship("WebhookEvent", back_populates="deliveries")
    endpoint = relationship("WebhookEndpoint", back_populates="deliveries")
    attempts = relationship(
        "WebhookDeliveryAttempt",
        back_populates="delivery",
        cascade="all, delete-orphan",
    )


class WebhookDeliveryAttempt(Base):
    """Individual delivery attempts with detailed logging"""

    __tablename__ = "webhook_delivery_attempts"

    id = Column(Integer, primary_key=True, index=True)
    delivery_id = Column(
        Integer, ForeignKey("webhook_deliveries.id", ondelete="CASCADE"), nullable=False
    )

    # Attempt details
    attempt_number = Column(Integer, nullable=False)
    attempted_at = Column(DateTime(timezone=True), nullable=False, index=True)

    # HTTP request details
    request_url = Column(String(2048))
    request_headers = Column(JSONB)
    request_body_hash = Column(String(64))  # SHA256 hash of request body

    # HTTP response details
    response_status_code = Column(Integer)
    response_headers = Column(JSONB)
    response_body = Column(Text)
    response_time_ms = Column(Integer)

    # Connection details
    dns_resolution_time_ms = Column(Integer)
    connection_time_ms = Column(Integer)
    ssl_handshake_time_ms = Column(Integer)

    # Error tracking
    error_type = Column(String(100))  # timeout, connection_error, ssl_error, etc.
    error_message = Column(Text)
    error_details = Column(JSONB)

    # Success indicators
    is_successful = Column(Boolean, default=False, index=True)

    # Relationships
    delivery = relationship("WebhookDelivery", back_populates="attempts")


class WebhookFilter(Base):
    """Conditional filters for webhook delivery"""

    __tablename__ = "webhook_filters"

    id = Column(Integer, primary_key=True, index=True)
    endpoint_id = Column(
        Integer, ForeignKey("webhook_endpoints.id", ondelete="CASCADE"), nullable=False
    )

    # Filter configuration
    name = Column(String(255), nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True)

    # Filter logic
    field_path = Column(
        String(500), nullable=False
    )  # JSON path to field (e.g., "customer.status")
    operator = Column(SQLEnum(FilterOperator), nullable=False)
    value = Column(String(1000))  # Expected value
    values = Column(JSONB)  # For IN/NOT_IN operators

    # Filter behavior
    include_on_match = Column(Boolean, default=True)  # True = include, False = exclude

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    endpoint = relationship("WebhookEndpoint", back_populates="filters")


class WebhookSecret(Base):
    """Webhook endpoint secrets for signature verification"""

    __tablename__ = "webhook_secrets"

    id = Column(Integer, primary_key=True, index=True)
    endpoint_id = Column(
        Integer, ForeignKey("webhook_endpoints.id", ondelete="CASCADE"), nullable=False
    )

    # Secret configuration
    name = Column(String(255), nullable=False)
    secret_value = Column(String(500), nullable=False)  # Encrypted secret
    algorithm = Column(
        SQLEnum(SignatureAlgorithm), default=SignatureAlgorithm.HMAC_SHA256
    )

    # Secret lifecycle
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime(timezone=True))

    # Usage tracking
    last_used_at = Column(DateTime(timezone=True))
    usage_count = Column(Integer, default=0)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(Integer, ForeignKey("administrators.id"))

    # Relationships
    endpoint = relationship("WebhookEndpoint", back_populates="secrets")


# Performance indexes
Index(
    "idx_webhook_events_type_occurred",
    WebhookEvent.event_type_id,
    WebhookEvent.occurred_at,
)
Index(
    "idx_webhook_events_processed", WebhookEvent.is_processed, WebhookEvent.created_at
)
Index(
    "idx_webhook_deliveries_status_scheduled",
    WebhookDelivery.status,
    WebhookDelivery.scheduled_at,
)
Index(
    "idx_webhook_deliveries_retry",
    WebhookDelivery.next_retry_at,
    WebhookDelivery.status,
)
Index(
    "idx_webhook_delivery_attempts_delivery_attempt",
    WebhookDeliveryAttempt.delivery_id,
    WebhookDeliveryAttempt.attempt_number,
)
Index(
    "idx_webhook_endpoints_status_active",
    WebhookEndpoint.status,
    WebhookEndpoint.is_active,
)
