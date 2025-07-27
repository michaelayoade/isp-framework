"""
Settings and configuration models for ISP Framework.

Provides runtime editable settings, feature flags, and configuration management.
"""
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Union
from enum import Enum
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON, Index, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.core.audit import AuditMixin


class SettingType(str, Enum):
    """Types of settings."""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    JSON = "json"
    SECRET = "secret"  # Encrypted values


class SettingCategory(str, Enum):
    """Categories of settings."""
    SYSTEM = "system"
    BILLING = "billing"
    NETWORK = "network"
    SECURITY = "security"
    COMMUNICATION = "communication"
    INTEGRATION = "integration"
    FEATURE_FLAGS = "feature_flags"
    UI = "ui"


class Setting(Base, AuditMixin):
    """Runtime editable settings table."""
    
    __tablename__ = "settings"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(255), unique=True, nullable=False, index=True)
    value = Column(Text, nullable=True)
    default_value = Column(Text, nullable=True)
    setting_type = Column(String(20), nullable=False, default=SettingType.STRING)
    category = Column(String(50), nullable=False, default=SettingCategory.SYSTEM)
    description = Column(Text, nullable=True)
    is_secret = Column(Boolean, default=False, nullable=False)
    is_readonly = Column(Boolean, default=False, nullable=False)
    validation_regex = Column(String(500), nullable=True)
    min_value = Column(String(50), nullable=True)  # For numeric types
    max_value = Column(String(50), nullable=True)  # For numeric types
    allowed_values = Column(JSON, nullable=True)  # For enum-like settings
    requires_restart = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Metadata
    display_name = Column(String(255), nullable=True)
    help_text = Column(Text, nullable=True)
    display_order = Column(Integer, default=0)
    
    # Relationships
    setting_history = relationship("SettingHistory", back_populates="setting", cascade="all, delete-orphan", lazy="dynamic")
    
    # Indexes
    __table_args__ = (
        Index('ix_settings_category_active', 'category', 'is_active'),
        Index('ix_settings_type_category', 'setting_type', 'category'),
    )
    
    def __repr__(self):
        return f"<Setting(key={self.key}, category={self.category})>"
    
    def get_typed_value(self) -> Any:
        """Get the value converted to the appropriate Python type."""
        if self.value is None:
            return self.get_typed_default()
        
        try:
            if self.setting_type == SettingType.BOOLEAN:
                return str(self.value).lower() in ('true', '1', 'yes', 'on')
            elif self.setting_type == SettingType.INTEGER:
                return int(self.value)
            elif self.setting_type == SettingType.FLOAT:
                return float(self.value)
            elif self.setting_type == SettingType.JSON:
                import json
                return json.loads(self.value)
            else:  # STRING or SECRET
                return str(self.value)
        except (ValueError, TypeError, json.JSONDecodeError):
            return self.get_typed_default()
    
    def get_typed_default(self) -> Any:
        """Get the default value converted to the appropriate Python type."""
        if self.default_value is None:
            if self.setting_type == SettingType.BOOLEAN:
                return False
            elif self.setting_type == SettingType.INTEGER:
                return 0
            elif self.setting_type == SettingType.FLOAT:
                return 0.0
            elif self.setting_type == SettingType.JSON:
                return {}
            else:
                return ""
        
        try:
            if self.setting_type == SettingType.BOOLEAN:
                return str(self.default_value).lower() in ('true', '1', 'yes', 'on')
            elif self.setting_type == SettingType.INTEGER:
                return int(self.default_value)
            elif self.setting_type == SettingType.FLOAT:
                return float(self.default_value)
            elif self.setting_type == SettingType.JSON:
                import json
                return json.loads(self.default_value)
            else:
                return str(self.default_value)
        except (ValueError, TypeError, json.JSONDecodeError):
            return self.default_value


