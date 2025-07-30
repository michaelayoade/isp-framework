"""
Plugin System Service Layer for ISP Framework

Handles dynamic plugin loading, registration, lifecycle management,
hook execution, and integration with the ISP Framework core systems.
"""

import logging
import importlib
import importlib.util
import sys
import os
import json
import traceback
import time
from typing import List, Optional, Dict, Any, Tuple, Type
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from pathlib import Path
import threading
from abc import ABC, abstractmethod

from app.models.plugins import (
    Plugin,
    PluginConfiguration,
    PluginHook,
    PluginDependency,
    PluginLog,
    PluginRegistry,
    PluginTemplate,
    PluginStatus,
    PluginType,
    PluginPriority
)
from app.schemas.plugins import (
    PluginCreate,
    PluginUpdate,
    PluginConfigurationCreate,
    PluginConfigurationUpdate,
    PluginHookCreate,
    PluginHookUpdate,
    PluginInstallRequest,
    PluginExecuteRequest
)

logger = logging.getLogger(__name__)


class PluginInterface(ABC):
    """Base interface that all plugins must implement"""
    
    def __init__(self, plugin_id: int, config: Dict[str, Any]):
        self.plugin_id = plugin_id
        self.config = config
        self.logger = logging.getLogger(f"plugin.{self.__class__.__name__}")
    
    @abstractmethod
    def initialize(self) -> bool:
        """Initialize the plugin. Return True if successful."""
        pass
    
    @abstractmethod
    def cleanup(self) -> bool:
        """Cleanup plugin resources. Return True if successful."""
        pass
    
    @abstractmethod
    def get_info(self) -> Dict[str, Any]:
        """Get plugin information and status."""
        pass
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check. Override in plugin if needed."""
        return {
            "status": "healthy",
            "checks": [
                {"name": "basic", "status": "pass", "message": "Plugin is loaded"}
            ]
        }


class PluginManager:
    """Core plugin manager for loading and managing plugins"""
    
    def __init__(self, db: Session):
        self.db = db
        self.loaded_plugins: Dict[int, Any] = {}
        self.plugin_classes: Dict[int, Type] = {}
        self.hooks: Dict[str, List[Tuple[int, str, int]]] = {}  # hook_name -> [(plugin_id, method, priority)]
        self.lock = threading.RLock()
    
    def load_plugin(self, plugin_id: int) -> bool:
        """Load a plugin by ID"""
        with self.lock:
            try:
                plugin = self.db.query(Plugin).filter(Plugin.id == plugin_id).first()
                if not plugin:
                    logger.error(f"Plugin {plugin_id} not found")
                    return False
                
                if plugin.status == PluginStatus.ACTIVE:
                    logger.info(f"Plugin {plugin.name} is already loaded")
                    return True
                
                # Update status to loading
                plugin.status = PluginStatus.LOADING
                self.db.commit()
                
                # Load the plugin module
                plugin_class = self._load_plugin_module(plugin)
                if not plugin_class:
                    plugin.status = PluginStatus.ERROR
                    plugin.last_error = "Failed to load plugin module"
                    self.db.commit()
                    return False
                
                # Get plugin configuration
                config = self._get_plugin_config(plugin_id)
                
                # Initialize plugin instance
                plugin_instance = plugin_class(plugin_id, config)
                
                # Initialize the plugin
                if not plugin_instance.initialize():
                    plugin.status = PluginStatus.ERROR
                    plugin.last_error = "Plugin initialization failed"
                    self.db.commit()
                    return False
                
                # Store plugin instance and class
                self.loaded_plugins[plugin_id] = plugin_instance
                self.plugin_classes[plugin_id] = plugin_class
                
                # Register plugin hooks
                self._register_plugin_hooks(plugin_id)
                
                # Update plugin status
                plugin.status = PluginStatus.ACTIVE
                plugin.last_loaded = datetime.now(timezone.utc)
                plugin.load_count += 1
                plugin.last_error = None
                self.db.commit()
                
                self._log_plugin_event(plugin_id, "INFO", f"Plugin {plugin.name} loaded successfully")
                logger.info(f"Plugin {plugin.name} loaded successfully")
                
                return True
                
            except Exception as e:
                logger.error(f"Failed to load plugin {plugin_id}: {str(e)}")
                plugin = self.db.query(Plugin).filter(Plugin.id == plugin_id).first()
                if plugin:
                    plugin.status = PluginStatus.ERROR
                    plugin.last_error = str(e)
                    plugin.error_count += 1
                    self.db.commit()
                
                self._log_plugin_event(plugin_id, "ERROR", f"Failed to load plugin: {str(e)}", traceback.format_exc())
                return False
    
    def unload_plugin(self, plugin_id: int) -> bool:
        """Unload a plugin by ID"""
        with self.lock:
            try:
                plugin = self.db.query(Plugin).filter(Plugin.id == plugin_id).first()
                if not plugin:
                    return False
                
                if plugin_id in self.loaded_plugins:
                    # Cleanup plugin
                    plugin_instance = self.loaded_plugins[plugin_id]
                    try:
                        plugin_instance.cleanup()
                    except Exception as e:
                        logger.warning(f"Plugin cleanup failed for {plugin.name}: {str(e)}")
                    
                    # Remove from loaded plugins
                    del self.loaded_plugins[plugin_id]
                    if plugin_id in self.plugin_classes:
                        del self.plugin_classes[plugin_id]
                
                # Unregister hooks
                self._unregister_plugin_hooks(plugin_id)
                
                # Update status
                plugin.status = PluginStatus.INACTIVE
                self.db.commit()
                
                self._log_plugin_event(plugin_id, "INFO", f"Plugin {plugin.name} unloaded successfully")
                logger.info(f"Plugin {plugin.name} unloaded successfully")
                
                return True
                
            except Exception as e:
                logger.error(f"Failed to unload plugin {plugin_id}: {str(e)}")
                self._log_plugin_event(plugin_id, "ERROR", f"Failed to unload plugin: {str(e)}", traceback.format_exc())
                return False
    
    def reload_plugin(self, plugin_id: int) -> bool:
        """Reload a plugin by ID"""
        if self.unload_plugin(plugin_id):
            return self.load_plugin(plugin_id)
        return False
    
    def execute_hook(self, hook_name: str, *args, **kwargs) -> List[Any]:
        """Execute all registered hooks for a given hook name"""
        results = []
        
        if hook_name not in self.hooks:
            return results
        
        # Sort hooks by priority (lower number = higher priority)
        sorted_hooks = sorted(self.hooks[hook_name], key=lambda x: x[2])
        
        for plugin_id, method_name, priority in sorted_hooks:
            try:
                if plugin_id not in self.loaded_plugins:
                    continue
                
                plugin_instance = self.loaded_plugins[plugin_id]
                if not hasattr(plugin_instance, method_name):
                    continue
                
                start_time = time.time()
                method = getattr(plugin_instance, method_name)
                result = method(*args, **kwargs)
                execution_time = int((time.time() - start_time) * 1000)
                
                results.append(result)
                
                # Update hook statistics
                hook = self.db.query(PluginHook).filter(
                    and_(
                        PluginHook.plugin_id == plugin_id,
                        PluginHook.hook_name == hook_name,
                        PluginHook.callback_method == method_name
                    )
                ).first()
                
                if hook:
                    hook.execution_count += 1
                    hook.last_executed = datetime.now(timezone.utc)
                    # Update average execution time
                    if hook.average_execution_time == 0:
                        hook.average_execution_time = execution_time
                    else:
                        hook.average_execution_time = int(
                            (hook.average_execution_time + execution_time) / 2
                        )
                    self.db.commit()
                
                self._log_plugin_event(
                    plugin_id, "DEBUG", 
                    f"Hook {hook_name} executed successfully",
                    context={"execution_time": execution_time, "hook_name": hook_name}
                )
                
            except Exception as e:
                logger.error(f"Hook execution failed for plugin {plugin_id}, hook {hook_name}: {str(e)}")
                self._log_plugin_event(
                    plugin_id, "ERROR", 
                    f"Hook {hook_name} execution failed: {str(e)}",
                    traceback.format_exc(),
                    hook_name=hook_name
                )
                
                # Update error count
                plugin = self.db.query(Plugin).filter(Plugin.id == plugin_id).first()
                if plugin:
                    plugin.error_count += 1
                    self.db.commit()
        
        return results
    
    def get_plugin_instance(self, plugin_id: int) -> Optional[Any]:
        """Get loaded plugin instance by ID"""
        return self.loaded_plugins.get(plugin_id)
    
    def is_plugin_loaded(self, plugin_id: int) -> bool:
        """Check if plugin is loaded"""
        return plugin_id in self.loaded_plugins
    
    def get_loaded_plugins(self) -> Dict[int, Any]:
        """Get all loaded plugins"""
        return self.loaded_plugins.copy()
    
    def _load_plugin_module(self, plugin: Plugin) -> Optional[Type]:
        """Load plugin module and return plugin class"""
        try:
            # Handle different module path formats
            if plugin.module_path.endswith('.py'):
                # File path
                spec = importlib.util.spec_from_file_location(plugin.name, plugin.module_path)
                if not spec or not spec.loader:
                    return None
                
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
            else:
                # Module path
                module = importlib.import_module(plugin.module_path)
            
            # Get plugin class
            if hasattr(module, plugin.entry_point):
                plugin_class = getattr(module, plugin.entry_point)
                
                # Verify it implements PluginInterface
                if not issubclass(plugin_class, PluginInterface):
                    logger.error(f"Plugin {plugin.name} does not implement PluginInterface")
                    return None
                
                return plugin_class
            else:
                logger.error(f"Entry point {plugin.entry_point} not found in plugin {plugin.name}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to load module for plugin {plugin.name}: {str(e)}")
            return None
    
    def _get_plugin_config(self, plugin_id: int) -> Dict[str, Any]:
        """Get plugin configuration as dictionary"""
        config = {}
        
        configurations = self.db.query(PluginConfiguration).filter(
            PluginConfiguration.plugin_id == plugin_id
        ).all()
        
        for conf in configurations:
            config[conf.config_key] = conf.config_value
        
        return config
    
    def _register_plugin_hooks(self, plugin_id: int):
        """Register all hooks for a plugin"""
        hooks = self.db.query(PluginHook).filter(
            and_(
                PluginHook.plugin_id == plugin_id,
                PluginHook.is_active == True
            )
        ).all()
        
        for hook in hooks:
            if hook.hook_name not in self.hooks:
                self.hooks[hook.hook_name] = []
            
            self.hooks[hook.hook_name].append((
                plugin_id,
                hook.callback_method,
                hook.priority
            ))
    
    def _unregister_plugin_hooks(self, plugin_id: int):
        """Unregister all hooks for a plugin"""
        for hook_name in list(self.hooks.keys()):
            self.hooks[hook_name] = [
                (pid, method, priority) for pid, method, priority in self.hooks[hook_name]
                if pid != plugin_id
            ]
            
            # Remove empty hook lists
            if not self.hooks[hook_name]:
                del self.hooks[hook_name]
    
    def _log_plugin_event(self, plugin_id: int, level: str, message: str, 
                         stack_trace: Optional[str] = None, hook_name: Optional[str] = None,
                         context: Optional[Dict[str, Any]] = None):
        """Log plugin event to database"""
        try:
            log_entry = PluginLog(
                plugin_id=plugin_id,
                log_level=level,
                message=message,
                context=context or {},
                hook_name=hook_name,
                stack_trace=stack_trace
            )
            
            self.db.add(log_entry)
            self.db.commit()
        except Exception as e:
            logger.error(f"Failed to log plugin event: {str(e)}")


class PluginService:
    """Main plugin service for managing plugins"""
    
    def __init__(self, db: Session):
        self.db = db
        self.plugin_manager = PluginManager(db)
    
    def create_plugin(self, plugin_data: PluginCreate, installed_by: int) -> Plugin:
        """Create and register a new plugin"""
        plugin = Plugin(
            **plugin_data.dict(),
            installed_by=installed_by
        )
        
        self.db.add(plugin)
        self.db.commit()
        self.db.refresh(plugin)
        
        logger.info(f"Plugin {plugin.name} created successfully")
        return plugin
    
    def get_plugin(self, plugin_id: int) -> Optional[Plugin]:
        """Get plugin by ID"""
        return self.db.query(Plugin).filter(Plugin.id == plugin_id).first()
    
    def get_plugins(
        self,
        skip: int = 0,
        limit: int = 100,
        plugin_type: Optional[PluginType] = None,
        status: Optional[PluginStatus] = None,
        is_enabled: Optional[bool] = None,
        search_term: Optional[str] = None
    ) -> Tuple[List[Plugin], int]:
        """Get plugins with filtering and pagination"""
        query = self.db.query(Plugin)
        
        if plugin_type:
            query = query.filter(Plugin.plugin_type == plugin_type)
        if status:
            query = query.filter(Plugin.status == status)
        if is_enabled is not None:
            query = query.filter(Plugin.is_enabled == is_enabled)
        if search_term:
            query = query.filter(
                or_(
                    Plugin.name.ilike(f"%{search_term}%"),
                    Plugin.display_name.ilike(f"%{search_term}%"),
                    Plugin.description.ilike(f"%{search_term}%")
                )
            )
        
        total = query.count()
        plugins = query.order_by(Plugin.created_at.desc()).offset(skip).limit(limit).all()
        
        return plugins, total
    
    def update_plugin(self, plugin_id: int, plugin_data: PluginUpdate) -> Optional[Plugin]:
        """Update a plugin"""
        plugin = self.get_plugin(plugin_id)
        if not plugin:
            return None
        
        if plugin.is_system:
            raise ValueError("System plugins cannot be modified")
        
        update_data = plugin_data.dict(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(plugin, field, value)
        
        self.db.commit()
        self.db.refresh(plugin)
        
        logger.info(f"Plugin {plugin.name} updated successfully")
        return plugin
    
    def delete_plugin(self, plugin_id: int) -> bool:
        """Delete a plugin"""
        plugin = self.get_plugin(plugin_id)
        if not plugin:
            return False
        
        if plugin.is_system:
            raise ValueError("System plugins cannot be deleted")
        
        # Unload plugin if loaded
        if self.plugin_manager.is_plugin_loaded(plugin_id):
            self.plugin_manager.unload_plugin(plugin_id)
        
        self.db.delete(plugin)
        self.db.commit()
        
        logger.info(f"Plugin {plugin.name} deleted successfully")
        return True
    
    def install_plugin(self, install_request: PluginInstallRequest, installed_by: int) -> Dict[str, Any]:
        """Install a plugin from various sources"""
        try:
            # Implement plugin installation from different sources
            if install_request.source_type == "registry":
                result = self._install_from_registry(install_request)
            elif install_request.source_type == "url":
                result = self._install_from_url(install_request)
            elif install_request.source_type == "file":
                result = self._install_from_file(install_request)
            elif install_request.source_type == "git":
                result = self._install_from_git(install_request)
            else:
                result = {
                    "success": False,
                    "message": f"Unsupported installation source: {install_request.source_type}",
                "plugin_id": None,
                "warnings": []
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Plugin installation failed: {str(e)}")
            return {
                "success": False,
                "message": f"Installation failed: {str(e)}",
                "plugin_id": None,
                "warnings": []
            }
    
    def enable_plugin(self, plugin_id: int) -> bool:
        """Enable and load a plugin"""
        plugin = self.get_plugin(plugin_id)
        if not plugin:
            return False
        
        plugin.is_enabled = True
        self.db.commit()
        
        return self.plugin_manager.load_plugin(plugin_id)
    
    def disable_plugin(self, plugin_id: int) -> bool:
        """Disable and unload a plugin"""
        plugin = self.get_plugin(plugin_id)
        if not plugin:
            return False
        
        plugin.is_enabled = False
        self.db.commit()
        
        return self.plugin_manager.unload_plugin(plugin_id)
    
    def execute_plugin_method(self, plugin_id: int, execute_request: PluginExecuteRequest) -> Dict[str, Any]:
        """Execute a plugin method"""
        try:
            plugin_instance = self.plugin_manager.get_plugin_instance(plugin_id)
            if not plugin_instance:
                return {
                    "success": False,
                    "error": "Plugin not loaded",
                    "execution_time": 0
                }
            
            if not hasattr(plugin_instance, execute_request.method_name):
                return {
                    "success": False,
                    "error": f"Method {execute_request.method_name} not found",
                    "execution_time": 0
                }
            
            start_time = time.time()
            method = getattr(plugin_instance, execute_request.method_name)
            result = method(**execute_request.parameters)
            execution_time = int((time.time() - start_time) * 1000)
            
            return {
                "success": True,
                "result": result,
                "execution_time": execution_time,
                "warnings": []
            }
            
        except Exception as e:
            logger.error(f"Plugin method execution failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "execution_time": 0
            }
    
    def get_plugin_stats(self) -> Dict[str, Any]:
        """Get plugin statistics"""
        total_plugins = self.db.query(Plugin).count()
        active_plugins = self.db.query(Plugin).filter(Plugin.status == PluginStatus.ACTIVE).count()
        inactive_plugins = self.db.query(Plugin).filter(Plugin.status == PluginStatus.INACTIVE).count()
        error_plugins = self.db.query(Plugin).filter(Plugin.status == PluginStatus.ERROR).count()
        
        # Stats by type
        type_stats = self.db.query(
            Plugin.plugin_type,
            func.count(Plugin.id)
        ).group_by(Plugin.plugin_type).all()
        
        # Stats by status
        status_stats = self.db.query(
            Plugin.status,
            func.count(Plugin.id)
        ).group_by(Plugin.status).all()
        
        # Top plugins by load count
        top_plugins = self.db.query(Plugin).order_by(
            Plugin.load_count.desc()
        ).limit(10).all()
        
        return {
            "total_plugins": total_plugins,
            "active_plugins": active_plugins,
            "inactive_plugins": inactive_plugins,
            "error_plugins": error_plugins,
            "by_type": {str(plugin_type): count for plugin_type, count in type_stats},
            "by_status": {str(status): count for status, count in status_stats},
            "top_plugins": [
                {
                    "id": plugin.id,
                    "name": plugin.name,
                    "display_name": plugin.display_name,
                    "load_count": plugin.load_count,
                    "status": plugin.status.value
                }
                for plugin in top_plugins
            ]
        }


# Factory function for dependency injection
def get_plugin_service(db: Session) -> PluginService:
    """Get plugin service instance"""
    return PluginService(db)
