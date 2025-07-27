"""
Webhook System Enums

Comprehensive enums for webhook system configuration and status tracking.
"""

import enum


class WebhookStatus(str, enum.Enum):
    """Webhook endpoint status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DISABLED = "disabled"
    FAILED = "failed"


class DeliveryStatus(str, enum.Enum):
    """Webhook delivery status"""
    PENDING = "pending"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETRYING = "retrying"
    ABANDONED = "abandoned"


class EventCategory(str, enum.Enum):
    """Event categories for organization"""
    CUSTOMER = "customer"
    BILLING = "billing"
    SERVICE = "service"
    NETWORK = "network"
    TICKETING = "ticketing"
    AUTHENTICATION = "authentication"
    SYSTEM = "system"
    DEVICE = "device"
    RESELLER = "reseller"


class FilterOperator(str, enum.Enum):
    """Filter operators for conditional webhooks"""
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    GREATER_EQUAL = "greater_equal"
    LESS_EQUAL = "less_equal"
    IN = "in"
    NOT_IN = "not_in"
    REGEX = "regex"
    EXISTS = "exists"
    NOT_EXISTS = "not_exists"


class RetryStrategy(str, enum.Enum):
    """Retry strategies for failed deliveries"""
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    FIXED_INTERVAL = "fixed_interval"
    LINEAR_BACKOFF = "linear_backoff"
    IMMEDIATE = "immediate"
    NONE = "none"


class SignatureAlgorithm(str, enum.Enum):
    """Signature algorithms for payload verification"""
    HMAC_SHA256 = "hmac_sha256"
    HMAC_SHA512 = "hmac_sha512"
    HMAC_SHA1 = "hmac_sha1"


class HttpMethod(str, enum.Enum):
    """HTTP methods for webhook delivery"""
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"


class ContentType(str, enum.Enum):
    """Content types for webhook payloads"""
    JSON = "application/json"
    FORM = "application/x-www-form-urlencoded"
    XML = "application/xml"