class SettingHistory(Base):
    """History of setting changes for audit trail."""
    
    __tablename__ = "setting_history"
    
    id = Column(Integer, primary_key=True, index=True)
    setting_id = Column(Integer, ForeignKey("settings.id"), nullable=False, index=True)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    changed_by_id = Column(Integer, nullable=True)  # Administrator ID
    changed_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), nullable=False)
    change_reason = Column(String(500), nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    
    # Relationship
    setting = relationship("Setting", back_populates="setting_history")
    
    def __repr__(self):
        return f"<SettingHistory(setting_id={self.setting_id}, changed_at={self.changed_at})>"


class FeatureFlag(Base, AuditMixin):
    """Feature flags for controlling application features."""
    
    __tablename__ = "feature_flags"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    is_enabled = Column(Boolean, default=False, nullable=False)
    
    # Targeting
    enabled_for_all = Column(Boolean, default=False, nullable=False)
    enabled_percentage = Column(Integer, default=0, nullable=False)  # 0-100
    enabled_user_ids = Column(JSON, nullable=True)  # List of user IDs
    enabled_ip_ranges = Column(JSON, nullable=True)  # List of IP ranges
    enabled_environments = Column(JSON, nullable=True)  # List of environments
    
    # Metadata
    category = Column(String(50), nullable=False, default="general")
    tags = Column(JSON, nullable=True)
    rollout_start_date = Column(DateTime(timezone=True), nullable=True)
    rollout_end_date = Column(DateTime(timezone=True), nullable=True)
    
    # Dependencies
    depends_on_flags = Column(JSON, nullable=True)  # List of flag names this depends on
    
    def __repr__(self):
        return f"<FeatureFlag(name={self.name}, enabled={self.is_enabled})>"
    
    def is_enabled_for_user(self, user_id: Optional[int] = None, 
                           ip_address: Optional[str] = None,
                           environment: Optional[str] = None) -> bool:
        """Check if feature is enabled for specific user/context."""
        if not self.is_enabled:
            return False
        
        # Check date range
        now = datetime.now(timezone.utc)
        if self.rollout_start_date and now < self.rollout_start_date:
            return False
        if self.rollout_end_date and now > self.rollout_end_date:
            return False
        
        # Check dependencies
        if self.depends_on_flags:
            # Would need to check other flags - simplified for now
            pass
        
        # Check targeting
        if self.enabled_for_all:
            return True
        
        # Check specific user IDs
        if user_id and self.enabled_user_ids:
            if user_id in self.enabled_user_ids:
                return True
        
        # Check IP ranges
        if ip_address and self.enabled_ip_ranges:
            import ipaddress
            try:
                ip = ipaddress.ip_address(ip_address)
                for range_str in self.enabled_ip_ranges:
                    if ip in ipaddress.ip_network(range_str):
                        return True
            except ValueError:
                pass
        
        # Check environments
        if environment and self.enabled_environments:
            if environment in self.enabled_environments:
                return True
        
        # Check percentage rollout
        if self.enabled_percentage > 0:
            # Simple hash-based percentage (deterministic)
            import hashlib
            hash_input = f"{self.name}:{user_id or ip_address or 'anonymous'}"
            hash_value = int(hashlib.md5(hash_input.encode()).hexdigest()[:8], 16)
            percentage = (hash_value % 100) + 1
            return percentage <= self.enabled_percentage
        
        return False


class ConfigurationTemplate(Base, AuditMixin):
    """Templates for common configuration sets."""
    
    __tablename__ = "configuration_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=False)
    template_data = Column(JSON, nullable=False)  # Settings key-value pairs
    is_active = Column(Boolean, default=True, nullable=False)
    
    def __repr__(self):
        return f"<ConfigurationTemplate(name={self.name}, category={self.category})>"


# Default settings that should be created on system initialization
DEFAULT_SETTINGS = [
    # System settings
    {
        "key": "system.maintenance_mode",
        "value": "false",
        "default_value": "false",
        "setting_type": SettingType.BOOLEAN,
        "category": SettingCategory.SYSTEM,
        "description": "Enable maintenance mode to block non-admin access",
        "display_name": "Maintenance Mode",
        "requires_restart": False
    },
    {
        "key": "system.max_upload_size_mb",
        "value": "100",
        "default_value": "100",
        "setting_type": SettingType.INTEGER,
        "category": SettingCategory.SYSTEM,
        "description": "Maximum file upload size in megabytes",
        "display_name": "Max Upload Size (MB)",
        "min_value": "1",
        "max_value": "1000"
    },
    
    # Billing settings
    {
        "key": "billing.grace_period_days",
        "value": "7",
        "default_value": "7",
        "setting_type": SettingType.INTEGER,
        "category": SettingCategory.BILLING,
        "description": "Grace period in days before service suspension",
        "display_name": "Billing Grace Period (Days)",
        "min_value": "0",
        "max_value": "30"
    },
    {
        "key": "billing.auto_suspend_enabled",
        "value": "true",
        "default_value": "true",
        "setting_type": SettingType.BOOLEAN,
        "category": SettingCategory.BILLING,
        "description": "Automatically suspend services for overdue accounts",
        "display_name": "Auto Suspend Services"
    },
    
    # Security settings
    {
        "key": "security.session_timeout_minutes",
        "value": "60",
        "default_value": "60",
        "setting_type": SettingType.INTEGER,
        "category": SettingCategory.SECURITY,
        "description": "User session timeout in minutes",
        "display_name": "Session Timeout (Minutes)",
        "min_value": "5",
        "max_value": "480"
    },
    {
        "key": "security.password_min_length",
        "value": "8",
        "default_value": "8",
        "setting_type": SettingType.INTEGER,
        "category": SettingCategory.SECURITY,
        "description": "Minimum password length requirement",
        "display_name": "Minimum Password Length",
        "min_value": "6",
        "max_value": "50"
    },
    
    # Feature flags
    {
        "key": "features.customer_portal_enabled",
        "value": "true",
        "default_value": "true",
        "setting_type": SettingType.BOOLEAN,
        "category": SettingCategory.FEATURE_FLAGS,
        "description": "Enable customer portal access",
        "display_name": "Customer Portal Enabled"
    },
    {
        "key": "features.reseller_portal_enabled",
        "value": "false",
        "default_value": "false",
        "setting_type": SettingType.BOOLEAN,
        "category": SettingCategory.FEATURE_FLAGS,
        "description": "Enable reseller portal access",
        "display_name": "Reseller Portal Enabled"
    },
    
    # Communication settings
    {
        "key": "communication.smtp_enabled",
        "value": "false",
        "default_value": "false",
        "setting_type": SettingType.BOOLEAN,
        "category": SettingCategory.COMMUNICATION,
        "description": "Enable SMTP email sending",
        "display_name": "SMTP Enabled"
    },
    {
        "key": "communication.sms_enabled",
        "value": "false",
        "default_value": "false",
        "setting_type": SettingType.BOOLEAN,
        "category": SettingCategory.COMMUNICATION,
        "description": "Enable SMS notifications",
        "display_name": "SMS Enabled"
    }
]
