"""
API Management Endpoints

Comprehensive REST API endpoints for API management including:
- API key management (CRUD operations)
- Rate limiting and quota enforcement
- Usage analytics and monitoring
- API documentation management
- Access control and security
"""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.v1.dependencies import get_current_admin
from app.models.auth import Administrator
from app.services.api_management_service import APIManagementService
from app.repositories.api_management_repository import (
    APIUsageRepository, APIRateLimitRepository
)
from app.schemas.api_management import (
    APIKeyCreate, APIKeyUpdate, APIKeyResponse, APIUsageCreate, 
    APIVersionCreate, APIVersionUpdate, 
    APIVersionResponse, QuotaStatus, APIQuotaStatus,
    APIKeyUsageStats, APIEndpointCreate, APIEndpointResponse,
    APIUsageAnalytics
)
from app.core.exceptions import NotFoundError, ValidationError, RateLimitError, QuotaExceededError
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["api-management"])


@router.post("/keys", response_model=APIKeyResponse)
async def create_api_key(
    key_data: APIKeyCreate,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Create a new API key"""
    service = APIManagementService(db)
    try:
        api_key = service.create_api_key(key_data)
        return APIKeyResponse.from_orm(api_key)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/keys", response_model=List[APIKeyResponse])
async def list_api_keys(
    partner_id: Optional[int] = Query(None, description="Filter by partner ID"),
    customer_id: Optional[int] = Query(None, description="Filter by customer ID"),
    admin_id: Optional[int] = Query(None, description="Filter by admin ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search in key name or description"),
    limit: int = Query(100, ge=1, le=1000, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """List API keys with filtering"""
    service = APIManagementService(db)
    keys = service.list_api_keys(
        partner_id=partner_id,
        customer_id=customer_id,
        admin_id=admin_id,
        is_active=is_active,
        search=search,
        limit=limit,
        offset=offset
    )
    return [APIKeyResponse.from_orm(key) for key in keys]


@router.get("/keys/{key_id}", response_model=APIKeyResponse)
async def get_api_key(
    key_id: int,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Get API key details"""
    service = APIManagementService(db)
    try:
        api_key = service.get_api_key(key_id)
        return APIKeyResponse.from_orm(api_key)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/keys/{key_id}", response_model=APIKeyResponse)
async def update_api_key(
    key_id: int,
    key_data: APIKeyUpdate,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Update API key configuration"""
    service = APIManagementService(db)
    try:
        api_key = service.update_api_key(key_id, key_data)
        return APIKeyResponse.from_orm(api_key)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/keys/{key_id}")
async def revoke_api_key(
    key_id: int,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Revoke an API key"""
    service = APIManagementService(db)
    try:
        service.revoke_api_key(key_id)
        return {"message": "API key revoked successfully"}
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/keys/{key_id}/usage", response_model=APIKeyUsageStats)
async def get_api_key_usage(
    key_id: int,
    start_date: Optional[datetime] = Query(None, description="Start date for usage data"),
    end_date: Optional[datetime] = Query(None, description="End date for usage data"),
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Get usage statistics for an API key"""
    service = APIManagementService(db)
    try:
        analytics = service.get_usage_analytics(
            api_key_id=key_id,
            start_date=start_date,
            end_date=end_date
        )
        
        return APIKeyUsageStats(
            key_id=key_id,
            total_requests=analytics.total_requests,
            successful_requests=analytics.successful_requests,
            failed_requests=analytics.failed_requests,
            average_response_time=analytics.average_response_time,
            requests_by_endpoint=analytics.requests_by_endpoint,
            requests_by_day=analytics.requests_by_day,
            last_used=analytics.requests_by_day.get(max(analytics.requests_by_day.keys())) if analytics.requests_by_day else None
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/keys/{key_id}/quota", response_model=QuotaStatus)
async def get_api_key_quota(
    key_id: int,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Get quota status for an API key"""
    service = APIManagementService(db)
    key = service.get_api_key(key_id)
    
    # Get daily quota usage
    daily_usage = service.check_quota(key_id, "daily")
    daily_usage_count = daily_usage.get("usage_count", 0)
    daily_limit = key.daily_quota
    
    # Get monthly quota usage
    monthly_usage = service.check_quota(key_id, "monthly")
    monthly_usage_count = monthly_usage.get("usage_count", 0)
    monthly_limit = key.monthly_quota
    
    return APIQuotaStatus(
        key_id=key_id,
        daily_used=daily_usage_count,
        daily_limit=daily_limit,
        daily_remaining=max(0, daily_limit - daily_usage_count),
        monthly_used=monthly_usage_count,
        monthly_limit=monthly_limit,
        monthly_remaining=max(0, monthly_limit - monthly_usage_count)
    )


@router.post("/versions", response_model=APIVersionResponse)
async def create_api_version(
    version_data: APIVersionCreate,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Create a new API version"""
    service = APIManagementService(db)
    try:
        version = service.create_api_version(version_data)
        return APIVersionResponse.from_orm(version)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/versions", response_model=List[APIVersionResponse])
async def list_api_versions(
    status: Optional[str] = Query(None, description="Filter by status"),
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """List API versions"""
    service = APIManagementService(db)
    versions = service.list_api_versions(status=status)
    return [APIVersionResponse.from_orm(version) for version in versions]


@router.get("/versions/{version_id}", response_model=APIVersionResponse)
async def get_api_version(
    version_id: int,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Get API version details"""
    service = APIManagementService(db)
    try:
        version = service.get_api_version(version_id)
        return APIVersionResponse.from_orm(version)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/versions/{version_id}", response_model=APIVersionResponse)
async def update_api_version(
    version_id: int,
    version_data: APIVersionUpdate,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Update API version"""
    service = APIManagementService(db)
    try:
        version = service.update_api_version(version_id, version_data)
        return APIVersionResponse.from_orm(version)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/versions/{version_id}/endpoints", response_model=APIEndpointResponse)
async def create_api_endpoint(
    version_id: int,
    endpoint_data: APIEndpointCreate,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Create a new API endpoint"""
    service = APIManagementService(db)
    try:
        endpoint = service.create_api_endpoint(endpoint_data)
        return APIEndpointResponse.from_orm(endpoint)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/versions/{version_id}/endpoints", response_model=List[APIEndpointResponse])
async def list_api_endpoints(
    version_id: int,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """List all endpoints for an API version"""
    service = APIManagementService(db)
    endpoints = service.get_api_endpoints(version_id)
    return [APIEndpointResponse.from_orm(endpoint) for endpoint in endpoints]


@router.get("/usage/analytics", response_model=APIUsageAnalytics)
async def get_usage_analytics(
    start_date: Optional[datetime] = Query(None, description="Start date for analytics"),
    end_date: Optional[datetime] = Query(None, description="End date for analytics"),
    api_key_id: Optional[int] = Query(None, description="Filter by API key ID"),
    endpoint: Optional[str] = Query(None, description="Filter by endpoint"),
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Get comprehensive usage analytics"""
    service = APIManagementService(db)
    analytics = service.get_usage_analytics(
        api_key_id=api_key_id,
        start_date=start_date,
        end_date=end_date,
        endpoint=endpoint
    )
    return analytics


@router.post("/cleanup")
async def cleanup_old_data(
    days_to_keep: int = Query(90, ge=1, le=365, description="Days of data to keep"),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Clean up old usage data"""
    service = APIManagementService(db)
    deleted_count = service.cleanup_old_usage_data(days_to_keep)
    
    return {
        "message": f"Cleaned up {deleted_count} old usage records",
        "days_to_keep": days_to_keep
    }


# Public endpoints for API key validation (no authentication required)

@router.get("/validate")
async def validate_api_key(
    api_key: str = Query(..., description="API key to validate"),
    client_ip: Optional[str] = Query(None, description="Client IP address"),
    user_agent: Optional[str] = Query(None, description="User agent string"),
    db: Session = Depends(get_db)
):
    """Validate an API key (no authentication required)"""
    service = APIManagementService(db)
    try:
        key = service.validate_api_key(api_key, client_ip, user_agent)
        return {
            "valid": True,
            "key_name": key.key_name,
            "expires_at": key.expires_at,
            "scopes": key.scopes,
            "permissions": key.permissions
        }
    except (NotFoundError, ValidationError) as e:
        return {"valid": False, "error": str(e)}


@router.post("/usage/log")
async def log_api_usage(
    usage_data: APIUsageCreate,
    db: Session = Depends(get_db)
):
    """Log API usage (for internal use)"""
    service = APIManagementService(db)
    try:
        usage = service.log_api_usage(usage_data)
        return {"message": "Usage logged successfully", "usage_id": usage.id}
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


# Rate limiting and quota checking endpoints

@router.get("/rate-limit/check")
async def check_rate_limit(
    api_key: str = Query(..., description="API key to check"),
    endpoint: Optional[str] = Query(None, description="Endpoint being accessed"),
    db: Session = Depends(get_db)
):
    """Check rate limit status"""
    service = APIManagementService(db)
    try:
        key = service.validate_api_key(api_key)
        service.check_rate_limit(key.id, endpoint)
        
        # Get current rate limit status
        rate_limit_repo = APIRateLimitRepository(db)
        rate_limit = rate_limit_repo.get_current_window(key.id)
        
        return {
            "allowed": True,
            "current_count": rate_limit.request_count if rate_limit else 0,
            "limit": key.rate_limit,
            "remaining": max(0, key.rate_limit - (rate_limit.request_count if rate_limit else 0))
        }
    except (NotFoundError, RateLimitError) as e:
        return {"allowed": False, "error": str(e)}


@router.get("/quota/check")
async def check_quota(
    api_key: str = Query(..., description="API key to check"),
    quota_type: str = Query("daily", pattern="^(daily|monthly)$"),
    db: Session = Depends(get_db)
):
    """Check quota status"""
    service = APIManagementService(db)
    try:
        key = service.validate_api_key(api_key)
        service.check_quota(key.id, quota_type)
        
        # Get current usage
        usage_repo = APIUsageRepository(db)
        usage = usage_repo.get_usage_analytics(api_key_id=key.id)
        
        if quota_type == "daily":
            limit = key.daily_quota
            used = sum(v for k, v in usage.get("daily_usage", {}).items())
        else:
            limit = key.monthly_quota
            used = usage.get("total_requests", 0)
        
        return {
            "allowed": True,
            "used": used,
            "limit": limit,
            "remaining": max(0, limit - used)
        }
    except (NotFoundError, QuotaExceededError) as e:
        return {"allowed": False, "error": str(e)}


# ============================================================================
# Backward Compatibility Redirects (Temporary - Remove after 6 months)
# ============================================================================

# ============================================================================
# Clean RESTful API - No Backward Compatibility Needed (Pre-Production)
# ============================================================================
