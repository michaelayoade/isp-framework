"""
Plugin System Schemas for ISP Framework

Pydantic schemas for plugin management, configuration, hooks, and registry
with comprehensive validation and type safety.
"""

from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List, Dict, Any
from datetime import datetime

from app.models.plugins import (
    PluginStatus,
    PluginType,
    PluginPriority
)


# Base schemas
class PluginBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, pattern="^[a-zA-Z0-9_-]+$")
    display_name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    version: str = Field(..., pattern="^\\d+\\.\\d+\\.\\d+(-[a-zA-Z0-9]+)?$")
    author: Optional[str] = Field(None, max_length=255)
    license: Optional[str] = Field(None, max_length=100)
    homepage: Optional[HttpUrl] = None
    plugin_type: PluginType
    category: Optional[str] = Field(None, max_length=100)
    tags: List[str] = Field(default_factory=list)
    priority: PluginPriority = PluginPriority.NORMAL
    is_enabled: bool = True
    module_path: str = Field(..., min_length=1, max_length=500)
    entry_point: str = Field(..., min_length=1, max_length=255)
    config_schema: Dict[str, Any] = Field(default_factory=dict)
    requirements: List[str] = Field(default_factory=list)
    supported_versions: List[str] = Field(default_factory=list)
    api_version: str = Field(default="1.0", max_length=20)


class PluginCreate(PluginBase):
    pass


class PluginUpdate(BaseModel):
    display_name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    author: Optional[str] = Field(None, max_length=255)
    license: Optional[str] = Field(None, max_length=100)
    homepage: Optional[HttpUrl] = None
    category: Optional[str] = Field(None, max_length=100)
    tags: Optional[List[str]] = None
    priority: Optional[PluginPriority] = None
    is_enabled: Optional[bool] = None
    config_schema: Optional[Dict[str, Any]] = None
    requirements: Optional[List[str]] = None
    supported_versions: Optional[List[str]] = None


class Plugin(PluginBase):
    id: int
    status: PluginStatus
    is_system: bool
    installed_at: datetime
    updated_at: Optional[datetime]
    last_loaded: Optional[datetime]
    installed_by: Optional[int]
    load_count: int
    error_count: int
    last_error: Optional[str]

    class Config:
        from_attributes = True


# Plugin Configuration schemas
class PluginConfigurationBase(BaseModel):
    config_key: str = Field(..., min_length=1, max_length=255)
    config_value: Any
    config_type: str = Field(default="string", pattern="^(string|number|boolean|object|array)$")
    is_encrypted: bool = False
    is_required: bool = False
    description: Optional[str] = None
    default_value: Any = None
    validation_rules: Dict[str, Any] = Field(default_factory=dict)


class PluginConfigurationCreate(PluginConfigurationBase):
    plugin_id: int


class PluginConfigurationUpdate(BaseModel):
    config_value: Optional[Any] = None
    config_type: Optional[str] = Field(None, pattern="^(string|number|boolean|object|array)$")
    is_encrypted: Optional[bool] = None
    is_required: Optional[bool] = None
    description: Optional[str] = None
    default_value: Optional[Any] = None
    validation_rules: Optional[Dict[str, Any]] = None


class PluginConfiguration(PluginConfigurationBase):
    id: int
    plugin_id: int
    created_at: datetime
    updated_at: Optional[datetime]
    updated_by: Optional[int]

    class Config:
        from_attributes = True


# Plugin Hook schemas
class PluginHookBase(BaseModel):
    hook_name: str = Field(..., min_length=1, max_length=255)
    hook_type: str = Field(..., pattern="^(action|filter|event)$")
    callback_method: str = Field(..., min_length=1, max_length=255)
    priority: int = Field(default=100, ge=1, le=1000)
    is_active: bool = True
    conditions: Dict[str, Any] = Field(default_factory=dict)
    description: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)
    return_type: Optional[str] = Field(None, max_length=100)


class PluginHookCreate(PluginHookBase):
    plugin_id: int


class PluginHookUpdate(BaseModel):
    hook_type: Optional[str] = Field(None, pattern="^(action|filter|event)$")
    callback_method: Optional[str] = Field(None, min_length=1, max_length=255)
    priority: Optional[int] = Field(None, ge=1, le=1000)
    is_active: Optional[bool] = None
    conditions: Optional[Dict[str, Any]] = None
    description: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    return_type: Optional[str] = Field(None, max_length=100)


