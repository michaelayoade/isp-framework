"""ISP Framework Models - Modular Architecture

This module provides access to all models in the ISP Framework through a modular,
domain-organized structure for better maintainability and scalability.
"""

# Import all models here to ensure they are registered with SQLAlchemy
from app.core.database import Base

# Authentication Models
from .auth import (
    Administrator, OAuthClient, OAuthAuthorizationCode, OAuthToken, 
    TwoFactorAuth, ApiKey
)

# Customer Portal Models
from .customer.portal_complete import (
    CustomerPortalSession, CustomerPortalPreferences, CustomerPortalPayment,
    CustomerPortalAutoPayment, CustomerPortalServiceRequest, CustomerPortalInvoiceView,
    CustomerPortalUsageView, CustomerPortalNotification, CustomerPortalFAQ,
    CustomerPortalActivity
)

# Ticketing System Models
from .ticketing import (
    Ticket, TicketType, TicketPriority, TicketStatus, TicketSource,
    TicketMessage, TicketAttachment, MessageAttachment, SLAPolicy,
    TicketEscalation, EscalationReason, TicketStatusHistory,
    TicketTimeEntry, FieldWorkOrder, FieldWorkStatus,
    NetworkIncident, KnowledgeBaseArticle, TicketTemplate
)

# Customer Management Models
from .customer import (
    Customer, CustomerExtended, CustomerLabel, CustomerNote, CustomerDocument,
    PortalConfig, PortalIDHistory
)

# Foundation Models
from .foundation import (
    Location, FileStorage, Reseller, Tariff, InternetTariffConfig,
    TariffBillingOption, TariffZonePricing, TariffPromotion
)

# Enhanced Audit Models
from .audit import (
    AuditQueue, ConfigurationSnapshot, CDCLog, AuditProcessingStatus
)

# Networking Models
from .networking import (
    IPPool, IPAllocation, DHCPReservation, IPRange, NetworkSite, NetworkDevice, DeviceConnection, Cable,
    RadiusSession, RADIUSInterimUpdate, CustomerOnline, CustomerStatistics, NASDevice, RADIUSServer, RADIUSClient, RADIUSAccounting
)

# Plugin System Models
from .plugins import (
    Plugin, PluginConfiguration, PluginHook, PluginDependency, PluginLog,
    PluginRegistry, PluginTemplate, PluginStatus, PluginType, PluginPriority
)

# Communications Models
from .communications import (
    CommunicationTemplate, CommunicationProvider, CommunicationLog,
    CommunicationQueue, CommunicationPreference, CommunicationRule
)

# Device Integration Models
from .devices import (
    ManagedDevice,
    DeviceInterface,
    DeviceMonitoring,
    DeviceAlert,
    DeviceConfigBackup,
    DeviceTemplate,
    MikroTikDevice,
    MikroTikInterface,
    MikroTikSimpleQueue,
    MikroTikFirewallRule,
    MikroTikDHCPLease,
    MikroTikPPPoESecret,
    MikroTikHotspotUser,
    MikroTikSystemStats,
    MikroTikInterfaceStats,
    CiscoDevice,
    CiscoInterface,
    CiscoVLAN,
    CiscoAccessList
)

# Service Management Models
from .services import (
    ServiceTemplate, InternetServiceTemplate, VoiceServiceTemplate, BundleServiceTemplate,
    CustomerService, CustomerInternetService, CustomerVoiceService, ServiceProvisioning, 
    ServiceIPAssignment, ServiceStatusHistory, ServiceSuspension, ServiceUsageTracking, ServiceAlert
)

# Billing System Models
from .billing import (
    CustomerBillingAccount, BillingTransaction, BalanceHistory,
    Invoice, InvoiceItem, PaymentMethod, Payment,
    CreditNote, PaymentPlan, DunningCase
)

# Webhook System Models
from .webhooks import (
    WebhookEndpoint, WebhookEvent, WebhookDelivery, WebhookEventType,
    WebhookFilter, WebhookSecret, WebhookDeliveryAttempt
)

# Settings & Configuration Models
from .settings import (
    Setting, SettingHistory, FeatureFlag, ConfigurationTemplate
)

# All models now use the new modular architecture





# Remove duplicate imports - already imported above

__all__ = [
    "Base",
    # Authentication Models
    "Administrator",
    "OAuthClient",
    "OAuthAuthorizationCode",
    "OAuthToken",
    "TwoFactorAuth",
    "ApiKey",
    
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
