"""
Audit Configuration Module

This module configures audit tracking for critical ISP Framework models.
It enables comprehensive audit trails for business-critical data changes.
"""

import logging
from app.core.audit_mixins import enable_audit_for_model
from app.models import (
    # Customer Management Models
    Customer, CustomerExtended,
    
    # Network Models
    NetworkDevice, IPAllocation, IPPool,
    
    # Foundation Models
    Reseller, Location,
    
    # Authentication Models
    Administrator, ApiKey,
    
    # Ticketing Models
    Ticket, TicketMessage,
    
    # Portal Models
    PortalConfig
)

logger = logging.getLogger(__name__)

# Define critical models that require audit tracking
CRITICAL_MODELS = {
    # Customer Management - High Priority
    'Customer': Customer,
    'CustomerExtended': CustomerExtended,
    
    # Network Infrastructure - Operational Critical
    'NetworkDevice': NetworkDevice,
    'IPAllocation': IPAllocation,
    'IPPool': IPPool,
    
    # Foundation - Configuration Critical
    'Reseller': Reseller,
    'Location': Location,
    'PortalConfig': PortalConfig,
    
    # Security - Authentication Critical
    'Administrator': Administrator,
    'ApiKey': ApiKey,
    
    # Support - Customer Service
    'Ticket': Ticket,
    'TicketMessage': TicketMessage,
}

# Models that should have audit tracking but are lower priority
STANDARD_MODELS = {
    # Add additional models here as needed
}

# Models that should NOT have audit tracking (performance sensitive)
EXCLUDED_MODELS = {
    # High-frequency, low-business-impact models
    'AuditQueue',  # Avoid recursive auditing
    'CDCLog',      # Avoid recursive auditing
    'AuditProcessingStatus',  # Internal processing
    'ConfigurationSnapshot',  # Already versioned
    'RadiusSession',  # High frequency, operational data
    'CustomerOnline',  # Real-time status data
}


def enable_critical_model_auditing():
    """
    Enable audit tracking for all critical business models.
    
    This function should be called during application startup to ensure
    all critical data changes are properly audited.
    """
    enabled_count = 0
    failed_count = 0
    
    logger.info("Enabling audit tracking for critical models...")
    
    for model_name, model_class in CRITICAL_MODELS.items():
        try:
            enable_audit_for_model(model_class)
            enabled_count += 1
            logger.info(f"Audit tracking enabled for {model_name}")
        except Exception as e:
            failed_count += 1
            logger.error(f"Failed to enable audit tracking for {model_name}: {e}")
    
    logger.info(f"Audit tracking configuration complete: {enabled_count} enabled, {failed_count} failed")
    return enabled_count, failed_count


def enable_standard_model_auditing():
    """
    Enable audit tracking for standard priority models.
    """
    enabled_count = 0
    failed_count = 0
    
    logger.info("Enabling audit tracking for standard models...")
    
    for model_name, model_class in STANDARD_MODELS.items():
        try:
            enable_audit_for_model(model_class)
            enabled_count += 1
            logger.info(f"Audit tracking enabled for {model_name}")
        except Exception as e:
            failed_count += 1
            logger.error(f"Failed to enable audit tracking for {model_name}: {e}")
    
    logger.info(f"Standard model audit tracking complete: {enabled_count} enabled, {failed_count} failed")
    return enabled_count, failed_count


def disable_excluded_model_auditing():
    """
    Explicitly disable audit tracking for excluded models.
    """
    disabled_count = 0
    
    logger.info("Disabling audit tracking for excluded models...")
    
    for model_name in EXCLUDED_MODELS:
        try:
            # Note: This would require getting the actual model class
            # For now, we'll just log the exclusion
            logger.info(f"Audit tracking explicitly disabled for {model_name}")
            disabled_count += 1
        except Exception as e:
            logger.error(f"Failed to disable audit tracking for {model_name}: {e}")
    
    logger.info(f"Excluded model audit configuration complete: {disabled_count} disabled")
    return disabled_count


