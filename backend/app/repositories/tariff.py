"""
ISP Tariff Repository

Simple repository for tariff operations aligned with ISP Framework vision.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from datetime import datetime, timezone

from .base import BaseRepository
from ..models.tariff import InternetTariff


class InternetTariffRepository(BaseRepository):
    """Repository for Internet tariff operations"""
    
    def __init__(self, db: Session):
        super().__init__(InternetTariff, db)
    
    def get_active_tariffs(self, partner_id: int = None) -> List[InternetTariff]:
        """Get all active tariffs, optionally filtered by partner"""
        query = self.db.query(InternetTariff).filter(InternetTariff.is_active == True)
        
        if partner_id:
            query = query.filter(InternetTariff.partners_ids.contains([partner_id]))
        
        return query.order_by(InternetTariff.speed_download, InternetTariff.price).all()
    
    def get_public_tariffs(self, partner_id: int = None) -> List[InternetTariff]:
        """Get all public tariffs visible to customers"""
        query = self.db.query(InternetTariff).filter(
            and_(
                InternetTariff.is_active == True,
                InternetTariff.is_public == True
            )
        )
        
        if partner_id:
            query = query.filter(InternetTariff.partners_ids.contains([partner_id]))
        
        # Check availability dates
        now = datetime.now(timezone.utc)
        query = query.filter(
            and_(
                or_(
                    InternetTariff.available_from.is_(None),
                    InternetTariff.available_from <= now
                ),
                or_(
                    InternetTariff.available_until.is_(None),
                    InternetTariff.available_until >= now
                )
            )
        )
        
        return query.order_by(InternetTariff.speed_download, InternetTariff.price).all()
    
    def search_tariffs(
        self, 
        filters: Dict[str, Any] = None,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[List[InternetTariff], int]:
        """Search tariffs with filtering"""
        query = self.db.query(InternetTariff)
        
        if filters:
            # Status filters
            if filters.get('is_active') is not None:
                query = query.filter(InternetTariff.is_active == filters['is_active'])
            
            if filters.get('is_public') is not None:
                query = query.filter(InternetTariff.is_public == filters['is_public'])
            
            # Partner filter
            if filters.get('partner_id'):
                query = query.filter(InternetTariff.partners_ids.contains([filters['partner_id']]))
            
            # Speed filters
            if filters.get('min_speed_download'):
                query = query.filter(InternetTariff.speed_download >= filters['min_speed_download'])
            
            if filters.get('max_speed_download'):
                query = query.filter(InternetTariff.speed_download <= filters['max_speed_download'])
            
            # Price filters
            if filters.get('min_price'):
                query = query.filter(InternetTariff.price >= filters['min_price'])
            
            if filters.get('max_price'):
                query = query.filter(InternetTariff.price <= filters['max_price'])
            
            # Billing type filter
            if filters.get('billing_type'):
                query = query.filter(InternetTariff.billing_types.contains([filters['billing_type']]))
            
            # Burst filter
            if filters.get('has_burst') is not None:
                if filters['has_burst']:
                    query = query.filter(
                        and_(
                            InternetTariff.burst_type != 'none',
                            InternetTariff.burst_limit > 0
                        )
                    )
                else:
                    query = query.filter(
                        or_(
                            InternetTariff.burst_type == 'none',
                            InternetTariff.burst_limit == 0
                        )
                    )
        
        # Get total count
        total = query.count()
        
        # Apply ordering and pagination
        tariffs = query.order_by(
            InternetTariff.speed_download,
            InternetTariff.price
        ).offset(skip).limit(limit).all()
        
        return tariffs, total
    
    def get_by_title(self, title: str) -> Optional[InternetTariff]:
        """Get tariff by title"""
        return self.db.query(InternetTariff).filter(InternetTariff.title == title).first()
    
    def get_by_service_name(self, service_name: str) -> Optional[InternetTariff]:
        """Get tariff by service name"""
        return self.db.query(InternetTariff).filter(InternetTariff.service_name == service_name).first()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get tariff statistics"""
        total_tariffs = self.db.query(func.count(InternetTariff.id)).scalar()
        active_tariffs = self.db.query(func.count(InternetTariff.id)).filter(
            InternetTariff.is_active == True
        ).scalar()
        public_tariffs = self.db.query(func.count(InternetTariff.id)).filter(
            and_(
                InternetTariff.is_active == True,
                InternetTariff.is_public == True
            )
        ).scalar()
        
        # Price statistics
        price_stats = self.db.query(
            func.avg(InternetTariff.price),
            func.min(InternetTariff.price),
            func.max(InternetTariff.price)
        ).filter(InternetTariff.is_active == True).first()
        
        # Speed statistics
        speed_stats = self.db.query(
            func.min(InternetTariff.speed_download),
            func.max(InternetTariff.speed_download),
            func.min(InternetTariff.speed_upload),
            func.max(InternetTariff.speed_upload)
        ).filter(InternetTariff.is_active == True).first()
        
        # Billing types count
        billing_types_count = {}
        tariffs_with_billing = self.db.query(InternetTariff).filter(
            and_(
                InternetTariff.is_active == True,
                InternetTariff.billing_types.isnot(None)
            )
        ).all()
        
        for tariff in tariffs_with_billing:
            if tariff.billing_types:
                for billing_type in tariff.billing_types:
                    billing_types_count[billing_type] = billing_types_count.get(billing_type, 0) + 1
        
        return {
            'total_tariffs': total_tariffs,
            'active_tariffs': active_tariffs,
            'public_tariffs': public_tariffs,
            'average_price': price_stats[0] or 0,
            'speed_ranges': {
                'min_download': speed_stats[0] or 0,
                'max_download': speed_stats[1] or 0,
                'min_upload': speed_stats[2] or 0,
                'max_upload': speed_stats[3] or 0
            },
            'billing_types_count': billing_types_count
        }
