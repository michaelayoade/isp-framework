"""
Plugin System API Endpoints for ISP Framework

FastAPI endpoints for plugin management, configuration, hooks, registry,
and comprehensive plugin lifecycle operations.
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_admin
from app.core.database import get_db
from app.models.auth.base import Administrator
from app.models.plugins import PluginStatus, PluginType
from app.repositories.plugin_repository import (
    PluginConfigurationRepository,
    PluginHookRepository,
    PluginLogRepository,
    PluginRegistryRepository,
    PluginTemplateRepository,
)
from app.schemas.plugins import (
    BulkPluginOperation,
    BulkPluginOperationResponse,
    PaginatedPluginLogs,
    PaginatedPluginRegistry,
    PaginatedPlugins,
    PaginatedPluginTemplates,
    Plugin,
    PluginConfiguration,
    PluginConfigurationCreate,
    PluginConfigurationUpdate,
    PluginCreate,
    PluginExecuteRequest,
    PluginExecuteResponse,
    PluginHealthResponse,
    PluginHook,
    PluginHookCreate,
    PluginInstallRequest,
    PluginInstallResponse,
    PluginStatsResponse,
    PluginTemplate,
    PluginTemplateCreate,
    PluginUpdate,
)
from app.services.plugin_service import get_plugin_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["plugins"])


# Plugin Management Endpoints
@router.post("/", response_model=Plugin, status_code=status.HTTP_201_CREATED)
async def create_plugin(
    plugin_data: PluginCreate,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin),
):
    """Create a new plugin"""
    try:
        plugin_service = get_plugin_service(db)
        plugin = plugin_service.create_plugin(plugin_data, current_admin.id)

        logger.info(f"Plugin {plugin.name} created by admin {current_admin.id}")
        return plugin

    except Exception as e:
        logger.error(f"Failed to create plugin: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create plugin: {str(e)}",
        )


@router.get("/", response_model=PaginatedPlugins)
async def get_plugins(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    plugin_type: Optional[PluginType] = None,
    status: Optional[PluginStatus] = None,
    is_enabled: Optional[bool] = None,
    search_term: Optional[str] = None,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin),
):
    """Get plugins with filtering and pagination"""
    try:
        plugin_service = get_plugin_service(db)
        plugins, total = plugin_service.get_plugins(
            skip=skip,
            limit=limit,
            plugin_type=plugin_type,
            status=status,
            is_enabled=is_enabled,
            search_term=search_term,
        )

        pages = (total + limit - 1) // limit

        return PaginatedPlugins(
            items=plugins,
            total=total,
            page=(skip // limit) + 1,
            size=limit,
            pages=pages,
        )

    except Exception as e:
        logger.error(f"Failed to get plugins: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get plugins: {str(e)}",
        )


@router.get("/{plugin_id}", response_model=Plugin)
async def get_plugin(
    plugin_id: int,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin),
):
    """Get plugin by ID"""
    try:
        plugin_service = get_plugin_service(db)
        plugin = plugin_service.get_plugin(plugin_id)

        if not plugin:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Plugin not found"
            )

        return plugin

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get plugin {plugin_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get plugin: {str(e)}",
        )


@router.put("/{plugin_id}", response_model=Plugin)
async def update_plugin(
    plugin_id: int,
    plugin_data: PluginUpdate,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin),
):
    """Update a plugin"""
    try:
        plugin_service = get_plugin_service(db)
        plugin = plugin_service.update_plugin(plugin_id, plugin_data)

        if not plugin:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Plugin not found"
            )

        logger.info(f"Plugin {plugin.name} updated by admin {current_admin.id}")
        return plugin

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update plugin {plugin_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update plugin: {str(e)}",
        )


@router.delete("/{plugin_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_plugin(
    plugin_id: int,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin),
):
    """Delete a plugin"""
    try:
        plugin_service = get_plugin_service(db)
        success = plugin_service.delete_plugin(plugin_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Plugin not found"
            )

        logger.info(f"Plugin {plugin_id} deleted by admin {current_admin.id}")

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to delete plugin {plugin_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete plugin: {str(e)}",
        )


# Plugin Lifecycle Endpoints
@router.post("/install", response_model=PluginInstallResponse)
async def install_plugin(
    install_request: PluginInstallRequest,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin),
):
    """Install a plugin from various sources"""
    try:
        plugin_service = get_plugin_service(db)
        result = plugin_service.install_plugin(install_request, current_admin.id)

        return PluginInstallResponse(**result)

    except Exception as e:
        logger.error(f"Failed to install plugin: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to install plugin: {str(e)}",
        )


@router.post("/{plugin_id}/enable")
async def enable_plugin(
    plugin_id: int,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin),
):
    """Enable and load a plugin"""
    try:
        plugin_service = get_plugin_service(db)
        success = plugin_service.enable_plugin(plugin_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to enable plugin",
            )

        logger.info(f"Plugin {plugin_id} enabled by admin {current_admin.id}")
        return {"message": "Plugin enabled successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to enable plugin {plugin_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to enable plugin: {str(e)}",
        )


@router.post("/{plugin_id}/disable")
async def disable_plugin(
    plugin_id: int,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin),
):
    """Disable and unload a plugin"""
    try:
        plugin_service = get_plugin_service(db)
        success = plugin_service.disable_plugin(plugin_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to disable plugin",
            )

        logger.info(f"Plugin {plugin_id} disabled by admin {current_admin.id}")
        return {"message": "Plugin disabled successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to disable plugin {plugin_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to disable plugin: {str(e)}",
        )


@router.post("/{plugin_id}/reload")
async def reload_plugin(
    plugin_id: int,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin),
):
    """Reload a plugin"""
    try:
        plugin_service = get_plugin_service(db)
        success = plugin_service.plugin_manager.reload_plugin(plugin_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to reload plugin",
            )

        logger.info(f"Plugin {plugin_id} reloaded by admin {current_admin.id}")
        return {"message": "Plugin reloaded successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to reload plugin {plugin_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reload plugin: {str(e)}",
        )


@router.post("/{plugin_id}/execute", response_model=PluginExecuteResponse)
async def execute_plugin_method(
    plugin_id: int,
    execute_request: PluginExecuteRequest,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin),
):
    """Execute a plugin method"""
    try:
        plugin_service = get_plugin_service(db)
        result = plugin_service.execute_plugin_method(plugin_id, execute_request)

        return PluginExecuteResponse(**result)

    except Exception as e:
        logger.error(f"Failed to execute plugin method: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute plugin method: {str(e)}",
        )


@router.get("/{plugin_id}/health", response_model=PluginHealthResponse)
async def get_plugin_health(
    plugin_id: int,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin),
):
    """Get plugin health status"""
    try:
        plugin_service = get_plugin_service(db)
        plugin_instance = plugin_service.plugin_manager.get_plugin_instance(plugin_id)

        if not plugin_instance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Plugin not loaded"
            )

        plugin = plugin_service.get_plugin(plugin_id)
        health_check = plugin_instance.health_check()

        return PluginHealthResponse(
            plugin_id=plugin_id,
            plugin_name=plugin.name,
            status=plugin.status,
            health_status=health_check.get("status", "unknown"),
            checks=health_check.get("checks", []),
            last_check=plugin.updated_at or plugin.created_at,
            uptime=_calculate_plugin_uptime(plugin),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get plugin health {plugin_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get plugin health: {str(e)}",
        )


# Plugin Configuration Endpoints
@router.get("/{plugin_id}/config", response_model=List[PluginConfiguration])
async def get_plugin_configurations(
    plugin_id: int,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin),
):
    """Get plugin configurations"""
    try:
        config_repo = PluginConfigurationRepository(db)
        configurations = config_repo.get_by_plugin_id(plugin_id)

        return configurations

    except Exception as e:
        logger.error(f"Failed to get plugin configurations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get plugin configurations: {str(e)}",
        )


@router.post(
    "/{plugin_id}/config",
    response_model=PluginConfiguration,
    status_code=status.HTTP_201_CREATED,
)
async def create_plugin_configuration(
    plugin_id: int,
    config_data: PluginConfigurationCreate,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin),
):
    """Create plugin configuration"""
    try:
        config_repo = PluginConfigurationRepository(db)

        # Set plugin_id from URL
        config_data.plugin_id = plugin_id

        configuration = config_repo.create(config_data.dict())

        logger.info(f"Plugin configuration created for plugin {plugin_id}")
        return configuration

    except Exception as e:
        logger.error(f"Failed to create plugin configuration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create plugin configuration: {str(e)}",
        )


@router.put("/{plugin_id}/config/{config_id}", response_model=PluginConfiguration)
async def update_plugin_configuration(
    plugin_id: int,
    config_id: int,
    config_data: PluginConfigurationUpdate,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin),
):
    """Update plugin configuration"""
    try:
        config_repo = PluginConfigurationRepository(db)

        configuration = config_repo.update(
            config_id, config_data.dict(exclude_unset=True)
        )

        if not configuration:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Configuration not found"
            )

        logger.info(f"Plugin configuration {config_id} updated")
        return configuration

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update plugin configuration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update plugin configuration: {str(e)}",
        )


@router.delete(
    "/{plugin_id}/config/{config_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_plugin_configuration(
    plugin_id: int,
    config_id: int,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin),
):
    """Delete plugin configuration"""
    try:
        config_repo = PluginConfigurationRepository(db)

        success = config_repo.delete(config_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Configuration not found"
            )

        logger.info(f"Plugin configuration {config_id} deleted")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete plugin configuration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete plugin configuration: {str(e)}",
        )


# Plugin Hook Endpoints
@router.get("/{plugin_id}/hooks", response_model=List[PluginHook])
async def get_plugin_hooks(
    plugin_id: int,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin),
):
    """Get plugin hooks"""
    try:
        hook_repo = PluginHookRepository(db)
        hooks = hook_repo.get_by_plugin_id(plugin_id)

        return hooks

    except Exception as e:
        logger.error(f"Failed to get plugin hooks: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get plugin hooks: {str(e)}",
        )


@router.post(
    "/{plugin_id}/hooks", response_model=PluginHook, status_code=status.HTTP_201_CREATED
)
async def create_plugin_hook(
    plugin_id: int,
    hook_data: PluginHookCreate,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin),
):
    """Create plugin hook"""
    try:
        hook_repo = PluginHookRepository(db)

        # Set plugin_id from URL
        hook_data.plugin_id = plugin_id

        hook = hook_repo.create(hook_data.dict())

        logger.info(f"Plugin hook created for plugin {plugin_id}")
        return hook

    except Exception as e:
        logger.error(f"Failed to create plugin hook: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create plugin hook: {str(e)}",
        )


# Plugin Statistics and Monitoring
@router.get("/stats", response_model=PluginStatsResponse)
async def get_plugin_stats(
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin),
):
    """Get plugin statistics"""
    try:
        plugin_service = get_plugin_service(db)
        stats = plugin_service.get_plugin_stats()

        return PluginStatsResponse(**stats)

    except Exception as e:
        logger.error(f"Failed to get plugin stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get plugin stats: {str(e)}",
        )


@router.get("/logs", response_model=PaginatedPluginLogs)
async def get_plugin_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    plugin_id: Optional[int] = None,
    log_level: Optional[str] = None,
    hook_name: Optional[str] = None,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin),
):
    """Get plugin logs with filtering"""
    try:
        log_repo = PluginLogRepository(db)
        logs, total = log_repo.search_logs(
            plugin_id=plugin_id,
            log_level=log_level,
            hook_name=hook_name,
            skip=skip,
            limit=limit,
        )

        pages = (total + limit - 1) // limit

        return PaginatedPluginLogs(
            items=logs, total=total, page=(skip // limit) + 1, size=limit, pages=pages
        )

    except Exception as e:
        logger.error(f"Failed to get plugin logs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get plugin logs: {str(e)}",
        )


# Plugin Registry Endpoints
@router.get("/registry", response_model=PaginatedPluginRegistry)
async def get_plugin_registry(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    plugin_type: Optional[PluginType] = None,
    is_verified: Optional[bool] = None,
    is_featured: Optional[bool] = None,
    search_term: Optional[str] = None,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin),
):
    """Get plugin registry with filtering"""
    try:
        registry_repo = PluginRegistryRepository(db)
        plugins, total = registry_repo.search_registry(
            search_term=search_term,
            plugin_type=plugin_type,
            is_verified=is_verified,
            is_featured=is_featured,
            skip=skip,
            limit=limit,
        )

        pages = (total + limit - 1) // limit

        return PaginatedPluginRegistry(
            items=plugins,
            total=total,
            page=(skip // limit) + 1,
            size=limit,
            pages=pages,
        )

    except Exception as e:
        logger.error(f"Failed to get plugin registry: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get plugin registry: {str(e)}",
        )


# Plugin Template Endpoints
@router.get("/templates", response_model=PaginatedPluginTemplates)
async def get_plugin_templates(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    plugin_type: Optional[PluginType] = None,
    is_active: Optional[bool] = None,
    search_term: Optional[str] = None,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin),
):
    """Get plugin templates with filtering"""
    try:
        template_repo = PluginTemplateRepository(db)
        templates, total = template_repo.search_templates(
            search_term=search_term,
            plugin_type=plugin_type,
            is_active=is_active,
            skip=skip,
            limit=limit,
        )

        pages = (total + limit - 1) // limit

        return PaginatedPluginTemplates(
            items=templates,
            total=total,
            page=(skip // limit) + 1,
            size=limit,
            pages=pages,
        )

    except Exception as e:
        logger.error(f"Failed to get plugin templates: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get plugin templates: {str(e)}",
        )


@router.post(
    "/templates", response_model=PluginTemplate, status_code=status.HTTP_201_CREATED
)
async def create_plugin_template(
    template_data: PluginTemplateCreate,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin),
):
    """Create plugin template"""
    try:
        template_repo = PluginTemplateRepository(db)

        template_dict = template_data.dict()
        template_dict["created_by"] = current_admin.id

        template = template_repo.create(template_dict)

        logger.info(
            f"Plugin template {template.name} created by admin {current_admin.id}"
        )
        return template

    except Exception as e:
        logger.error(f"Failed to create plugin template: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create plugin template: {str(e)}",
        )


# Bulk Operations
@router.post("/bulk", response_model=BulkPluginOperationResponse)
async def bulk_plugin_operation(
    operation_request: BulkPluginOperation,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin),
):
    """Perform bulk operations on plugins"""
    try:
        plugin_service = get_plugin_service(db)
        successful = []
        failed = []
        warnings = []

        for plugin_id in operation_request.plugin_ids:
            try:
                if operation_request.operation == "enable":
                    success = plugin_service.enable_plugin(plugin_id)
                elif operation_request.operation == "disable":
                    success = plugin_service.disable_plugin(plugin_id)
                elif operation_request.operation == "update":
                    # Implement bulk update
                    success = plugin_service.update_plugin_from_registry(plugin_id)
                    if not success:
                        warnings.append(f"No update available for plugin {plugin_id}")
                elif operation_request.operation == "uninstall":
                    success = plugin_service.delete_plugin(plugin_id)
                else:
                    success = False
                    warnings.append(f"Unknown operation: {operation_request.operation}")

                if success:
                    successful.append(plugin_id)
                else:
                    failed.append(
                        {
                            "plugin_id": plugin_id,
                            "error": f"Operation {operation_request.operation} failed",
                        }
                    )

            except Exception as e:
                failed.append({"plugin_id": plugin_id, "error": str(e)})

        summary = {
            "total": len(operation_request.plugin_ids),
            "successful": len(successful),
            "failed": len(failed),
        }

        logger.info(
            f"Bulk operation {operation_request.operation} completed by admin {current_admin.id}"
        )

        return BulkPluginOperationResponse(
            successful=successful, failed=failed, warnings=warnings, summary=summary
        )

    except Exception as e:
        logger.error(f"Failed to perform bulk operation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to perform bulk operation: {str(e)}",
        )


# Helper Functions
def _calculate_plugin_uptime(plugin) -> int:
    """Calculate plugin uptime in seconds since last restart/activation."""
    from datetime import datetime, timezone

    if not plugin.updated_at and not plugin.created_at:
        return 0

    # Use the most recent timestamp (updated_at if available, otherwise created_at)
    last_restart = plugin.updated_at or plugin.created_at

    # Calculate uptime in seconds
    now = datetime.now(timezone.utc)
    if last_restart.tzinfo is None:
        # Handle naive datetime by assuming UTC
        last_restart = last_restart.replace(tzinfo=timezone.utc)

    uptime_delta = now - last_restart
    return int(uptime_delta.total_seconds())
