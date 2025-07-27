from fastapi import APIRouter
from app.api.v1.endpoints import (
    # Core business endpoints
    auth, customers, billing, webhooks, ticketing,
    # Service & network management
    services, device_management, radius,
    # Platform & monitoring
    alerts, audit_management, operational_dashboard,
    # Platform services
    api_management, files, communications, dead_letter_queue,
    # Additional endpoints (maintained for compatibility)
    portal_auth, two_factor, service_plans, customer_services, oauth,
    reseller, reseller_auth, service_instances, service_provisioning,
    service_templates, customer_portal
)
# Redirects removed - using direct RESTful URLs

api_router = APIRouter()

# ============================================================================
# Core Business API
# ============================================================================

# Authentication & Authorization
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(portal_auth.router, prefix="/auth/portal", tags=["authentication"])
api_router.include_router(two_factor.router, prefix="/auth/two-factor", tags=["authentication"])
api_router.include_router(oauth.router, prefix="/auth/oauth", tags=["authentication"])
api_router.include_router(reseller_auth.router, prefix="/auth/resellers", tags=["authentication"])

# Customer Management
api_router.include_router(customers.router, prefix="/customers", tags=["customers"])
api_router.include_router(customer_portal.router, prefix="/customers", tags=["customers"])

# Service Management (Consolidated)
api_router.include_router(services.router, prefix="/services", tags=["services"])
api_router.include_router(service_templates.router, prefix="/services/templates", tags=["services"])  # Replaces service_plans
api_router.include_router(service_instances.router, prefix="/services/subscriptions", tags=["services"])  # Renamed for clarity
api_router.include_router(service_provisioning.router, prefix="/services/provisioning", tags=["services"])
# Note: service_plans deprecated - use service_templates instead

# Customer Services (Proper RESTful nesting - handled in customers router)
# Note: Customer services are nested under /customers/{id}/services

# Billing & Payments
api_router.include_router(billing.router, prefix="/billing", tags=["billing"])

# Support & Ticketing (Clean RESTful naming)
api_router.include_router(ticketing.router, prefix="/support", tags=["support"])

# Reseller Management (Business Alignment)
api_router.include_router(reseller.router, prefix="/resellers", tags=["resellers"])

# ============================================================================
# Network & Infrastructure
# ============================================================================

# Network Management
api_router.include_router(device_management.router, prefix="/network/devices", tags=["network"])
api_router.include_router(radius.router, prefix="/network/radius", tags=["network"])
# Note: radius_integration merged into radius endpoints

# ============================================================================
# Platform & Operations
# ============================================================================

# Monitoring & Alerting (Consolidated)
api_router.include_router(alerts.router, prefix="/monitoring/alerts", tags=["monitoring"])
api_router.include_router(operational_dashboard.router, prefix="/monitoring/dashboard", tags=["monitoring"])

# Audit & Compliance
api_router.include_router(audit_management.router, prefix="/audit", tags=["compliance"])

# ============================================================================
# Platform Services
# ============================================================================

# API Management (Avoid confusion with /api/v1 base)
api_router.include_router(api_management.router, prefix="/management", tags=["platform"])

# File Management
api_router.include_router(files.router, prefix="/files", tags=["platform"])

# Communications
api_router.include_router(communications.router, prefix="/communications", tags=["platform"])

# Webhooks (Clean RESTful naming)
api_router.include_router(webhooks.router, prefix="/webhooks", tags=["integrations"])

# Background Processing (Clean RESTful naming)
api_router.include_router(dead_letter_queue.router, prefix="/background", tags=["background"])

# ============================================================================
# RESTful API Structure Complete
# ============================================================================
# All endpoints now use proper RESTful naming conventions
# No backward compatibility redirects needed (pre-production)

# Note: Plugin, Security, and Settings endpoints need to be implemented or imported from correct location
