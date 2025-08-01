"""
API Management Repository

Repository layer for API management including:
- API Key CRUD operations and authentication
- Usage tracking and analytics
- Rate limiting and quota management
- API versioning and endpoint documentation
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy import and_, or_, desc, asc, func, text
from sqlalchemy.orm import Session, joinedload

from app.models.api_management import (
    APIKey,
    APIUsage,
    APIRateLimit,
    APIVersion,
    APIEndpoint,
    APIQuota
)
from app.repositories.base import BaseRepository


class APIKeyRepository(BaseRepository[APIKey]):
    """Repository for API key management."""

    def __init__(self, db: Session):
        super().__init__(APIKey, db)

    def create_api_key(
        self,
        key_name: str,
        api_key: str,
        api_secret: str,
        reseller_id: Optional[int] = None,
        customer_id: Optional[int] = None,
        admin_id: Optional[int] = None,
        permissions: Optional[Dict[str, Any]] = None,
        scopes: Optional[List[str]] = None,
        rate_limit: int = 1000,
        daily_quota: int = 10000,
        monthly_quota: int = 100000
    ) -> APIKey:
        """Create a new API key."""
        api_key_record = APIKey(
            key_name=key_name,
            api_key=api_key,
            api_secret=api_secret,
            reseller_id=reseller_id,
            customer_id=customer_id,
            admin_id=admin_id,
            permissions=permissions or {},
            scopes=scopes or [],
            rate_limit=rate_limit,
            daily_quota=daily_quota,
            monthly_quota=monthly_quota,
            is_active=True
        )
        self.db.add(api_key_record)
        self.db.commit()
        self.db.refresh(api_key_record)
        return api_key_record

    def get_by_api_key(self, api_key: str) -> Optional[APIKey]:
        """Get API key record by key value."""
        return self.db.query(APIKey).filter(
            and_(
                APIKey.api_key == api_key,
                APIKey.is_active == True
            )
        ).first()

    def authenticate_api_key(self, api_key: str, api_secret: str) -> Optional[APIKey]:
        """Authenticate API key and secret."""
        return self.db.query(APIKey).filter(
            and_(
                APIKey.api_key == api_key,
                APIKey.api_secret == api_secret,
                APIKey.is_active == True
            )
        ).first()

    def list_api_keys(
        self,
        page: int = 1,
        per_page: int = 25,
        reseller_id: Optional[int] = None,
        customer_id: Optional[int] = None,
        admin_id: Optional[int] = None,
        is_active: Optional[bool] = None
    ) -> Dict[str, Any]:
        """List API keys with pagination and filtering."""
        query = self.db.query(APIKey)

        # Apply filters
        if reseller_id:
            query = query.filter(APIKey.reseller_id == reseller_id)
        if customer_id:
            query = query.filter(APIKey.customer_id == customer_id)
        if admin_id:
            query = query.filter(APIKey.admin_id == admin_id)
        if is_active is not None:
            query = query.filter(APIKey.is_active == is_active)

        # Get total count
        total = query.count()

        # Apply pagination
        offset = (page - 1) * per_page
        keys = query.order_by(desc(APIKey.created_at)).offset(offset).limit(per_page).all()

        return {
            "api_keys": keys,
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": (total + per_page - 1) // per_page
        }

    def update_last_used(self, api_key_id: int) -> Optional[APIKey]:
        """Update last used timestamp for API key."""
        key_record = self.get(api_key_id)
        if not key_record:
            return None

        key_record.last_used_at = datetime.now(timezone.utc)
        key_record.total_requests += 1
        self.db.commit()
        self.db.refresh(key_record)
        return key_record

    def deactivate_api_key(self, api_key_id: int) -> Optional[APIKey]:
        """Deactivate an API key."""
        key_record = self.get(api_key_id)
        if not key_record:
            return None

        key_record.is_active = False
        key_record.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(key_record)
        return key_record

    def update_permissions(
        self,
        api_key_id: int,
        permissions: Dict[str, Any],
        scopes: Optional[List[str]] = None
    ) -> Optional[APIKey]:
        """Update API key permissions and scopes."""
        key_record = self.get(api_key_id)
        if not key_record:
            return None

        key_record.permissions = permissions
        if scopes is not None:
            key_record.scopes = scopes
        key_record.updated_at = datetime.now(timezone.utc)
        
        self.db.commit()
        self.db.refresh(key_record)
        return key_record

    def get_keys_by_owner(
        self,
        reseller_id: Optional[int] = None,
        customer_id: Optional[int] = None,
        admin_id: Optional[int] = None
    ) -> List[APIKey]:
        """Get all API keys for a specific owner."""
        query = self.db.query(APIKey)
        
        if reseller_id:
            query = query.filter(APIKey.reseller_id == reseller_id)
        elif customer_id:
            query = query.filter(APIKey.customer_id == customer_id)
        elif admin_id:
            query = query.filter(APIKey.admin_id == admin_id)
        
        return query.order_by(desc(APIKey.created_at)).all()


class APIUsageRepository(BaseRepository[APIUsage]):
    """Repository for API usage tracking."""

    def __init__(self, db: Session):
        super().__init__(APIUsage, db)

    def log_api_request(
        self,
        api_key_id: int,
        endpoint: str,
        method: str,
        status_code: int,
        response_time: float,
        client_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
        referrer: Optional[str] = None,
        request_size: int = 0,
        response_size: int = 0,
        error_type: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> APIUsage:
        """Log an API request."""
        usage_record = APIUsage(
            api_key_id=api_key_id,
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            response_time=response_time,
            client_ip=client_ip,
            user_agent=user_agent,
            referrer=referrer,
            request_size=request_size,
            response_size=response_size,
            error_type=error_type,
            error_message=error_message
        )
        self.db.add(usage_record)
        self.db.commit()
        self.db.refresh(usage_record)
        return usage_record

    def get_usage_stats(
        self,
        api_key_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get usage statistics."""
        query = self.db.query(APIUsage)
        
        if api_key_id:
            query = query.filter(APIUsage.api_key_id == api_key_id)
        if start_date:
            query = query.filter(APIUsage.created_at >= start_date)
        if end_date:
            query = query.filter(APIUsage.created_at <= end_date)

        stats = {}

        # Total requests
        stats["total_requests"] = query.count()

        # Requests by status code
        status_counts = query.with_entities(
            APIUsage.status_code,
            func.count(APIUsage.id)
        ).group_by(APIUsage.status_code).all()
        
        stats["by_status_code"] = {str(status): count for status, count in status_counts}

        # Requests by endpoint
        endpoint_counts = query.with_entities(
            APIUsage.endpoint,
            func.count(APIUsage.id)
        ).group_by(APIUsage.endpoint).order_by(desc(func.count(APIUsage.id))).limit(10).all()
        
        stats["top_endpoints"] = [{"endpoint": endpoint, "count": count} for endpoint, count in endpoint_counts]

        # Average response time
        avg_response_time = query.with_entities(func.avg(APIUsage.response_time)).scalar()
        stats["avg_response_time"] = float(avg_response_time) if avg_response_time else 0

        # Error rate
        error_count = query.filter(APIUsage.status_code >= 400).count()
        stats["error_rate"] = (error_count / stats["total_requests"]) * 100 if stats["total_requests"] > 0 else 0

        return stats

    def get_usage_by_time_period(
        self,
        api_key_id: int,
        period: str = "day",  # day, week, month
        limit: int = 30
    ) -> List[Dict[str, Any]]:
        """Get usage grouped by time period."""
        if period == "day":
            date_format = "%Y-%m-%d"
            date_trunc = "day"
        elif period == "week":
            date_format = "%Y-%W"
            date_trunc = "week"
        elif period == "month":
            date_format = "%Y-%m"
            date_trunc = "month"
        else:
            raise ValueError("Period must be 'day', 'week', or 'month'")

        # Use database-specific date truncation
        results = self.db.query(
            func.date_trunc(date_trunc, APIUsage.created_at).label("period"),
            func.count(APIUsage.id).label("request_count"),
            func.avg(APIUsage.response_time).label("avg_response_time")
        ).filter(
            APIUsage.api_key_id == api_key_id
        ).group_by(
            func.date_trunc(date_trunc, APIUsage.created_at)
        ).order_by(
            desc(func.date_trunc(date_trunc, APIUsage.created_at))
        ).limit(limit).all()

        return [
            {
                "period": result.period.strftime(date_format),
                "request_count": result.request_count,
                "avg_response_time": float(result.avg_response_time) if result.avg_response_time else 0
            }
            for result in results
        ]


