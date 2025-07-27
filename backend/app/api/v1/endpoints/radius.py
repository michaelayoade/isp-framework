"""
RADIUS Session Management API Endpoints

This module contains FastAPI endpoints for RADIUS session tracking,
customer online status, and network usage statistics.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta

from ....core.database import get_db
from ....api.v1.dependencies import get_current_admin
from ....models.auth import Administrator
from ....services.radius import RadiusSessionService, CustomerOnlineService, CustomerStatisticsService
from ....schemas.radius import (
    RadiusSession, RadiusSessionCreate, RadiusSessionUpdate, RadiusSessionList,
    CustomerOnline, CustomerOnlineCreate, CustomerOnlineUpdate, CustomerOnlineList,
    CustomerStatistics, CustomerStatisticsCreate, CustomerStatisticsUpdate, CustomerStatisticsList,
    SessionAnalytics, CustomerUsageSummary, NetworkUtilization, TopCustomersByUsage
)
from ....core.exceptions import ValidationError, NotFoundError

router = APIRouter()


# RADIUS Session Management Endpoints
@router.post("/sessions", response_model=RadiusSession)
async def start_radius_session(
    session_data: RadiusSessionCreate,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Start a new RADIUS session"""
    service = RadiusSessionService(db)
    return service.start_session(session_data.dict())