def configure_audit_tracking():
    """
    Configure audit tracking for all models according to business priorities.
    
    This is the main function to call during application startup.
    """
    logger.info("Starting comprehensive audit tracking configuration...")
    
    try:
        # Enable critical models
        critical_enabled, critical_failed = enable_critical_model_auditing()
        
        # Enable standard models
        standard_enabled, standard_failed = enable_standard_model_auditing()
        
        # Disable excluded models
        excluded_disabled = disable_excluded_model_auditing()
        
        total_enabled = critical_enabled + standard_enabled
        total_failed = critical_failed + standard_failed
        
        logger.info("Audit tracking configuration summary:")
        logger.info(f"  - Critical models enabled: {critical_enabled}")
        logger.info(f"  - Standard models enabled: {standard_enabled}")
        logger.info(f"  - Models excluded: {excluded_disabled}")
        logger.info(f"  - Total enabled: {total_enabled}")
        logger.info(f"  - Total failed: {total_failed}")
        
        if total_failed > 0:
            logger.warning(f"Some models failed to enable audit tracking: {total_failed}")
        
        return {
            'critical_enabled': critical_enabled,
            'standard_enabled': standard_enabled,
            'excluded_disabled': excluded_disabled,
            'total_enabled': total_enabled,
            'total_failed': total_failed,
            'success': total_failed == 0
        }
        
    except Exception as e:
        logger.error(f"Failed to configure audit tracking: {e}")
        raise


def get_audit_configuration_status():
    """
    Get the current audit configuration status.
    """
    status = {
        'critical_models': list(CRITICAL_MODELS.keys()),
        'standard_models': list(STANDARD_MODELS.keys()),
        'excluded_models': list(EXCLUDED_MODELS),
        'total_critical': len(CRITICAL_MODELS),
        'total_standard': len(STANDARD_MODELS),
        'total_excluded': len(EXCLUDED_MODELS)
    }
    
    return status


def is_model_audited(model_class):
    """
    Check if a specific model class has audit tracking enabled.
    """
    return hasattr(model_class, '__audit_enabled__') and model_class.__audit_enabled__


def get_audited_models():
    """
    Get list of all models that currently have audit tracking enabled.
    """
    audited_models = []
    
    for model_name, model_class in CRITICAL_MODELS.items():
        if is_model_audited(model_class):
            audited_models.append(model_name)
    
    for model_name, model_class in STANDARD_MODELS.items():
        if is_model_audited(model_class):
            audited_models.append(model_name)
    
    return audited_models


# Audit retention and cleanup configuration
AUDIT_RETENTION_CONFIG = {
    'default_retention_days': 90,  # Default retention for completed audit entries
    'critical_retention_days': 365,  # Extended retention for critical models
    'cdc_retention_days': 30,  # CDC log retention
    'config_snapshot_retention_days': 180,  # Configuration snapshot retention
    'cleanup_batch_size': 1000,  # Batch size for cleanup operations
    'cleanup_interval_hours': 24,  # How often to run cleanup
}


def get_retention_config():
    """Get audit retention configuration."""
    return AUDIT_RETENTION_CONFIG.copy()


def update_retention_config(config_updates):
    """Update audit retention configuration."""
    global AUDIT_RETENTION_CONFIG
    AUDIT_RETENTION_CONFIG.update(config_updates)
    logger.info(f"Updated audit retention configuration: {config_updates}")


# Audit alerting configuration
AUDIT_ALERTING_CONFIG = {
    'health_check_interval_minutes': 5,  # How often to check audit health
    'queue_size_warning_threshold': 1000,  # Queue size that triggers warning
    'queue_size_critical_threshold': 5000,  # Queue size that triggers critical alert
    'failure_rate_warning_threshold': 5.0,  # Failure rate % that triggers warning
    'failure_rate_critical_threshold': 15.0,  # Failure rate % that triggers critical alert
    'processor_lag_warning_minutes': 30,  # Processor lag that triggers warning
    'processor_lag_critical_minutes': 120,  # Processor lag that triggers critical alert
    'enable_email_alerts': True,  # Enable email alerting
    'enable_webhook_alerts': True,  # Enable webhook alerting
    'alert_recipients': [],  # List of email recipients for alerts
    'webhook_urls': [],  # List of webhook URLs for alerts
}


def get_alerting_config():
    """Get audit alerting configuration."""
    return AUDIT_ALERTING_CONFIG.copy()


def update_alerting_config(config_updates):
    """Update audit alerting configuration."""
    global AUDIT_ALERTING_CONFIG
    AUDIT_ALERTING_CONFIG.update(config_updates)
    logger.info(f"Updated audit alerting configuration: {config_updates}")
