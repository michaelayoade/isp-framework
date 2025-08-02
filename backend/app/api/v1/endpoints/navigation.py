"""
Navigation endpoints for UI module and submodule management.
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.permissions import require_permission
from app.services.navigation_service import NavigationService
from app.schemas.navigation import (
    UIModule, UIModuleCreate, UIModuleUpdate,
    UISubmodule, UISubmoduleCreate, UISubmoduleUpdate,
    GlobalNavigationResponse
)
from app.models.auth.base import Administrator

router = APIRouter()


@router.get("/global", response_model=GlobalNavigationResponse)
async def get_global_navigation(
    tenant_scope: Optional[str] = Query(None, description="Filter by tenant scope"),
    current_user: Administrator = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get global navigation structure for top-bar search.
    
    This endpoint returns a lightweight structure of modules and submodules
    that can be used for navigation discovery in the frontend top-bar search.
    Results are filtered by user permissions and tenant scope.
    """
    try:
        service = NavigationService(db)
        
        # Get user permissions (simplified - in production, extract from user roles)
        user_permissions = []
        if current_user.is_superuser:
            # Superuser has all permissions
            user_permissions = None
        else:
            # Extract permissions from user roles
            # This would typically come from the RBAC system
            user_permissions = []
        
        # Get navigation structure
        navigation = service.get_global_navigation(
            tenant_scope=tenant_scope,
            user_permissions=user_permissions
        )
        
        return navigation
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving navigation: {str(e)}")


@router.get("/modules", response_model=List[UIModule])
async def get_modules(
    skip: int = Query(0, ge=0, description="Number of modules to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of modules to return"),
    enabled_only: bool = Query(True, description="Filter by enabled modules only"),
    tenant_scope: Optional[str] = Query(None, description="Filter by tenant scope"),
    current_user: Administrator = Depends(require_permission("admin.view")),
    db: Session = Depends(get_db)
):
    """Get all UI modules with optional filtering."""
    service = NavigationService(db)
    return service.get_modules(skip, limit, enabled_only, tenant_scope)


@router.post("/modules", response_model=UIModule)
async def create_module(
    module_data: UIModuleCreate,
    current_user: Administrator = Depends(require_permission("admin.create")),
    db: Session = Depends(get_db)
):
    """Create a new UI module."""
    service = NavigationService(db)
    
    # Check if module code already exists
    existing = service.get_module_by_code(module_data.code)
    if existing:
        raise HTTPException(status_code=400, detail=f"Module with code '{module_data.code}' already exists")
    
    return service.create_module(module_data)


@router.get("/modules/{module_id}", response_model=UIModule)
async def get_module(
    module_id: UUID,
    current_user: Administrator = Depends(require_permission("admin.view")),
    db: Session = Depends(get_db)
):
    """Get a UI module by ID."""
    service = NavigationService(db)
    module = service.get_module_by_id(module_id)
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")
    return module


@router.put("/modules/{module_id}", response_model=UIModule)
async def update_module(
    module_id: UUID,
    module_data: UIModuleUpdate,
    current_user: Administrator = Depends(require_permission("admin.update")),
    db: Session = Depends(get_db)
):
    """Update a UI module."""
    service = NavigationService(db)
    updated_module = service.update_module(module_id, module_data)
    if not updated_module:
        raise HTTPException(status_code=404, detail="Module not found")
    return updated_module


@router.delete("/modules/{module_id}")
async def delete_module(
    module_id: UUID,
    current_user: Administrator = Depends(require_permission("admin.delete")),
    db: Session = Depends(get_db)
):
    """Delete a UI module."""
    service = NavigationService(db)
    success = service.delete_module(module_id)
    if not success:
        raise HTTPException(status_code=404, detail="Module not found")
    return {"message": "Module deleted successfully"}


@router.get("/submodules", response_model=List[UISubmodule])
async def get_submodules(
    module_id: Optional[UUID] = Query(None, description="Filter by module ID"),
    skip: int = Query(0, ge=0, description="Number of submodules to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of submodules to return"),
    enabled_only: bool = Query(True, description="Filter by enabled submodules only"),
    current_user: Administrator = Depends(require_permission("admin.view")),
    db: Session = Depends(get_db)
):
    """Get UI submodules with optional filtering."""
    service = NavigationService(db)
    return service.get_submodules(module_id, skip, limit, enabled_only)


@router.post("/submodules", response_model=UISubmodule)
async def create_submodule(
    submodule_data: UISubmoduleCreate,
    current_user: Administrator = Depends(require_permission("admin.create")),
    db: Session = Depends(get_db)
):
    """Create a new UI submodule."""
    service = NavigationService(db)
    
    # Check if parent module exists
    module = service.get_module_by_id(submodule_data.module_id)
    if not module:
        raise HTTPException(status_code=400, detail="Parent module not found")
    
    return service.create_submodule(submodule_data)


@router.get("/submodules/{submodule_id}", response_model=UISubmodule)
async def get_submodule(
    submodule_id: UUID,
    current_user: Administrator = Depends(require_permission("admin.view")),
    db: Session = Depends(get_db)
):
    """Get a UI submodule by ID."""
    service = NavigationService(db)
    submodule = service.get_submodule_by_id(submodule_id)
    if not submodule:
        raise HTTPException(status_code=404, detail="Submodule not found")
    return submodule


@router.put("/submodules/{submodule_id}", response_model=UISubmodule)
async def update_submodule(
    submodule_id: UUID,
    submodule_data: UISubmoduleUpdate,
    current_user: Administrator = Depends(require_permission("admin.update")),
    db: Session = Depends(get_db)
):
    """Update a UI submodule."""
    service = NavigationService(db)
    updated_submodule = service.update_submodule(submodule_id, submodule_data)
    if not updated_submodule:
        raise HTTPException(status_code=404, detail="Submodule not found")
    return updated_submodule


@router.delete("/submodules/{submodule_id}")
async def delete_submodule(
    submodule_id: UUID,
    current_user: Administrator = Depends(require_permission("admin.delete")),
    db: Session = Depends(get_db)
):
    """Delete a UI submodule."""
    service = NavigationService(db)
    success = service.delete_submodule(submodule_id)
    if not success:
        raise HTTPException(status_code=404, detail="Submodule not found")
    return {"message": "Submodule deleted successfully"}


@router.post("/seed")
async def seed_navigation_data(
    current_user: Administrator = Depends(require_permission("admin.create")),
    db: Session = Depends(get_db)
):
    """Seed initial navigation data for the ISP Framework."""
    service = NavigationService(db)
    result = service.seed_initial_data()
    return {
        "message": "Navigation data seeded successfully",
        "modules_created": result["modules_created"],
        "submodules_created": result["submodules_created"]
    }
