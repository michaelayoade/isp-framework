"""
Settings management service for ISP Framework.

Provides centralized settings management with caching, validation, and secrets handling.
"""
import os
import json
import re
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.core.database import SessionLocal
from app.models.settings import Setting, SettingHistory, FeatureFlag, DEFAULT_SETTINGS
from app.models.settings import SettingType, SettingCategory
from app.core.observability import log_audit_event
import structlog

logger = structlog.get_logger("isp.settings")


class SettingsCache:
    """In-memory cache for settings to avoid database hits."""
    
    def __init__(self):
        self._cache: Dict[str, Any] = {}
        self._last_refresh = None
        self._cache_ttl = 300  # 5 minutes
    
    def get(self, key: str) -> Optional[Any]:
        """Get cached setting value."""
        if self._is_cache_expired():
            return None
        return self._cache.get(key)
    
    def set(self, key: str, value: Any):
        """Set cached setting value."""
        self._cache[key] = value
        if self._last_refresh is None:
            self._last_refresh = datetime.now()
    
    def invalidate(self, key: Optional[str] = None):
        """Invalidate cache for specific key or all keys."""
        if key:
            self._cache.pop(key, None)
        else:
            self._cache.clear()
            self._last_refresh = None
    
    def _is_cache_expired(self) -> bool:
        """Check if cache has expired."""
        if self._last_refresh is None:
            return True
        return (datetime.now() - self._last_refresh).seconds > self._cache_ttl


# Global settings cache
settings_cache = SettingsCache()


