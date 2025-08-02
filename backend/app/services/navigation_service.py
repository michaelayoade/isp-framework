"""
Navigation service for UI module and submodule management.
"""
from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
import logging

from app.repositories.navigation_repository import NavigationRepository
from app.schemas.navigation import (
    UIModuleCreate, UIModuleUpdate, UIModule,
    UISubmoduleCreate, UISubmoduleUpdate, UISubmodule,
    NavigationItem, NavigationModule, NavigationSubmodule, GlobalNavigationResponse
)

logger = logging.getLogger(__name__)


class NavigationService:
    """Service for navigation-related operations."""

    def __init__(self, db: Session):
        self.db = db
        self.repository = NavigationRepository(db)
        self._cache: Dict[str, Any] = {}
        self._cache_ttl = 3600  # 1 hour cache

    # UI Module operations
    def get_modules(
        self,
        skip: int = 0,
        limit: int = 100,
        enabled_only: bool = True,
        tenant_scope: Optional[str] = None
    ) -> List[UIModule]:
        """Get all UI modules with optional filtering."""
        return self.repository.get_modules(skip, limit, enabled_only, tenant_scope)

    def get_module_by_id(self, module_id: UUID) -> Optional[UIModule]:
        """Get a UI module by ID."""
        return self.repository.get_module_by_id(module_id)

    def get_module_by_code(self, code: str) -> Optional[UIModule]:
        """Get a UI module by code."""
        return self.repository.get_module_by_code(code)

    def create_module(self, module_data: UIModuleCreate) -> UIModule:
        """Create a new UI module."""
        # Clear cache when creating new module
        self._clear_navigation_cache()
        return self.repository.create_module(module_data)

    def update_module(self, module_id: UUID, module_data: UIModuleUpdate) -> Optional[UIModule]:
        """Update a UI module."""
        # Clear cache when updating module
        self._clear_navigation_cache()
        return self.repository.update_module(module_id, module_data)

    def delete_module(self, module_id: UUID) -> bool:
        """Delete a UI module."""
        # Clear cache when deleting module
        self._clear_navigation_cache()
        return self.repository.delete_module(module_id)

    # UI Submodule operations
    def get_submodules(
        self,
        module_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100,
        enabled_only: bool = True
    ) -> List[UISubmodule]:
        """Get UI submodules with optional filtering."""
        return self.repository.get_submodules(module_id, skip, limit, enabled_only)

    def get_submodule_by_id(self, submodule_id: UUID) -> Optional[UISubmodule]:
        """Get a UI submodule by ID."""
        return self.repository.get_submodule_by_id(submodule_id)

    def create_submodule(self, submodule_data: UISubmoduleCreate) -> UISubmodule:
        """Create a new UI submodule."""
        # Clear cache when creating new submodule
        self._clear_navigation_cache()
        return self.repository.create_submodule(submodule_data)

    def update_submodule(self, submodule_id: UUID, submodule_data: UISubmoduleUpdate) -> Optional[UISubmodule]:
        """Update a UI submodule."""
        # Clear cache when updating submodule
        self._clear_navigation_cache()
        return self.repository.update_submodule(submodule_id, submodule_data)

    def delete_submodule(self, submodule_id: UUID) -> bool:
        """Delete a UI submodule."""
        # Clear cache when deleting submodule
        self._clear_navigation_cache()
        return self.repository.delete_submodule(submodule_id)

    # Global navigation operations
    def get_global_navigation(
        self,
        tenant_scope: Optional[str] = None,
        user_permissions: Optional[List[str]] = None
    ) -> GlobalNavigationResponse:
        """Get the global navigation structure for top-bar search."""
        cache_key = f"nav_{tenant_scope}_{hash(tuple(sorted(user_permissions or [])))}"
        
        # Check cache first
        if cache_key in self._cache:
            logger.debug(f"Returning cached navigation for key: {cache_key}")
            return self._cache[cache_key]
        
        try:
            # Get navigation structure from repository
            modules = self.repository.get_navigation_structure(tenant_scope, user_permissions)
            
            # Transform to navigation response format
            navigation_items = []
            total_submodules = 0
            
            for module in modules:
                # Create navigation module
                nav_module = NavigationModule(
                    code=module.code,
                    name=module.name,
                    icon=module.icon,
                    route=module.route
                )
                
                # Create navigation submodules
                nav_submodules = []
                for submodule in module.submodules:
                    nav_submodule = NavigationSubmodule(
                        code=submodule.code,
                        name=submodule.name,
                        icon=submodule.icon,
                        route=submodule.route
                    )
                    nav_submodules.append(nav_submodule)
                    total_submodules += 1
                
                # Create navigation item
                nav_item = NavigationItem(
                    module=nav_module,
                    submodules=nav_submodules
                )
                navigation_items.append(nav_item)
            
            # Create response
            response = GlobalNavigationResponse(
                navigation=navigation_items,
                total_modules=len(navigation_items),
                total_submodules=total_submodules
            )
            
            # Cache the response
            self._cache[cache_key] = response
            logger.info(f"Cached navigation structure: {len(navigation_items)} modules, {total_submodules} submodules")
            
            return response
            
        except Exception as e:
            logger.error(f"Error getting global navigation: {str(e)}")
            raise

    def _clear_navigation_cache(self):
        """Clear the navigation cache."""
        self._cache.clear()
        logger.debug("Navigation cache cleared")

    def seed_initial_data(self) -> Dict[str, int]:
        """Seed initial navigation data for the ISP Framework."""
        try:
            # Define initial modules and submodules
            modules_data = [
                {
                    "code": "dashboard",
                    "name": "Dashboard",
                    "icon": "dashboard",
                    "route": "/dashboard",
                    "order_idx": 1,
                    "tenant_scope": "GLOBAL",
                    "description": "Main dashboard and analytics",
                    "submodules": [
                        {"code": "overview", "name": "Overview", "icon": "chart-line", "route": "/dashboard", "order_idx": 1},
                        {"code": "financial", "name": "Financial", "icon": "dollar-sign", "route": "/dashboard/financial", "order_idx": 2, "required_permission": "dashboard.financial"},
                        {"code": "network", "name": "Network", "icon": "network-wired", "route": "/dashboard/network", "order_idx": 3, "required_permission": "dashboard.network"},
                        {"code": "reports", "name": "Reports", "icon": "file-chart", "route": "/dashboard/reports", "order_idx": 4, "required_permission": "dashboard.view"}
                    ]
                },
                {
                    "code": "customers",
                    "name": "Customers",
                    "icon": "users",
                    "route": "/customers",
                    "order_idx": 2,
                    "tenant_scope": "GLOBAL",
                    "description": "Customer management and services",
                    "submodules": [
                        {"code": "list", "name": "Customer List", "icon": "list", "route": "/customers", "order_idx": 1, "required_permission": "customers.view"},
                        {"code": "create", "name": "Add Customer", "icon": "user-plus", "route": "/customers/create", "order_idx": 2, "required_permission": "customers.create"},
                        {"code": "statuses", "name": "Customer Statuses", "icon": "tags", "route": "/customers/statuses", "order_idx": 3, "required_permission": "customers.view"},
                        {"code": "segments", "name": "Customer Segments", "icon": "layer-group", "route": "/customers/segments", "order_idx": 4, "required_permission": "customers.view"}
                    ]
                },
                {
                    "code": "services",
                    "name": "Services",
                    "icon": "cogs",
                    "route": "/services",
                    "order_idx": 3,
                    "tenant_scope": "GLOBAL",
                    "description": "Service management and provisioning",
                    "submodules": [
                        {"code": "catalog", "name": "Service Catalog", "icon": "book", "route": "/services/catalog", "order_idx": 1, "required_permission": "services.view"},
                        {"code": "active", "name": "Active Services", "icon": "play-circle", "route": "/services/active", "order_idx": 2, "required_permission": "services.view"},
                        {"code": "templates", "name": "Service Templates", "icon": "template", "route": "/services/templates", "order_idx": 3, "required_permission": "services.admin"},
                        {"code": "provisioning", "name": "Provisioning", "icon": "gear", "route": "/services/provisioning", "order_idx": 4, "required_permission": "services.provision"}
                    ]
                },
                {
                    "code": "billing",
                    "name": "Billing",
                    "icon": "credit-card",
                    "route": "/billing",
                    "order_idx": 4,
                    "tenant_scope": "GLOBAL",
                    "description": "Billing and financial management",
                    "submodules": [
                        {"code": "invoices", "name": "Invoices", "icon": "file-invoice", "route": "/billing/invoices", "order_idx": 1, "required_permission": "billing.view"},
                        {"code": "payments", "name": "Payments", "icon": "money-check", "route": "/billing/payments", "order_idx": 2, "required_permission": "billing.view"},
                        {"code": "credit-notes", "name": "Credit Notes", "icon": "file-minus", "route": "/billing/credit-notes", "order_idx": 3, "required_permission": "billing.view"},
                        {"code": "tariffs", "name": "Tariffs", "icon": "tags", "route": "/billing/tariffs", "order_idx": 4, "required_permission": "billing.admin"}
                    ]
                },
                {
                    "code": "devices",
                    "name": "Devices",
                    "icon": "server",
                    "route": "/devices",
                    "order_idx": 5,
                    "tenant_scope": "GLOBAL",
                    "description": "Network device management",
                    "submodules": [
                        {"code": "inventory", "name": "Device Inventory", "icon": "list", "route": "/devices", "order_idx": 1, "required_permission": "devices.view"},
                        {"code": "groups", "name": "Device Groups", "icon": "layer-group", "route": "/devices/groups", "order_idx": 2, "required_permission": "devices.view"},
                        {"code": "monitoring", "name": "Monitoring", "icon": "chart-area", "route": "/devices/monitoring", "order_idx": 3, "required_permission": "devices.monitor"},
                        {"code": "configuration", "name": "Configuration", "icon": "cog", "route": "/devices/config", "order_idx": 4, "required_permission": "devices.admin"}
                    ]
                },
                {
                    "code": "support",
                    "name": "Support",
                    "icon": "life-ring",
                    "route": "/support",
                    "order_idx": 6,
                    "tenant_scope": "GLOBAL",
                    "description": "Support and ticketing system",
                    "submodules": [
                        {"code": "tickets", "name": "Tickets", "icon": "ticket-alt", "route": "/support/tickets", "order_idx": 1, "required_permission": "support.view"},
                        {"code": "create-ticket", "name": "Create Ticket", "icon": "plus-circle", "route": "/support/tickets/create", "order_idx": 2, "required_permission": "support.create"},
                        {"code": "knowledge-base", "name": "Knowledge Base", "icon": "book-open", "route": "/support/kb", "order_idx": 3, "required_permission": "support.view"},
                        {"code": "escalations", "name": "Escalations", "icon": "exclamation-triangle", "route": "/support/escalations", "order_idx": 4, "required_permission": "support.admin"}
                    ]
                },
                {
                    "code": "admin",
                    "name": "Administration",
                    "icon": "user-shield",
                    "route": "/admin",
                    "order_idx": 7,
                    "tenant_scope": "GLOBAL",
                    "description": "System administration and configuration",
                    "submodules": [
                        {"code": "users", "name": "Users", "icon": "users-cog", "route": "/admin/users", "order_idx": 1, "required_permission": "admin.users"},
                        {"code": "roles", "name": "Roles & Permissions", "icon": "key", "route": "/admin/roles", "order_idx": 2, "required_permission": "admin.rbac"},
                        {"code": "settings", "name": "System Settings", "icon": "cogs", "route": "/admin/settings", "order_idx": 3, "required_permission": "admin.settings"},
                        {"code": "audit", "name": "Audit Logs", "icon": "history", "route": "/admin/audit", "order_idx": 4, "required_permission": "admin.audit"}
                    ]
                }
            ]
            
            created_modules = 0
            created_submodules = 0
            
            for module_data in modules_data:
                # Extract submodules data
                submodules_data = module_data.pop("submodules", [])
                
                # Check if module already exists
                existing_module = self.repository.get_module_by_code(module_data["code"])
                if existing_module:
                    logger.info(f"Module '{module_data['code']}' already exists, skipping")
                    continue
                
                # Create module
                module_create = UIModuleCreate(**module_data)
                created_module = self.repository.create_module(module_create)
                created_modules += 1
                logger.info(f"Created module: {created_module.name}")
                
                # Create submodules
                for submodule_data in submodules_data:
                    submodule_data["module_id"] = created_module.id
                    submodule_create = UISubmoduleCreate(**submodule_data)
                    created_submodule = self.repository.create_submodule(submodule_create)
                    created_submodules += 1
                    logger.info(f"Created submodule: {created_submodule.name}")
            
            # Clear cache after seeding
            self._clear_navigation_cache()
            
            return {
                "modules_created": created_modules,
                "submodules_created": created_submodules
            }
            
        except Exception as e:
            logger.error(f"Error seeding navigation data: {str(e)}")
            raise
