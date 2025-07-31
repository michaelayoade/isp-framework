"""
Plugin System Repository Layer for ISP Framework

Repository classes for plugin management with comprehensive CRUD operations,
filtering, and database interactions for all plugin-related entities.
"""

from datetime import datetime
from typing import List, Optional, Tuple

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.models.plugins import (
    Plugin,
    PluginConfiguration,
    PluginDependency,
    PluginHook,
    PluginLog,
    PluginPriority,
    PluginRegistry,
    PluginStatus,
    PluginTemplate,
    PluginType,
)
from app.repositories.base import BaseRepository


class PluginRepository(BaseRepository[Plugin]):
    """Repository for Plugin model"""

    def __init__(self, db: Session):
        super().__init__(db, Plugin)

    def get_by_name(self, name: str) -> Optional[Plugin]:
        """Get plugin by name"""
        return self.db.query(Plugin).filter(Plugin.name == name).first()

    def get_by_status(self, status: PluginStatus) -> List[Plugin]:
        """Get plugins by status"""
        return self.db.query(Plugin).filter(Plugin.status == status).all()

    def get_by_type(self, plugin_type: PluginType) -> List[Plugin]:
        """Get plugins by type"""
        return self.db.query(Plugin).filter(Plugin.plugin_type == plugin_type).all()

    def get_enabled_plugins(self) -> List[Plugin]:
        """Get all enabled plugins"""
        return self.db.query(Plugin).filter(Plugin.is_enabled is True).all()

    def get_system_plugins(self) -> List[Plugin]:
        """Get all system plugins"""
        return self.db.query(Plugin).filter(Plugin.is_system is True).all()

    def search_plugins(
        self,
        search_term: Optional[str] = None,
        plugin_type: Optional[PluginType] = None,
        status: Optional[PluginStatus] = None,
        is_enabled: Optional[bool] = None,
        is_system: Optional[bool] = None,
        category: Optional[str] = None,
        author: Optional[str] = None,
        tags: Optional[List[str]] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[Plugin], int]:
        """Search plugins with comprehensive filtering"""
        query = self.db.query(Plugin)

        if search_term:
            query = query.filter(
                or_(
                    Plugin.name.ilike(f"%{search_term}%"),
                    Plugin.display_name.ilike(f"%{search_term}%"),
                    Plugin.description.ilike(f"%{search_term}%"),
                )
            )

        if plugin_type:
            query = query.filter(Plugin.plugin_type == plugin_type)

        if status:
            query = query.filter(Plugin.status == status)

        if is_enabled is not None:
            query = query.filter(Plugin.is_enabled == is_enabled)

        if is_system is not None:
            query = query.filter(Plugin.is_system == is_system)

        if category:
            query = query.filter(Plugin.category == category)

        if author:
            query = query.filter(Plugin.author.ilike(f"%{author}%"))

        if tags:
            for tag in tags:
                query = query.filter(Plugin.tags.contains([tag]))

        total = query.count()
        plugins = (
            query.order_by(Plugin.created_at.desc()).offset(skip).limit(limit).all()
        )

        return plugins, total

    def get_plugins_by_priority(self, priority: PluginPriority) -> List[Plugin]:
        """Get plugins by priority"""
        return self.db.query(Plugin).filter(Plugin.priority == priority).all()

    def get_most_loaded_plugins(self, limit: int = 10) -> List[Plugin]:
        """Get plugins with highest load count"""
        return (
            self.db.query(Plugin).order_by(Plugin.load_count.desc()).limit(limit).all()
        )

    def get_plugins_with_errors(self) -> List[Plugin]:
        """Get plugins that have errors"""
        return self.db.query(Plugin).filter(Plugin.error_count > 0).all()

    def get_plugins_by_installed_by(self, user_id: int) -> List[Plugin]:
        """Get plugins installed by specific user"""
        return self.db.query(Plugin).filter(Plugin.installed_by == user_id).all()