class SettingsService:
    """Service for managing application settings."""
    
    def __init__(self, db: Session = None):
        self.db = db or SessionLocal()
        self._should_close_db = db is None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._should_close_db:
            self.db.close()
    
    def get_setting(self, key: str, default: Any = None, use_cache: bool = True) -> Any:
        """Get a setting value by key."""
        # Check cache first
        if use_cache:
            cached_value = settings_cache.get(key)
            if cached_value is not None:
                return cached_value
        
        # Query database
        setting = self.db.query(Setting).filter(
            and_(Setting.key == key, Setting.is_active is True)
        ).first()
        
        if setting:
            value = setting.get_typed_value()
            if use_cache:
                settings_cache.set(key, value)
            return value
        
        return default
    
    def set_setting(self, key: str, value: Any, changed_by_id: Optional[int] = None,
                   change_reason: Optional[str] = None, ip_address: Optional[str] = None,
                   user_agent: Optional[str] = None) -> Setting:
        """Set a setting value."""
        setting = self.db.query(Setting).filter(Setting.key == key).first()
        
        if not setting:
            raise ValueError(f"Setting '{key}' not found")
        
        if setting.is_readonly:
            raise ValueError(f"Setting '{key}' is read-only")
        
        # Validate value
        self._validate_setting_value(setting, value)
        
        # Store old value for history
        old_value = setting.value
        
        # Convert value to string for storage
        if setting.setting_type == SettingType.JSON:
            new_value = json.dumps(value) if value is not None else None
        elif setting.setting_type == SettingType.BOOLEAN:
            new_value = str(bool(value)).lower()
        else:
            new_value = str(value) if value is not None else None
        
        # Update setting
        setting.value = new_value
        setting.updated_at = datetime.now(timezone.utc)
        setting.updated_by_id = changed_by_id
        
        # Create history record
        history = SettingHistory(
            setting_id=setting.id,
            old_value=old_value,
            new_value=new_value,
            changed_by_id=changed_by_id,
            change_reason=change_reason,
            ip_address=ip_address,
            user_agent=user_agent
        )
        self.db.add(history)
        
        self.db.commit()
        
        # Invalidate cache
        settings_cache.invalidate(key)
        
        # Log audit event
        log_audit_event(
            domain="settings",
            event="setting_changed",
            setting_key=key,
            old_value=old_value,
            new_value=new_value,
            changed_by_id=changed_by_id,
            requires_restart=setting.requires_restart
        )
        
        logger.info("Setting updated", 
                   key=key, 
                   old_value=old_value, 
                   new_value=new_value,
                   changed_by_id=changed_by_id)
        
        return setting
    
    def _validate_setting_value(self, setting: Setting, value: Any):
        """Validate a setting value against its constraints."""
        if value is None:
            return  # Allow None values
        
        # Type validation
        if setting.setting_type == SettingType.INTEGER:
            try:
                int_value = int(value)
                if setting.min_value and int_value < int(setting.min_value):
                    raise ValueError(f"Value {int_value} is below minimum {setting.min_value}")
                if setting.max_value and int_value > int(setting.max_value):
                    raise ValueError(f"Value {int_value} is above maximum {setting.max_value}")
            except ValueError as e:
                raise ValueError(f"Invalid integer value: {e}")
        
        elif setting.setting_type == SettingType.FLOAT:
            try:
                float_value = float(value)
                if setting.min_value and float_value < float(setting.min_value):
                    raise ValueError(f"Value {float_value} is below minimum {setting.min_value}")
                if setting.max_value and float_value > float(setting.max_value):
                    raise ValueError(f"Value {float_value} is above maximum {setting.max_value}")
            except ValueError as e:
                raise ValueError(f"Invalid float value: {e}")
        
        elif setting.setting_type == SettingType.BOOLEAN:
            if not isinstance(value, bool) and str(value).lower() not in ('true', 'false', '1', '0', 'yes', 'no'):
                raise ValueError("Invalid boolean value")
        
        elif setting.setting_type == SettingType.JSON:
            try:
                json.dumps(value)
            except (TypeError, ValueError) as e:
                raise ValueError(f"Invalid JSON value: {e}")
        
        # Regex validation
        if setting.validation_regex and isinstance(value, str):
            if not re.match(setting.validation_regex, value):
                raise ValueError(f"Value does not match required pattern: {setting.validation_regex}")
        
        # Allowed values validation
        if setting.allowed_values:
            if value not in setting.allowed_values:
                raise ValueError(f"Value must be one of: {setting.allowed_values}")
    
    def get_settings_by_category(self, category: SettingCategory) -> List[Setting]:
        """Get all settings in a category."""
        return self.db.query(Setting).filter(
            and_(Setting.category == category, Setting.is_active is True)
        ).order_by(Setting.display_order, Setting.key).all()
    
    def get_all_settings(self) -> Dict[str, Any]:
        """Get all settings as a dictionary."""
        settings = self.db.query(Setting).filter(Setting.is_active is True).all()
        return {setting.key: setting.get_typed_value() for setting in settings}
    
    def create_setting(self, key: str, value: Any, setting_type: SettingType,
                      category: SettingCategory, description: str = None,
                      **kwargs) -> Setting:
        """Create a new setting."""
        # Check if setting already exists
        existing = self.db.query(Setting).filter(Setting.key == key).first()
        if existing:
            raise ValueError(f"Setting '{key}' already exists")
        
        # Convert value to string for storage
        if setting_type == SettingType.JSON:
            str_value = json.dumps(value) if value is not None else None
        elif setting_type == SettingType.BOOLEAN:
            str_value = str(bool(value)).lower() if value is not None else None
        else:
            str_value = str(value) if value is not None else None
        
        setting = Setting(
            key=key,
            value=str_value,
            default_value=str_value,
            setting_type=setting_type,
            category=category,
            description=description,
            **kwargs
        )
        
        self.db.add(setting)
        self.db.commit()
        
        log_audit_event(
            domain="settings",
            event="setting_created",
            setting_key=key,
            setting_type=setting_type,
            category=category
        )
        
        return setting
    
    def delete_setting(self, key: str, changed_by_id: Optional[int] = None):
        """Delete a setting (soft delete by marking inactive)."""
        setting = self.db.query(Setting).filter(Setting.key == key).first()
        if not setting:
            raise ValueError(f"Setting '{key}' not found")
        
        if setting.is_readonly:
            raise ValueError(f"Setting '{key}' is read-only and cannot be deleted")
        
        setting.is_active = False
        setting.updated_at = datetime.now(timezone.utc)
        setting.updated_by_id = changed_by_id
        
        self.db.commit()
        
        # Invalidate cache
        settings_cache.invalidate(key)
        
        log_audit_event(
            domain="settings",
            event="setting_deleted",
            setting_key=key,
            changed_by_id=changed_by_id
        )
    
    def get_setting_history(self, key: str, limit: int = 50) -> List[SettingHistory]:
        """Get change history for a setting."""
        setting = self.db.query(Setting).filter(Setting.key == key).first()
        if not setting:
            raise ValueError(f"Setting '{key}' not found")
        
        return self.db.query(SettingHistory).filter(
            SettingHistory.setting_id == setting.id
        ).order_by(SettingHistory.changed_at.desc()).limit(limit).all()
    
    def initialize_default_settings(self):
        """Initialize default settings if they don't exist."""
        created_count = 0
        
        for setting_data in DEFAULT_SETTINGS:
            existing = self.db.query(Setting).filter(Setting.key == setting_data["key"]).first()
            if not existing:
                setting = Setting(**setting_data)
                self.db.add(setting)
                created_count += 1
        
        if created_count > 0:
            self.db.commit()
            logger.info("Default settings initialized", count=created_count)
        
        return created_count