class PluginHook(PluginHookBase):
    id: int
    plugin_id: int
    execution_count: int
    last_executed: Optional[datetime]
    average_execution_time: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# Plugin Dependency schemas
class PluginDependencyBase(BaseModel):
    dependency_type: str = Field(..., pattern="^(plugin|package|service)$")
    dependency_name: str = Field(..., min_length=1, max_length=255)
    version_constraint: Optional[str] = Field(None, max_length=100)
    is_optional: bool = False
    description: Optional[str] = None
    install_command: Optional[str] = Field(None, max_length=500)


class PluginDependencyCreate(PluginDependencyBase):
    plugin_id: int


class PluginDependencyUpdate(BaseModel):
    version_constraint: Optional[str] = Field(None, max_length=100)
    is_optional: Optional[bool] = None
    description: Optional[str] = None
    install_command: Optional[str] = Field(None, max_length=500)


class PluginDependency(PluginDependencyBase):
    id: int
    plugin_id: int
    is_satisfied: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# Plugin Log schemas
class PluginLogBase(BaseModel):
    log_level: str = Field(..., pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    message: str = Field(..., min_length=1)
    context: Dict[str, Any] = Field(default_factory=dict)
    hook_name: Optional[str] = Field(None, max_length=255)
    execution_time: Optional[int] = Field(None, ge=0)
    stack_trace: Optional[str] = None
    request_id: Optional[str] = Field(None, max_length=100)
    ip_address: Optional[str] = Field(None, max_length=45)


class PluginLogCreate(PluginLogBase):
    plugin_id: int
    user_id: Optional[int] = None


class PluginLog(PluginLogBase):
    id: int
    plugin_id: int
    user_id: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


# Plugin Registry schemas
class PluginRegistryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, pattern="^[a-zA-Z0-9_-]+$")
    display_name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    plugin_type: PluginType
    latest_version: str = Field(..., pattern="^\\d+\\.\\d+\\.\\d+(-[a-zA-Z0-9]+)?$")
    author: Optional[str] = Field(None, max_length=255)
    license: Optional[str] = Field(None, max_length=100)
    repository_url: Optional[HttpUrl] = None
    download_url: Optional[HttpUrl] = None
    documentation_url: Optional[HttpUrl] = None
    requirements: List[str] = Field(default_factory=list)
    supported_versions: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    screenshots: List[str] = Field(default_factory=list)
    is_verified: bool = False
    is_featured: bool = False
    is_deprecated: bool = False


class PluginRegistryCreate(PluginRegistryBase):
    pass


class PluginRegistryUpdate(BaseModel):
    display_name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    latest_version: Optional[str] = Field(None, pattern="^\\d+\\.\\d+\\.\\d+(-[a-zA-Z0-9]+)?$")
    author: Optional[str] = Field(None, max_length=255)
    license: Optional[str] = Field(None, max_length=100)
    repository_url: Optional[HttpUrl] = None
    download_url: Optional[HttpUrl] = None
    documentation_url: Optional[HttpUrl] = None
    requirements: Optional[List[str]] = None
    supported_versions: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    screenshots: Optional[List[str]] = None
    is_verified: Optional[bool] = None
    is_featured: Optional[bool] = None
    is_deprecated: Optional[bool] = None


class PluginRegistry(PluginRegistryBase):
    id: int
    download_count: int
    rating: int
    review_count: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# Plugin Template schemas
class PluginTemplateBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, pattern="^[a-zA-Z0-9_-]+$")
    display_name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    plugin_type: PluginType
    template_version: str = Field(..., pattern="^\\d+\\.\\d+\\.\\d+(-[a-zA-Z0-9]+)?$")
    template_files: Dict[str, str] = Field(default_factory=dict)
    config_schema: Dict[str, Any] = Field(default_factory=dict)
    author: Optional[str] = Field(None, max_length=255)
    documentation: Optional[str] = None
    example_usage: Optional[str] = None
    is_active: bool = True


class PluginTemplateCreate(PluginTemplateBase):
    pass


class PluginTemplateUpdate(BaseModel):
    display_name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    template_version: Optional[str] = Field(None, pattern="^\\d+\\.\\d+\\.\\d+(-[a-zA-Z0-9]+)?$")
    template_files: Optional[Dict[str, str]] = None
    config_schema: Optional[Dict[str, Any]] = None
    author: Optional[str] = Field(None, max_length=255)
    documentation: Optional[str] = None
    example_usage: Optional[str] = None
    is_active: Optional[bool] = None