class APIRateLimitRepository(BaseRepository[APIRateLimit]):
    """Repository for API rate limit tracking."""

    def __init__(self, db: Session):
        super().__init__(APIRateLimit, db)

    def get_current_window(self, api_key_id: int, window_size_minutes: int = 60) -> Optional[APIRateLimit]:
        """Get current rate limit window for API key."""
        now = datetime.now(timezone.utc)
        window_start = now.replace(minute=0, second=0, microsecond=0)
        window_end = window_start + timedelta(minutes=window_size_minutes)

        return self.db.query(APIRateLimit).filter(
            and_(
                APIRateLimit.api_key_id == api_key_id,
                APIRateLimit.window_start <= now,
                APIRateLimit.window_end > now
            )
        ).first()

    def increment_request_count(self, api_key_id: int, window_size_minutes: int = 60) -> APIRateLimit:
        """Increment request count for current window."""
        current_window = self.get_current_window(api_key_id, window_size_minutes)
        
        if not current_window:
            # Create new window
            now = datetime.now(timezone.utc)
            window_start = now.replace(minute=0, second=0, microsecond=0)
            window_end = window_start + timedelta(minutes=window_size_minutes)
            
            current_window = APIRateLimit(
                api_key_id=api_key_id,
                window_start=window_start,
                window_end=window_end,
                request_count=1
            )
            self.db.add(current_window)
        else:
            current_window.request_count += 1
            current_window.updated_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(current_window)
        return current_window

    def check_rate_limit(self, api_key_id: int, rate_limit: int, window_size_minutes: int = 60) -> bool:
        """Check if API key has exceeded rate limit."""
        current_window = self.get_current_window(api_key_id, window_size_minutes)
        
        if not current_window:
            return False  # No requests yet, not exceeded
        
        return current_window.request_count >= rate_limit

    def cleanup_old_windows(self, days_to_keep: int = 7) -> int:
        """Clean up old rate limit windows."""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_to_keep)
        
        deleted_count = self.db.query(APIRateLimit).filter(
            APIRateLimit.window_end < cutoff_date
        ).delete()
        
        self.db.commit()
        return deleted_count


