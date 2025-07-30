"""
OpenAPI Tags Constants

Centralized definition of all API tags to ensure consistency across the application.
This prevents duplicate tags in Swagger UI and provides a single source of truth.
"""

# Core API Tags
AUTHENTICATION = "authentication"
CUSTOMERS = "customers"
ADMINISTRATORS = "administrators"
RESELLERS = "resellers"
BILLING = "billing"
TICKETING = "ticketing"
SETTINGS = "settings"

# Service Management Tags
SERVICES = "services"
INTERNET_SERVICES = "internet-services"
VOICE_SERVICES = "voice-services"
BUNDLE_SERVICES = "bundle-services"

# Network & Infrastructure Tags
NETWORK = "network"
DEVICES = "devices"
DEVICE_MANAGEMENT = "device-management"

# System & Operations Tags
PLUGINS = "plugins"
API_MANAGEMENT = "api-management"
COMMUNICATIONS = "communications"
FILE_STORAGE = "file-storage"
WEBHOOKS = "webhooks"
AUTOMATION = "automation"

# Lookup & Configuration Tags
LOOKUPS = "lookups"
RBAC = "rbac"

# System Health Tags
HEALTH = "health"
ROOT = "root"

# Tag descriptions for OpenAPI documentation
TAG_DESCRIPTIONS = {
    AUTHENTICATION: "Authentication and authorization endpoints",
    CUSTOMERS: "Customer management and portal operations",
    ADMINISTRATORS: "Administrator management and operations",
    RESELLERS: "Reseller management and operations",
    BILLING: "Billing operations including invoices, payments, and accounting",
    TICKETING: "Support ticket management and tracking",
    SETTINGS: "System configuration and settings management",
    
    SERVICES: "Service management and provisioning",
    INTERNET_SERVICES: "Internet service plans and configurations",
    VOICE_SERVICES: "Voice service plans and configurations",
    BUNDLE_SERVICES: "Bundle service plans and configurations",
    
    NETWORK: "Network infrastructure and topology management",
    DEVICES: "Network device management and monitoring",
    DEVICE_MANAGEMENT: "Advanced device management operations",
    
    PLUGINS: "Plugin system management and configuration",
    API_MANAGEMENT: "API key management and access control",
    COMMUNICATIONS: "Communication templates and messaging",
    FILE_STORAGE: "File upload and storage operations",
    WEBHOOKS: "Webhook configuration and management",
    AUTOMATION: "Ansible automation and provisioning",
    
    LOOKUPS: "Lookup tables and reference data",
    RBAC: "Role-based access control and permissions",
    
    HEALTH: "System health and monitoring endpoints",
    ROOT: "Root application endpoints"
}

# Ordered list of tags for consistent display in Swagger UI
TAG_ORDER = [
    AUTHENTICATION,
    CUSTOMERS,
    ADMINISTRATORS,
    RESELLERS,
    BILLING,
    TICKETING,
    SERVICES,
    INTERNET_SERVICES,
    VOICE_SERVICES,
    BUNDLE_SERVICES,
    NETWORK,
    DEVICES,
    DEVICE_MANAGEMENT,
    AUTOMATION,
    PLUGINS,
    API_MANAGEMENT,
    COMMUNICATIONS,
    FILE_STORAGE,
    WEBHOOKS,
    LOOKUPS,
    RBAC,
    SETTINGS,
    HEALTH,
    ROOT
]
