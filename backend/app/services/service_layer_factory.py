"""
Service Layer Factory - ISP Service Management System

Centralized factory for creating all service layer business logic components with:
- Service templates services (templates, internet, voice, bundle)
- Service instances services (customer services, internet, voice)
- Service provisioning services (workflows, templates, queue)
- Service management services (IP, status, suspension, usage, alerts)

Provides unified access to all service business logic with dependency injection
and configuration management for the entire service management system.
"""

from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from .service_instances_service import (
    CustomerInternetServiceService,
    CustomerServiceService,
    CustomerVoiceServiceService,
)
from .service_management_service import (
    ServiceAlertService,
    ServiceIPAssignmentService,
    ServiceStatusHistoryService,
    ServiceSuspensionService,
    ServiceUsageTrackingService,
)
from .service_provisioning_service import (
    ProvisioningTemplateService,
    ServiceProvisioningService,
)

# Import all service modules
from .service_templates_service import (
    BundleServiceTemplateService,
    InternetServiceTemplateService,
    ServiceTemplateService,
    VoiceServiceTemplateService,
)


class ServiceLayerFactory:
    """
    Centralized factory for all service layer business logic

    Provides unified access to all service business logic with proper
    dependency injection and configuration management.
    """

    def __init__(self, db: Session):
        self.db = db
        self._services: Dict[str, Any] = {}

    # Service Templates Services
    def get_service_template_service(self) -> ServiceTemplateService:
        """Get service template service"""
        if "service_template" not in self._services:
            self._services["service_template"] = ServiceTemplateService(self.db)
        return self._services["service_template"]

    def get_internet_template_service(self) -> InternetServiceTemplateService:
        """Get internet service template service"""
        if "internet_template" not in self._services:
            self._services["internet_template"] = InternetServiceTemplateService(
                self.db
            )
        return self._services["internet_template"]

    def get_voice_template_service(self) -> VoiceServiceTemplateService:
        """Get voice service template service"""
        if "voice_template" not in self._services:
            self._services["voice_template"] = VoiceServiceTemplateService(self.db)
        return self._services["voice_template"]

    def get_bundle_template_service(self) -> BundleServiceTemplateService:
        """Get bundle service template service"""
        if "bundle_template" not in self._services:
            self._services["bundle_template"] = BundleServiceTemplateService(self.db)
        return self._services["bundle_template"]

    # Service Instances Services
    def get_customer_service_service(self) -> CustomerServiceService:
        """Get customer service service"""
        if "customer_service" not in self._services:
            self._services["customer_service"] = CustomerServiceService(self.db)
        return self._services["customer_service"]

    def get_internet_service_service(self) -> CustomerInternetServiceService:
        """Get customer internet service service"""
        if "internet_service" not in self._services:
            self._services["internet_service"] = CustomerInternetServiceService(self.db)
        return self._services["internet_service"]

    def get_voice_service_service(self) -> CustomerVoiceServiceService:
        """Get customer voice service service"""
        if "voice_service" not in self._services:
            self._services["voice_service"] = CustomerVoiceServiceService(self.db)
        return self._services["voice_service"]

    # Service Provisioning Services
    def get_provisioning_service(self) -> ServiceProvisioningService:
        """Get service provisioning service"""
        if "provisioning" not in self._services:
            self._services["provisioning"] = ServiceProvisioningService(self.db)
        return self._services["provisioning"]

    def get_provisioning_template_service(self) -> ProvisioningTemplateService:
        """Get provisioning template service"""
        if "provisioning_template" not in self._services:
            self._services["provisioning_template"] = ProvisioningTemplateService(
                self.db
            )
        return self._services["provisioning_template"]

    # Service Management Services
    def get_ip_assignment_service(self) -> ServiceIPAssignmentService:
        """Get service IP assignment service"""
        if "ip_assignment" not in self._services:
            self._services["ip_assignment"] = ServiceIPAssignmentService(self.db)
        return self._services["ip_assignment"]

    def get_status_history_service(self) -> ServiceStatusHistoryService:
        """Get service status history service"""
        if "status_history" not in self._services:
            self._services["status_history"] = ServiceStatusHistoryService(self.db)
        return self._services["status_history"]

    def get_suspension_service(self) -> ServiceSuspensionService:
        """Get service suspension service"""
        if "suspension" not in self._services:
            self._services["suspension"] = ServiceSuspensionService(self.db)
        return self._services["suspension"]

    def get_usage_tracking_service(self) -> ServiceUsageTrackingService:
        """Get service usage tracking service"""
        if "usage_tracking" not in self._services:
            self._services["usage_tracking"] = ServiceUsageTrackingService(self.db)
        return self._services["usage_tracking"]

    def get_alert_service(self) -> ServiceAlertService:
        """Get service alert service"""
        if "alert" not in self._services:
            self._services["alert"] = ServiceAlertService(self.db)
        return self._services["alert"]

    # Convenience Methods
    def get_all_template_services(self) -> Dict[str, Any]:
        """Get all service template services"""
        return {
            "service_template": self.get_service_template_service(),
            "internet_template": self.get_internet_template_service(),
            "voice_template": self.get_voice_template_service(),
            "bundle_template": self.get_bundle_template_service(),
        }

    def get_all_instance_services(self) -> Dict[str, Any]:
        """Get all service instance services"""
        return {
            "customer_service": self.get_customer_service_service(),
            "internet_service": self.get_internet_service_service(),
            "voice_service": self.get_voice_service_service(),
        }

    def get_all_provisioning_services(self) -> Dict[str, Any]:
        """Get all service provisioning services"""
        return {
            "provisioning": self.get_provisioning_service(),
            "provisioning_template": self.get_provisioning_template_service(),
        }

    def get_all_management_services(self) -> Dict[str, Any]:
        """Get all service management services"""
        return {
            "ip_assignment": self.get_ip_assignment_service(),
            "status_history": self.get_status_history_service(),
            "suspension": self.get_suspension_service(),
            "usage_tracking": self.get_usage_tracking_service(),
            "alert": self.get_alert_service(),
        }

    def get_all_services(self) -> Dict[str, Any]:
        """Get all service layer services"""
        all_services = {}
        all_services.update(self.get_all_template_services())
        all_services.update(self.get_all_instance_services())
        all_services.update(self.get_all_provisioning_services())
        all_services.update(self.get_all_management_services())
        return all_services

    # Service Statistics and Health Check
    def get_service_stats(self) -> Dict[str, Any]:
        """Get statistics about loaded services"""
        return {
            "total_services": len(self._services),
            "loaded_services": list(self._services.keys()),
            "template_services": len(
                [k for k in self._services.keys() if "template" in k]
            ),
            "instance_services": len(
                [
                    k
                    for k in self._services.keys()
                    if "service" in k and "template" not in k
                ]
            ),
            "provisioning_services": len(
                [k for k in self._services.keys() if "provisioning" in k]
            ),
            "management_services": len(
                [
                    k
                    for k in self._services.keys()
                    if k
                    in [
                        "ip_assignment",
                        "status_history",
                        "suspension",
                        "usage_tracking",
                        "alert",
                    ]
                ]
            ),
        }

    def validate_services(self) -> Dict[str, Any]:
        """Validate all services are properly configured"""
        validation_results = {"is_valid": True, "errors": [], "warnings": []}

        # Test database connection
        try:
            self.db.execute("SELECT 1")
        except Exception as e:
            validation_results["is_valid"] = False
            validation_results["errors"].append(f"Database connection failed: {str(e)}")

        # Test service instantiation
        service_types = [
            ("service_template", ServiceTemplateService),
            ("internet_template", InternetServiceTemplateService),
            ("voice_template", VoiceServiceTemplateService),
            ("bundle_template", BundleServiceTemplateService),
            ("customer_service", CustomerServiceService),
            ("internet_service", CustomerInternetServiceService),
            ("voice_service", CustomerVoiceServiceService),
            ("provisioning", ServiceProvisioningService),
            ("provisioning_template", ProvisioningTemplateService),
            ("ip_assignment", ServiceIPAssignmentService),
            ("status_history", ServiceStatusHistoryService),
            ("suspension", ServiceSuspensionService),
            ("usage_tracking", ServiceUsageTrackingService),
            ("alert", ServiceAlertService),
        ]

        for service_name, service_class in service_types:
            try:
                service_instance = service_class(self.db)
                if not hasattr(service_instance, "db"):
                    validation_results["warnings"].append(
                        f"Service {service_name} missing db attribute"
                    )
            except Exception as e:
                validation_results["is_valid"] = False
                validation_results["errors"].append(
                    f"Failed to instantiate {service_name}: {str(e)}"
                )

        return validation_results

    def clear_cache(self):
        """Clear service cache"""
        self._services.clear()


