"""
Navigation schemas for UI module and submodule registry.
"""
from typing import List, Optional
from pydantic import BaseModel, Field
from uuid import UUID


class UISubmoduleBase(BaseModel):
    """Base schema for UI submodule."""
    code: str = Field(..., max_length=50, description="Unique code for the submodule")
    name: str = Field(..., max_length=100, description="Display name for the submodule")
    icon: Optional[str] = Field(None, max_length=50, description="Icon name for the submodule")
    route: str = Field(..., max_length=200, description="Route path for the submodule")
    order_idx: int = Field(0, description="Order index for sorting")
    is_enabled: bool = Field(True, description="Whether the submodule is enabled")
    required_permission: Optional[str] = Field(None, max_length=100, description="Required permission to access")
    description: Optional[str] = Field(None, description="Description of the submodule")


class UISubmoduleCreate(UISubmoduleBase):
    """Schema for creating a UI submodule."""
    module_id: UUID = Field(..., description="ID of the parent module")


class UISubmoduleUpdate(BaseModel):
    """Schema for updating a UI submodule."""
    name: Optional[str] = Field(None, max_length=100)
    icon: Optional[str] = Field(None, max_length=50)
    route: Optional[str] = Field(None, max_length=200)
    order_idx: Optional[int] = None
    is_enabled: Optional[bool] = None
    required_permission: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None


class UISubmodule(UISubmoduleBase):
    """Schema for UI submodule response."""
    id: UUID
    module_id: UUID

    class Config:
        from_attributes = True


class UIModuleBase(BaseModel):
    """Base schema for UI module."""
    code: str = Field(..., max_length=50, description="Unique code for the module")
    name: str = Field(..., max_length=100, description="Display name for the module")
    icon: Optional[str] = Field(None, max_length=50, description="Icon name for the module")
    route: str = Field(..., max_length=200, description="Base route path for the module")
    order_idx: int = Field(0, description="Order index for sorting")
    is_enabled: bool = Field(True, description="Whether the module is enabled")
    tenant_scope: str = Field("GLOBAL", max_length=20, description="Tenant scope (GLOBAL, RESELLER, CUSTOMER)")
    description: Optional[str] = Field(None, description="Description of the module")


class UIModuleCreate(UIModuleBase):
    """Schema for creating a UI module."""
    pass


class UIModuleUpdate(BaseModel):
    """Schema for updating a UI module."""
    name: Optional[str] = Field(None, max_length=100)
    icon: Optional[str] = Field(None, max_length=50)
    route: Optional[str] = Field(None, max_length=200)
    order_idx: Optional[int] = None
    is_enabled: Optional[bool] = None
    tenant_scope: Optional[str] = Field(None, max_length=20)
    description: Optional[str] = None


class UIModule(UIModuleBase):
    """Schema for UI module response."""
    id: UUID
    submodules: List[UISubmodule] = []

    class Config:
        from_attributes = True


class NavigationModule(BaseModel):
    """Schema for navigation module in global search response."""
    code: str
    name: str
    icon: Optional[str] = None
    route: str


class NavigationSubmodule(BaseModel):
    """Schema for navigation submodule in global search response."""
    code: str
    name: str
    icon: Optional[str] = None
    route: str


class NavigationItem(BaseModel):
    """Schema for navigation item in global search response."""
    module: NavigationModule
    submodules: List[NavigationSubmodule] = []


class GlobalNavigationResponse(BaseModel):
    """Schema for global navigation search response."""
    navigation: List[NavigationItem] = Field(..., description="List of available modules and submodules")
    total_modules: int = Field(..., description="Total number of modules")
    total_submodules: int = Field(..., description="Total number of submodules")
