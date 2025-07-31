"""
ISP Service Management System - Services Module

Complete modular service management system with:
- Service templates (what can be sold)
- Customer service instances (what customers have)
- Provisioning workflows (how services are deployed)
- Service management (IP assignment, status tracking, suspension)

This modular approach provides clean separation of concerns and easy maintenance.
"""

# Import all enums
from .enums import (
    BillingModel,
    ChangeMethod,
    ConnectionType,
    ContentFilterLevel,
    IPAssignmentType,
    ProvisioningStatus,
    QualityProfile,
    ServiceCategory,
    ServiceStatus,
    ServiceSubcategory,
    ServiceType,
    SupportLevel,
    SuspensionReason,
    SuspensionType,
    TrafficPriority,
    VoiceCodec,
)

# Import customer service instances
from .instances import CustomerInternetService, CustomerService, CustomerVoiceService

# Import management models
from .management import (
    ServiceAlert,
    ServiceIPAssignment,
    ServiceStatusHistory,
    ServiceSuspension,
    ServiceUsageTracking,
)

# Import provisioning models
from .provisioning import ProvisioningQueue, ProvisioningTemplate, ServiceProvisioning

# Import service templates
from .templates import (
    BundleServiceTemplate,
    InternetServiceTemplate,
    ServiceTemplate,
    VoiceServiceTemplate,
)

# Export all models for easy importing
__all__ = [
    # Enums
    "ServiceStatus",
    "ServiceType",
    "ProvisioningStatus",
    "SuspensionReason",
    "ConnectionType",
    "IPAssignmentType",
    "SuspensionType",
    "ServiceCategory",
    "ServiceSubcategory",
    "QualityProfile",
    "SupportLevel",
    "ChangeMethod",
    "BillingModel",
    "VoiceCodec",
    "TrafficPriority",
    "ContentFilterLevel",
    # Service Templates
    "ServiceTemplate",
    "InternetServiceTemplate",
    "VoiceServiceTemplate",
    "BundleServiceTemplate",
    # Customer Service Instances
    "CustomerService",
    "CustomerInternetService",
    "CustomerVoiceService",
    # Provisioning
    "ServiceProvisioning",
    "ProvisioningTemplate",
    "ProvisioningQueue",
    # Management
    "ServiceIPAssignment",
    "ServiceStatusHistory",
    "ServiceSuspension",
    "ServiceUsageTracking",
    "ServiceAlert",
]


# Convenience functions for common operations
def get_all_service_models():
    """Get all service-related model classes"""
    return [
        ServiceTemplate,
        InternetServiceTemplate,
        VoiceServiceTemplate,
        BundleServiceTemplate,
        CustomerService,
        CustomerInternetService,
        CustomerVoiceService,
        ServiceProvisioning,
        ProvisioningTemplate,
        ProvisioningQueue,
        ServiceIPAssignment,
        ServiceStatusHistory,
        ServiceSuspension,
        ServiceUsageTracking,
        ServiceAlert,
    ]


def get_template_models():
    """Get service template model classes"""
    return [
        ServiceTemplate,
        InternetServiceTemplate,
        VoiceServiceTemplate,
        BundleServiceTemplate,
    ]


def get_instance_models():
    """Get customer service instance model classes"""
    return [CustomerService, CustomerInternetService, CustomerVoiceService]


def get_provisioning_models():
    """Get provisioning-related model classes"""
    return [ServiceProvisioning, ProvisioningTemplate, ProvisioningQueue]


def get_management_models():
    """Get service management model classes"""
    return [
        ServiceIPAssignment,
        ServiceStatusHistory,
        ServiceSuspension,
        ServiceUsageTracking,
        ServiceAlert,
    ]


# Configuration and validation functions
def validate_service_configuration():
    """Validate service module configuration"""
    errors = []
    warnings = []

    # Check if all required enums are defined
    required_enums = [ServiceStatus, ServiceType, ProvisioningStatus, SuspensionReason]

    for enum_class in required_enums:
        if not hasattr(enum_class, "__members__"):
            errors.append(f"Enum {enum_class.__name__} is not properly defined")

    # Check if all models have required relationships
    models_with_relationships = [
        CustomerService,
        ServiceProvisioning,
        ServiceIPAssignment,
    ]

    for model_class in models_with_relationships:
        if not hasattr(model_class, "__mapper__"):
            warnings.append(f"Model {model_class.__name__} may not be properly mapped")

    return {"is_valid": len(errors) == 0, "errors": errors, "warnings": warnings}


def get_service_statistics():
    """Get service module statistics"""
    return {
        "total_models": len(get_all_service_models()),
        "template_models": len(get_template_models()),
        "instance_models": len(get_instance_models()),
        "provisioning_models": len(get_provisioning_models()),
        "management_models": len(get_management_models()),
        "total_enums": len(
            [
                ServiceStatus,
                ServiceType,
                ProvisioningStatus,
                SuspensionReason,
                ConnectionType,
                IPAssignmentType,
                SuspensionType,
                ServiceCategory,
                ServiceSubcategory,
                QualityProfile,
                SupportLevel,
                ChangeMethod,
                BillingModel,
                VoiceCodec,
                TrafficPriority,
                ContentFilterLevel,
            ]
        ),
    }


# Module metadata
__version__ = "1.0.0"
__author__ = "ISP Framework Team"
__description__ = "Service management system for ISP operations"
__license__ = "MIT"

# Module configuration
SERVICE_MODULE_CONFIG = {
    "version": __version__,
    "modular_architecture": True,
    "supports_internet_services": True,
    "supports_voice_services": True,
    "supports_bundle_services": True,
    "supports_provisioning": True,
    "supports_suspension": True,
    "supports_usage_tracking": True,
    "supports_alerts": True,
    "database_backend": "postgresql",
    "orm": "sqlalchemy",
}
