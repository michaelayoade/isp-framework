"""
Security management endpoints for ISP Framework.

Provides endpoints for JWT key rotation, security scanning, and security monitoring.
"""
from typing import Dict, List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse

from app.core.jwt_rotation import (
    rotate_jwt_keys, 
    cleanup_expired_jwt_keys, 
    get_jwt_key_info
)
from app.core.dependency_scanner import (
    run_security_scan,
    get_security_scan_summary,
    check_security_requirements
)
from app.core.security_middleware import (
    get_security_stats,
    cleanup_security_store
)
from app.api.dependencies import get_current_admin_user
from app.models.auth.base import Administrator

router = APIRouter()


@router.post("/jwt/rotate")
async def rotate_jwt_signing_keys(
    force: bool = False,
    current_admin: Administrator = Depends(get_current_admin_user)
):
    """Rotate JWT signing keys."""
    try:
        new_key_id = rotate_jwt_keys(force=force)
        return {
            "message": "JWT keys rotated successfully",
            "new_key_id": new_key_id,
            "forced": force
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Key rotation failed: {str(e)}"
        )


@router.delete("/jwt/cleanup")
async def cleanup_jwt_keys(
    keep_days: int = 30,
    current_admin: Administrator = Depends(get_current_admin_user)
):
    """Clean up expired JWT keys."""
    try:
        removed_keys = cleanup_expired_jwt_keys(keep_days=keep_days)
        return {
            "message": "JWT key cleanup completed",
            "removed_keys": removed_keys,
            "removed_count": len(removed_keys)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Key cleanup failed: {str(e)}"
        )


@router.get("/jwt/keys")
async def get_jwt_keys_info(
    current_admin: Administrator = Depends(get_current_admin_user)
):
    """Get information about JWT keys."""
    try:
        key_info = get_jwt_key_info()
        return {
            "keys": key_info,
            "total_keys": len(key_info)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get key info: {str(e)}"
        )


@router.post("/scan")
async def run_vulnerability_scan(
    current_admin: Administrator = Depends(get_current_admin_user)
):
    """Run comprehensive security vulnerability scan."""
    try:
        scan_results = run_security_scan()
        
        # Return appropriate status code based on findings
        summary = scan_results.get('summary', {})
        critical_count = summary.get('critical_count', 0)
        high_count = summary.get('high_count', 0)
        
        status_code = status.HTTP_200_OK
        if critical_count > 0:
            status_code = status.HTTP_206_PARTIAL_CONTENT  # Critical issues found
        elif high_count > 0:
            status_code = status.HTTP_202_ACCEPTED  # High issues found
        
        return JSONResponse(
            status_code=status_code,
            content=scan_results
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Security scan failed: {str(e)}"
        )


@router.get("/scan/summary")
async def get_scan_summary(
    current_admin: Administrator = Depends(get_current_admin_user)
):
    """Get summary of last security scan."""
    try:
        summary = get_security_scan_summary()
        return summary
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get scan summary: {str(e)}"
        )


@router.get("/scan/requirements")
async def check_scan_requirements(
    current_admin: Administrator = Depends(get_current_admin_user)
):
    """Check if security scanning tools are installed."""
    try:
        tools_available, missing_tools = check_security_requirements()
        return {
            "tools_available": tools_available,
            "missing_tools": missing_tools,
            "install_command": f"pip install {' '.join(missing_tools)}" if missing_tools else None
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check requirements: {str(e)}"
        )


@router.get("/stats")
async def get_security_statistics(
    current_admin: Administrator = Depends(get_current_admin_user)
):
    """Get security middleware statistics."""
    try:
        stats = await get_security_stats()
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get security stats: {str(e)}"
        )


@router.post("/cleanup")
async def cleanup_security_data(
    current_admin: Administrator = Depends(get_current_admin_user)
):
    """Clean up expired security data (rate limits, blocked IPs)."""
    try:
        cleanup_security_store()
        return {"message": "Security data cleanup completed"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Security cleanup failed: {str(e)}"
        )


@router.get("/health", include_in_schema=False)
async def security_health_check():
    """Security system health check (no auth required)."""
    try:
        # Check if security tools are available
        tools_available, missing_tools = check_security_requirements()
        
        # Get basic security stats
        stats = await get_security_stats()
        
        # Get JWT key status
        key_info = get_jwt_key_info()
        active_keys = [k for k in key_info.values() if k['status'] == 'active']
        
        health_status = {
            "security_middleware": "healthy",
            "jwt_keys": {
                "status": "healthy" if active_keys else "warning",
                "active_keys": len(active_keys),
                "total_keys": len(key_info)
            },
            "security_tools": {
                "status": "healthy" if tools_available else "warning",
                "available_tools": len([t for t in ['bandit', 'safety', 'pip-audit'] if t not in missing_tools]),
                "missing_tools": missing_tools
            },
            "rate_limiting": {
                "status": "healthy",
                "blocked_ips": stats.get("blocked_ips", 0),
                "active_limits": stats.get("active_rate_limits", 0)
            }
        }
        
        # Determine overall status
        overall_status = "healthy"
        if not active_keys or not tools_available:
            overall_status = "warning"
        
        return {
            "status": overall_status,
            "components": health_status,
            "timestamp": stats.get("timestamp")
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": None
        }