class PluginTemplate(PluginTemplateBase):
    id: int
    is_system: bool
    usage_count: int
    created_at: datetime
    updated_at: Optional[datetime]
    created_by: Optional[int]

    class Config:
        from_attributes = True


# Request/Response schemas
class PluginInstallRequest(BaseModel):
    """Request to install a plugin"""
    source_type: str = Field(..., pattern="^(registry|upload|git|local)$")
    source_location: str = Field(..., min_length=1)
    version: Optional[str] = None
    configuration: Dict[str, Any] = Field(default_factory=dict)
    auto_enable: bool = True


class PluginInstallResponse(BaseModel):
    """Response after plugin installation"""
    plugin_id: int
    status: PluginStatus
    message: str
    warnings: List[str] = Field(default_factory=list)
    dependencies_installed: List[str] = Field(default_factory=list)


class PluginExecuteRequest(BaseModel):
    """Request to execute a plugin method"""
    method_name: str = Field(..., min_length=1, max_length=255)
    parameters: Dict[str, Any] = Field(default_factory=dict)
    context: Dict[str, Any] = Field(default_factory=dict)


class PluginExecuteResponse(BaseModel):
    """Response from plugin execution"""
    success: bool
    result: Any = None
    error: Optional[str] = None
    execution_time: int  # Milliseconds
    warnings: List[str] = Field(default_factory=list)


class PluginStatsResponse(BaseModel):
    """Plugin statistics response"""
    total_plugins: int
    active_plugins: int
    inactive_plugins: int
    error_plugins: int
    by_type: Dict[str, int]
    by_status: Dict[str, int]
    top_plugins: List[Dict[str, Any]]
    recent_activity: List[Dict[str, Any]]


class PluginHealthResponse(BaseModel):
    """Plugin health check response"""
    plugin_id: int
    plugin_name: str
    status: PluginStatus
    health_status: str  # healthy, warning, error
    checks: List[Dict[str, Any]]
    last_check: datetime
    uptime: int  # Seconds


# Search and filter schemas
class PluginSearchFilters(BaseModel):
    """Search filters for plugins"""
    plugin_type: Optional[PluginType] = None
    status: Optional[PluginStatus] = None
    category: Optional[str] = None
    author: Optional[str] = None
    is_system: Optional[bool] = None
    is_enabled: Optional[bool] = None
    search_term: Optional[str] = None
    tags: Optional[List[str]] = None


class PluginRegistrySearchFilters(BaseModel):
    """Search filters for plugin registry"""
    plugin_type: Optional[PluginType] = None
    is_verified: Optional[bool] = None
    is_featured: Optional[bool] = None
    is_deprecated: Optional[bool] = None
    search_term: Optional[str] = None
    tags: Optional[List[str]] = None
    min_rating: Optional[int] = Field(None, ge=1, le=5)


class PluginLogSearchFilters(BaseModel):
    """Search filters for plugin logs"""
    plugin_id: Optional[int] = None
    log_level: Optional[str] = Field(None, pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    hook_name: Optional[str] = None
    user_id: Optional[int] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    search_term: Optional[str] = None


# Pagination schemas
class PaginatedPlugins(BaseModel):
    """Paginated plugins response"""
    items: List[Plugin]
    total: int
    page: int
    size: int
    pages: int


class PaginatedPluginRegistry(BaseModel):
    """Paginated plugin registry response"""
    items: List[PluginRegistry]
    total: int
    page: int
    size: int
    pages: int


class PaginatedPluginLogs(BaseModel):
    """Paginated plugin logs response"""
    items: List[PluginLog]
    total: int
    page: int
    size: int
    pages: int


class PaginatedPluginTemplates(BaseModel):
    """Paginated plugin templates response"""
    items: List[PluginTemplate]
    total: int
    page: int
    size: int
    pages: int


# Bulk operation schemas
class BulkPluginOperation(BaseModel):
    """Bulk plugin operation request"""
    plugin_ids: List[int] = Field(..., min_items=1)
    operation: str = Field(..., pattern="^(enable|disable|update|uninstall)$")
    parameters: Dict[str, Any] = Field(default_factory=dict)


class BulkPluginOperationResponse(BaseModel):
    """Bulk plugin operation response"""
    successful: List[int]
    failed: List[Dict[str, Any]]
    warnings: List[str] = Field(default_factory=list)
    summary: Dict[str, int]
