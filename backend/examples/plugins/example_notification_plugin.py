"""
Example Notification Plugin for ISP Framework

This is a demonstration plugin that shows how to implement the PluginInterface
and integrate with the ISP Framework's hook system for customer notifications.
"""

import logging
from typing import Dict, Any
from datetime import datetime, timezone

from app.services.plugin_service import PluginInterface


class ExampleNotificationPlugin(PluginInterface):
    """
    Example notification plugin that demonstrates:
    - Plugin initialization and cleanup
    - Configuration management
    - Hook method implementation
    - Health checking
    - Logging integration
    """
    
    def __init__(self, plugin_id: int, config: Dict[str, Any]):
        super().__init__(plugin_id, config)
        
        # Plugin-specific configuration
        self.notification_enabled = config.get('notification_enabled', True)
        self.notification_template = config.get('notification_template', 'Welcome {customer_name}!')
        self.max_retries = config.get('max_retries', 3)
        self.timeout = config.get('timeout', 30)
        
        # Plugin state
        self.initialized = False
        self.notification_count = 0
        self.error_count = 0
        self.last_notification = None
    
    def initialize(self) -> bool:
        """Initialize the notification plugin"""
        try:
            self.logger.info("Initializing Example Notification Plugin")
            
            # Validate configuration
            if not isinstance(self.notification_enabled, bool):
                raise ValueError("notification_enabled must be a boolean")
            
            if not isinstance(self.notification_template, str):
                raise ValueError("notification_template must be a string")
            
            if not isinstance(self.max_retries, int) or self.max_retries < 0:
                raise ValueError("max_retries must be a non-negative integer")
            
            if not isinstance(self.timeout, int) or self.timeout <= 0:
                raise ValueError("timeout must be a positive integer")
            
            # Initialize plugin resources
            self.initialized = True
            self.logger.info("Example Notification Plugin initialized successfully")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Example Notification Plugin: {str(e)}")
            return False
    
    def cleanup(self) -> bool:
        """Cleanup plugin resources"""
        try:
            self.logger.info("Cleaning up Example Notification Plugin")
            
            # Cleanup any resources
            self.initialized = False
            
            self.logger.info(f"Plugin processed {self.notification_count} notifications with {self.error_count} errors")
            self.logger.info("Example Notification Plugin cleaned up successfully")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup Example Notification Plugin: {str(e)}")
            return False
    
    def get_info(self) -> Dict[str, Any]:
        """Get plugin information and status"""
        return {
            "name": "Example Notification Plugin",
            "version": "1.0.0",
            "author": "ISP Framework Team",
            "description": "Example plugin demonstrating notification functionality",
            "status": "active" if self.initialized else "inactive",
            "statistics": {
                "notification_count": self.notification_count,
                "error_count": self.error_count,
                "last_notification": self.last_notification.isoformat() if self.last_notification else None
            },
            "configuration": {
                "notification_enabled": self.notification_enabled,
                "max_retries": self.max_retries,
                "timeout": self.timeout
            }
        }
    
    def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check"""
        checks = []
        overall_status = "healthy"
        
        # Check initialization status
        if self.initialized:
            checks.append({
                "name": "initialization",
                "status": "pass",
                "message": "Plugin is properly initialized"
            })
        else:
            checks.append({
                "name": "initialization",
                "status": "fail",
                "message": "Plugin is not initialized"
            })
            overall_status = "error"
        
        # Check configuration
        try:
            if self.notification_enabled and self.notification_template:
                checks.append({
                    "name": "configuration",
                    "status": "pass",
                    "message": "Configuration is valid"
                })
            else:
                checks.append({
                    "name": "configuration",
                    "status": "warning",
                    "message": "Notifications are disabled or template is empty"
                })
                if overall_status == "healthy":
                    overall_status = "warning"
        except Exception as e:
            checks.append({
                "name": "configuration",
                "status": "fail",
                "message": f"Configuration error: {str(e)}"
            })
            overall_status = "error"
        
        # Check error rate
        if self.notification_count > 0:
            error_rate = (self.error_count / self.notification_count) * 100
            if error_rate > 50:
                checks.append({
                    "name": "error_rate",
                    "status": "fail",
                    "message": f"High error rate: {error_rate:.1f}%"
                })
                overall_status = "error"
            elif error_rate > 20:
                checks.append({
                    "name": "error_rate",
                    "status": "warning",
                    "message": f"Elevated error rate: {error_rate:.1f}%"
                })
                if overall_status == "healthy":
                    overall_status = "warning"
            else:
                checks.append({
                    "name": "error_rate",
                    "status": "pass",
                    "message": f"Error rate is acceptable: {error_rate:.1f}%"
                })
        else:
            checks.append({
                "name": "error_rate",
                "status": "pass",
                "message": "No notifications processed yet"
            })
        
        return {
            "status": overall_status,
            "checks": checks,
            "last_check": datetime.now(timezone.utc).isoformat(),
            "uptime": "N/A"  # Could calculate actual uptime
        }
    
    # Hook Methods - These are called by the framework when events occur
    
    def on_customer_created(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Hook method called when a new customer is created
        This demonstrates the 'action' hook type
        """
        try:
            if not self.initialized or not self.notification_enabled:
                return {"processed": False, "reason": "Plugin not ready or disabled"}
            
            customer_name = customer_data.get('name', 'Customer')
            customer_email = customer_data.get('email', '')
            
            # Format notification message
            message = self.notification_template.format(
                customer_name=customer_name,
                customer_email=customer_email
            )
            
            # Simulate sending notification
            self.logger.info(f"Sending welcome notification to {customer_name} ({customer_email})")
            self.logger.info(f"Notification message: {message}")
            
            # Update statistics
            self.notification_count += 1
            self.last_notification = datetime.now(timezone.utc)
            
            return {
                "processed": True,
                "customer_id": customer_data.get('id'),
                "customer_name": customer_name,
                "message": message,
                "timestamp": self.last_notification.isoformat()
            }
            
        except Exception as e:
            self.error_count += 1
            self.logger.error(f"Failed to process customer creation notification: {str(e)}")
            return {
                "processed": False,
                "error": str(e),
                "customer_id": customer_data.get('id')
            }
    
    def filter_customer_data(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Hook method that filters/modifies customer data
        This demonstrates the 'filter' hook type
        """
        try:
            if not self.initialized:
                return customer_data
            
            # Example: Add a notification preference field
            if 'preferences' not in customer_data:
                customer_data['preferences'] = {}
            
            customer_data['preferences']['notifications_enabled'] = self.notification_enabled
            customer_data['preferences']['processed_by_plugin'] = True
            customer_data['preferences']['processed_at'] = datetime.now(timezone.utc).isoformat()
            
            self.logger.debug(f"Filtered customer data for customer {customer_data.get('id')}")
            
            return customer_data
            
        except Exception as e:
            self.logger.error(f"Failed to filter customer data: {str(e)}")
            return customer_data
    
    def on_billing_event(self, billing_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Hook method called for billing events
        This demonstrates cross-domain plugin integration
        """
        try:
            if not self.initialized or not self.notification_enabled:
                return {"processed": False, "reason": "Plugin not ready or disabled"}
            
            event_type = billing_data.get('event_type', 'unknown')
            customer_id = billing_data.get('customer_id')
            amount = billing_data.get('amount', 0)
            
            # Process different billing events
            if event_type == 'payment_received':
                message = f"Payment of ${amount} received for customer {customer_id}"
            elif event_type == 'invoice_generated':
                message = f"Invoice for ${amount} generated for customer {customer_id}"
            elif event_type == 'payment_failed':
                message = f"Payment of ${amount} failed for customer {customer_id}"
            else:
                message = f"Billing event '{event_type}' for customer {customer_id}"
            
            self.logger.info(f"Processing billing notification: {message}")
            
            # Update statistics
            self.notification_count += 1
            self.last_notification = datetime.now(timezone.utc)
            
            return {
                "processed": True,
                "event_type": event_type,
                "customer_id": customer_id,
                "message": message,
                "timestamp": self.last_notification.isoformat()
            }
            
        except Exception as e:
            self.error_count += 1
            self.logger.error(f"Failed to process billing notification: {str(e)}")
            return {
                "processed": False,
                "error": str(e),
                "event_type": billing_data.get('event_type'),
                "customer_id": billing_data.get('customer_id')
            }
    
    # Custom Plugin Methods - These can be called directly via the execute endpoint
    
    def send_custom_notification(self, recipient: str, message: str, **kwargs) -> Dict[str, Any]:
        """
        Custom method that can be called via the plugin execute endpoint
        """
        try:
            if not self.initialized:
                return {"success": False, "error": "Plugin not initialized"}
            
            self.logger.info(f"Sending custom notification to {recipient}: {message}")
            
            # Simulate sending notification
            # In a real plugin, this would integrate with actual notification services
            
            self.notification_count += 1
            self.last_notification = datetime.now(timezone.utc)
            
            return {
                "success": True,
                "recipient": recipient,
                "message": message,
                "sent_at": self.last_notification.isoformat(),
                "additional_params": kwargs
            }
            
        except Exception as e:
            self.error_count += 1
            self.logger.error(f"Failed to send custom notification: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "recipient": recipient
            }
    
    def get_notification_statistics(self) -> Dict[str, Any]:
        """
        Get detailed notification statistics
        """
        return {
            "total_notifications": self.notification_count,
            "total_errors": self.error_count,
            "success_rate": ((self.notification_count - self.error_count) / max(self.notification_count, 1)) * 100,
            "last_notification": self.last_notification.isoformat() if self.last_notification else None,
            "plugin_status": "active" if self.initialized else "inactive",
            "configuration": {
                "enabled": self.notification_enabled,
                "template": self.notification_template,
                "max_retries": self.max_retries,
                "timeout": self.timeout
            }
        }
    
    def reset_statistics(self) -> Dict[str, Any]:
        """
        Reset plugin statistics
        """
        old_count = self.notification_count
        old_errors = self.error_count
        
        self.notification_count = 0
        self.error_count = 0
        self.last_notification = None
        
        self.logger.info("Plugin statistics reset")
        
        return {
            "success": True,
            "message": "Statistics reset successfully",
            "previous_stats": {
                "notifications": old_count,
                "errors": old_errors
            },
            "reset_at": datetime.now(timezone.utc).isoformat()
        }
