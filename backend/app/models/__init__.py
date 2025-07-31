"""ISP Framework Models - Modular Architecture

This module provides access to all models in the ISP Framework through a modular,
domain-organized structure for better maintainability and scalability.
"""

# Import all models here to ensure they are registered with SQLAlchemy
# API Management Models
from .api_management import (
    APIEndpoint,
    APIKey,
    APIQuota,
    APIRateLimit,
    APIUsage,
    APIVersion,
)

# Enhanced Audit Models
from .audit import AuditProcessingStatus, AuditQueue, CDCLog, ConfigurationSnapshot

# Authentication Models
from .auth import (
    Administrator,
    ApiKey,
    OAuthAuthorizationCode,
    OAuthClient,
    OAuthToken,
    TwoFactorAuth,
)
from .base import Base

# Billing System Models
from .billing import (
    BalanceHistory,
    BillingTransaction,
    CreditNote,
    CustomerBillingAccount,
    DunningCase,
    Invoice,
    InvoiceItem,
    Payment,
    PaymentMethod,
    PaymentPlan,
)

# Communications Models
from .communications import (
    CommunicationLog,
    CommunicationPreference,
    CommunicationProvider,
    CommunicationQueue,
    CommunicationRule,
    CommunicationTemplate,
)

# Customer Management Models
from .customer import (
    Customer,
    CustomerDocument,
    CustomerExtended,
    CustomerLabel,
    CustomerNote,
    PortalConfig,
    PortalIDHistory,
)

# Customer Portal Models
from .customer.portal_complete import (
    CustomerPortalActivity,
    CustomerPortalAutoPayment,
    CustomerPortalFAQ,
    CustomerPortalInvoiceView,
    CustomerPortalNotification,
    CustomerPortalPayment,
    CustomerPortalPreferences,
    CustomerPortalServiceRequest,
    CustomerPortalSession,
    CustomerPortalUsageView,
)

# Device Integration Models
from .devices import (
    CiscoAccessList,
    CiscoDevice,
    CiscoInterface,
    CiscoVLAN,
    DeviceAlert,
    DeviceConfigBackup,
    DeviceInterface,
    DeviceMonitoring,
    DeviceTemplate,
    ManagedDevice,
    MikroTikDevice,
    MikroTikDHCPLease,
    MikroTikFirewallRule,
    MikroTikHotspotUser,
    MikroTikInterface,
    MikroTikInterfaceStats,
    MikroTikPPPoESecret,
    MikroTikSimpleQueue,
    MikroTikSystemStats,
)

# File Storage Models
from .file_storage import (
    ExportJob,
    FileMetadata,
    FilePermission,
    ImportJob,
)

# Foundation Models
from .foundation import (
    FileStorage,
    InternetTariffConfig,
    Location,
    Reseller,
    Tariff,
    TariffBillingOption,
    TariffPromotion,
    TariffZonePricing,
)

# Networking Models
from .networking import (
    Cable,
    CustomerOnline,
    CustomerStatistics,
    DeviceConnection,
    DHCPReservation,
    IPAllocation,
    IPPool,
    IPRange,
    NASDevice,
    NetworkDevice,
    NetworkSite,
    RADIUSAccounting,
    RADIUSClient,
    RADIUSInterimUpdate,
    RADIUSServer,
    RadiusSession,
)

# Plugin System Models
from .plugins import (
    Plugin,
    PluginConfiguration,
    PluginDependency,
    PluginHook,
    PluginLog,
    PluginPriority,
    PluginRegistry,
    PluginStatus,
    PluginTemplate,
    PluginType,
)

# RBAC Models
from .rbac import (
    Permission,
    Role,
    RolePermission,
    UserRole,
)

# Service Management Models
from .services import (
    BundleServiceTemplate,
    CustomerInternetService,
    CustomerService,
    CustomerVoiceService,
    InternetServiceTemplate,
    ServiceAlert,
    ServiceIPAssignment,
    ServiceProvisioning,
    ServiceStatusHistory,
    ServiceSuspension,
    ServiceTemplate,
    ServiceUsageTracking,
    VoiceServiceTemplate,
)

# Settings & Configuration Models
from .settings import ConfigurationTemplate, FeatureFlag, Setting, SettingHistory

# Ticketing System Models
from .ticketing import (
    EscalationReason,
    FieldWorkOrder,
    FieldWorkStatus,
    KnowledgeBaseArticle,
    MessageAttachment,
    NetworkIncident,
    SLAPolicy,
    Ticket,
    TicketAttachment,
    TicketEscalation,
    TicketMessage,
    TicketPriority,
    TicketSource,
    TicketStatus,
    TicketStatusHistory,
    TicketTemplate,
    TicketTimeEntry,
    TicketType,
)

# Webhook System Models
from .webhooks import (
    WebhookDelivery,
    WebhookDeliveryAttempt,
    WebhookEndpoint,
    WebhookEvent,
    WebhookEventType,
    WebhookFilter,
    WebhookSecret,
)

