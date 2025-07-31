"""
API Management Repository Layer

Comprehensive repository layer for API management data access
with advanced querying and filtering capabilities
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc

from app.models.api_management import APIKey, APIUsage, APIRateLimit, APIVersion, APIEndpoint, APIQuota
from app.repositories.base import BaseRepository
import logging

logger = logging.getLogger(__name__)


class APIKeyRepository(BaseRepository[APIKey]):
    """Repository for API key management"""
    
    def __init__(self, db: Session):
        super().__init__(APIKey, db)
    
    def get_by_key(self, api_key: str) -> Optional[APIKey]:
        """Get API key by key value"""
        return self.db.query(APIKey).filter(APIKey.api_key == api_key).first()
    
    def get_by_secret_hash(self, secret_hash: str) -> Optional[APIKey]:
        """Get API key by secret hash"""
        return self.db.query(APIKey).filter(APIKey.api_secret == secret_hash).first()
    
    def list_active_keys(
        self,
        partner_id: Optional[int] = None,
        customer_id: Optional[int] = None,
        admin_id: Optional[int] = None,
        search: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[APIKey]:
        """List active API keys with filtering"""
        query = self.db.query(APIKey).filter(APIKey.is_active is True)
        
        if partner_id:
            query = query.filter(APIKey.partner_id == partner_id)
        if customer_id:
            query = query.filter(APIKey.customer_id == customer_id)
        if admin_id:
            query = query.filter(APIKey.admin_id == admin_id)
        if search:
            query = query.filter(
                or_(
                    APIKey.key_name.ilike(f"%{search}%"),
                    APIKey.description.ilike(f"%{search}%"),
                    APIKey.api_key.ilike(f"%{search}%")
                )
            )
        
        return query.order_by(desc(APIKey.created_at)).offset(offset).limit(limit).all()
    
    def list_expired_keys(self) -> List[APIKey]:
        """Get all expired API keys"""
        now = datetime.now(timezone.utc)
        return self.db.query(APIKey).filter(
            and_(
                APIKey.is_active is True,
                APIKey.expires_at < now
            )
        ).all()
    
    def get_usage_statistics(self, key_id: int) -> Dict[str, Any]:
        """Get usage statistics for an API key"""
        key = self.get_by_id(key_id)
        if not key:
            return {}
        
        # Total usage count
        total_usage = self.db.query(APIUsage).filter(
            APIUsage.api_key_id == key_id
        ).count()
        
        # Usage in last 24 hours
        last_24h = datetime.now(timezone.utc) - timedelta(hours=24)
        usage_24h = self.db.query(APIUsage).filter(
            and_(
                APIUsage.api_key_id == key_id,
                APIUsage.created_at >= last_24h
            )
        ).count()
        
        # Usage in last 30 days
        last_30d = datetime.now(timezone.utc) - timedelta(days=30)
        usage_30d = self.db.query(APIUsage).filter(
            and_(
                APIUsage.api_key_id == key_id,
                APIUsage.created_at >= last_30d
            )
        ).count()
        
        # Last used timestamp
        last_used = self.db.query(APIUsage).filter(
            APIUsage.api_key_id == key_id
        ).order_by(desc(APIUsage.created_at)).first()
        
        return {
            "total_usage": total_usage,
            "usage_24h": usage_24h,
            "usage_30d": usage_30d,
            "last_used": last_used.created_at if last_used else None,
            "key_name": key.key_name,
            "is_active": key.is_active
        }


class APIUsageRepository(BaseRepository[APIUsage]):
    """Repository for API usage tracking"""
    
    def __init__(self, db: Session):
        super().__init__(APIUsage, db)
    
    def log_usage(
        self,
        api_key_id: int,
        endpoint: str,
        method: str,
        status_code: int,
        response_time: float,
        client_ip: str = None,
        user_agent: str = None,
        error_type: str = None,
        request_size: int = 0,
        response_size: int = 0
    ) -> APIUsage:
        """Log API usage with comprehensive details"""
        usage = APIUsage(
            api_key_id=api_key_id,
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            response_time=response_time,
            client_ip=client_ip,
            user_agent=user_agent,
            error_type=error_type,
            request_size=request_size,
            response_size=response_size
        )
        
        self.db.add(usage)
        self.db.commit()
        self.db.refresh(usage)
        
        return usage
    
    def get_usage_analytics(
        self,
        api_key_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        endpoint: Optional[str] = None,
        method: Optional[str] = None,
        status_code: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get comprehensive usage analytics"""
        query = self.db.query(APIUsage)
        
        if api_key_id:
            query = query.filter(APIUsage.api_key_id == api_key_id)
        if start_date:
            query = query.filter(APIUsage.created_at >= start_date)
        if end_date:
            query = query.filter(APIUsage.created_at <= end_date)
        if endpoint:
            query = query.filter(APIUsage.endpoint == endpoint)
        if method:
            query = query.filter(APIUsage.method == method)
        if status_code:
            query = query.filter(APIUsage.status_code == status_code)
        
        # Basic metrics
        total_requests = query.count()
        successful_requests = query.filter(APIUsage.status_code < 400).count()
        failed_requests = query.filter(APIUsage.status_code >= 400).count()
        
        # Performance metrics
        avg_response_time = query.with_entities(
            func.avg(APIUsage.response_time)
        ).scalar() or 0
        
        min_response_time = query.with_entities(
            func.min(APIUsage.response_time)
        ).scalar() or 0
        
        max_response_time = query.with_entities(
            func.max(APIUsage.response_time)
        ).scalar() or 0
        
        # Error analysis
        error_types = query.with_entities(
            APIUsage.error_type,
            func.count().label('count')
        ).filter(APIUsage.error_type.isnot(None)).group_by(APIUsage.error_type).all()
        
        # Status code distribution
        status_codes = query.with_entities(
            APIUsage.status_code,
            func.count().label('count')
        ).group_by(APIUsage.status_code).all()
        
        # Endpoint usage
        endpoints = query.with_entities(
            APIUsage.endpoint,
            func.count().label('count')
        ).group_by(APIUsage.endpoint).all()
        
        # Method usage
        methods = query.with_entities(
            APIUsage.method,
            func.count().label('count')
        ).group_by(APIUsage.method).all()
        
        # Time-based analysis
        hourly_usage = query.with_entities(
            func.date_trunc('hour', APIUsage.created_at).label('hour'),
            func.count().label('count')
        ).group_by('hour').all()
        
        daily_usage = query.with_entities(
            func.date_trunc('day', APIUsage.created_at).label('day'),
            func.count().label('count')
        ).group_by('day').all()
        
        return {
            "total_requests": total_requests,
            "successful_requests": successful_requests,
            "failed_requests": failed_requests,
            "avg_response_time": avg_response_time,
            "min_response_time": min_response_time,
            "max_response_time": max_response_time,
            "error_types": dict(error_types),
            "status_codes": dict(status_codes),
            "endpoints": dict(endpoints),
            "methods": dict(methods),
            "hourly_usage": {str(h): c for h, c in hourly_usage},
            "daily_usage": {str(d): c for d, c in daily_usage}
        }
    
    def get_top_endpoints(
        self,
        limit: int = 10,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get top endpoints by usage"""
        query = self.db.query(APIUsage)
        
        if start_date:
            query = query.filter(APIUsage.created_at >= start_date)
        if end_date:
            query = query.filter(APIUsage.created_at <= end_date)
        
        return query.with_entities(
            APIUsage.endpoint,
            APIUsage.method,
            func.count().label('request_count'),
            func.avg(APIUsage.response_time).label('avg_response_time')
        ).group_by(APIUsage.endpoint, APIUsage.method).order_by(
            desc('request_count')
        ).limit(limit).all()


class APIRateLimitRepository(BaseRepository[APIRateLimit]):
    """Repository for API rate limit tracking"""
    
    def __init__(self, db: Session):
        super().__init__(APIRateLimit, db)
    
    def get_current_window(self, api_key_id: int) -> Optional[APIRateLimit]:
        """Get current rate limit window for API key"""
        now = datetime.now(timezone.utc)
        window_start = now.replace(minute=0, second=0, microsecond=0)
        window_end = window_start + timedelta(hours=1)
        
        return self.db.query(APIRateLimit).filter(
            and_(
                APIRateLimit.api_key_id == api_key_id,
                APIRateLimit.window_start == window_start,
                APIRateLimit.window_end == window_end
            )
        ).first()
    
    def increment_or_create(self, api_key_id: int) -> APIRateLimit:
        """Increment rate limit counter or create new window"""
        now = datetime.now(timezone.utc)
        window_start = now.replace(minute=0, second=0, microsecond=0)
        window_end = window_start + timedelta(hours=1)
        
        rate_limit = self.get_current_window(api_key_id)
        
        if rate_limit:
            rate_limit.request_count += 1
            rate_limit.updated_at = now
        else:
            rate_limit = APIRateLimit(
                api_key_id=api_key_id,
                window_start=window_start,
                window_end=window_end,
                request_count=1
            )
            self.db.add(rate_limit)
        
        self.db.commit()
        self.db.refresh(rate_limit)
        return rate_limit
    
    def cleanup_old_windows(self, days_to_keep: int = 7) -> int:
        """Clean up old rate limit windows"""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_to_keep)
        
        deleted_count = self.db.query(APIRateLimit).filter(
            APIRateLimit.window_end < cutoff_date
        ).delete()
        
        self.db.commit()
        return deleted_count


class APIVersionRepository(BaseRepository[APIVersion]):
    """Repository for API version management"""
    
    def __init__(self, db: Session):
        super().__init__(APIVersion, db)
    
    def get_default_version(self) -> Optional[APIVersion]:
        """Get the default API version"""
        return self.db.query(APIVersion).filter(APIVersion.is_default is True).first()
    
    def get_by_version(self, version: str) -> Optional[APIVersion]:
        """Get API version by version string"""
        return self.db.query(APIVersion).filter(APIVersion.version == version).first()
    
    def list_active_versions(self) -> List[APIVersion]:
        """List all active API versions"""
        return self.db.query(APIVersion).filter(
            APIVersion.status == "active"
        ).order_by(APIVersion.version).all()
    
    def set_default_version(self, version_id: int) -> APIVersion:
        """Set a version as default and unset others"""
        # Unset all other versions
        self.db.query(APIVersion).update({"is_default": False})
        
        # Set the specified version as default
        version = self.get_by_id(version_id)
        if version:
            version.is_default = True
            self.db.commit()
            self.db.refresh(version)
        
        return version


class APIEndpointRepository(BaseRepository[APIEndpoint]):
    """Repository for API endpoint management"""
    
    def __init__(self, db: Session):
        super().__init__(APIEndpoint, db)
    
    def get_by_path_and_method(self, api_version_id: int, path: str, method: str) -> Optional[APIEndpoint]:
        """Get endpoint by path and method"""
        return self.db.query(APIEndpoint).filter(
            and_(
                APIEndpoint.api_version_id == api_version_id,
                APIEndpoint.path == path,
                APIEndpoint.method == method
            )
        ).first()
    
    def list_by_version(self, api_version_id: int) -> List[APIEndpoint]:
        """List all endpoints for an API version"""
        return self.db.query(APIEndpoint).filter(
            APIEndpoint.api_version_id == api_version_id
        ).order_by(APIEndpoint.path, APIEndpoint.method).all()
    
    def search_endpoints(
        self,
        api_version_id: int,
        search: Optional[str] = None,
        method: Optional[str] = None,
        category: Optional[str] = None
    ) -> List[APIEndpoint]:
        """Search endpoints with filtering"""
        query = self.db.query(APIEndpoint).filter(
            APIEndpoint.api_version_id == api_version_id
        )
        
        if search:
            query = query.filter(
                or_(
                    APIEndpoint.path.ilike(f"%{search}%"),
                    APIEndpoint.description.ilike(f"%{search}%"),
                    APIEndpoint.summary.ilike(f"%{search}%")
                )
            )
        
        if method:
            query = query.filter(APIEndpoint.method == method)
        
        if category:
            query = query.filter(APIEndpoint.category == category)
        
        return query.order_by(APIEndpoint.path, APIEndpoint.method).all()


class APIQuotaRepository(BaseRepository[APIQuota]):
    """Repository for API quota management"""
    
    def __init__(self, db: Session):
        super().__init__(APIQuota, db)
    
    def get_current_usage(self, api_key_id: int, quota_type: str) -> Dict[str, Any]:
        """Get current quota usage for API key"""
        now = datetime.now(timezone.utc)
        
        if quota_type == "daily":
            period_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            period_end = period_start + timedelta(days=1)
        elif quota_type == "monthly":
            period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if now.month == 12:
                period_end = now.replace(year=now.year + 1, month=1, day=1)
            else:
                period_end = now.replace(month=now.month + 1, day=1)
        else:
            return {}
        
        usage_count = self.db.query(APIUsage).filter(
            and_(
                APIUsage.api_key_id == api_key_id,
                APIUsage.created_at >= period_start,
                APIUsage.created_at < period_end
            )
        ).count()
        
        return {
            "period_start": period_start,
            "period_end": period_end,
            "usage_count": usage_count,
            "quota_type": quota_type
        }
