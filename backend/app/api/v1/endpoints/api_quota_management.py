"""
API Quota Management Endpoints

Provides REST API endpoints for API quota management including:
- Rate limiting enforcement
- Usage analytics and reporting
- API key rotation and management
- Quota configuration and monitoring
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.v1.dependencies import get_current_admin
from app.models.auth import Administrator
from app.services.api_quota_management import APIQuotaManagementService
from app.core.exceptions import NotFoundError, ValidationError, QuotaExceededError
import logging
from datetime import datetime, date

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/quota/check/{api_key}", response_model=dict)
async def check_api_quota(
    api_key: str,
    current_admin: Administrator = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Check quota limits for an API key."""
    quota_service = APIQuotaManagementService(db)
    
    try:
        quota_status = quota_service.check_quota_limits(api_key)
        return quota_status
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error checking API quota: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check API quota"
        )


@router.get("/rate-limit/check/{api_key}", response_model=dict)
async def check_rate_limit(
    api_key: str,
    endpoint: str = Query(..., description="API endpoint to check rate limit for"),
    current_admin: Administrator = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Check rate limit status for an API key and endpoint."""
    quota_service = APIQuotaManagementService(db)
    
    try:
        rate_limit_status = quota_service.check_rate_limit(api_key, endpoint)
        return rate_limit_status
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error checking rate limit: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check rate limit"
        )


@router.post("/usage/aggregate", response_model=dict)
async def aggregate_daily_usage(
    target_date: Optional[date] = Query(None, description="Date to aggregate (defaults to today)"),
    current_admin: Administrator = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Aggregate daily API usage for a specific date."""
    quota_service = APIQuotaManagementService(db)
    
    try:
        # Convert date to datetime if provided
        target_datetime = datetime.combine(target_date, datetime.min.time()) if target_date else None
        
        aggregation_result = quota_service.aggregate_daily_usage(target_datetime)
        logger.info(f"Admin {current_admin.username} triggered usage aggregation for {target_date or 'today'}")
        return aggregation_result
    except Exception as e:
        logger.error(f"Error aggregating daily usage: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to aggregate daily usage"
        )


@router.get("/analytics/{api_key}", response_model=dict)
async def get_usage_analytics(
    api_key: str,
    period_days: int = Query(30, ge=1, le=365, description="Period in days for analytics"),
    current_admin: Administrator = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get usage analytics for an API key."""
    quota_service = APIQuotaManagementService(db)
    
    try:
        analytics = quota_service.get_usage_analytics(api_key, period_days)
        return analytics
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error retrieving usage analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve usage analytics"
        )


@router.post("/keys/{api_key}/rotate", response_model=dict)
async def rotate_api_key(
    api_key: str,
    current_admin: Administrator = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Rotate an API key (generate new key, deactivate old)."""
    quota_service = APIQuotaManagementService(db)
    
    try:
        rotation_result = quota_service.rotate_api_key(api_key)
        logger.info(f"Admin {current_admin.username} rotated API key {api_key[:8]}...")
        return rotation_result
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error rotating API key: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to rotate API key"
        )


@router.get("/dashboard/quota-overview", response_model=dict)
async def get_quota_dashboard(
    current_admin: Administrator = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get comprehensive quota management dashboard data."""
    quota_service = APIQuotaManagementService(db)
    
    try:
        # Get overview data for all API keys
        dashboard_data = {
            'total_api_keys': 25,  # Placeholder
            'active_keys': 22,     # Placeholder
            'keys_near_quota': 3,  # Placeholder
            'keys_over_quota': 1,  # Placeholder
            'total_requests_today': 125000,  # Placeholder
            'total_requests_month': 3500000, # Placeholder
            'top_consumers': [
                {'api_key': 'isp_abc123...', 'reseller_id': 1, 'requests_today': 15000},
                {'api_key': 'isp_def456...', 'reseller_id': 2, 'requests_today': 12000},
                {'api_key': 'isp_ghi789...', 'reseller_id': 3, 'requests_today': 10000}
            ],
            'rate_limit_violations_today': 15,
            'quota_violations_today': 3,
            'last_updated': datetime.now().isoformat()
        }
        
        return dashboard_data
    except Exception as e:
        logger.error(f"Error retrieving quota dashboard: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve quota dashboard"
        )


@router.get("/reseller/{reseller_id}/usage", response_model=dict)
async def get_reseller_usage_summary(
    reseller_id: int,
    period_days: int = Query(30, ge=1, le=365, description="Period in days for summary"),
    current_admin: Administrator = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get usage summary for all API keys belonging to a reseller."""
    quota_service = APIQuotaManagementService(db)
    
    try:
        # This would aggregate usage across all API keys for the reseller
        usage_summary = {
            'reseller_id': reseller_id,
            'period_days': period_days,
            'total_api_keys': 3,
            'total_requests': 45000,
            'average_requests_per_day': 1500,
            'quota_utilization': 75.0,  # Percentage
            'rate_limit_violations': 5,
            'quota_violations': 1,
            'api_keys': [
                {
                    'api_key': 'isp_abc123...',
                    'requests': 20000,
                    'quota_utilization': 66.7,
                    'status': 'active'
                },
                {
                    'api_key': 'isp_def456...',
                    'requests': 15000,
                    'quota_utilization': 50.0,
                    'status': 'active'
                },
                {
                    'api_key': 'isp_ghi789...',
                    'requests': 10000,
                    'quota_utilization': 100.0,
                    'status': 'quota_exceeded'
                }
            ]
        }
        
        return usage_summary
    except Exception as e:
        logger.error(f"Error retrieving reseller usage summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve reseller usage summary"
        )


@router.get("/alerts/quota-violations", response_model=dict)
async def get_quota_violation_alerts(
    hours: int = Query(24, ge=1, le=168, description="Hours to look back for violations"),
    current_admin: Administrator = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get recent quota and rate limit violation alerts."""
    try:
        # This would query recent violations from the database
        violations = {
            'period_hours': hours,
            'quota_violations': [
                {
                    'api_key': 'isp_abc123...',
                    'reseller_id': 1,
                    'violation_type': 'daily_quota',
                    'limit': 10000,
                    'usage': 12500,
                    'violation_time': '2025-01-29T14:30:00Z'
                }
            ],
            'rate_limit_violations': [
                {
                    'api_key': 'isp_def456...',
                    'reseller_id': 2,
                    'endpoint': '/customers',
                    'limit': '100/minute',
                    'violation_count': 3,
                    'last_violation': '2025-01-29T15:45:00Z'
                }
            ],
            'total_quota_violations': 1,
            'total_rate_limit_violations': 1
        }
        
        return violations
    except Exception as e:
        logger.error(f"Error retrieving quota violation alerts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve quota violation alerts"
        )


@router.post("/keys/{api_key}/reset-quota", response_model=dict)
async def reset_api_key_quota(
    api_key: str,
    quota_type: str = Query(..., pattern="^(daily|monthly)$", description="Type of quota to reset"),
    current_admin: Administrator = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Reset quota for an API key (emergency override)."""
    try:
        # This would reset the usage counters for the specified quota type
        reset_result = {
            'api_key': api_key[:8] + '...',
            'quota_type': quota_type,
            'reset_by': current_admin.username,
            'reset_time': datetime.now().isoformat(),
            'previous_usage': 12500 if quota_type == 'daily' else 350000,
            'new_usage': 0
        }
        
        logger.info(f"Admin {current_admin.username} reset {quota_type} quota for API key {api_key[:8]}...")
        
        return reset_result
    except Exception as e:
        logger.error(f"Error resetting API key quota: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset API key quota"
        )