class PluginConfigurationRepository(BaseRepository[PluginConfiguration]):
    """Repository for PluginConfiguration model"""

    def __init__(self, db: Session):
        super().__init__(db, PluginConfiguration)

    def get_by_plugin_id(self, plugin_id: int) -> List[PluginConfiguration]:
        """Get all configurations for a plugin"""
        return (
            self.db.query(PluginConfiguration)
            .filter(PluginConfiguration.plugin_id == plugin_id)
            .all()
        )

    def get_by_plugin_and_key(
        self, plugin_id: int, config_key: str
    ) -> Optional[PluginConfiguration]:
        """Get specific configuration by plugin ID and key"""
        return (
            self.db.query(PluginConfiguration)
            .filter(
                and_(
                    PluginConfiguration.plugin_id == plugin_id,
                    PluginConfiguration.config_key == config_key,
                )
            )
            .first()
        )

    def get_required_configs(self, plugin_id: int) -> List[PluginConfiguration]:
        """Get required configurations for a plugin"""
        return (
            self.db.query(PluginConfiguration)
            .filter(
                and_(
                    PluginConfiguration.plugin_id == plugin_id,
                    PluginConfiguration.is_required is True,
                )
            )
            .all()
        )

    def get_encrypted_configs(self, plugin_id: int) -> List[PluginConfiguration]:
        """Get encrypted configurations for a plugin"""
        return (
            self.db.query(PluginConfiguration)
            .filter(
                and_(
                    PluginConfiguration.plugin_id == plugin_id,
                    PluginConfiguration.is_encrypted is True,
                )
            )
            .all()
        )

    def get_configs_by_type(
        self, plugin_id: int, config_type: str
    ) -> List[PluginConfiguration]:
        """Get configurations by type for a plugin"""
        return (
            self.db.query(PluginConfiguration)
            .filter(
                and_(
                    PluginConfiguration.plugin_id == plugin_id,
                    PluginConfiguration.config_type == config_type,
                )
            )
            .all()
        )


class PluginHookRepository(BaseRepository[PluginHook]):
    """Repository for PluginHook model"""

    def __init__(self, db: Session):
        super().__init__(db, PluginHook)

    def get_by_plugin_id(self, plugin_id: int) -> List[PluginHook]:
        """Get all hooks for a plugin"""
        return self.db.query(PluginHook).filter(PluginHook.plugin_id == plugin_id).all()

    def get_by_hook_name(self, hook_name: str) -> List[PluginHook]:
        """Get all hooks by name"""
        return (
            self.db.query(PluginHook)
            .filter(PluginHook.hook_name == hook_name)
            .order_by(PluginHook.priority.asc())
            .all()
        )

    def get_active_hooks(self, hook_name: str) -> List[PluginHook]:
        """Get active hooks by name, ordered by priority"""
        return (
            self.db.query(PluginHook)
            .filter(
                and_(PluginHook.hook_name == hook_name, PluginHook.is_active is True)
            )
            .order_by(PluginHook.priority.asc())
            .all()
        )

    def get_by_hook_type(self, hook_type: str) -> List[PluginHook]:
        """Get hooks by type"""
        return self.db.query(PluginHook).filter(PluginHook.hook_type == hook_type).all()

    def get_hooks_by_plugin_and_type(
        self, plugin_id: int, hook_type: str
    ) -> List[PluginHook]:
        """Get hooks by plugin ID and type"""
        return (
            self.db.query(PluginHook)
            .filter(
                and_(
                    PluginHook.plugin_id == plugin_id, PluginHook.hook_type == hook_type
                )
            )
            .all()
        )

    def get_most_executed_hooks(self, limit: int = 10) -> List[PluginHook]:
        """Get hooks with highest execution count"""
        return (
            self.db.query(PluginHook)
            .order_by(PluginHook.execution_count.desc())
            .limit(limit)
            .all()
        )

    def get_slowest_hooks(self, limit: int = 10) -> List[PluginHook]:
        """Get hooks with highest average execution time"""
        return (
            self.db.query(PluginHook)
            .order_by(PluginHook.average_execution_time.desc())
            .limit(limit)
            .all()
        )