# Global factory instance management
_factory_instances: Dict[str, ServiceLayerFactory] = {}


def get_service_layer_factory(
    db: Session, cache_key: Optional[str] = None
) -> ServiceLayerFactory:
    """
    Get or create a service layer factory instance

    Args:
        db: Database session
        cache_key: Optional cache key for factory instance reuse

    Returns:
        ServiceLayerFactory instance
    """
    if cache_key and cache_key in _factory_instances:
        # Update database session in cached factory
        _factory_instances[cache_key].db = db
        return _factory_instances[cache_key]

    factory = ServiceLayerFactory(db)

    if cache_key:
        _factory_instances[cache_key] = factory

    return factory


def clear_factory_cache():
    """Clear all cached factory instances"""
    global _factory_instances
    _factory_instances.clear()


# Dependency injection helpers for FastAPI
def get_service_templates_services(db: Session) -> Dict[str, Any]:
    """Dependency injection for service template services"""
    factory = get_service_layer_factory(db)
    return factory.get_all_template_services()


def get_service_instances_services(db: Session) -> Dict[str, Any]:
    """Dependency injection for service instance services"""
    factory = get_service_layer_factory(db)
    return factory.get_all_instance_services()


def get_service_provisioning_services(db: Session) -> Dict[str, Any]:
    """Dependency injection for service provisioning services"""
    factory = get_service_layer_factory(db)
    return factory.get_all_provisioning_services()


