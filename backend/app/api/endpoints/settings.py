"""
Settings management endpoints for ISP Framework.

Provides REST API for managing application settings and feature flags.
"""
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, Field

from app.services.settings_service import get_settings_service, get_feature_flag_service
from app.models.settings import SettingType, SettingCategory
from app.api.dependencies import get_current_admin_user
from app.models.auth.base import Administrator

router = APIRouter()


# Pydantic models for API
class SettingResponse(BaseModel):
    key: str
    value: Any
    default_value: Any
    setting_type: str
    category: str
    description: Optional[str]
    display_name: Optional[str]
    help_text: Optional[str]
    is_secret: bool
    is_readonly: bool
    requires_restart: bool
    validation_regex: Optional[str]
    min_value: Optional[str]
    max_value: Optional[str]
    allowed_values: Optional[List[Any]]


class SettingUpdateRequest(BaseModel):
    value: Any
    change_reason: Optional[str] = None


class SettingCreateRequest(BaseModel):
    key: str
    value: Any
    setting_type: SettingType
    category: SettingCategory
    description: Optional[str] = None
    display_name: Optional[str] = None
    help_text: Optional[str] = None
    is_secret: bool = False
    is_readonly: bool = False
    requires_restart: bool = False
    validation_regex: Optional[str] = None
    min_value: Optional[str] = None
    max_value: Optional[str] = None
    allowed_values: Optional[List[Any]] = None


class FeatureFlagResponse(BaseModel):
    name: str
    description: Optional[str]
    is_enabled: bool
    enabled_for_all: bool
    enabled_percentage: int
    enabled_user_ids: Optional[List[int]]
    enabled_ip_ranges: Optional[List[str]]
    enabled_environments: Optional[List[str]]
    category: str
    tags: Optional[List[str]]


class FeatureFlagUpdateRequest(BaseModel):
    description: Optional[str] = None
    is_enabled: Optional[bool] = None
    enabled_for_all: Optional[bool] = None
    enabled_percentage: Optional[int] = Field(None, ge=0, le=100)
    enabled_user_ids: Optional[List[int]] = None
    enabled_ip_ranges: Optional[List[str]] = None
    enabled_environments: Optional[List[str]] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None


@router.get("/", response_model=List[SettingResponse])
async def get_all_settings(
    category: Optional[SettingCategory] = None,
    current_admin: Administrator = Depends(get_current_admin_user)
):
    """Get all settings, optionally filtered by category."""
    try:
        with get_settings_service() as service:
            if category:
                settings = service.get_settings_by_category(category)
            else:
                settings = service.db.query(service.db.query(service.db.query.__class__.__bases__[0]).model).filter(
                    service.db.query.__class__.__bases__[0].model.is_active == True
                ).all()
                # Simplified - get all active settings
                settings = []
                all_settings = service.get_all_settings()
                for key, value in all_settings.items():
                    setting_obj = service.db.query(service.db.query.__class__.__bases__[0]).filter(
                        service.db.query.__class__.__bases__[0].key == key
                    ).first()
                    if setting_obj:
                        settings.append(setting_obj)
            
            return [
                SettingResponse(
                    key=setting.key,
                    value=setting.get_typed_value(),
                    default_value=setting.get_typed_default(),
                    setting_type=setting.setting_type,
                    category=setting.category,
                    description=setting.description,
                    display_name=setting.display_name,
                    help_text=setting.help_text,
                    is_secret=setting.is_secret,
                    is_readonly=setting.is_readonly,
                    requires_restart=setting.requires_restart,
                    validation_regex=setting.validation_regex,
                    min_value=setting.min_value,
                    max_value=setting.max_value,
                    allowed_values=setting.allowed_values
                )
                for setting in settings
            ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get settings: {str(e)}"
        )


@router.get("/{key}", response_model=SettingResponse)
async def get_setting(
    key: str,
    current_admin: Administrator = Depends(get_current_admin_user)
):
    """Get a specific setting by key."""
    try:
        with get_settings_service() as service:
            setting = service.db.query(service.db.query.__class__.__bases__[0]).filter(
                service.db.query.__class__.__bases__[0].key == key
            ).first()
            
            if not setting:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Setting '{key}' not found"
                )
            
            return SettingResponse(
                key=setting.key,
                value=setting.get_typed_value(),
                default_value=setting.get_typed_default(),
                setting_type=setting.setting_type,
                category=setting.category,
                description=setting.description,
                display_name=setting.display_name,
                help_text=setting.help_text,
                is_secret=setting.is_secret,
                is_readonly=setting.is_readonly,
                requires_restart=setting.requires_restart,
                validation_regex=setting.validation_regex,
                min_value=setting.min_value,
                max_value=setting.max_value,
                allowed_values=setting.allowed_values
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get setting: {str(e)}"
        )


@router.put("/{key}")
async def update_setting(
    key: str,
    request_data: SettingUpdateRequest,
    request: Request,
    current_admin: Administrator = Depends(get_current_admin_user)
):
    """Update a setting value."""
    try:
        with get_settings_service() as service:
            setting = service.set_setting(
                key=key,
                value=request_data.value,
                changed_by_id=current_admin.id,
                change_reason=request_data.change_reason,
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("User-Agent")
            )
            
            return {
                "message": "Setting updated successfully",
                "key": key,
                "new_value": setting.get_typed_value(),
                "requires_restart": setting.requires_restart
            }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update setting: {str(e)}"
        )


