"""
API Management Service Layer

Comprehensive service layer for API management including:
- API key generation and management
- Rate limiting and quota enforcement
- Usage analytics and monitoring
- API documentation management
- Access control and security
"""

import hashlib
import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from sqlalchemy import and_, desc, func, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import (
    NotFoundError,
    QuotaExceededError,
    RateLimitError,
    ValidationError,
)
from app.models.api_management import (
    APIEndpoint,
    APIKey,
    APIRateLimit,
    APIUsage,
    APIVersion,
)
from app.schemas.api_management import (
    APIEndpointCreate,
    APIKeyCreate,
    APIKeyUpdate,
    APIUsageAnalytics,
    APIUsageCreate,
    APIVersionCreate,
)

logger = logging.getLogger(__name__)


class APIManagementService:
    """Service for comprehensive API management"""

    def __init__(self, db: Session):
        self.db = db

    def generate_api_key(self) -> tuple[str, str]:
        """Generate a secure API key and secret"""
        key = secrets.token_urlsafe(32)
        secret = secrets.token_urlsafe(32)
        return key, secret

    def hash_secret(self, secret: str) -> str:
        """Hash API secret for secure storage"""
        return hashlib.sha256(secret.encode()).hexdigest()

    def create_api_key(self, key_data: APIKeyCreate) -> APIKey:
        """Create a new API key with proper security"""
        try:
            # Generate key and secret
            api_key, api_secret = self.generate_api_key()

            # Create API key
            db_key = APIKey(
                key_name=key_data.key_name,
                api_key=api_key,
                api_secret=self.hash_secret(api_secret),
                partner_id=key_data.partner_id,
                customer_id=key_data.customer_id,
                admin_id=key_data.admin_id,
                permissions=key_data.permissions,
                scopes=key_data.scopes,
                rate_limit=key_data.rate_limit,
                daily_quota=key_data.daily_quota,
                monthly_quota=key_data.monthly_quota,
                expires_at=key_data.expires_at,
                ip_whitelist=key_data.ip_whitelist,
                referrer_whitelist=key_data.referrer_whitelist,
                user_agent_whitelist=key_data.user_agent_whitelist,
                description=key_data.description,
            )

            self.db.add(db_key)
            self.db.commit()
            self.db.refresh(db_key)

            # Add the unhashed secret for initial response
            db_key.api_secret = api_secret

            logger.info(f"Created API key: {key_data.key_name} (ID: {db_key.id})")
            return db_key

        except IntegrityError as e:
            self.db.rollback()
            raise ValidationError(f"API key creation failed: {str(e)}")

    def get_api_key(self, key_id: int) -> APIKey:
        """Get API key by ID"""
        key = self.db.query(APIKey).filter(APIKey.id == key_id).first()
        if not key:
            raise NotFoundError(f"API key with ID {key_id} not found")
        return key

    def get_api_key_by_key(self, api_key: str) -> Optional[APIKey]:
        """Get API key by key value"""
        return self.db.query(APIKey).filter(APIKey.api_key == api_key).first()

    def list_api_keys(
        self,
        partner_id: Optional[int] = None,
        customer_id: Optional[int] = None,
        admin_id: Optional[int] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[APIKey]:
        """List API keys with filtering"""
        query = self.db.query(APIKey)

        if partner_id:
            query = query.filter(APIKey.partner_id == partner_id)
        if customer_id:
            query = query.filter(APIKey.customer_id == customer_id)
        if admin_id:
            query = query.filter(APIKey.admin_id == admin_id)
        if is_active is not None:
            query = query.filter(APIKey.is_active == is_active)
        if search:
            query = query.filter(
                or_(
                    APIKey.key_name.ilike(f"%{search}%"),
                    APIKey.description.ilike(f"%{search}%"),
                )
            )

        return query.order_by(desc(APIKey.created_at)).offset(offset).limit(limit).all()

    def update_api_key(self, key_id: int, key_data: APIKeyUpdate) -> APIKey:
        """Update API key configuration"""
        key = self.get_api_key(key_id)

        update_data = key_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(key, field, value)

        key.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(key)

        logger.info(f"Updated API key: {key.key_name} (ID: {key_id})")
        return key

    def revoke_api_key(self, key_id: int) -> APIKey:
        """Revoke an API key"""
        key = self.get_api_key(key_id)
        key.is_active = False
        key.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(key)

        logger.info(f"Revoked API key: {key.key_name} (ID: {key_id})")
        return key

    def validate_api_key(
        self, api_key: str, client_ip: str = None, user_agent: str = None
    ) -> APIKey:
        """Validate API key and check access restrictions"""
        key = self.get_api_key_by_key(api_key)
        if not key:
            raise NotFoundError("Invalid API key")

        if not key.is_active:
            raise ValidationError("API key is inactive")

        if key.expires_at and key.expires_at < datetime.now(timezone.utc):
            key.is_active = False
            self.db.commit()
            raise ValidationError("API key has expired")

        # Check IP whitelist
        if key.ip_whitelist and client_ip not in key.ip_whitelist:
            raise ValidationError(f"IP address {client_ip} not allowed")

        # Check user agent whitelist
        if key.user_agent_whitelist and user_agent not in key.user_agent_whitelist:
            raise ValidationError("User agent not allowed")

        return key

    def check_rate_limit(self, api_key_id: int, endpoint: str = None) -> bool:
        """Check if API key is within rate limits"""
        key = self.get_api_key(api_key_id)

        # Get current time window (1 hour)
        now = datetime.now(timezone.utc)
        window_start = now.replace(minute=0, second=0, microsecond=0)
        window_end = window_start + timedelta(hours=1)

        # Check existing rate limit record
        rate_limit = (
            self.db.query(APIRateLimit)
            .filter(
                and_(
                    APIRateLimit.api_key_id == api_key_id,
                    APIRateLimit.window_start == window_start,
                    APIRateLimit.window_end == window_end,
                )
            )
            .first()
        )

        if not rate_limit:
            # Create new rate limit record
            rate_limit = APIRateLimit(
                api_key_id=api_key_id,
                window_start=window_start,
                window_end=window_end,
                request_count=0,
            )
            self.db.add(rate_limit)
            self.db.commit()

        if rate_limit.request_count >= key.rate_limit:
            raise RateLimitError(
                f"Rate limit exceeded. Limit: {key.rate_limit} requests per hour"
            )

        return True

    def increment_rate_limit(self, api_key_id: int) -> None:
        """Increment rate limit counter"""
        now = datetime.now(timezone.utc)
        window_start = now.replace(minute=0, second=0, microsecond=0)
        window_end = window_start + timedelta(hours=1)

        rate_limit = (
            self.db.query(APIRateLimit)
            .filter(
                and_(
                    APIRateLimit.api_key_id == api_key_id,
                    APIRateLimit.window_start == window_start,
                    APIRateLimit.window_end == window_end,
                )
            )
            .first()
        )

        if rate_limit:
            rate_limit.request_count += 1
            rate_limit.updated_at = now
            self.db.commit()

    def check_quota(self, api_key_id: int, quota_type: str = "daily") -> bool:
        """Check if API key is within quota limits"""
        key = self.get_api_key(api_key_id)
        now = datetime.now(timezone.utc)

        if quota_type == "daily":
            period_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            period_end = period_start + timedelta(days=1)
            limit = key.daily_quota
        elif quota_type == "monthly":
            period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if now.month == 12:
                period_end = now.replace(year=now.year + 1, month=1, day=1)
            else:
                period_end = now.replace(month=now.month + 1, day=1)
            limit = key.monthly_quota
        else:
            raise ValidationError(f"Invalid quota type: {quota_type}")

        # Get current usage
        usage_count = (
            self.db.query(APIUsage)
            .filter(
                and_(
                    APIUsage.api_key_id == api_key_id,
                    APIUsage.created_at >= period_start,
                    APIUsage.created_at < period_end,
                )
            )
            .count()
        )

        if usage_count >= limit:
            raise QuotaExceededError(
                f"{quota_type.capitalize()} quota exceeded. Limit: {limit} requests"
            )

        return True

    def log_api_usage(self, usage_data: APIUsageCreate) -> APIUsage:
        """Log API usage for analytics"""
        usage = APIUsage(**usage_data.dict())
        self.db.add(usage)

        # Update API key usage count and last used
        key = self.get_api_key(usage_data.api_key_id)
        key.usage_count += 1
        key.last_used = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(usage)

        return usage

    def get_usage_analytics(
        self,
        api_key_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        endpoint: Optional[str] = None,
    ) -> APIUsageAnalytics:
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

        # Basic metrics
        total_requests = query.count()
        successful_requests = query.filter(APIUsage.status_code < 400).count()
        failed_requests = query.filter(APIUsage.status_code >= 400).count()

        # Average response time
        avg_response_time = (
            query.with_entities(func.avg(APIUsage.response_time)).scalar() or 0
        )

        # Unique endpoints and users
        unique_endpoints = (
            query.with_entities(func.count(func.distinct(APIUsage.endpoint))).scalar()
            or 0
        )
        unique_users = (
            query.with_entities(func.count(func.distinct(APIUsage.api_key_id))).scalar()
            or 0
        )

        # Time-based breakdowns
        requests_by_hour = {}
        requests_by_day = {}
        requests_by_endpoint = {}

        # Get hourly breakdown
        hourly_data = (
            query.with_entities(
                func.date_trunc("hour", APIUsage.created_at).label("hour"),
                func.count().label("count"),
            )
            .group_by("hour")
            .all()
        )

        for hour, count in hourly_data:
            requests_by_hour[hour.isoformat()] = count

        # Get daily breakdown
        daily_data = (
            query.with_entities(
                func.date_trunc("day", APIUsage.created_at).label("day"),
                func.count().label("count"),
            )
            .group_by("day")
            .all()
        )

        for day, count in daily_data:
            requests_by_day[day.isoformat()] = count

        # Get endpoint breakdown
        endpoint_data = (
            query.with_entities(APIUsage.endpoint, func.count().label("count"))
            .group_by(APIUsage.endpoint)
            .all()
        )

        for endpoint_path, count in endpoint_data:
            requests_by_endpoint[endpoint_path] = count

        # Error analysis
        error_breakdown = {}
        status_code_distribution = {}

        error_data = (
            query.with_entities(APIUsage.error_type, func.count().label("count"))
            .filter(APIUsage.error_type.isnot(None))
            .group_by(APIUsage.error_type)
            .all()
        )

        for error_type, count in error_data:
            error_breakdown[error_type] = count

        status_data = (
            query.with_entities(APIUsage.status_code, func.count().label("count"))
            .group_by(APIUsage.status_code)
            .all()
        )

        for status_code, count in status_data:
            status_code_distribution[status_code] = count

        # Performance percentiles
        response_times = query.with_entities(APIUsage.response_time).all()
        response_times = [rt[0] for rt in response_times]

        response_time_percentiles = {}
        if response_times:
            response_times.sort()
            n = len(response_times)
            response_time_percentiles = {
                "p50": response_times[int(n * 0.5)],
                "p95": response_times[int(n * 0.95)],
                "p99": response_times[int(n * 0.99)],
            }

        return APIUsageAnalytics(
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            average_response_time=avg_response_time,
            unique_endpoints=unique_endpoints,
            unique_users=unique_users,
            requests_by_hour=requests_by_hour,
            requests_by_day=requests_by_day,
            requests_by_endpoint=requests_by_endpoint,
            error_breakdown=error_breakdown,
            status_code_distribution=status_code_distribution,
            response_time_percentiles=response_time_percentiles,
        )

    def create_api_version(self, version_data: APIVersionCreate) -> APIVersion:
        """Create a new API version"""
        # Ensure only one default version
        if version_data.is_default:
            self.db.query(APIVersion).update({"is_default": False})

        version = APIVersion(**version_data.dict())
        self.db.add(version)
        self.db.commit()
        self.db.refresh(version)

        logger.info(f"Created API version: {version_data.version}")
        return version

    def get_api_version(self, version_id: int) -> APIVersion:
        """Get API version by ID"""
        version = self.db.query(APIVersion).filter(APIVersion.id == version_id).first()
        if not version:
            raise NotFoundError(f"API version with ID {version_id} not found")
        return version

    def list_api_versions(self, status: Optional[str] = None) -> List[APIVersion]:
        """List API versions"""
        query = self.db.query(APIVersion)
        if status:
            query = query.filter(APIVersion.status == status)
        return query.order_by(APIVersion.version).all()

    def create_api_endpoint(self, endpoint_data: APIEndpointCreate) -> APIEndpoint:
        """Create a new API endpoint"""
        endpoint = APIEndpoint(**endpoint_data.dict())
        self.db.add(endpoint)
        self.db.commit()
        self.db.refresh(endpoint)

        logger.info(
            f"Created API endpoint: {endpoint_data.method} {endpoint_data.path}"
        )
        return endpoint

    def get_api_endpoints(self, api_version_id: int) -> List[APIEndpoint]:
        """Get all endpoints for an API version"""
        return (
            self.db.query(APIEndpoint)
            .filter(APIEndpoint.api_version_id == api_version_id)
            .order_by(APIEndpoint.path, APIEndpoint.method)
            .all()
        )

    def cleanup_old_usage_data(self, days_to_keep: int = 90) -> int:
        """Clean up old usage data"""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_to_keep)

        deleted_count = (
            self.db.query(APIUsage).filter(APIUsage.created_at < cutoff_date).delete()
        )

        # Clean up old rate limit records
        self.db.query(APIRateLimit).filter(
            APIRateLimit.window_end < cutoff_date
        ).delete()

        self.db.commit()
        logger.info(f"Cleaned up {deleted_count} old usage records")
        return deleted_count