class PluginDependencyRepository(BaseRepository[PluginDependency]):
    """Repository for PluginDependency model"""

    def __init__(self, db: Session):
        super().__init__(db, PluginDependency)

    def get_by_plugin_id(self, plugin_id: int) -> List[PluginDependency]:
        """Get all dependencies for a plugin"""
        return (
            self.db.query(PluginDependency)
            .filter(PluginDependency.plugin_id == plugin_id)
            .all()
        )

    def get_required_dependencies(self, plugin_id: int) -> List[PluginDependency]:
        """Get required dependencies for a plugin"""
        return (
            self.db.query(PluginDependency)
            .filter(
                and_(
                    PluginDependency.plugin_id == plugin_id,
                    PluginDependency.is_optional is False,
                )
            )
            .all()
        )

    def get_optional_dependencies(self, plugin_id: int) -> List[PluginDependency]:
        """Get optional dependencies for a plugin"""
        return (
            self.db.query(PluginDependency)
            .filter(
                and_(
                    PluginDependency.plugin_id == plugin_id,
                    PluginDependency.is_optional is True,
                )
            )
            .all()
        )

    def get_unsatisfied_dependencies(self, plugin_id: int) -> List[PluginDependency]:
        """Get unsatisfied dependencies for a plugin"""
        return (
            self.db.query(PluginDependency)
            .filter(
                and_(
                    PluginDependency.plugin_id == plugin_id,
                    PluginDependency.is_satisfied is False,
                )
            )
            .all()
        )

    def get_by_dependency_type(self, dependency_type: str) -> List[PluginDependency]:
        """Get dependencies by type"""
        return (
            self.db.query(PluginDependency)
            .filter(PluginDependency.dependency_type == dependency_type)
            .all()
        )

    def get_by_dependency_name(self, dependency_name: str) -> List[PluginDependency]:
        """Get dependencies by name"""
        return (
            self.db.query(PluginDependency)
            .filter(PluginDependency.dependency_name == dependency_name)
            .all()
        )