# All models now use the new modular architecture


# Remove duplicate imports - already imported above

__all__ = [
    "Base",
    # API Management Models
    "APIEndpoint",
    "APIKey",
    "APIQuota",
    "APIRateLimit",
    "APIUsage",
    "APIVersion",
    # File Storage Models
    "ExportJob",
    "FileMetadata",
    "FilePermission",
    "ImportJob",
    # Authentication Models
    "Administrator",
    "OAuthClient",
    "OAuthAuthorizationCode",
    "OAuthToken",
    "TwoFactorAuth",
    "ApiKey",
    # RBAC Models
    "Permission",
    "Role",
    "RolePermission",
    "UserRole",
    # Customer Models
    "Customer",
    "CustomerExtended",
    "CustomerLabel",
    "CustomerNote",
    "CustomerDocument",
    # Portal Models
    "PortalConfig",
    "PortalIDHistory",
    # Customer Portal Models
    "CustomerPortalSession",
    "CustomerPortalPreferences",
    "CustomerPortalPayment",
    "CustomerPortalAutoPayment",
    "CustomerPortalServiceRequest",
    "CustomerPortalInvoiceView",
    "CustomerPortalUsageView",
    "CustomerPortalNotification",
    "CustomerPortalFAQ",
    "CustomerPortalActivity",
    # Ticketing System Models
    "Ticket",
    "TicketType",
    "TicketPriority",
    "TicketStatus",
    "TicketSource",
    "TicketMessage",
    "TicketAttachment",
    "MessageAttachment",
    "SLAPolicy",
    "TicketEscalation",
    "EscalationReason",
    "TicketStatusHistory",
    "TicketTimeEntry",
    "FieldWorkOrder",
    "FieldWorkStatus",
    "NetworkIncident",
    "KnowledgeBaseArticle",
    "TicketTemplate",
    # Foundation Models
    "Location",
    "FileStorage",
    "Reseller",
    # Enhanced Audit Models
    "AuditQueue",
    "ConfigurationSnapshot",
    "CDCLog",
    "AuditProcessingStatus",
    "Tariff",
    "InternetTariffConfig",
    "TariffBillingOption",
    "TariffZonePricing",
    "TariffPromotion",
    # Networking Models
    "IPPool",
    "IPAllocation",
    "DHCPReservation",
    "IPRange",
    "NetworkSite",
    "NetworkDevice",
    "DeviceConnection",
    "Cable",
    "RadiusSession",
    "RADIUSInterimUpdate",
    "CustomerOnline",
    "CustomerStatistics",
    "NASDevice",
    "RADIUSServer",
    "RADIUSClient",
    "RADIUSAccounting",
    # Communications Models
    "CommunicationTemplate",
    "CommunicationProvider",
    "CommunicationLog",
    "CommunicationQueue",
    "CommunicationPreference",
    "CommunicationRule",
    # Device Models
    "ManagedDevice",
    "DeviceInterface",
    "DeviceMonitoring",
    "DeviceAlert",
    "DeviceConfigBackup",
    "DeviceTemplate",
    "MikroTikDevice",
    "MikroTikInterface",
    "MikroTikSimpleQueue",
    "MikroTikFirewallRule",
    "MikroTikDHCPLease",
    "MikroTikPPPoESecret",
    "MikroTikHotspotUser",
    "MikroTikSystemStats",
    "MikroTikInterfaceStats",
    "CiscoDevice",
    "CiscoInterface",
    "CiscoVLAN",
    "CiscoAccessList",
    # Service Management Models
    "ServiceTemplate",
    "InternetServiceTemplate",
    "VoiceServiceTemplate",
    "BundleServiceTemplate",
    "CustomerService",
    "CustomerInternetService",
    "CustomerVoiceService",
    "ServiceProvisioning",
    "ServiceIPAssignment",
    "ServiceStatusHistory",
    "ServiceSuspension",
    "ServiceUsageTracking",
    "ServiceAlert",
    # Billing System Models
    "CustomerBillingAccount",
    "BillingTransaction",
    "BalanceHistory",
    "Invoice",
    "InvoiceItem",
    "PaymentMethod",
    "Payment",
    "CreditNote",
    "PaymentPlan",
    "DunningCase",
    # Webhook System Models
    "WebhookEndpoint",
    "WebhookEvent",
    "WebhookDelivery",
    "WebhookEventType",
    "WebhookFilter",
    "WebhookSecret",
    "WebhookDeliveryAttempt",
    # Plugin System Models
    "Plugin",
    "PluginConfiguration",
    "PluginHook",
    "PluginDependency",
    "PluginLog",
    "PluginRegistry",
    "PluginTemplate",
    "PluginStatus",
    "PluginType",
    "PluginPriority",
    # Settings & Configuration Models
    "Setting",
    "SettingHistory",
    "FeatureFlag",
    "ConfigurationTemplate",
]
