"""
Service Templates Service Layer - ISP Service Management System

Business logic layer for service template management including:
- Service template operations (CRUD, validation, availability)
- Internet service template management (speed validation, FUP logic)
- Voice service template management (minutes validation, feature management)
- Bundle service template management (discount calculation, service validation)

Provides high-level business operations with validation, caching, and integration
with tariff, location, and customer management systems.
"""

import logging
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.repositories.service_repository_factory import ServiceRepositoryFactory
from app.models.services import (
    ServiceTemplate, InternetServiceTemplate, VoiceServiceTemplate,
    BundleServiceTemplate, ServiceType, ServiceStatus, ServiceCategory
)
from app.models.foundation import Location
from app.models.foundation.tariff import Tariff

# Create alias for backward compatibility
InternetTariff = Tariff
from app.core.exceptions import ValidationError, NotFoundError, BusinessLogicError

logger = logging.getLogger(__name__)


class ServiceTemplateService:
    """Service layer for service template operations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.repo_factory = ServiceRepositoryFactory(db)
        self.template_repo = self.repo_factory.get_service_template_repo()
    
    async def create_service_template(
        self,
        template_data: Dict[str, Any],
        admin_id: int
    ) -> ServiceTemplate:
        """Create a new service template with validation"""
        logger.info(f"Creating service template: {template_data.get('name')}")
        
        try:
            # Validate required fields
            self._validate_template_data(template_data)
            
            # Check for duplicate code
            existing_template = self.template_repo.get_by_code(template_data['code'])
            if existing_template:
                raise ValidationError(f"Service template with code '{template_data['code']}' already exists")
            
            # Validate tariff reference if provided
            if template_data.get('tariff_id'):
                await self._validate_tariff_reference(template_data['tariff_id'], template_data['service_type'])
            
            # Validate location availability
            if template_data.get('available_locations'):
                await self._validate_location_availability(template_data['available_locations'])
            
            # Create template
            template_data['created_by_id'] = admin_id
            template_data['created_at'] = datetime.now(timezone.utc)
            
            template = ServiceTemplate(**template_data)
            template = self.template_repo.create(template)
            
            logger.info(f"Service template created successfully: {template.id}")
            return template
            
        except IntegrityError as e:
            logger.error(f"Database integrity error creating template: {str(e)}")
            raise ValidationError("Failed to create service template due to data constraints")
        except Exception as e:
            logger.error(f"Error creating service template: {str(e)}")
            raise BusinessLogicError(f"Failed to create service template: {str(e)}")
    
    async def update_service_template(
        self,
        template_id: int,
        update_data: Dict[str, Any],
        admin_id: int
    ) -> ServiceTemplate:
        """Update an existing service template"""
        logger.info(f"Updating service template: {template_id}")
        
        try:
            template = self.template_repo.get_by_id(template_id)
            if not template:
                raise NotFoundError(f"Service template {template_id} not found")
            
            # Validate update data
            if 'code' in update_data and update_data['code'] != template.code:
                existing_template = self.template_repo.get_by_code(update_data['code'])
                if existing_template:
                    raise ValidationError(f"Service template with code '{update_data['code']}' already exists")
            
            # Validate tariff reference if being updated
            if 'tariff_id' in update_data:
                await self._validate_tariff_reference(
                    update_data['tariff_id'], 
                    update_data.get('service_type', template.service_type)
                )
            
            # Validate location availability if being updated
            if 'available_locations' in update_data:
                await self._validate_location_availability(update_data['available_locations'])
            
            # Update template
            update_data['updated_by_id'] = admin_id
            update_data['updated_at'] = datetime.now(timezone.utc)
            
            template = self.template_repo.update(template, update_data)
            
            logger.info(f"Service template updated successfully: {template_id}")
            return template
            
        except Exception as e:
            logger.error(f"Error updating service template {template_id}: {str(e)}")
            raise
    
    async def get_available_templates(
        self,
        location_id: Optional[int] = None,
        service_type: Optional[ServiceType] = None,
        category: Optional[ServiceCategory] = None,
        customer_id: Optional[int] = None
    ) -> List[ServiceTemplate]:
        """Get available service templates for a location/customer"""
        logger.info(f"Getting available templates for location: {location_id}, type: {service_type}")
        
        try:
            templates = self.template_repo.get_available_templates(
                location_id=location_id,
                service_type=service_type,
                category=category
            )
            
            # Additional customer-specific filtering if needed
            if customer_id:
                templates = await self._filter_templates_for_customer(templates, customer_id)
            
            logger.info(f"Found {len(templates)} available templates")
            return templates
            
        except Exception as e:
            logger.error(f"Error getting available templates: {str(e)}")
            raise BusinessLogicError(f"Failed to get available templates: {str(e)}")
    
    async def search_templates(
        self,
        search_params: Dict[str, Any],
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[ServiceTemplate], int, Dict[str, Any]]:
        """Search service templates with pagination and metadata"""
        logger.info(f"Searching templates with params: {search_params}")
        
        try:
            offset = (page - 1) * page_size
            
            templates, total = self.template_repo.search_templates(
                search_term=search_params.get('search_term'),
                service_type=search_params.get('service_type'),
                category=search_params.get('category'),
                is_active=search_params.get('is_active'),
                is_public=search_params.get('is_public'),
                limit=page_size,
                offset=offset
            )
            
            # Calculate pagination metadata
            total_pages = (total + page_size - 1) // page_size
            metadata = {
                'page': page,
                'page_size': page_size,
                'total_items': total,
                'total_pages': total_pages,
                'has_next': page < total_pages,
                'has_prev': page > 1
            }
            
            logger.info(f"Found {total} templates matching search criteria")
            return templates, total, metadata
            
        except Exception as e:
            logger.error(f"Error searching templates: {str(e)}")
            raise BusinessLogicError(f"Failed to search templates: {str(e)}")
    
    async def activate_template(self, template_id: int, admin_id: int) -> ServiceTemplate:
        """Activate a service template"""
        logger.info(f"Activating service template: {template_id}")
        
        try:
            template = self.template_repo.get_by_id(template_id)
            if not template:
                raise NotFoundError(f"Service template {template_id} not found")
            
            if template.is_active:
                raise ValidationError("Service template is already active")
            
            # Validate template can be activated
            await self._validate_template_activation(template)
            
            # Activate template
            template = self.template_repo.update(template, {
                'is_active': True,
                'updated_by_id': admin_id,
                'updated_at': datetime.now(timezone.utc)
            })
            
            logger.info(f"Service template activated: {template_id}")
            return template
            
        except Exception as e:
            logger.error(f"Error activating template {template_id}: {str(e)}")
            raise
    
    async def deactivate_template(self, template_id: int, admin_id: int) -> ServiceTemplate:
        """Deactivate a service template"""
        logger.info(f"Deactivating service template: {template_id}")
        
        try:
            template = self.template_repo.get_by_id(template_id)
            if not template:
                raise NotFoundError(f"Service template {template_id} not found")
            
            if not template.is_active:
                raise ValidationError("Service template is already inactive")
            
            # Check if template is in use
            await self._validate_template_deactivation(template)
            
            # Deactivate template
            template = self.template_repo.update(template, {
                'is_active': False,
                'updated_by_id': admin_id,
                'updated_at': datetime.now(timezone.utc)
            })
            
            logger.info(f"Service template deactivated: {template_id}")
            return template
            
        except Exception as e:
            logger.error(f"Error deactivating template {template_id}: {str(e)}")
            raise
    
    async def get_template_statistics(self) -> Dict[str, Any]:
        """Get comprehensive template statistics"""
        logger.info("Getting template statistics")
        
        try:
            stats = self.template_repo.get_template_statistics()
            
            # Add additional business metrics
            stats['utilization_rate'] = (
                stats['active_templates'] / stats['total_templates'] * 100
                if stats['total_templates'] > 0 else 0
            )
            
            # Add trend data (last 30 days)
            stats['recent_activity'] = await self._get_template_activity_stats()
            
            logger.info("Template statistics retrieved successfully")
            return stats
            
        except Exception as e:
            logger.error(f"Error getting template statistics: {str(e)}")
            raise BusinessLogicError(f"Failed to get template statistics: {str(e)}")
    
    # Private helper methods
    def _validate_template_data(self, template_data: Dict[str, Any]):
        """Validate service template data"""
        required_fields = ['name', 'code', 'service_type', 'category']
        
        for field in required_fields:
            if field not in template_data or not template_data[field]:
                raise ValidationError(f"Required field '{field}' is missing or empty")
        
        # Validate service type
        if template_data['service_type'] not in ServiceType:
            raise ValidationError(f"Invalid service type: {template_data['service_type']}")
        
        # Validate category
        if template_data['category'] not in ServiceCategory:
            raise ValidationError(f"Invalid category: {template_data['category']}")
        
        # Validate availability dates
        if template_data.get('available_from') and template_data.get('available_until'):
            if template_data['available_from'] >= template_data['available_until']:
                raise ValidationError("Available from date must be before available until date")
    
    async def _validate_tariff_reference(self, tariff_id: int, service_type: ServiceType):
        """Validate tariff reference exists and matches service type"""
        # This would integrate with tariff service to validate tariff exists
        # For now, we'll do a basic check
        if service_type == ServiceType.INTERNET:
            tariff = self.db.query(InternetTariff).filter(InternetTariff.id == tariff_id).first()
            if not tariff:
                raise ValidationError(f"Internet tariff {tariff_id} not found")
    
    async def _validate_location_availability(self, location_ids: List[int]):
        """Validate location IDs exist"""
        for location_id in location_ids:
            location = self.db.query(Location).filter(Location.id == location_id).first()
            if not location:
                raise ValidationError(f"Location {location_id} not found")
    
    async def _filter_templates_for_customer(
        self, 
        templates: List[ServiceTemplate], 
        customer_id: int
    ) -> List[ServiceTemplate]:
        """Apply customer-specific filtering to templates"""
        # This could include checking customer eligibility, existing services, etc.
        # For now, return all templates
        return templates
    
    async def _validate_template_activation(self, template: ServiceTemplate):
        """Validate template can be activated"""
        # Check if required tariff exists and is active
        if template.tariff_id:
            await self._validate_tariff_reference(template.tariff_id, template.service_type)
    
    async def _validate_template_deactivation(self, template: ServiceTemplate):
        """Validate template can be deactivated"""
        # Check if template is currently in use by active services
        customer_service_repo = self.repo_factory.get_customer_service_repo()
        active_services = customer_service_repo.get_services_by_template(template.id)
        
        active_count = len([s for s in active_services if s.status == ServiceStatus.ACTIVE])
        if active_count > 0:
            raise ValidationError(
                f"Cannot deactivate template: {active_count} active services are using this template"
            )
    
    async def _get_template_activity_stats(self) -> Dict[str, Any]:
        """Get recent template activity statistics"""
        # This would track template usage, creation, modifications, etc.
        # For now, return basic stats
        return {
            'templates_created_last_30_days': 0,
            'templates_modified_last_30_days': 0,
            'most_popular_template': None
        }


class InternetServiceTemplateService:
    """Service layer for internet service template operations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.repo_factory = ServiceRepositoryFactory(db)
        self.internet_template_repo = self.repo_factory.get_internet_template_repo()
    
    async def create_internet_template(
        self,
        template_data: Dict[str, Any],
        admin_id: int
    ) -> InternetServiceTemplate:
        """Create a new internet service template"""
        logger.info(f"Creating internet service template: {template_data.get('download_speed')}Mbps")
        
        try:
            # Validate internet-specific data
            self._validate_internet_template_data(template_data)
            
            # Create template
            template_data['created_by_id'] = admin_id
            template_data['created_at'] = datetime.now(timezone.utc)
            
            template = InternetServiceTemplate(**template_data)
            template = self.internet_template_repo.create(template)
            
            logger.info(f"Internet service template created: {template.id}")
            return template
            
        except Exception as e:
            logger.error(f"Error creating internet template: {str(e)}")
            raise
    
    async def get_templates_by_speed_range(
        self,
        min_download: Optional[int] = None,
        max_download: Optional[int] = None,
        min_upload: Optional[int] = None,
        max_upload: Optional[int] = None
    ) -> List[InternetServiceTemplate]:
        """Get internet templates by speed range"""
        logger.info("Getting internet templates by speed range")
        
        try:
            templates = self.internet_template_repo.get_by_speed_range(
                min_download=min_download,
                max_download=max_download,
                min_upload=min_upload,
                max_upload=max_upload
            )
            
            logger.info(f"Found {len(templates)} internet templates in speed range")
            return templates
            
        except Exception as e:
            logger.error(f"Error getting templates by speed range: {str(e)}")
            raise BusinessLogicError(f"Failed to get templates by speed range: {str(e)}")
    
    def _validate_internet_template_data(self, template_data: Dict[str, Any]):
        """Validate internet service template data"""
        required_fields = ['download_speed', 'upload_speed']
        
        for field in required_fields:
            if field not in template_data or template_data[field] is None:
                raise ValidationError(f"Required field '{field}' is missing")
        
        # Validate speed values
        if template_data['download_speed'] <= 0:
            raise ValidationError("Download speed must be greater than 0")
        
        if template_data['upload_speed'] <= 0:
            raise ValidationError("Upload speed must be greater than 0")
        
        # Validate FUP settings
        if template_data.get('fup_limit') and template_data['fup_limit'] <= 0:
            raise ValidationError("FUP limit must be greater than 0")