class PluginLogRepository(BaseRepository[PluginLog]):
    """Repository for PluginLog model"""

    def __init__(self, db: Session):
        super().__init__(db, PluginLog)

    def get_by_plugin_id(
        self, plugin_id: int, skip: int = 0, limit: int = 100
    ) -> Tuple[List[PluginLog], int]:
        """Get logs for a plugin with pagination"""
        query = self.db.query(PluginLog).filter(PluginLog.plugin_id == plugin_id)
        total = query.count()
        logs = (
            query.order_by(PluginLog.created_at.desc()).offset(skip).limit(limit).all()
        )
        return logs, total

    def get_by_log_level(
        self, log_level: str, skip: int = 0, limit: int = 100
    ) -> Tuple[List[PluginLog], int]:
        """Get logs by level with pagination"""
        query = self.db.query(PluginLog).filter(PluginLog.log_level == log_level)
        total = query.count()
        logs = (
            query.order_by(PluginLog.created_at.desc()).offset(skip).limit(limit).all()
        )
        return logs, total

    def get_by_hook_name(
        self, hook_name: str, skip: int = 0, limit: int = 100
    ) -> Tuple[List[PluginLog], int]:
        """Get logs by hook name with pagination"""
        query = self.db.query(PluginLog).filter(PluginLog.hook_name == hook_name)
        total = query.count()
        logs = (
            query.order_by(PluginLog.created_at.desc()).offset(skip).limit(limit).all()
        )
        return logs, total

    def search_logs(
        self,
        plugin_id: Optional[int] = None,
        log_level: Optional[str] = None,
        hook_name: Optional[str] = None,
        user_id: Optional[int] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        search_term: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[PluginLog], int]:
        """Search logs with comprehensive filtering"""
        query = self.db.query(PluginLog)

        if plugin_id:
            query = query.filter(PluginLog.plugin_id == plugin_id)

        if log_level:
            query = query.filter(PluginLog.log_level == log_level)

        if hook_name:
            query = query.filter(PluginLog.hook_name == hook_name)

        if user_id:
            query = query.filter(PluginLog.user_id == user_id)

        if date_from:
            query = query.filter(PluginLog.created_at >= date_from)

        if date_to:
            query = query.filter(PluginLog.created_at <= date_to)

        if search_term:
            query = query.filter(
                or_(
                    PluginLog.message.ilike(f"%{search_term}%"),
                    PluginLog.stack_trace.ilike(f"%{search_term}%"),
                )
            )

        total = query.count()
        logs = (
            query.order_by(PluginLog.created_at.desc()).offset(skip).limit(limit).all()
        )

        return logs, total

    def get_error_logs(
        self, plugin_id: Optional[int] = None, skip: int = 0, limit: int = 100
    ) -> Tuple[List[PluginLog], int]:
        """Get error logs with optional plugin filter"""
        query = self.db.query(PluginLog).filter(
            PluginLog.log_level.in_(["ERROR", "CRITICAL"])
        )

        if plugin_id:
            query = query.filter(PluginLog.plugin_id == plugin_id)

        total = query.count()
        logs = (
            query.order_by(PluginLog.created_at.desc()).offset(skip).limit(limit).all()
        )

        return logs, total

    def get_recent_logs(
        self, hours: int = 24, skip: int = 0, limit: int = 100
    ) -> Tuple[List[PluginLog], int]:
        """Get recent logs within specified hours"""
        from datetime import timedelta

        cutoff_time = datetime.now() - timedelta(hours=hours)

        query = self.db.query(PluginLog).filter(PluginLog.created_at >= cutoff_time)

        total = query.count()
        logs = (
            query.order_by(PluginLog.created_at.desc()).offset(skip).limit(limit).all()
        )

        return logs, total


