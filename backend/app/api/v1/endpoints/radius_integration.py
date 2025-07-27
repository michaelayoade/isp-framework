#!/usr/bin/env python3
"""
RADIUS Integration API Endpoints

This module provides REST API endpoints for RADIUS authentication,
session management, and service integration.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from ....core.database import get_db
from ..dependencies import get_current_admin
from ....services.radius_integration import RadiusServiceIntegration
from ....schemas.radius_integration import (
    RadiusAuthRequest, RadiusAuthResponse, RadiusSessionStart,
    RadiusSessionStop, RadiusAccountingUpdate, RadiusSessionResponse,
    CustomerSessionsResponse, ServiceEnforcementResponse
)
from ....models.auth import Administrator

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/authenticate", response_model=RadiusAuthResponse)
async def radius_authenticate(
    auth_request: RadiusAuthRequest,
    db: Session = Depends(get_db)
):
    """
    RADIUS Authentication Endpoint
    
    Authenticates a customer using portal ID and password,
    returns service plan attributes for RADIUS enforcement.
    """
    try:
        radius_service = RadiusServiceIntegration(db)
        
        auth_result = radius_service.authenticate_customer(
            portal_id=auth_request.username,  # username contains the portal_id
            password=auth_request.password,
            nas_ip=auth_request.nas_ip
        )
        
        if not auth_result.get("authenticated"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=auth_result.get("reason", "Authentication failed")
            )
        
        return RadiusAuthResponse(
            authenticated=True,
            customer_id=auth_result["customer_id"],
            portal_id=auth_result["portal_id"],
            service_plan_id=auth_result["service_plan_id"],
            radius_attributes=auth_result["radius_attributes"],
            customer_info=auth_result["customer_info"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in RADIUS authentication: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication system error"
        )


@router.post("/session/start", response_model=RadiusSessionResponse)
async def start_radius_session(
    session_start: RadiusSessionStart,
    db: Session = Depends(get_db)
):
    """
    Start RADIUS Session Endpoint
    
    Starts a new RADIUS session with service plan enforcement
    and IP address assignment.
    """
    try:
        radius_service = RadiusServiceIntegration(db)
        
        # First authenticate the customer
        auth_result = radius_service.authenticate_customer(
            portal_id=session_start.username,  # username contains the portal_id
            password=session_start.password,
            nas_ip=session_start.nas_ip
        )
        
        if not auth_result.get("authenticated"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=auth_result.get("reason", "Authentication failed")
            )
        
        # Start the session
        session = radius_service.start_session(
            auth_result=auth_result,
            session_data={
                "session_id": session_start.session_id,
                "nas_ip": session_start.nas_ip,
                "nas_port": session_start.nas_port
            }
        )
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to start RADIUS session"
            )
        
        return RadiusSessionResponse(
            session_id=session.id,
            customer_id=session.customer_id,
            portal_id=session.portal_id,
            service_plan_id=session.service_plan_id,
            framed_ip_address=session.framed_ip_address,
            start_time=session.start_time,
            status=session.status,
            radius_attributes=auth_result["radius_attributes"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting RADIUS session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start session"
        )


@router.post("/session/stop")
async def stop_radius_session(
    session_stop: RadiusSessionStop,
    db: Session = Depends(get_db)
):
    """
    Stop RADIUS Session Endpoint
    
    Stops a RADIUS session and updates usage statistics.
    """
    try:
        radius_service = RadiusServiceIntegration(db)
        
        success = radius_service.stop_session(
            session_id=session_stop.session_id,
            session_data={
                "bytes_in": session_stop.bytes_in,
                "bytes_out": session_stop.bytes_out,
                "packets_in": session_stop.packets_in,
                "packets_out": session_stop.packets_out,
                "termination_cause": session_stop.termination_cause
            }
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found or already stopped"
            )
        
        return {"message": "Session stopped successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error stopping RADIUS session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to stop session"
        )


@router.post("/session/accounting")
async def update_session_accounting(
    accounting_update: RadiusAccountingUpdate,
    db: Session = Depends(get_db)
):
    """
    Update Session Accounting Endpoint
    
    Updates session accounting data (interim updates).
    """
    try:
        radius_service = RadiusServiceIntegration(db)
        
        success = radius_service.update_session_accounting(
            session_id=accounting_update.session_id,
            accounting_data={
                "bytes_in": accounting_update.bytes_in,
                "bytes_out": accounting_update.bytes_out,
                "packets_in": accounting_update.packets_in,
                "packets_out": accounting_update.packets_out
            }
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        return {"message": "Accounting updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating session accounting: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update accounting"
        )


@router.get("/sessions/customer/{customer_id}", response_model=CustomerSessionsResponse)
async def get_customer_sessions(
    customer_id: int,
    active_only: bool = Query(False, description="Return only active sessions"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of sessions to return"),
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """
    Get Customer Sessions Endpoint
    
    Retrieves all sessions for a specific customer.
    """
    try:
        radius_service = RadiusServiceIntegration(db)
        
        sessions = radius_service.get_customer_sessions(
            customer_id=customer_id,
            active_only=active_only
        )
        
        # Limit results
        sessions = sessions[:limit]
        
        session_data = []
        for session in sessions:
            session_data.append({
                "session_id": session.id,
                "portal_id": session.portal_id,
                "service_plan_id": session.service_plan_id,
                "framed_ip_address": session.framed_ip_address,
                "start_time": session.start_time,
                "end_time": session.end_time,
                "status": session.status,
                "bytes_in": session.bytes_in,
                "bytes_out": session.bytes_out,
                "session_duration": session.session_duration,
                "termination_cause": session.termination_cause
            })
        
        return CustomerSessionsResponse(
            customer_id=customer_id,
            total_sessions=len(sessions),
            sessions=session_data
        )
        
    except Exception as e:
        logger.error(f"Error getting customer sessions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve sessions"
        )


@router.get("/service-plan/{service_plan_id}/enforcement", response_model=ServiceEnforcementResponse)
async def get_service_plan_enforcement(
    service_plan_id: int,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """
    Get Service Plan Enforcement Attributes
    
    Returns RADIUS attributes for service plan enforcement.
    """
    try:
        radius_service = RadiusServiceIntegration(db)
        
        attributes = radius_service.get_service_plan_enforcement_attributes(service_plan_id)
        
        if not attributes:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Service plan not found"
            )
        
        return ServiceEnforcementResponse(
            service_plan_id=service_plan_id,
            radius_attributes=attributes
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting service plan enforcement: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve enforcement attributes"
        )


@router.get("/sessions/active")
async def get_active_sessions(
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of sessions to return"),
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """
    Get Active Sessions Endpoint
    
    Returns all currently active RADIUS sessions.
    """
    try:
        radius_service = RadiusServiceIntegration(db)
        
        # Get all active sessions across all customers
        active_sessions = []
        
        # This is a simplified implementation - in production you might want
        # to implement this more efficiently with a direct database query
        from ....models.radius import RadiusSession
        sessions = db.query(RadiusSession).filter(
            RadiusSession.status == "active"
        ).limit(limit).all()
        
        for session in sessions:
            active_sessions.append({
                "session_id": session.id,
                "customer_id": session.customer_id,
                "portal_id": session.portal_id,
                "service_plan_id": session.service_plan_id,
                "framed_ip_address": session.framed_ip_address,
                "start_time": session.start_time,
                "nas_ip_address": session.nas_ip_address,
                "nas_port": session.nas_port,
                "bytes_in": session.bytes_in,
                "bytes_out": session.bytes_out,
                "last_update": session.last_update
            })
        
        return {
            "total_active_sessions": len(active_sessions),
            "sessions": active_sessions
        }
        
    except Exception as e:
        logger.error(f"Error getting active sessions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve active sessions"
        )


@router.get("/statistics/overview")
async def get_radius_statistics(
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """
    Get RADIUS Statistics Overview
    
    Returns overall RADIUS system statistics.
    """
    try:
        from ....models.radius import RadiusSession, CustomerOnline, CustomerStatistics
        
        # Get basic statistics
        total_sessions = db.query(RadiusSession).count()
        active_sessions = db.query(RadiusSession).filter(
            RadiusSession.status == "active"
        ).count()
        
        customers_online = db.query(CustomerOnline).filter(
            CustomerOnline.status == "online"
        ).count()
        
        # Get usage statistics
        total_stats = db.query(
            func.sum(CustomerStatistics.total_bytes_in),
            func.sum(CustomerStatistics.total_bytes_out),
            func.sum(CustomerStatistics.total_session_time)
        ).first()
        
        return {
            "total_sessions": total_sessions,
            "active_sessions": active_sessions,
            "customers_online": customers_online,
            "total_bytes_in": total_stats[0] or 0,
            "total_bytes_out": total_stats[1] or 0,
            "total_session_time": total_stats[2] or 0,
            "timestamp": datetime.now(timezone.utc)
        }
        
    except Exception as e:
        logger.error(f"Error getting RADIUS statistics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve statistics"
        )