class FeatureFlagService:
    """Service for managing feature flags."""
    
    def __init__(self, db: Session = None):
        self.db = db or SessionLocal()
        self._should_close_db = db is None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._should_close_db:
            self.db.close()
    
    def is_enabled(self, flag_name: str, user_id: Optional[int] = None,
                  ip_address: Optional[str] = None, environment: Optional[str] = None) -> bool:
        """Check if a feature flag is enabled for the given context."""
        flag = self.db.query(FeatureFlag).filter(
            and_(FeatureFlag.name == flag_name, FeatureFlag.is_enabled is True)
        ).first()
        
        if not flag:
            return False
        
        return flag.is_enabled_for_user(user_id, ip_address, environment)
    
    def create_flag(self, name: str, description: str = None, **kwargs) -> FeatureFlag:
        """Create a new feature flag."""
        existing = self.db.query(FeatureFlag).filter(FeatureFlag.name == name).first()
        if existing:
            raise ValueError(f"Feature flag '{name}' already exists")
        
        flag = FeatureFlag(name=name, description=description, **kwargs)
        self.db.add(flag)
        self.db.commit()
        
        log_audit_event(
            domain="feature_flags",
            event="flag_created",
            flag_name=name
        )
        
        return flag
    
    def update_flag(self, name: str, **kwargs) -> FeatureFlag:
        """Update a feature flag."""
        flag = self.db.query(FeatureFlag).filter(FeatureFlag.name == name).first()
        if not flag:
            raise ValueError(f"Feature flag '{name}' not found")
        
        for key, value in kwargs.items():
            if hasattr(flag, key):
                setattr(flag, key, value)
        
        flag.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        
        log_audit_event(
            domain="feature_flags",
            event="flag_updated",
            flag_name=name,
            changes=kwargs
        )
        
        return flag
    
    def get_all_flags(self) -> List[FeatureFlag]:
        """Get all feature flags."""
        return self.db.query(FeatureFlag).order_by(FeatureFlag.name).all()


# Global service instances
def get_settings_service() -> SettingsService:
    """Get a settings service instance."""
    return SettingsService()


def get_feature_flag_service() -> FeatureFlagService:
    """Get a feature flag service instance."""
    return FeatureFlagService()


# Convenience functions
def get_setting(key: str, default: Any = None) -> Any:
    """Get a setting value (convenience function)."""
    with get_settings_service() as service:
        return service.get_setting(key, default)


def is_feature_enabled(flag_name: str, user_id: Optional[int] = None,
                      ip_address: Optional[str] = None, environment: Optional[str] = None) -> bool:
    """Check if a feature flag is enabled (convenience function)."""
    with get_feature_flag_service() as service:
        return service.is_enabled(flag_name, user_id, ip_address, environment)


# Settings-based configuration override
def override_settings_from_env():
    """Override settings from environment variables."""
    with get_settings_service() as service:
        settings = service.get_all_settings()
        
        for key in settings:
            env_key = f"ISP_{key.upper().replace('.', '_')}"
            env_value = os.getenv(env_key)
            
            if env_value is not None:
                try:
                    service.set_setting(key, env_value, change_reason="Environment variable override")
                    logger.info("Setting overridden from environment", key=key, env_key=env_key)
                except Exception as e:
                    logger.warning("Failed to override setting from environment", 
                                 key=key, env_key=env_key, error=str(e))