class APIQuotaRepository(BaseRepository[APIQuota]):
    """Repository for API quota management."""

    def __init__(self, db: Session):
        super().__init__(APIQuota, db)

    def get_current_quota(self, api_key_id: int, quota_type: str) -> Optional[APIQuota]:
        """Get current quota for API key and type."""
        now = datetime.now(timezone.utc)
        
        return self.db.query(APIQuota).filter(
            and_(
                APIQuota.api_key_id == api_key_id,
                APIQuota.quota_type == quota_type,
                APIQuota.period_start <= now,
                APIQuota.period_end > now
            )
        ).first()

    def increment_usage(self, api_key_id: int, quota_type: str, requests: int = 1, responses: int = 1) -> APIQuota:
        """Increment quota usage."""
        current_quota = self.get_current_quota(api_key_id, quota_type)
        
        if not current_quota:
            # Create new quota period
            now = datetime.now(timezone.utc)
            
            if quota_type == "daily":
                period_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
                period_end = period_start + timedelta(days=1)
            elif quota_type == "monthly":
                period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                next_month = period_start.replace(month=period_start.month + 1) if period_start.month < 12 else period_start.replace(year=period_start.year + 1, month=1)
                period_end = next_month
            else:
                raise ValueError("Quota type must be 'daily' or 'monthly'")
            
            # Get API key to determine limits
            api_key = self.db.query(APIKey).get(api_key_id)
            if not api_key:
                raise ValueError("API key not found")
            
            request_limit = api_key.daily_quota if quota_type == "daily" else api_key.monthly_quota
            
            current_quota = APIQuota(
                api_key_id=api_key_id,
                quota_type=quota_type,
                period_start=period_start,
                period_end=period_end,
                request_limit=request_limit,
                requests_used=requests,
                responses_sent=responses
            )
            self.db.add(current_quota)
        else:
            current_quota.requests_used += requests
            current_quota.responses_sent += responses
            current_quota.updated_at = datetime.now(timezone.utc)

        # Check if quota is exceeded
        current_quota.is_exceeded = current_quota.requests_used >= current_quota.request_limit
        
        self.db.commit()
        self.db.refresh(current_quota)
        return current_quota

    def check_quota_exceeded(self, api_key_id: int, quota_type: str) -> bool:
        """Check if quota is exceeded."""
        current_quota = self.get_current_quota(api_key_id, quota_type)
        
        if not current_quota:
            return False  # No usage yet, not exceeded
        
        return current_quota.is_exceeded

    def get_quota_usage(self, api_key_id: int) -> Dict[str, Dict[str, Any]]:
        """Get quota usage for all types."""
        quotas = self.db.query(APIQuota).filter(
            APIQuota.api_key_id == api_key_id
        ).all()
        
        usage = {}
        for quota in quotas:
            now = datetime.now(timezone.utc)
            if quota.period_start <= now <= quota.period_end:
                usage[quota.quota_type] = {
                    "requests_used": quota.requests_used,
                    "request_limit": quota.request_limit,
                    "usage_percentage": (quota.requests_used / quota.request_limit) * 100 if quota.request_limit > 0 else 0,
                    "is_exceeded": quota.is_exceeded,
                    "period_start": quota.period_start,
                    "period_end": quota.period_end
                }
        
        return usage