class VoiceServiceTemplateService:
    """Service layer for voice service template operations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.repo_factory = ServiceRepositoryFactory(db)
        self.voice_template_repo = self.repo_factory.get_voice_template_repo()
    
    async def create_voice_template(
        self,
        template_data: Dict[str, Any],
        admin_id: int
    ) -> VoiceServiceTemplate:
        """Create a new voice service template"""
        logger.info(f"Creating voice service template: {template_data.get('included_minutes')} minutes")
        
        try:
            # Validate voice-specific data
            self._validate_voice_template_data(template_data)
            
            # Create template
            template_data['created_by_id'] = admin_id
            template_data['created_at'] = datetime.now(timezone.utc)
            
            template = VoiceServiceTemplate(**template_data)
            template = self.voice_template_repo.create(template)
            
            logger.info(f"Voice service template created: {template.id}")
            return template
            
        except Exception as e:
            logger.error(f"Error creating voice template: {str(e)}")
            raise
    
    def _validate_voice_template_data(self, template_data: Dict[str, Any]):
        """Validate voice service template data"""
        # Validate minutes settings
        if not template_data.get('unlimited_minutes', False):
            if 'included_minutes' not in template_data or template_data['included_minutes'] <= 0:
                raise ValidationError("Included minutes must be greater than 0 for non-unlimited plans")


class BundleServiceTemplateService:
    """Service layer for bundle service template operations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.repo_factory = ServiceRepositoryFactory(db)
        self.bundle_template_repo = self.repo_factory.get_bundle_template_repo()
    
    async def create_bundle_template(
        self,
        template_data: Dict[str, Any],
        admin_id: int
    ) -> BundleServiceTemplate:
        """Create a new bundle service template"""
        logger.info(f"Creating bundle service template with {len(template_data.get('included_services', []))} services")
        
        try:
            # Validate bundle-specific data
            self._validate_bundle_template_data(template_data)
            
            # Create template
            template_data['created_by_id'] = admin_id
            template_data['created_at'] = datetime.now(timezone.utc)
            
            template = BundleServiceTemplate(**template_data)
            template = self.bundle_template_repo.create(template)
            
            logger.info(f"Bundle service template created: {template.id}")
            return template
            
        except Exception as e:
            logger.error(f"Error creating bundle template: {str(e)}")
            raise
    
    def _validate_bundle_template_data(self, template_data: Dict[str, Any]):
        """Validate bundle service template data"""
        # Validate included services
        if not template_data.get('included_services') or len(template_data['included_services']) < 2:
            raise ValidationError("Bundle must include at least 2 services")
        
        # Validate discount settings
        if template_data.get('discount_percentage', 0) < 0 or template_data.get('discount_percentage', 0) > 100:
            raise ValidationError("Discount percentage must be between 0 and 100")


# Service factory for template services
class ServiceTemplateServiceFactory:
    """Factory for creating service template services"""
    
    @staticmethod
    def create_service_template_service(db: Session) -> ServiceTemplateService:
        return ServiceTemplateService(db)
    
    @staticmethod
    def create_internet_template_service(db: Session) -> InternetServiceTemplateService:
        return InternetServiceTemplateService(db)
    
    @staticmethod
    def create_voice_template_service(db: Session) -> VoiceServiceTemplateService:
        return VoiceServiceTemplateService(db)
    
    @staticmethod
    def create_bundle_template_service(db: Session) -> BundleServiceTemplateService:
        return BundleServiceTemplateService(db)
    
    @staticmethod
    def create_all_services(db: Session) -> Dict[str, Any]:
        """Create all service template services"""
        return {
            'service_template': ServiceTemplateService(db),
            'internet_template': InternetServiceTemplateService(db),
            'voice_template': VoiceServiceTemplateService(db),
            'bundle_template': BundleServiceTemplateService(db)
        }
