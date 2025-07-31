"""
Service Repository Factory - ISP Service Management System

Centralized factory for creating all service-related repositories with:
- Service templates repositories (templates, internet, voice, bundle)
- Service instances repositories (customer services, internet, voice)
- Service provisioning repositories (workflows, templates, queue)
- Service management repositories (IP, status, suspension, usage, alerts)

Provides unified access to all service repositories with dependency injection
and configuration management for the entire service management system.
"""

from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from .service_instances_repository import (
    CustomerInternetServiceRepository,
    CustomerServiceRepository,
    CustomerVoiceServiceRepository,
)
from .service_management_repository import (
    ServiceAlertRepository,
    ServiceIPAssignmentRepository,
    ServiceStatusHistoryRepository,
    ServiceSuspensionRepository,
    ServiceUsageTrackingRepository,
)
from .service_provisioning_repository import (
    ProvisioningQueueRepository,
    ProvisioningTemplateRepository,
    ServiceProvisioningRepository,
)

# Import all repository modules
from .service_templates_repository import (
    BundleServiceTemplateRepository,
    InternetServiceTemplateRepository,
    ServiceTemplateRepository,
    VoiceServiceTemplateRepository,
)


class ServiceRepositoryFactory:
    """
    Centralized factory for all service-related repositories

    Provides unified access to all service repositories with proper
    dependency injection and configuration management.
    """

    def __init__(self, db: Session):
        self.db = db
        self._repositories: Dict[str, Any] = {}

    # Service Templates Repositories
    def get_service_template_repo(self) -> ServiceTemplateRepository:
        """Get service template repository"""
        if "service_template" not in self._repositories:
            self._repositories["service_template"] = ServiceTemplateRepository(self.db)
        return self._repositories["service_template"]

    def get_internet_template_repo(self) -> InternetServiceTemplateRepository:
        """Get internet service template repository"""
        if "internet_template" not in self._repositories:
            self._repositories["internet_template"] = InternetServiceTemplateRepository(
                self.db
            )
        return self._repositories["internet_template"]

    def get_voice_template_repo(self) -> VoiceServiceTemplateRepository:
        """Get voice service template repository"""
        if "voice_template" not in self._repositories:
            self._repositories["voice_template"] = VoiceServiceTemplateRepository(
                self.db
            )
        return self._repositories["voice_template"]

    def get_bundle_template_repo(self) -> BundleServiceTemplateRepository:
        """Get bundle service template repository"""
        if "bundle_template" not in self._repositories:
            self._repositories["bundle_template"] = BundleServiceTemplateRepository(
                self.db
            )
        return self._repositories["bundle_template"]

    # Service Instances Repositories
    def get_customer_service_repo(self) -> CustomerServiceRepository:
        """Get customer service repository"""
        if "customer_service" not in self._repositories:
            self._repositories["customer_service"] = CustomerServiceRepository(self.db)
        return self._repositories["customer_service"]

    def get_internet_service_repo(self) -> CustomerInternetServiceRepository:
        """Get customer internet service repository"""
        if "internet_service" not in self._repositories:
            self._repositories["internet_service"] = CustomerInternetServiceRepository(
                self.db
            )
        return self._repositories["internet_service"]

    def get_voice_service_repo(self) -> CustomerVoiceServiceRepository:
        """Get customer voice service repository"""
        if "voice_service" not in self._repositories:
            self._repositories["voice_service"] = CustomerVoiceServiceRepository(
                self.db
            )
        return self._repositories["voice_service"]

    # Service Provisioning Repositories
    def get_provisioning_repo(self) -> ServiceProvisioningRepository:
        """Get service provisioning repository"""
        if "provisioning" not in self._repositories:
            self._repositories["provisioning"] = ServiceProvisioningRepository(self.db)
        return self._repositories["provisioning"]

    def get_provisioning_template_repo(self) -> ProvisioningTemplateRepository:
        """Get provisioning template repository"""
        if "provisioning_template" not in self._repositories:
            self._repositories["provisioning_template"] = (
                ProvisioningTemplateRepository(self.db)
            )
        return self._repositories["provisioning_template"]

    def get_provisioning_queue_repo(self) -> ProvisioningQueueRepository:
        """Get provisioning queue repository"""
        if "provisioning_queue" not in self._repositories:
            self._repositories["provisioning_queue"] = ProvisioningQueueRepository(
                self.db
            )
        return self._repositories["provisioning_queue"]

    # Service Management Repositories
    def get_ip_assignment_repo(self) -> ServiceIPAssignmentRepository:
        """Get service IP assignment repository"""
        if "ip_assignment" not in self._repositories:
            self._repositories["ip_assignment"] = ServiceIPAssignmentRepository(self.db)
        return self._repositories["ip_assignment"]

    def get_status_history_repo(self) -> ServiceStatusHistoryRepository:
        """Get service status history repository"""
        if "status_history" not in self._repositories:
            self._repositories["status_history"] = ServiceStatusHistoryRepository(
                self.db
            )
        return self._repositories["status_history"]

    def get_suspension_repo(self) -> ServiceSuspensionRepository:
        """Get service suspension repository"""
        if "suspension" not in self._repositories:
            self._repositories["suspension"] = ServiceSuspensionRepository(self.db)
        return self._repositories["suspension"]

    def get_usage_tracking_repo(self) -> ServiceUsageTrackingRepository:
        """Get service usage tracking repository"""
        if "usage_tracking" not in self._repositories:
            self._repositories["usage_tracking"] = ServiceUsageTrackingRepository(
                self.db
            )
        return self._repositories["usage_tracking"]

    def get_alert_repo(self) -> ServiceAlertRepository:
        """Get service alert repository"""
        if "alert" not in self._repositories:
            self._repositories["alert"] = ServiceAlertRepository(self.db)
        return self._repositories["alert"]

    # Convenience Methods
    def get_all_template_repos(self) -> Dict[str, Any]:
        """Get all service template repositories"""
        return {
            "service_template": self.get_service_template_repo(),
            "internet_template": self.get_internet_template_repo(),
            "voice_template": self.get_voice_template_repo(),
            "bundle_template": self.get_bundle_template_repo(),
        }

    def get_all_instance_repos(self) -> Dict[str, Any]:
        """Get all service instance repositories"""
        return {
            "customer_service": self.get_customer_service_repo(),
            "internet_service": self.get_internet_service_repo(),
            "voice_service": self.get_voice_service_repo(),
        }

    def get_all_provisioning_repos(self) -> Dict[str, Any]:
        """Get all service provisioning repositories"""
        return {
            "provisioning": self.get_provisioning_repo(),
            "provisioning_template": self.get_provisioning_template_repo(),
            "provisioning_queue": self.get_provisioning_queue_repo(),
        }

    def get_all_management_repos(self) -> Dict[str, Any]:
        """Get all service management repositories"""
        return {
            "ip_assignment": self.get_ip_assignment_repo(),
            "status_history": self.get_status_history_repo(),
            "suspension": self.get_suspension_repo(),
            "usage_tracking": self.get_usage_tracking_repo(),
            "alert": self.get_alert_repo(),
        }

    def get_all_repos(self) -> Dict[str, Any]:
        """Get all service repositories"""
        all_repos = {}
        all_repos.update(self.get_all_template_repos())
        all_repos.update(self.get_all_instance_repos())
        all_repos.update(self.get_all_provisioning_repos())
        all_repos.update(self.get_all_management_repos())
        return all_repos

    # Repository Statistics and Health Check
    def get_repository_stats(self) -> Dict[str, Any]:
        """Get statistics about loaded repositories"""
        return {
            "total_repositories": len(self._repositories),
            "loaded_repositories": list(self._repositories.keys()),
            "template_repos": len(
                [k for k in self._repositories.keys() if "template" in k]
            ),
            "instance_repos": len(
                [
                    k
                    for k in self._repositories.keys()
                    if "service" in k and "template" not in k
                ]
            ),
            "provisioning_repos": len(
                [k for k in self._repositories.keys() if "provisioning" in k]
            ),
            "management_repos": len(
                [
                    k
                    for k in self._repositories.keys()
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

    def validate_repositories(self) -> Dict[str, Any]:
        """Validate all repositories are properly configured"""
        validation_results = {"is_valid": True, "errors": [], "warnings": []}

        # Test database connection
        try:
            self.db.execute("SELECT 1")
        except Exception as e:
            validation_results["is_valid"] = False
            validation_results["errors"].append(f"Database connection failed: {str(e)}")

        # Test repository instantiation
        repository_types = [
            ("service_template", ServiceTemplateRepository),
            ("internet_template", InternetServiceTemplateRepository),
            ("voice_template", VoiceServiceTemplateRepository),
            ("bundle_template", BundleServiceTemplateRepository),
            ("customer_service", CustomerServiceRepository),
            ("internet_service", CustomerInternetServiceRepository),
            ("voice_service", CustomerVoiceServiceRepository),
            ("provisioning", ServiceProvisioningRepository),
            ("provisioning_template", ProvisioningTemplateRepository),
            ("provisioning_queue", ProvisioningQueueRepository),
            ("ip_assignment", ServiceIPAssignmentRepository),
            ("status_history", ServiceStatusHistoryRepository),
            ("suspension", ServiceSuspensionRepository),
            ("usage_tracking", ServiceUsageTrackingRepository),
            ("alert", ServiceAlertRepository),
        ]

        for repo_name, repo_class in repository_types:
            try:
                repo_instance = repo_class(self.db)
                if not hasattr(repo_instance, "model"):
                    validation_results["warnings"].append(
                        f"Repository {repo_name} missing model attribute"
                    )
            except Exception as e:
                validation_results["is_valid"] = False
                validation_results["errors"].append(
                    f"Failed to instantiate {repo_name}: {str(e)}"
                )

        return validation_results

    def clear_cache(self):
        """Clear repository cache"""
        self._repositories.clear()


# Global factory instance management
_factory_instances: Dict[str, ServiceRepositoryFactory] = {}


def get_service_repository_factory(
    db: Session, cache_key: Optional[str] = None
) -> ServiceRepositoryFactory:
    """
    Get or create a service repository factory instance

    Args:
        db: Database session
        cache_key: Optional cache key for factory instance reuse

    Returns:
        ServiceRepositoryFactory instance
    """
    if cache_key and cache_key in _factory_instances:
        # Update database session in cached factory
        _factory_instances[cache_key].db = db
        return _factory_instances[cache_key]

    factory = ServiceRepositoryFactory(db)

    if cache_key:
        _factory_instances[cache_key] = factory

    return factory


def clear_factory_cache():
    """Clear all cached factory instances"""
    global _factory_instances
    _factory_instances.clear()


# Dependency injection helpers for FastAPI
def get_service_templates_repos(db: Session) -> Dict[str, Any]:
    """Dependency injection for service template repositories"""
    factory = get_service_repository_factory(db)
    return factory.get_all_template_repos()


def get_service_instances_repos(db: Session) -> Dict[str, Any]:
    """Dependency injection for service instance repositories"""
    factory = get_service_repository_factory(db)
    return factory.get_all_instance_repos()


def get_service_provisioning_repos(db: Session) -> Dict[str, Any]:
    """Dependency injection for service provisioning repositories"""
    factory = get_service_repository_factory(db)
    return factory.get_all_provisioning_repos()


def get_service_management_repos(db: Session) -> Dict[str, Any]:
    """Dependency injection for service management repositories"""
    factory = get_service_repository_factory(db)
    return factory.get_all_management_repos()


def get_all_service_repos(db: Session) -> Dict[str, Any]:
    """Dependency injection for all service repositories"""
    factory = get_service_repository_factory(db)
    return factory.get_all_repos()


# Configuration and utilities
SERVICE_REPOSITORY_CONFIG = {
    "cache_enabled": True,
    "validation_on_startup": True,
    "auto_clear_cache_on_error": True,
    "default_page_size": 50,
    "max_page_size": 200,
    "enable_query_logging": False,
    "enable_performance_monitoring": True,
}


def configure_service_repositories(config: Dict[str, Any]):
    """Configure service repository behavior"""
    global SERVICE_REPOSITORY_CONFIG
    SERVICE_REPOSITORY_CONFIG.update(config)


def get_service_repository_config() -> Dict[str, Any]:
    """Get current service repository configuration"""
    return SERVICE_REPOSITORY_CONFIG.copy()


# Health check and monitoring
def health_check_service_repositories(db: Session) -> Dict[str, Any]:
    """Perform health check on service repositories"""
    factory = get_service_repository_factory(db)

    health_status = {
        "status": "healthy",
        "timestamp": str(datetime.now()),
        "database_connection": "ok",
        "repository_validation": "ok",
        "factory_stats": factory.get_repository_stats(),
        "errors": [],
        "warnings": [],
    }

    # Validate repositories
    validation_results = factory.validate_repositories()

    if not validation_results["is_valid"]:
        health_status["status"] = "unhealthy"
        health_status["repository_validation"] = "failed"
        health_status["errors"].extend(validation_results["errors"])

    if validation_results["warnings"]:
        health_status["warnings"].extend(validation_results["warnings"])

    return health_status
