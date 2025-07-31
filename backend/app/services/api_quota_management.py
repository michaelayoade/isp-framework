"""
API Quota Management Service

Service layer for API key quota enforcement and usage tracking including:
- Rate limiting per API key
- Daily/monthly usage aggregation
- Quota enforcement and alerts
- Usage analytics for resellers
"""

import logging
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationError
from app.services.webhook_integration_service import WebhookTriggers

logger = logging.getLogger(__name__)


class APIQuotaManagementService:
    """Service layer for API quota management and enforcement."""

    def __init__(self, db: Session):
        self.db = db
        self.webhook_triggers = WebhookTriggers(db)
        # In-memory rate limiting cache (in production, use Redis)
        self._rate_limit_cache = defaultdict(lambda: defaultdict(list))

    def check_rate_limit(self, api_key: str, endpoint: str) -> Dict[str, Any]:
        """Check if API key is within rate limits for the endpoint."""
        try:
            # Get API key configuration
            api_key_config = self._get_api_key_config(api_key)
            if not api_key_config:
                raise NotFoundError("API key not found")

            if not api_key_config["is_active"]:
                raise ValidationError("API key is inactive")

            # Get rate limit rules for this key and endpoint
            rate_limits = self._get_rate_limit_rules(api_key_config, endpoint)

            # Check each rate limit rule
            for rule in rate_limits:
                if not self._check_individual_rate_limit(api_key, endpoint, rule):
                    return {
                        "allowed": False,
                        "reason": "rate_limit_exceeded",
                        "rule": rule,
                        "retry_after_seconds": rule["window_seconds"],
                    }

            # Record the API call
            self._record_api_call(api_key, endpoint)

            return {
                "allowed": True,
                "remaining_calls": self._get_remaining_calls(
                    api_key, endpoint, rate_limits
                ),
                "reset_time": self._get_next_reset_time(rate_limits),
            }

        except Exception as e:
            logger.error(f"Error checking rate limit for API key {api_key}: {e}")
            raise

    def check_quota_limits(self, api_key: str) -> Dict[str, Any]:
        """Check if API key is within daily/monthly quota limits."""
        try:
            # Get API key configuration
            api_key_config = self._get_api_key_config(api_key)
            if not api_key_config:
                raise NotFoundError("API key not found")

            # Get current usage
            daily_usage = self._get_daily_usage(api_key)
            monthly_usage = self._get_monthly_usage(api_key)

            # Check daily quota
            if (
                api_key_config["daily_quota"]
                and daily_usage >= api_key_config["daily_quota"]
            ):
                return {
                    "within_quota": False,
                    "quota_type": "daily",
                    "usage": daily_usage,
                    "limit": api_key_config["daily_quota"],
                    "reset_time": self._get_daily_reset_time(),
                }

            # Check monthly quota
            if (
                api_key_config["monthly_quota"]
                and monthly_usage >= api_key_config["monthly_quota"]
            ):
                return {
                    "within_quota": False,
                    "quota_type": "monthly",
                    "usage": monthly_usage,
                    "limit": api_key_config["monthly_quota"],
                    "reset_time": self._get_monthly_reset_time(),
                }

            return {
                "within_quota": True,
                "daily_usage": daily_usage,
                "daily_limit": api_key_config["daily_quota"],
                "monthly_usage": monthly_usage,
                "monthly_limit": api_key_config["monthly_quota"],
            }

        except Exception as e:
            logger.error(f"Error checking quota limits for API key {api_key}: {e}")
            raise

    def aggregate_daily_usage(self, date: Optional[datetime] = None) -> Dict[str, Any]:
        """Aggregate API usage for a specific date."""
        if not date:
            date = datetime.now(timezone.utc).date()

        try:
            # Get all API calls for the date
            api_calls = self._get_api_calls_for_date(date)

            # Aggregate by API key
            usage_by_key = defaultdict(
                lambda: {
                    "total_calls": 0,
                    "successful_calls": 0,
                    "failed_calls": 0,
                    "endpoints": defaultdict(int),
                    "reseller_id": None,
                }
            )

            for call in api_calls:
                key_stats = usage_by_key[call["api_key"]]
                key_stats["total_calls"] += 1
                key_stats["reseller_id"] = call.get("reseller_id")

                if call["status_code"] < 400:
                    key_stats["successful_calls"] += 1
                else:
                    key_stats["failed_calls"] += 1

                key_stats["endpoints"][call["endpoint"]] += 1

            # Store aggregated data
            aggregation_results = []
            for api_key, stats in usage_by_key.items():
                aggregation_record = self._store_daily_aggregation(api_key, date, stats)
                aggregation_results.append(aggregation_record)

            logger.info(
                f"Aggregated daily usage for {date}: {len(aggregation_results)} API keys processed"
            )

            return {
                "date": date.isoformat(),
                "api_keys_processed": len(aggregation_results),
                "total_calls": sum(
                    stats["total_calls"] for stats in usage_by_key.values()
                ),
                "aggregation_results": aggregation_results,
            }

        except Exception as e:
            logger.error(f"Error aggregating daily usage for {date}: {e}")
            raise

    def get_usage_analytics(
        self, api_key: str, period_days: int = 30
    ) -> Dict[str, Any]:
        """Get usage analytics for an API key."""
        try:
            # Get API key configuration
            api_key_config = self._get_api_key_config(api_key)
            if not api_key_config:
                raise NotFoundError("API key not found")

            period_start = datetime.now(timezone.utc) - timedelta(days=period_days)

            # Get usage data for the period
            usage_data = self._get_usage_data(api_key, period_start)

            # Calculate analytics
            analytics = self._calculate_usage_analytics(usage_data, period_days)

            return {
                "api_key": api_key,
                "reseller_id": api_key_config["reseller_id"],
                "period_start": period_start.isoformat(),
                "period_end": datetime.now(timezone.utc).isoformat(),
                "period_days": period_days,
                "analytics": analytics,
            }

        except Exception as e:
            logger.error(f"Error getting usage analytics for API key {api_key}: {e}")
            raise

    def rotate_api_key(self, api_key: str) -> Dict[str, Any]:
        """Rotate an API key (generate new key, deactivate old)."""
        try:
            # Get existing API key configuration
            api_key_config = self._get_api_key_config(api_key)
            if not api_key_config:
                raise NotFoundError("API key not found")

            # Generate new API key
            new_api_key = self._generate_new_api_key()

            # Create new API key record with same configuration
            new_key_config = {
                **api_key_config,
                "key": new_api_key,
                "created_at": datetime.now(timezone.utc),
                "rotated_from": api_key,
            }

            # Store new key
            self._store_api_key_config(new_key_config)

            # Deactivate old key (with grace period)
            self._deactivate_api_key(api_key, grace_period_hours=24)

            # Trigger webhook for key rotation
            self.webhook_triggers.api_key_rotated(
                {
                    "old_api_key": api_key[:8] + "...",  # Masked for security
                    "new_api_key": new_api_key[:8] + "...",  # Masked for security
                    "reseller_id": api_key_config["reseller_id"],
                    "rotated_at": datetime.now(timezone.utc).isoformat(),
                    "grace_period_hours": 24,
                }
            )

            logger.info(f"Rotated API key for reseller {api_key_config['reseller_id']}")

            return {
                "new_api_key": new_api_key,
                "old_api_key_expires_at": (
                    datetime.now(timezone.utc) + timedelta(hours=24)
                ).isoformat(),
                "rotation_time": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            logger.error(f"Error rotating API key {api_key}: {e}")
            raise

    def _get_api_key_config(self, api_key: str) -> Optional[Dict[str, Any]]:
        """Get API key configuration from database."""
        # Placeholder - implement when API key repository is available
        # This would query the api_management_keys table
        return {
            "key": api_key,
            "reseller_id": 1,
            "is_active": True,
            "daily_quota": 10000,
            "monthly_quota": 300000,
            "rate_limits": [
                {"requests": 100, "window_seconds": 60},  # 100 requests per minute
                {"requests": 1000, "window_seconds": 3600},  # 1000 requests per hour
            ],
        }

    def _get_rate_limit_rules(
        self, api_key_config: Dict[str, Any], endpoint: str
    ) -> List[Dict[str, Any]]:
        """Get rate limit rules for an API key and endpoint."""
        # Default rate limits from API key config
        rate_limits = api_key_config.get("rate_limits", [])

        # Endpoint-specific rate limits could be added here
        # endpoint_limits = self._get_endpoint_specific_limits(endpoint)
        # rate_limits.extend(endpoint_limits)

        return rate_limits

    def _check_individual_rate_limit(
        self, api_key: str, endpoint: str, rule: Dict[str, Any]
    ) -> bool:
        """Check if a specific rate limit rule is satisfied."""
        window_seconds = rule["window_seconds"]
        max_requests = rule["requests"]

        # Get current time window
        now = datetime.now(timezone.utc)
        window_start = now - timedelta(seconds=window_seconds)

        # Get calls in the current window from cache
        cache_key = f"{api_key}:{endpoint}:{window_seconds}"
        call_times = self._rate_limit_cache[cache_key]["calls"]

        # Remove old calls outside the window
        call_times[:] = [
            call_time for call_time in call_times if call_time > window_start
        ]

        # Check if within limit
        return len(call_times) < max_requests

    def _record_api_call(self, api_key: str, endpoint: str):
        """Record an API call for rate limiting and usage tracking."""
        now = datetime.now(timezone.utc)

        # Record in rate limiting cache for all applicable windows
        api_key_config = self._get_api_key_config(api_key)
        rate_limits = self._get_rate_limit_rules(api_key_config, endpoint)

        for rule in rate_limits:
            window_seconds = rule["window_seconds"]
            cache_key = f"{api_key}:{endpoint}:{window_seconds}"
            self._rate_limit_cache[cache_key]["calls"].append(now)

        # Record in database for usage tracking
        # self._store_api_call_record(api_key, endpoint, now)

    def _get_remaining_calls(
        self, api_key: str, endpoint: str, rate_limits: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """Get remaining calls for each rate limit window."""
        remaining = {}

        for rule in rate_limits:
            window_seconds = rule["window_seconds"]
            max_requests = rule["requests"]
            cache_key = f"{api_key}:{endpoint}:{window_seconds}"
            current_calls = len(self._rate_limit_cache[cache_key]["calls"])
            remaining[f"{window_seconds}s"] = max(0, max_requests - current_calls)

        return remaining

    def _get_next_reset_time(self, rate_limits: List[Dict[str, Any]]) -> str:
        """Get the next reset time for rate limits."""
        now = datetime.now(timezone.utc)
        next_reset = now + timedelta(
            seconds=min(rule["window_seconds"] for rule in rate_limits)
        )
        return next_reset.isoformat()

    def _get_daily_usage(self, api_key: str) -> int:
        """Get daily usage count for an API key."""
        # Placeholder - implement when usage repository is available
        return 1500  # Mock usage

    def _get_monthly_usage(self, api_key: str) -> int:
        """Get monthly usage count for an API key."""
        # Placeholder - implement when usage repository is available
        return 45000  # Mock usage

    def _get_daily_reset_time(self) -> str:
        """Get the next daily quota reset time."""
        now = datetime.now(timezone.utc)
        next_day = (now + timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        return next_day.isoformat()

    def _get_monthly_reset_time(self) -> str:
        """Get the next monthly quota reset time."""
        now = datetime.now(timezone.utc)
        if now.month == 12:
            next_month = now.replace(
                year=now.year + 1,
                month=1,
                day=1,
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
            )
        else:
            next_month = now.replace(
                month=now.month + 1, day=1, hour=0, minute=0, second=0, microsecond=0
            )
        return next_month.isoformat()

    def _get_api_calls_for_date(self, date: datetime.date) -> List[Dict[str, Any]]:
        """Get all API calls for a specific date."""
        # Placeholder - implement when API call log repository is available
        return []

    def _store_daily_aggregation(
        self, api_key: str, date: datetime.date, stats: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Store daily usage aggregation."""
        # Placeholder - implement when aggregation repository is available
        return {
            "api_key": api_key,
            "date": date.isoformat(),
            "total_calls": stats["total_calls"],
            "successful_calls": stats["successful_calls"],
            "failed_calls": stats["failed_calls"],
        }

    def _get_usage_data(
        self, api_key: str, period_start: datetime
    ) -> List[Dict[str, Any]]:
        """Get usage data for an API key over a period."""
        # Placeholder - implement when usage repository is available
        return []

    def _calculate_usage_analytics(
        self, usage_data: List[Dict[str, Any]], period_days: int
    ) -> Dict[str, Any]:
        """Calculate usage analytics from raw usage data."""
        # Placeholder - implement analytics calculations
        return {
            "total_calls": 45000,
            "average_calls_per_day": 1500,
            "success_rate": 98.5,
            "most_used_endpoints": [
                {"endpoint": "/customers", "calls": 15000},
                {"endpoint": "/services", "calls": 12000},
                {"endpoint": "/billing", "calls": 8000},
            ],
            "peak_usage_hour": 14,  # 2 PM
            "error_rate_by_endpoint": {
                "/customers": 1.2,
                "/services": 2.1,
                "/billing": 0.8,
            },
        }

    def _generate_new_api_key(self) -> str:
        """Generate a new API key."""
        import secrets

        return f"isp_{secrets.token_urlsafe(32)}"

    def _store_api_key_config(self, config: Dict[str, Any]):
        """Store API key configuration in database."""
        # Placeholder - implement when API key repository is available
        pass

    def _deactivate_api_key(self, api_key: str, grace_period_hours: int = 0):
        """Deactivate an API key with optional grace period."""
        # Placeholder - implement when API key repository is available
        pass
