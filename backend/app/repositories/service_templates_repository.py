"""
Service Templates Repository - ISP Service Management System

Repository layer for service template management including:
- Service templates (base templates for all service types)
- Internet service templates (internet-specific configurations)
- Voice service templates (voice service configurations)
- Bundle service templates (multi-service bundles)

Provides database operations with advanced querying and filtering capabilities.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, desc, func
from datetime import datetime, timezone

from app.repositories.base import BaseRepository
from app.models.services import (
    ServiceTemplate, InternetServiceTemplate, VoiceServiceTemplate,
    BundleServiceTemplate, ServiceType, ServiceCategory
)


class ServiceTemplateRepository(BaseRepository[ServiceTemplate]):
    """Repository for service template operations"""
    
    def __init__(self, db: Session):
        super().__init__(ServiceTemplate, db)
    
    def get_by_code(self, code: str) -> Optional[ServiceTemplate]:
        """Get service template by unique code"""
        return self.db.query(ServiceTemplate).filter(
            ServiceTemplate.code == code
        ).first()
    
    def get_active_templates(self, service_type: Optional[ServiceType] = None) -> List[ServiceTemplate]:
        """Get all active service templates, optionally filtered by type"""
        query = self.db.query(ServiceTemplate).filter(
            ServiceTemplate.is_active is True
        )
        
        if service_type:
            query = query.filter(ServiceTemplate.service_type == service_type)
        
        return query.order_by(ServiceTemplate.display_order, ServiceTemplate.name).all()
    
    def get_available_templates(
        self, 
        location_id: Optional[int] = None,
        service_type: Optional[ServiceType] = None,
        category: Optional[ServiceCategory] = None
    ) -> List[ServiceTemplate]:
        """Get templates available for a specific location and criteria"""
        query = self.db.query(ServiceTemplate).filter(
            ServiceTemplate.is_active is True,
            ServiceTemplate.is_public is True
        )
        
        # Filter by service type
        if service_type:
            query = query.filter(ServiceTemplate.service_type == service_type)
        
        # Filter by category
        if category:
            query = query.filter(ServiceTemplate.category == category)
        
        # Filter by location availability
        if location_id:
            query = query.filter(
                or_(
                    ServiceTemplate.available_locations is None,
                    ServiceTemplate.available_locations.contains([location_id])
                )
            )
        
        # Filter by availability dates
        now = datetime.now(timezone.utc)
        query = query.filter(
            or_(
                ServiceTemplate.available_from is None,
                ServiceTemplate.available_from <= now
            ),
            or_(
                ServiceTemplate.available_until is None,
                ServiceTemplate.available_until >= now
            )
        )
        
        return query.order_by(ServiceTemplate.display_order, ServiceTemplate.name).all()
    
    def search_templates(
        self,
        search_term: Optional[str] = None,
        service_type: Optional[ServiceType] = None,
        category: Optional[ServiceCategory] = None,
        is_active: Optional[bool] = None,
        is_public: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0
    ) -> tuple[List[ServiceTemplate], int]:
        """Search service templates with pagination"""
        query = self.db.query(ServiceTemplate)
        
        # Text search
        if search_term:
            search_filter = or_(
                ServiceTemplate.name.ilike(f"%{search_term}%"),
                ServiceTemplate.code.ilike(f"%{search_term}%"),
                ServiceTemplate.description.ilike(f"%{search_term}%")
            )
            query = query.filter(search_filter)
        
        # Filter by service type
        if service_type:
            query = query.filter(ServiceTemplate.service_type == service_type)
        
        # Filter by category
        if category:
            query = query.filter(ServiceTemplate.category == category)
        
        # Filter by active status
        if is_active is not None:
            query = query.filter(ServiceTemplate.is_active == is_active)
        
        # Filter by public status
        if is_public is not None:
            query = query.filter(ServiceTemplate.is_public == is_public)
        
        # Get total count
        total = query.count()
        
        # Apply pagination and ordering
        templates = query.order_by(
            ServiceTemplate.display_order,
            ServiceTemplate.name
        ).offset(offset).limit(limit).all()
        
        return templates, total
    
    def get_templates_with_tariffs(self, service_type: ServiceType) -> List[ServiceTemplate]:
        """Get templates with their associated tariffs loaded"""
        return self.db.query(ServiceTemplate).filter(
            ServiceTemplate.service_type == service_type,
            ServiceTemplate.is_active is True
        ).options(
            joinedload(ServiceTemplate.tariff)
        ).order_by(ServiceTemplate.display_order).all()
    
    def get_template_statistics(self) -> Dict[str, Any]:
        """Get service template statistics"""
        stats = {}
        
        # Total templates
        stats['total_templates'] = self.db.query(ServiceTemplate).count()
        
        # Active templates
        stats['active_templates'] = self.db.query(ServiceTemplate).filter(
            ServiceTemplate.is_active is True
        ).count()
        
        # Templates by type
        type_stats = self.db.query(
            ServiceTemplate.service_type,
            func.count(ServiceTemplate.id).label('count')
        ).group_by(ServiceTemplate.service_type).all()
        
        stats['by_type'] = {str(type_stat[0]): type_stat[1] for type_stat in type_stats}
        
        # Templates by category
        category_stats = self.db.query(
            ServiceTemplate.category,
            func.count(ServiceTemplate.id).label('count')
        ).group_by(ServiceTemplate.category).all()
        
        stats['by_category'] = {str(cat_stat[0]): cat_stat[1] for cat_stat in category_stats}
        
        # Public vs private
        stats['public_templates'] = self.db.query(ServiceTemplate).filter(
            ServiceTemplate.is_public is True
        ).count()
        
        stats['private_templates'] = self.db.query(ServiceTemplate).filter(
            ServiceTemplate.is_public is False
        ).count()
        
        return stats


class InternetServiceTemplateRepository(BaseRepository[InternetServiceTemplate]):
    """Repository for internet service template operations"""
    
    def __init__(self, db: Session):
        super().__init__(InternetServiceTemplate, db)
    
    def get_by_speed_range(
        self, 
        min_download: Optional[int] = None,
        max_download: Optional[int] = None,
        min_upload: Optional[int] = None,
        max_upload: Optional[int] = None
    ) -> List[InternetServiceTemplate]:
        """Get internet templates by speed range"""
        query = self.db.query(InternetServiceTemplate).join(ServiceTemplate).filter(
            ServiceTemplate.is_active is True
        )
        
        if min_download:
            query = query.filter(InternetServiceTemplate.download_speed >= min_download)
        
        if max_download:
            query = query.filter(InternetServiceTemplate.download_speed <= max_download)
        
        if min_upload:
            query = query.filter(InternetServiceTemplate.upload_speed >= min_upload)
        
        if max_upload:
            query = query.filter(InternetServiceTemplate.upload_speed <= max_upload)
        
        return query.order_by(InternetServiceTemplate.download_speed).all()
    
    def get_with_fup(self, has_fup: bool = True) -> List[InternetServiceTemplate]:
        """Get internet templates with or without FUP"""
        query = self.db.query(InternetServiceTemplate).join(ServiceTemplate).filter(
            ServiceTemplate.is_active is True
        )
        
        if has_fup:
            query = query.filter(InternetServiceTemplate.fup_limit.isnot(None))
        else:
            query = query.filter(InternetServiceTemplate.fup_limit.is_(None))
        
        return query.order_by(InternetServiceTemplate.download_speed).all()


class VoiceServiceTemplateRepository(BaseRepository[VoiceServiceTemplate]):
    """Repository for voice service template operations"""
    
    def __init__(self, db: Session):
        super().__init__(VoiceServiceTemplate, db)
    
    def get_by_minutes_range(
        self,
        min_minutes: Optional[int] = None,
        max_minutes: Optional[int] = None
    ) -> List[VoiceServiceTemplate]:
        """Get voice templates by included minutes range"""
        query = self.db.query(VoiceServiceTemplate).join(ServiceTemplate).filter(
            ServiceTemplate.is_active is True
        )
        
        if min_minutes:
            query = query.filter(VoiceServiceTemplate.included_minutes >= min_minutes)
        
        if max_minutes:
            query = query.filter(VoiceServiceTemplate.included_minutes <= max_minutes)
        
        return query.order_by(VoiceServiceTemplate.included_minutes).all()
    
    def get_unlimited_plans(self) -> List[VoiceServiceTemplate]:
        """Get voice templates with unlimited minutes"""
        return self.db.query(VoiceServiceTemplate).join(ServiceTemplate).filter(
            ServiceTemplate.is_active is True,
            VoiceServiceTemplate.unlimited_minutes is True
        ).order_by(ServiceTemplate.name).all()


class BundleServiceTemplateRepository(BaseRepository[BundleServiceTemplate]):
    """Repository for bundle service template operations"""
    
    def __init__(self, db: Session):
        super().__init__(BundleServiceTemplate, db)
    
    def get_by_service_types(self, service_types: List[ServiceType]) -> List[BundleServiceTemplate]:
        """Get bundle templates that include specific service types"""
        query = self.db.query(BundleServiceTemplate).join(ServiceTemplate).filter(
            ServiceTemplate.is_active is True
        )
        
        for service_type in service_types:
            query = query.filter(
                BundleServiceTemplate.included_services.contains([str(service_type)])
            )
        
        return query.order_by(ServiceTemplate.name).all()
    
    def get_with_discounts(self, min_discount: Optional[float] = None) -> List[BundleServiceTemplate]:
        """Get bundle templates with discounts"""
        query = self.db.query(BundleServiceTemplate).join(ServiceTemplate).filter(
            ServiceTemplate.is_active is True,
            BundleServiceTemplate.discount_percentage > 0
        )
        
        if min_discount:
            query = query.filter(BundleServiceTemplate.discount_percentage >= min_discount)
        
        return query.order_by(desc(BundleServiceTemplate.discount_percentage)).all()
    
    def get_bundle_statistics(self) -> Dict[str, Any]:
        """Get bundle template statistics"""
        stats = {}
        
        # Total bundles
        stats['total_bundles'] = self.db.query(BundleServiceTemplate).count()
        
        # Average discount
        avg_discount = self.db.query(
            func.avg(BundleServiceTemplate.discount_percentage)
        ).scalar()
        stats['average_discount'] = float(avg_discount) if avg_discount else 0.0
        
        # Bundles with contracts
        stats['with_contracts'] = self.db.query(BundleServiceTemplate).filter(
            BundleServiceTemplate.contract_months > 0
        ).count()
        
        return stats


# Repository factory for service templates
class ServiceTemplateRepositoryFactory:
    """Factory for creating service template repositories"""
    
    @staticmethod
    def create_service_template_repo(db: Session) -> ServiceTemplateRepository:
        return ServiceTemplateRepository(db)
    
    @staticmethod
    def create_internet_template_repo(db: Session) -> InternetServiceTemplateRepository:
        return InternetServiceTemplateRepository(db)
    
    @staticmethod
    def create_voice_template_repo(db: Session) -> VoiceServiceTemplateRepository:
        return VoiceServiceTemplateRepository(db)
    
    @staticmethod
    def create_bundle_template_repo(db: Session) -> BundleServiceTemplateRepository:
        return BundleServiceTemplateRepository(db)
    
    @staticmethod
    def create_all_repos(db: Session) -> Dict[str, Any]:
        """Create all service template repositories"""
        return {
            'service_template': ServiceTemplateRepository(db),
            'internet_template': InternetServiceTemplateRepository(db),
            'voice_template': VoiceServiceTemplateRepository(db),
            'bundle_template': BundleServiceTemplateRepository(db)
        }
