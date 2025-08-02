"""
Navigation repository for UI module and submodule management.
"""
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import and_

from app.models.navigation import UIModule, UISubmodule
from app.schemas.navigation import UIModuleCreate, UIModuleUpdate, UISubmoduleCreate, UISubmoduleUpdate


class NavigationRepository:
    """Repository for navigation-related database operations."""

    def __init__(self, db: Session):
        self.db = db

    # UI Module operations
    def get_modules(
        self,
        skip: int = 0,
        limit: int = 100,
        enabled_only: bool = True,
        tenant_scope: Optional[str] = None
    ) -> List[UIModule]:
        """Get all UI modules with optional filtering."""
        query = self.db.query(UIModule).options(selectinload(UIModule.submodules))
        
        if enabled_only:
            query = query.filter(UIModule.is_enabled == True)
        
        if tenant_scope:
            query = query.filter(UIModule.tenant_scope == tenant_scope)
        
        return query.order_by(UIModule.order_idx, UIModule.name).offset(skip).limit(limit).all()

    def get_module_by_id(self, module_id: UUID) -> Optional[UIModule]:
        """Get a UI module by ID."""
        return self.db.query(UIModule).options(selectinload(UIModule.submodules)).filter(UIModule.id == module_id).first()

    def get_module_by_code(self, code: str) -> Optional[UIModule]:
        """Get a UI module by code."""
        return self.db.query(UIModule).options(selectinload(UIModule.submodules)).filter(UIModule.code == code).first()

    def create_module(self, module_data: UIModuleCreate) -> UIModule:
        """Create a new UI module."""
        db_module = UIModule(**module_data.model_dump())
        self.db.add(db_module)
        self.db.commit()
        self.db.refresh(db_module)
        return db_module

    def update_module(self, module_id: UUID, module_data: UIModuleUpdate) -> Optional[UIModule]:
        """Update a UI module."""
        db_module = self.get_module_by_id(module_id)
        if not db_module:
            return None
        
        update_data = module_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_module, field, value)
        
        self.db.commit()
        self.db.refresh(db_module)
        return db_module

    def delete_module(self, module_id: UUID) -> bool:
        """Delete a UI module."""
        db_module = self.get_module_by_id(module_id)
        if not db_module:
            return False
        
        self.db.delete(db_module)
        self.db.commit()
        return True

    # UI Submodule operations
    def get_submodules(
        self,
        module_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100,
        enabled_only: bool = True
    ) -> List[UISubmodule]:
        """Get UI submodules with optional filtering."""
        query = self.db.query(UISubmodule)
        
        if module_id:
            query = query.filter(UISubmodule.module_id == module_id)
        
        if enabled_only:
            query = query.filter(UISubmodule.is_enabled == True)
        
        return query.order_by(UISubmodule.order_idx, UISubmodule.name).offset(skip).limit(limit).all()

    def get_submodule_by_id(self, submodule_id: UUID) -> Optional[UISubmodule]:
        """Get a UI submodule by ID."""
        return self.db.query(UISubmodule).filter(UISubmodule.id == submodule_id).first()

    def get_submodule_by_code(self, module_id: UUID, code: str) -> Optional[UISubmodule]:
        """Get a UI submodule by module ID and code."""
        return self.db.query(UISubmodule).filter(
            and_(UISubmodule.module_id == module_id, UISubmodule.code == code)
        ).first()

    def create_submodule(self, submodule_data: UISubmoduleCreate) -> UISubmodule:
        """Create a new UI submodule."""
        db_submodule = UISubmodule(**submodule_data.model_dump())
        self.db.add(db_submodule)
        self.db.commit()
        self.db.refresh(db_submodule)
        return db_submodule

    def update_submodule(self, submodule_id: UUID, submodule_data: UISubmoduleUpdate) -> Optional[UISubmodule]:
        """Update a UI submodule."""
        db_submodule = self.get_submodule_by_id(submodule_id)
        if not db_submodule:
            return None
        
        update_data = submodule_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_submodule, field, value)
        
        self.db.commit()
        self.db.refresh(db_submodule)
        return db_submodule

    def delete_submodule(self, submodule_id: UUID) -> bool:
        """Delete a UI submodule."""
        db_submodule = self.get_submodule_by_id(submodule_id)
        if not db_submodule:
            return False
        
        self.db.delete(db_submodule)
        self.db.commit()
        return True

    # Navigation-specific queries
    def get_navigation_structure(
        self,
        tenant_scope: Optional[str] = None,
        user_permissions: Optional[List[str]] = None
    ) -> List[UIModule]:
        """Get the complete navigation structure for global search."""
        query = self.db.query(UIModule).options(selectinload(UIModule.submodules))
        
        # Filter by enabled modules
        query = query.filter(UIModule.is_enabled == True)
        
        # Filter by tenant scope
        if tenant_scope:
            query = query.filter(UIModule.tenant_scope.in_(["GLOBAL", tenant_scope]))
        
        modules = query.order_by(UIModule.order_idx, UIModule.name).all()
        
        # Filter submodules by permissions and enabled status
        if user_permissions is not None:
            for module in modules:
                module.submodules = [
                    sub for sub in module.submodules
                    if sub.is_enabled and (
                        not sub.required_permission or 
                        sub.required_permission in user_permissions
                    )
                ]
        else:
            for module in modules:
                module.submodules = [sub for sub in module.submodules if sub.is_enabled]
        
        return modules