@router.post("/")
async def create_setting(
    request_data: SettingCreateRequest,
    current_admin: Administrator = Depends(get_current_admin_user)
):
    """Create a new setting."""
    try:
        with get_settings_service() as service:
            setting = service.create_setting(
                key=request_data.key,
                value=request_data.value,
                setting_type=request_data.setting_type,
                category=request_data.category,
                description=request_data.description,
                display_name=request_data.display_name,
                help_text=request_data.help_text,
                is_secret=request_data.is_secret,
                is_readonly=request_data.is_readonly,
                requires_restart=request_data.requires_restart,
                validation_regex=request_data.validation_regex,
                min_value=request_data.min_value,
                max_value=request_data.max_value,
                allowed_values=request_data.allowed_values
            )
            
            return {
                "message": "Setting created successfully",
                "key": setting.key,
                "id": setting.id
            }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create setting: {str(e)}"
        )


@router.delete("/{key}")
async def delete_setting(
    key: str,
    current_admin: Administrator = Depends(get_current_admin_user)
):
    """Delete a setting (soft delete)."""
    try:
        with get_settings_service() as service:
            service.delete_setting(key, changed_by_id=current_admin.id)
            
            return {"message": f"Setting '{key}' deleted successfully"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete setting: {str(e)}"
        )


@router.get("/{key}/history")
async def get_setting_history(
    key: str,
    limit: int = 50,
    current_admin: Administrator = Depends(get_current_admin_user)
):
    """Get change history for a setting."""
    try:
        with get_settings_service() as service:
            history = service.get_setting_history(key, limit)
            
            return [
                {
                    "id": h.id,
                    "old_value": h.old_value,
                    "new_value": h.new_value,
                    "changed_by_id": h.changed_by_id,
                    "changed_at": h.changed_at.isoformat(),
                    "change_reason": h.change_reason,
                    "ip_address": h.ip_address
                }
                for h in history
            ]
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get setting history: {str(e)}"
        )


@router.post("/initialize")
async def initialize_default_settings(
    current_admin: Administrator = Depends(get_current_admin_user)
):
    """Initialize default settings."""
    try:
        with get_settings_service() as service:
            count = service.initialize_default_settings()
            
            return {
                "message": "Default settings initialized",
                "created_count": count
            }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize settings: {str(e)}"
        )


# Feature Flags endpoints
@router.get("/flags/", response_model=List[FeatureFlagResponse])
async def get_all_feature_flags(
    current_admin: Administrator = Depends(get_current_admin_user)
):
    """Get all feature flags."""
    try:
        with get_feature_flag_service() as service:
            flags = service.get_all_flags()
            
            return [
                FeatureFlagResponse(
                    name=flag.name,
                    description=flag.description,
                    is_enabled=flag.is_enabled,
                    enabled_for_all=flag.enabled_for_all,
                    enabled_percentage=flag.enabled_percentage,
                    enabled_user_ids=flag.enabled_user_ids,
                    enabled_ip_ranges=flag.enabled_ip_ranges,
                    enabled_environments=flag.enabled_environments,
                    category=flag.category,
                    tags=flag.tags
                )
                for flag in flags
            ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get feature flags: {str(e)}"
        )


@router.get("/flags/{name}")
async def check_feature_flag(
    name: str,
    user_id: Optional[int] = None,
    ip_address: Optional[str] = None,
    environment: Optional[str] = None,
    current_admin: Administrator = Depends(get_current_admin_user)
):
    """Check if a feature flag is enabled for given context."""
    try:
        with get_feature_flag_service() as service:
            is_enabled = service.is_enabled(name, user_id, ip_address, environment)
            
            return {
                "flag_name": name,
                "is_enabled": is_enabled,
                "context": {
                    "user_id": user_id,
                    "ip_address": ip_address,
                    "environment": environment
                }
            }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check feature flag: {str(e)}"
        )


@router.put("/flags/{name}")
async def update_feature_flag(
    name: str,
    request_data: FeatureFlagUpdateRequest,
    current_admin: Administrator = Depends(get_current_admin_user)
):
    """Update a feature flag."""
    try:
        with get_feature_flag_service() as service:
            # Filter out None values
            update_data = {k: v for k, v in request_data.dict().items() if v is not None}
            
            flag = service.update_flag(name, **update_data)
            
            return {
                "message": "Feature flag updated successfully",
                "flag_name": flag.name,
                "is_enabled": flag.is_enabled
            }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update feature flag: {str(e)}"
        )


@router.get("/categories/")
async def get_setting_categories():
    """Get all available setting categories."""
    return [
        {"value": category.value, "name": category.value.replace("_", " ").title()}
        for category in SettingCategory
    ]


@router.get("/types/")
async def get_setting_types():
    """Get all available setting types."""
    return [
        {"value": setting_type.value, "name": setting_type.value.title()}
        for setting_type in SettingType
    ]