def get_service_management_services(db: Session) -> Dict[str, Any]:
    """Dependency injection for service management services"""
    factory = get_service_layer_factory(db)
    return factory.get_all_management_services()


def get_all_service_services(db: Session) -> Dict[str, Any]:
    """Dependency injection for all service services"""
    factory = get_service_layer_factory(db)
    return factory.get_all_services()


# Configuration and utilities
SERVICE_LAYER_CONFIG = {
    "cache_enabled": True,
    "validation_on_startup": True,
    "auto_clear_cache_on_error": True,
    "enable_async_operations": True,
    "enable_business_intelligence": True,
    "enable_audit_logging": True,
    "enable_performance_monitoring": True,
}


def configure_service_layer(config: Dict[str, Any]):
    """Configure service layer behavior"""
    global SERVICE_LAYER_CONFIG
    SERVICE_LAYER_CONFIG.update(config)


def get_service_layer_config() -> Dict[str, Any]:
    """Get current service layer configuration"""
    return SERVICE_LAYER_CONFIG.copy()


# Health check and monitoring
def health_check_service_layer(db: Session) -> Dict[str, Any]:
    """Perform health check on service layer"""
    factory = get_service_layer_factory(db)

    health_status = {
        "status": "healthy",
        "timestamp": str(datetime.now()),
        "database_connection": "ok",
        "service_validation": "ok",
        "factory_stats": factory.get_service_stats(),
        "errors": [],
        "warnings": [],
    }

    # Validate services
    validation_results = factory.validate_services()

    if not validation_results["is_valid"]:
        health_status["status"] = "unhealthy"
        health_status["service_validation"] = "failed"
        health_status["errors"].extend(validation_results["errors"])

    if validation_results["warnings"]:
        health_status["warnings"].extend(validation_results["warnings"])

    return health_status


# Business Intelligence and Analytics
class ServiceBusinessIntelligence:
    """Business intelligence and analytics for service management"""

    def __init__(self, db: Session):
        self.db = db
        self.factory = get_service_layer_factory(db)

    async def get_service_overview_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive service overview dashboard"""
        dashboard_data = {}

        # Service statistics
        customer_service = self.factory.get_customer_service_service()
        dashboard_data["service_stats"] = (
            await customer_service.get_service_statistics()
        )

        # Template statistics
        template_service = self.factory.get_service_template_service()
        dashboard_data["template_stats"] = (
            await template_service.get_template_statistics()
        )

        # Suspension statistics
        self.factory.get_suspension_service()
        dashboard_data["suspension_stats"] = {"active_suspensions": 0}  # Placeholder

        # Usage statistics
        usage_service = self.factory.get_usage_tracking_service()
        dashboard_data["usage_stats"] = (
            await usage_service.get_network_usage_statistics()
        )

        # Alert statistics
        self.factory.get_alert_service()
        dashboard_data["alert_stats"] = {"active_alerts": 0}  # Placeholder

        return dashboard_data

    async def get_revenue_analytics(self) -> Dict[str, Any]:
        """Get revenue analytics from service data"""
        # This would integrate with billing system
        return {
            "monthly_recurring_revenue": 0.0,
            "average_revenue_per_service": 0.0,
            "revenue_growth_rate": 0.0,
            "churn_rate": 0.0,
        }

    async def get_operational_metrics(self) -> Dict[str, Any]:
        """Get operational metrics"""
        return {
            "service_activation_time": 0.0,
            "provisioning_success_rate": 0.0,
            "customer_satisfaction_score": 0.0,
            "network_utilization": 0.0,
        }


# Module metadata
__version__ = "1.0.0"
__author__ = "ISP Framework Team"
__description__ = "Service layer for ISP service management operations"
__license__ = "MIT"

# Module configuration
SERVICE_LAYER_MODULE_CONFIG = {
    "version": __version__,
    "modular_architecture": True,
    "supports_templates": True,
    "supports_instances": True,
    "supports_provisioning": True,
    "supports_management": True,
    "supports_business_intelligence": True,
    "async_operations": True,
    "caching_enabled": True,
    "monitoring_enabled": True,
}
