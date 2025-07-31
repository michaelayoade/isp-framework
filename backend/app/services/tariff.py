"""
ISP Tariff Service

Simple service layer for tariff operations aligned with ISP Framework vision.
"""

import logging
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from ..repositories.tariff import InternetTariffRepository
from ..models.tariff import InternetTariff
from ..core.exceptions import NotFoundError, ValidationError

logger = logging.getLogger(__name__)


class TariffService:
    """Service for tariff management operations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.internet_tariff_repo = InternetTariffRepository(db)
    
    def create_internet_tariff(self, tariff_data: Dict[str, Any]) -> InternetTariff:
        """Create a new Internet tariff"""
        try:
            # Validate unique constraints
            if self.internet_tariff_repo.get_by_title(tariff_data.get('title')):
                raise ValidationError(f"Tariff with title '{tariff_data.get('title')}' already exists")
            
            if tariff_data.get('service_name') and self.internet_tariff_repo.get_by_service_name(tariff_data.get('service_name')):
                raise ValidationError(f"Tariff with service name '{tariff_data.get('service_name')}' already exists")
            
            # Create tariff
            tariff = self.internet_tariff_repo.create(tariff_data)
            logger.info(f"Created Internet tariff: {tariff.title} (ID: {tariff.id})")
            return tariff
            
        except Exception as e:
            logger.error(f"Error creating Internet tariff: {str(e)}")
            raise
    
    def get_internet_tariff(self, tariff_id: int) -> InternetTariff:
        """Get Internet tariff by ID"""
        tariff = self.internet_tariff_repo.get(tariff_id)
        if not tariff:
            raise NotFoundError(f"Internet tariff with ID {tariff_id} not found")
        return tariff
    
    def update_internet_tariff(self, tariff_id: int, update_data: Dict[str, Any]) -> InternetTariff:
        """Update Internet tariff"""
        try:
            tariff = self.get_internet_tariff(tariff_id)
            
            # Validate unique constraints if being updated
            if 'title' in update_data and update_data['title'] != tariff.title:
                existing = self.internet_tariff_repo.get_by_title(update_data['title'])
                if existing and existing.id != tariff_id:
                    raise ValidationError(f"Tariff with title '{update_data['title']}' already exists")
            
            if 'service_name' in update_data and update_data['service_name'] != tariff.service_name:
                existing = self.internet_tariff_repo.get_by_service_name(update_data['service_name'])
                if existing and existing.id != tariff_id:
                    raise ValidationError(f"Tariff with service name '{update_data['service_name']}' already exists")
            
            # Update tariff
            updated_tariff = self.internet_tariff_repo.update(tariff_id, update_data)
            logger.info(f"Updated Internet tariff: {updated_tariff.title} (ID: {tariff_id})")
            return updated_tariff
            
        except Exception as e:
            logger.error(f"Error updating Internet tariff {tariff_id}: {str(e)}")
            raise
    
    def delete_internet_tariff(self, tariff_id: int) -> bool:
        """Delete Internet tariff"""
        try:
            tariff = self.get_internet_tariff(tariff_id)
            success = self.internet_tariff_repo.delete(tariff_id)
            if success:
                logger.info(f"Deleted Internet tariff: {tariff.title} (ID: {tariff_id})")
            return success
            
        except Exception as e:
            logger.error(f"Error deleting Internet tariff {tariff_id}: {str(e)}")
            raise
    
    def get_active_internet_tariffs(self, partner_id: int = None) -> List[InternetTariff]:
        """Get all active Internet tariffs"""
        return self.internet_tariff_repo.get_active_tariffs(partner_id)
    
    def get_public_internet_tariffs(self, partner_id: int = None) -> List[InternetTariff]:
        """Get all public Internet tariffs visible to customers"""
        return self.internet_tariff_repo.get_public_tariffs(partner_id)
    
    def search_internet_tariffs(
        self, 
        filters: Dict[str, Any] = None,
        page: int = 1,
        per_page: int = 50
    ) -> Dict[str, Any]:
        """Search Internet tariffs with pagination"""
        skip = (page - 1) * per_page
        tariffs, total = self.internet_tariff_repo.search_tariffs(filters, skip, per_page)
        
        return {
            'tariffs': tariffs,
            'total': total,
            'page': page,
            'per_page': per_page,
            'has_next': skip + per_page < total,
            'has_prev': page > 1
        }
    
    def get_tariff_statistics(self) -> Dict[str, Any]:
        """Get tariff statistics"""
        return self.internet_tariff_repo.get_statistics()
    
    def validate_tariff_for_service(self, tariff_id: int, partner_id: int = None) -> bool:
        """Validate if tariff can be used for service provisioning"""
        try:
            tariff = self.get_internet_tariff(tariff_id)
            
            # Check if tariff is active
            if not tariff.is_active:
                return False
            
            # Check partner restrictions
            if partner_id and partner_id not in tariff.partners_ids:
                return False
            
            # Check availability dates
            now = datetime.now(timezone.utc)
            if tariff.available_from and now < tariff.available_from:
                return False
            
            if tariff.available_until and now > tariff.available_until:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating tariff {tariff_id}: {str(e)}")
            return False
    
    def get_tariff_for_provisioning(self, tariff_id: int) -> Dict[str, Any]:
        """Get tariff data formatted for service provisioning"""
        tariff = self.get_internet_tariff(tariff_id)
        
        return {
            'id': tariff.id,
            'title': tariff.title,
            'service_name': tariff.service_name,
            'speed_download': tariff.speed_download,
            'speed_upload': tariff.speed_upload,
            'speed_limit_at': tariff.speed_limit_at,
            'aggregation': tariff.aggregation,
            'burst_config': {
                'burst_limit': tariff.burst_limit,
                'burst_limit_fixed_down': tariff.burst_limit_fixed_down,
                'burst_limit_fixed_up': tariff.burst_limit_fixed_up,
                'burst_threshold': tariff.burst_threshold,
                'burst_threshold_fixed_down': tariff.burst_threshold_fixed_down,
                'burst_threshold_fixed_up': tariff.burst_threshold_fixed_up,
                'burst_time': tariff.burst_time,
                'burst_type': tariff.burst_type
            },
            'speed_limit_config': {
                'speed_limit_type': tariff.speed_limit_type,
                'speed_limit_fixed_down': tariff.speed_limit_fixed_down,
                'speed_limit_fixed_up': tariff.speed_limit_fixed_up
            },
            'billing_types': tariff.billing_types,
            'price': tariff.price,
            'effective_price': tariff.effective_price,
            'with_vat': tariff.with_vat,
            'vat_percent': tariff.vat_percent
        }