class PluginRegistryRepository(BaseRepository[PluginRegistry]):
    """Repository for PluginRegistry model"""

    def __init__(self, db: Session):
        super().__init__(db, PluginRegistry)

    def get_by_name(self, name: str) -> Optional[PluginRegistry]:
        """Get registry entry by name"""
        return self.db.query(PluginRegistry).filter(PluginRegistry.name == name).first()

    def get_by_type(self, plugin_type: PluginType) -> List[PluginRegistry]:
        """Get registry entries by type"""
        return (
            self.db.query(PluginRegistry)
            .filter(PluginRegistry.plugin_type == plugin_type)
            .all()
        )

    def get_verified_plugins(self) -> List[PluginRegistry]:
        """Get verified plugins from registry"""
        return (
            self.db.query(PluginRegistry)
            .filter(PluginRegistry.is_verified is True)
            .all()
        )

    def get_featured_plugins(self) -> List[PluginRegistry]:
        """Get featured plugins from registry"""
        return (
            self.db.query(PluginRegistry)
            .filter(PluginRegistry.is_featured is True)
            .all()
        )

    def get_popular_plugins(self, limit: int = 10) -> List[PluginRegistry]:
        """Get most popular plugins by download count"""
        return (
            self.db.query(PluginRegistry)
            .order_by(PluginRegistry.download_count.desc())
            .limit(limit)
            .all()
        )

    def get_top_rated_plugins(self, limit: int = 10) -> List[PluginRegistry]:
        """Get top rated plugins"""
        return (
            self.db.query(PluginRegistry)
            .order_by(PluginRegistry.rating.desc())
            .limit(limit)
            .all()
        )

    def search_registry(
        self,
        search_term: Optional[str] = None,
        plugin_type: Optional[PluginType] = None,
        is_verified: Optional[bool] = None,
        is_featured: Optional[bool] = None,
        is_deprecated: Optional[bool] = None,
        tags: Optional[List[str]] = None,
        min_rating: Optional[int] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[PluginRegistry], int]:
        """Search registry with comprehensive filtering"""
        query = self.db.query(PluginRegistry)

        if search_term:
            query = query.filter(
                or_(
                    PluginRegistry.name.ilike(f"%{search_term}%"),
                    PluginRegistry.display_name.ilike(f"%{search_term}%"),
                    PluginRegistry.description.ilike(f"%{search_term}%"),
                )
            )

        if plugin_type:
            query = query.filter(PluginRegistry.plugin_type == plugin_type)

        if is_verified is not None:
            query = query.filter(PluginRegistry.is_verified == is_verified)

        if is_featured is not None:
            query = query.filter(PluginRegistry.is_featured == is_featured)

        if is_deprecated is not None:
            query = query.filter(PluginRegistry.is_deprecated == is_deprecated)

        if tags:
            for tag in tags:
                query = query.filter(PluginRegistry.tags.contains([tag]))

        if min_rating:
            query = query.filter(PluginRegistry.rating >= min_rating)

        total = query.count()
        plugins = (
            query.order_by(PluginRegistry.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

        return plugins, total


class PluginTemplateRepository(BaseRepository[PluginTemplate]):
    """Repository for PluginTemplate model"""

    def __init__(self, db: Session):
        super().__init__(db, PluginTemplate)

    def get_by_name(self, name: str) -> Optional[PluginTemplate]:
        """Get template by name"""
        return self.db.query(PluginTemplate).filter(PluginTemplate.name == name).first()

    def get_by_type(self, plugin_type: PluginType) -> List[PluginTemplate]:
        """Get templates by plugin type"""
        return (
            self.db.query(PluginTemplate)
            .filter(PluginTemplate.plugin_type == plugin_type)
            .all()
        )

    def get_active_templates(self) -> List[PluginTemplate]:
        """Get active templates"""
        return (
            self.db.query(PluginTemplate).filter(PluginTemplate.is_active is True).all()
        )

    def get_system_templates(self) -> List[PluginTemplate]:
        """Get system templates"""
        return (
            self.db.query(PluginTemplate).filter(PluginTemplate.is_system is True).all()
        )

    def get_most_used_templates(self, limit: int = 10) -> List[PluginTemplate]:
        """Get most used templates"""
        return (
            self.db.query(PluginTemplate)
            .order_by(PluginTemplate.usage_count.desc())
            .limit(limit)
            .all()
        )

    def get_templates_by_author(self, author: str) -> List[PluginTemplate]:
        """Get templates by author"""
        return (
            self.db.query(PluginTemplate)
            .filter(PluginTemplate.author.ilike(f"%{author}%"))
            .all()
        )

    def search_templates(
        self,
        search_term: Optional[str] = None,
        plugin_type: Optional[PluginType] = None,
        is_active: Optional[bool] = None,
        is_system: Optional[bool] = None,
        author: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[PluginTemplate], int]:
        """Search templates with filtering"""
        query = self.db.query(PluginTemplate)

        if search_term:
            query = query.filter(
                or_(
                    PluginTemplate.name.ilike(f"%{search_term}%"),
                    PluginTemplate.display_name.ilike(f"%{search_term}%"),
                    PluginTemplate.description.ilike(f"%{search_term}%"),
                )
            )

        if plugin_type:
            query = query.filter(PluginTemplate.plugin_type == plugin_type)

        if is_active is not None:
            query = query.filter(PluginTemplate.is_active == is_active)

        if is_system is not None:
            query = query.filter(PluginTemplate.is_system == is_system)

        if author:
            query = query.filter(PluginTemplate.author.ilike(f"%{author}%"))

        total = query.count()
        templates = (
            query.order_by(PluginTemplate.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

        return templates, total
