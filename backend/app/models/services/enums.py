"""
ISP Service Management System - Enums and Types

All enums and constant types used across the service management system.
"""

import enum


class ServiceStatus(enum.Enum):
    """Service lifecycle status"""
    PENDING = "pending"                    # Ordered, awaiting activation
    ACTIVE = "active"                      # Currently providing service
    SUSPENDED = "suspended"                # Temporarily disabled (billing, technical)
    TERMINATED = "terminated"              # Permanently cancelled
    EXPIRED = "expired"                    # End date reached, no longer active
    PENDING_UPGRADE = "pending_upgrade"    # Upgrade scheduled
    PENDING_DOWNGRADE = "pending_downgrade" # Downgrade scheduled
    PENDING_RELOCATION = "pending_relocation" # Moving to new address


class ServiceType(enum.Enum):
    """Types of services offered"""
    INTERNET = "internet"
    VOICE = "voice"
    BUNDLE = "bundle"
    ADDON = "addon"
    ONE_TIME = "one_time"


class ProvisioningStatus(enum.Enum):
    """Service provisioning workflow status"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    REQUIRES_MANUAL = "requires_manual"


class SuspensionReason(enum.Enum):
    """Reasons for service suspension"""
    NON_PAYMENT = "non_payment"
    CUSTOMER_REQUEST = "customer_request"
    TECHNICAL_ISSUE = "technical_issue"
    ABUSE = "abuse"
    MAINTENANCE = "maintenance"
    CONTRACT_VIOLATION = "contract_violation"


class ConnectionType(enum.Enum):
    """Network connection types"""
    PPPOE = "pppoe"
    DHCP = "dhcp"
    STATIC = "static"
    BRIDGE = "bridge"


class IPAssignmentType(enum.Enum):
    """IP address assignment types"""
    STATIC = "static"
    DYNAMIC = "dynamic"
    RESERVED = "reserved"


class SuspensionType(enum.Enum):
    """Types of service suspension"""
    FULL = "full"
    PARTIAL = "partial"
    SPEED_LIMIT = "speed_limit"


class ServiceCategory(enum.Enum):
    """Service categories for classification"""
    RESIDENTIAL = "residential"
    BUSINESS = "business"
    ENTERPRISE = "enterprise"
    GOVERNMENT = "government"


class ServiceSubcategory(enum.Enum):
    """Service subcategories"""
    HOME = "home"
    SOHO = "soho"
    SMB = "smb"
    CORPORATE = "corporate"
    CARRIER = "carrier"


class QualityProfile(enum.Enum):
    """Service quality profiles"""
    BASIC = "basic"
    STANDARD = "standard"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


class SupportLevel(enum.Enum):
    """Customer support levels"""
    BASIC = "basic"
    STANDARD = "standard"
    PREMIUM = "premium"


class AlertSeverity(enum.Enum):
    """Alert severity levels for service monitoring"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertStatus(enum.Enum):
    """Alert status for tracking resolution"""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    IGNORED = "ignored"


class UsageMetricType(enum.Enum):
    """Types of usage metrics tracked"""
    BANDWIDTH = "bandwidth"
    DATA_TRANSFER = "data_transfer"
    SESSION_TIME = "session_time"
    COST = "cost"
    QUALITY = "quality"


class ProvisioningTaskStatus(enum.Enum):
    """Status of individual provisioning tasks"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"


class ServiceQualityLevel(enum.Enum):
    """Service quality levels for SLA and monitoring"""
    BASIC = "basic"
    STANDARD = "standard"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


class ChangeMethod(enum.Enum):
    """Methods for service changes"""
    MANUAL = "manual"
    AUTOMATIC = "automatic"
    API = "api"
    BILLING = "billing"
    CUSTOMER_PORTAL = "customer_portal"


class BillingModel(enum.Enum):
    """Service billing models"""
    POSTPAID = "postpaid"
    PREPAID = "prepaid"
    HYBRID = "hybrid"


# Voice service specific enums
class VoiceCodec(enum.Enum):
    """Voice codecs"""
    G711 = "G.711"
    G729 = "G.729"
    G722 = "G.722"
    OPUS = "OPUS"


# Internet service specific enums
class TrafficPriority(enum.Enum):
    """Traffic priority levels"""
    LOW = 1
    NORMAL = 5
    HIGH = 8
    CRITICAL = 10


class ContentFilterLevel(enum.Enum):
    """Content filtering levels"""
    NONE = "none"
    BASIC = "basic"
    FAMILY = "family"
    STRICT = "strict"
    CUSTOM = "custom"