@router.get("/sessions", response_model=RadiusSessionList)
async def get_radius_sessions(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    customer_id: Optional[int] = Query(None),
    login: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Get RADIUS sessions with filtering and pagination"""
    service = RadiusSessionService(db)
    
    if customer_id:
        sessions = service.get_customer_sessions(customer_id, days)
    elif status == "active":
        sessions = service.get_active_sessions()
    else:
        # Get all sessions for the specified period
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)
        sessions = service.repo.get_sessions_by_date_range(start_date, end_date)
    
    # Apply additional filters
    if login:
        sessions = [s for s in sessions if login.lower() in s.login.lower()]
    if status and status != "active":
        sessions = [s for s in sessions if s.session_status == status]
    
    # Apply pagination
    total = len(sessions)
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    paginated_sessions = sessions[start_idx:end_idx]
    
    return RadiusSessionList(
        sessions=paginated_sessions,
        total=total,
        page=page,
        per_page=per_page
    )


@router.get("/sessions/{session_id}", response_model=RadiusSession)
async def get_radius_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Get a specific RADIUS session"""
    service = RadiusSessionService(db)
    return service.get_session(session_id)


@router.put("/sessions/{session_id}", response_model=RadiusSession)
async def update_radius_session(
    session_id: int,
    session_update: RadiusSessionUpdate,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Update RADIUS session usage data"""
    service = RadiusSessionService(db)
    session = service.get_session(session_id)
    
    update_data = session_update.dict(exclude_unset=True)
    if update_data:
        for key, value in update_data.items():
            setattr(session, key, value)
        db.commit()
        db.refresh(session)
    
    return session


@router.post("/sessions/{session_id}/stop")
async def stop_radius_session(
    session_id: int,
    end_time: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Stop a RADIUS session"""
    service = RadiusSessionService(db)
    session = service.repo.get_by_id(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="RADIUS session not found")
    
    success = service.stop_session(session.session_id, end_time)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to stop session")
    
    return {"message": "Session stopped successfully", "session_id": session_id}


@router.post("/sessions/session/{session_id}/update-usage")
async def update_session_usage(
    session_id: str,
    in_bytes: int,
    out_bytes: int,
    time_on: int,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Update session usage statistics"""
    service = RadiusSessionService(db)
    session = service.update_session_usage(session_id, in_bytes, out_bytes, time_on)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {"message": "Usage updated successfully", "session": session}


@router.get("/sessions/analytics", response_model=SessionAnalytics)
async def get_session_analytics(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Get RADIUS session analytics"""
    service = RadiusSessionService(db)
    analytics = service.get_session_analytics(days)
    
    # Get additional metrics
    online_service = CustomerOnlineService(db)
    online_count = online_service.get_online_count()
    
    return SessionAnalytics(
        total_sessions=analytics["total_sessions"],
        active_sessions=analytics["active_sessions"],
        stopped_sessions=analytics["stopped_sessions"],
        total_customers_online=online_count,
        total_data_transferred_gb=analytics["total_data_gb"],
        average_session_duration_minutes=analytics["average_session_duration_minutes"],
        peak_concurrent_users=online_count  # This would need historical tracking
    )


# Customer Online Status Endpoints
@router.get("/online", response_model=CustomerOnlineList)
async def get_online_customers(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Get currently online customers"""
    service = CustomerOnlineService(db)
    online_customers = service.get_online_customers()
    
    # Apply pagination
    total = len(online_customers)
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    paginated_customers = online_customers[start_idx:end_idx]
    
    return CustomerOnlineList(
        online_customers=paginated_customers,
        total=total,
        page=page,
        per_page=per_page
    )


@router.get("/online/count")
async def get_online_count(
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Get count of online customers"""
    service = CustomerOnlineService(db)
    count = service.get_online_count()
    return {"online_count": count}


@router.get("/online/customer/{customer_id}", response_model=Optional[CustomerOnline])
async def get_customer_online_status(
    customer_id: int,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Get online status for a specific customer"""
    service = CustomerOnlineService(db)
    return service.get_customer_online_status(customer_id)


@router.get("/online/ip/{ip_address}", response_model=Optional[CustomerOnline])
async def get_customer_by_ip(
    ip_address: str,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Get online customer by IP address"""
    service = CustomerOnlineService(db)
    return service.get_by_ip(ip_address)


@router.get("/online/login/{login}", response_model=Optional[CustomerOnline])
async def get_customer_by_login(
    login: str,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Get online customer by login"""
    service = CustomerOnlineService(db)
    return service.get_by_login(login)


@router.post("/online/disconnect/{customer_id}")
async def disconnect_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Disconnect a customer"""
    service = CustomerOnlineService(db)
    success = service.disconnect_customer(customer_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Customer not found online")
    
    return {"message": "Customer disconnected successfully", "customer_id": customer_id}


@router.get("/online/summary")
async def get_online_summary(
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Get online customers summary"""
    service = CustomerOnlineService(db)
    return service.get_online_summary()


# Customer Statistics Endpoints
@router.get("/statistics", response_model=CustomerStatisticsList)
async def get_customer_statistics(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    customer_id: Optional[int] = Query(None),
    period_type: Optional[str] = Query(None),
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Get customer usage statistics"""
    service = CustomerStatisticsService(db)
    
    if customer_id:
        statistics = service.get_customer_statistics(customer_id, days)
    else:
        # Get all statistics for the period
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)
        statistics = service.repo.db.query(service.repo.model).filter(
            service.repo.model.period_start >= start_date,
            service.repo.model.period_end <= end_date
        ).all()
    
    # Apply period type filter
    if period_type:
        statistics = [s for s in statistics if s.period_type == period_type]
    
    # Apply pagination
    total = len(statistics)
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    paginated_stats = statistics[start_idx:end_idx]
    
    return CustomerStatisticsList(
        statistics=paginated_stats,
        total=total,
        page=page,
        per_page=per_page
    )


@router.get("/statistics/customer/{customer_id}/summary")
async def get_customer_usage_summary(
    customer_id: int,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Get customer usage summary"""
    service = CustomerStatisticsService(db)
    return service.get_customer_usage_summary(customer_id, days)


@router.get("/statistics/top-users", response_model=List[CustomerStatistics])
async def get_top_users_by_usage(
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Get top users by data usage"""
    service = CustomerStatisticsService(db)
    return service.get_top_users_by_usage(days, limit)


@router.post("/statistics/generate/daily/{date}")
async def generate_daily_statistics(
    date: str,  # Format: YYYY-MM-DD
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Generate daily statistics for a specific date"""
    try:
        target_date = datetime.strptime(date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    service = CustomerStatisticsService(db)
    count = service.generate_daily_statistics(target_date)
    
    return {
        "message": f"Generated daily statistics for {date}",
        "customers_processed": count,
        "date": date
    }


@router.post("/statistics/generate/monthly/{year}/{month}")
async def generate_monthly_statistics(
    year: int,
    month: int,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Generate monthly statistics for a specific month"""
    if month < 1 or month > 12:
        raise HTTPException(status_code=400, detail="Month must be between 1 and 12")
    
    service = CustomerStatisticsService(db)
    count = service.generate_monthly_statistics(year, month)
    
    return {
        "message": f"Generated monthly statistics for {year}-{month:02d}",
        "customers_processed": count,
        "year": year,
        "month": month
    }


@router.get("/statistics/network-utilization", response_model=NetworkUtilization)
async def get_network_utilization(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Get network utilization statistics"""
    service = CustomerStatisticsService(db)
    utilization = service.get_network_utilization(days)
    
    return NetworkUtilization(
        period_start=utilization["period_start"],
        period_end=utilization["period_end"],
        total_data_gb=utilization["total_data_gb"],
        peak_concurrent_users=utilization["current_online_users"],  # Approximation
        average_concurrent_users=float(utilization["current_online_users"]),  # Approximation
        total_session_time_hours=utilization["total_session_time_hours"],
        unique_customers=utilization["unique_customers"]
    )
