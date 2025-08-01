from fastapi import APIRouter

from app.api.v1.endpoints import (  # Core business endpoints; Service & network management; Platform & monitoring; Platform services; Additional endpoints (maintained for compatibility); Lookup tables; RBAC system; Device management; Ansible automation
    alerts,
    api_management,
    audit_management,
    auth,
    automation,
    billing,
    # billing_enhanced,  # Temporarily disabled due to Pydantic schema issues
    billing_types,
    communications,
    contact_types,
    customer_portal,
    customer_services,
    customer_statuses,
    customers,
    dead_letter_queue,
    device_management,
    devices,
    files,
    oauth,
    operational_dashboard,
    portal_auth,
    radius,
    rbac,
    reseller,
    reseller_auth,
    service_instances,
    service_provisioning,
    service_templates,
    service_types,
    services,
    ticket_statuses,
    ticketing,
    two_factor,
    webhooks,
)
from app.api.v1 import config_management

# Redirects removed - using direct RESTful URLs

api_router = APIRouter()

# ============================================================================
# Core Business API
# ============================================================================

# Authentication & Authorization
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(
    portal_auth.router, prefix="/auth/portal", tags=["authentication"]
)
api_router.include_router(
    two_factor.router, prefix="/auth/two-factor", tags=["authentication"]
)
api_router.include_router(oauth.router, prefix="/auth/oauth", tags=["authentication"])
api_router.include_router(
    reseller_auth.router, prefix="/auth/resellers", tags=["authentication"]
)

# Customer Management
api_router.include_router(customers.router, prefix="/customers", tags=["customers"])
api_router.include_router(
    customer_portal.router, prefix="/customers", tags=["customers"]
)
api_router.include_router(
    contact_types.router, prefix="/contact-types", tags=["lookups"]
)
api_router.include_router(
    customer_statuses.router, prefix="/customer-statuses", tags=["lookups"]
)
api_router.include_router(
    service_types.router, prefix="/service-types", tags=["lookups"]
)
api_router.include_router(
    ticket_statuses.router, prefix="/ticket-statuses", tags=["lookups"]
)
api_router.include_router(
    billing_types.router, prefix="/billing-types", tags=["lookups"]
)

# RBAC System
api_router.include_router(rbac.router, prefix="/rbac", tags=["rbac"])

# Configuration Management
api_router.include_router(config_management.router, prefix="/config", tags=["configuration"])

# Device Management
api_router.include_router(devices.router, prefix="/devices", tags=["devices"])

# Ansible Automation
api_router.include_router(automation.router, prefix="/automation", tags=["automation"])

# Service Management (Consolidated)
api_router.include_router(services.router, prefix="/services", tags=["services"])
api_router.include_router(
    customer_services.router, prefix="/customer-services", tags=["services"]
)
api_router.include_router(
    service_templates.router, prefix="/services/templates", tags=["services"]
)  # Replaces service_plans
api_router.include_router(
    service_instances.router, prefix="/services/subscriptions", tags=["services"]
)  # Renamed for clarity
api_router.include_router(
    service_provisioning.router, prefix="/services/provisioning", tags=["services"]
)
# Note: service_plans deprecated - use service_templates instead

# Customer Services (Proper RESTful nesting - handled in customers router)
# Note: Customer services are nested under /customers/{id}/services

# Billing & Payments
api_router.include_router(billing.router, prefix="/billing", tags=["billing"])
# api_router.include_router(billing_enhanced.router, prefix="/billing", tags=["billing"])  # Temporarily disabled

# Support & Ticketing (Clean RESTful naming)
api_router.include_router(ticketing.router, prefix="/support", tags=["support"])

# Reseller Management (Business Alignment)
api_router.include_router(reseller.router, prefix="/resellers", tags=["resellers"])

# ============================================================================
# Network & Infrastructure
# ============================================================================

# Network Management
api_router.include_router(
    device_management.router, prefix="/network/devices", tags=["network"]
)
api_router.include_router(radius.router, prefix="/network/radius", tags=["network"])
# Note: radius_integration merged into radius endpoints

# ============================================================================
# Platform & Operations
# ============================================================================

# Monitoring & Alerting (Consolidated)
api_router.include_router(
    alerts.router, prefix="/monitoring/alerts", tags=["monitoring"]
)
api_router.include_router(
    operational_dashboard.router, prefix="/monitoring/dashboard", tags=["monitoring"]
)

# Audit & Compliance
api_router.include_router(audit_management.router, prefix="/audit", tags=["compliance"])

# ============================================================================
# Platform Services
# ============================================================================

# API Management (Avoid confusion with /api/v1 base)
api_router.include_router(
    api_management.router, prefix="/management", tags=["platform"]
)

# File Management
api_router.include_router(files.router, prefix="/files", tags=["platform"])

# Communications
api_router.include_router(
    communications.router, prefix="/communications", tags=["platform"]
)

# Webhooks (Clean RESTful naming)
api_router.include_router(webhooks.router, prefix="/webhooks", tags=["integrations"])

# Background Processing (Clean RESTful naming)
api_router.include_router(
    dead_letter_queue.router, prefix="/background", tags=["background"]
)

# ============================================================================
# RESTful API Structure Complete
# ============================================================================
# All endpoints now use proper RESTful naming conventions
# No backward compatibility redirects needed (pre-production)

# Note: Plugin, Security, and Settings endpoints need to be implemented or imported from correct location
