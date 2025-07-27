"""
RADIUS Session Management Repositories

This module contains repository classes for RADIUS session tracking,
customer online status, and network usage statistics.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc
from datetime import datetime, timezone, timedelta
from .base import BaseRepository
from ..models.networking.radius import RadiusSession, CustomerOnline, CustomerStatistics


class RadiusSessionRepository(BaseRepository[RadiusSession]):
    """Repository for RADIUS session management"""
    
    def __init__(self, db: Session):
        super().__init__(db, RadiusSession)
    
    def get_by_customer(self, customer_id: int) -> List[RadiusSession]:
        """Get all sessions for a customer"""
        return self.get_all(filters={"customer_id": customer_id})
    
    def get_active_sessions(self) -> List[RadiusSession]:
        """Get all active sessions"""
        return self.get_all(filters={"session_status": "active"})
    
    def get_by_session_id(self, session_id: str) -> Optional[RadiusSession]:
        """Get session by session ID"""
        return self.db.query(self.model).filter(self.model.session_id == session_id).first()
    
    def get_by_login(self, login: str) -> List[RadiusSession]:
        """Get sessions by login"""
        return self.get_all(filters={"login": login})
    
    def get_sessions_by_date_range(self, start_date: datetime, end_date: datetime) -> List[RadiusSession]:
        """Get sessions within a date range"""
        return self.db.query(self.model).filter(
            and_(
                self.model.start_session >= start_date,
                self.model.start_session <= end_date
            )
        ).all()
    
    def get_customer_sessions_by_date(self, customer_id: int, start_date: datetime, 
                                    end_date: datetime) -> List[RadiusSession]:
        """Get customer sessions within a date range"""
        return self.db.query(self.model).filter(
            and_(
                self.model.customer_id == customer_id,
                self.model.start_session >= start_date,
                self.model.start_session <= end_date
            )
        ).all()
    
    def stop_session(self, session_id: str, end_time: Optional[datetime] = None) -> bool:
        """Stop an active session"""
        session = self.get_by_session_id(session_id)
        if session and session.session_status == "active":
            session.session_status = "stopped"
            session.end_session = end_time or datetime.now(timezone.utc)
            self.db.commit()
            return True
        return False
    
    def update_session_usage(self, session_id: str, in_bytes: int, out_bytes: int, 
                           time_on: int) -> Optional[RadiusSession]:
        """Update session usage statistics"""
        session = self.get_by_session_id(session_id)
        if session:
            session.in_bytes = in_bytes
            session.out_bytes = out_bytes
            session.time_on = time_on
            session.last_change = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(session)
        return session
    
    def get_session_analytics(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get session analytics for a date range"""
        sessions = self.get_sessions_by_date_range(start_date, end_date)
        
        total_sessions = len(sessions)
        active_sessions = len([s for s in sessions if s.session_status == "active"])
        stopped_sessions = total_sessions - active_sessions
        
        total_bytes = sum(s.total_bytes for s in sessions)
        total_time = sum(s.time_on for s in sessions if s.time_on)
        
        return {
            "total_sessions": total_sessions,
            "active_sessions": active_sessions,
            "stopped_sessions": stopped_sessions,
            "total_data_gb": round(total_bytes / (1024**3), 2) if total_bytes else 0,
            "total_time_hours": round(total_time / 3600, 2) if total_time else 0,
            "average_session_duration_minutes": round(total_time / total_sessions / 60, 2) if total_sessions and total_time else 0
        }


class CustomerOnlineRepository(BaseRepository[CustomerOnline]):
    """Repository for customer online status management"""
    
    def __init__(self, db: Session):
        super().__init__(db, CustomerOnline)
    
    def get_by_customer(self, customer_id: int) -> Optional[CustomerOnline]:
        """Get online status for a customer"""
        return self.db.query(self.model).filter(self.model.customer_id == customer_id).first()
    
    def get_by_session_id(self, session_id: str) -> Optional[CustomerOnline]:
        """Get online customer by session ID"""
        return self.db.query(self.model).filter(self.model.session_id == session_id).first()
    
    def get_by_ip(self, ip_address: str) -> Optional[CustomerOnline]:
        """Get online customer by IP address"""
        return self.db.query(self.model).filter(
            or_(self.model.ipv4 == ip_address, self.model.ipv6 == ip_address)
        ).first()
    
    def get_by_login(self, login: str) -> Optional[CustomerOnline]:
        """Get online customer by login"""
        return self.db.query(self.model).filter(self.model.login == login).first()
    
    def get_all_online(self) -> List[CustomerOnline]:
        """Get all currently online customers"""
        return self.get_all()
    
    def get_online_count(self) -> int:
        """Get count of online customers"""
        return self.count()
    
    def update_session_data(self, session_id: str, in_bytes: int, out_bytes: int, 
                          time_on: int) -> Optional[CustomerOnline]:
        """Update online session data"""
        customer = self.get_by_session_id(session_id)
        if customer:
            customer.in_bytes = in_bytes
            customer.out_bytes = out_bytes
            customer.time_on = time_on
            customer.last_change = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(customer)
        return customer
    
    def remove_customer(self, customer_id: int) -> bool:
        """Remove customer from online status"""
        customer = self.get_by_customer(customer_id)
        if customer:
            self.db.delete(customer)
            self.db.commit()
            return True
        return False
    
    def remove_by_session_id(self, session_id: str) -> bool:
        """Remove customer by session ID"""
        customer = self.get_by_session_id(session_id)
        if customer:
            self.db.delete(customer)
            self.db.commit()
            return True
        return False


class CustomerStatisticsRepository(BaseRepository[CustomerStatistics]):
    """Repository for customer usage statistics"""
    
    def __init__(self, db: Session):
        super().__init__(db, CustomerStatistics)
    
    def get_by_customer(self, customer_id: int) -> List[CustomerStatistics]:
        """Get all statistics for a customer"""
        return self.get_all(filters={"customer_id": customer_id})
    
    def get_by_customer_and_period(self, customer_id: int, period_type: str, 
                                 period_start: datetime, period_end: datetime) -> Optional[CustomerStatistics]:
        """Get statistics for a customer and specific period"""
        return self.db.query(self.model).filter(
            and_(
                self.model.customer_id == customer_id,
                self.model.period_type == period_type,
                self.model.period_start == period_start,
                self.model.period_end == period_end
            )
        ).first()
    
    def get_by_period(self, period_type: str, period_start: datetime, 
                     period_end: datetime) -> List[CustomerStatistics]:
        """Get all statistics for a specific period"""
        return self.db.query(self.model).filter(
            and_(
                self.model.period_type == period_type,
                self.model.period_start == period_start,
                self.model.period_end == period_end
            )
        ).all()
    
    def get_top_users_by_usage(self, period_start: datetime, period_end: datetime, 
                              limit: int = 10) -> List[CustomerStatistics]:
        """Get top users by data usage"""
        return self.db.query(self.model).filter(
            and_(
                self.model.period_start >= period_start,
                self.model.period_end <= period_end
            )
        ).order_by(desc(self.model.in_bytes + self.model.out_bytes)).limit(limit).all()
    
    def get_customer_usage_summary(self, customer_id: int, days: int = 30) -> Dict[str, Any]:
        """Get customer usage summary for the last N days"""
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)
        
        stats = self.db.query(self.model).filter(
            and_(
                self.model.customer_id == customer_id,
                self.model.period_start >= start_date,
                self.model.period_end <= end_date
            )
        ).all()
        
        total_bytes = sum((s.in_bytes or 0) + (s.out_bytes or 0) for s in stats)
        total_time = sum(s.time_on or 0 for s in stats)
        
        return {
            "customer_id": customer_id,
            "period_days": days,
            "total_records": len(stats),
            "total_data_gb": round(total_bytes / (1024**3), 2) if total_bytes else 0,
            "total_time_hours": round(total_time / 3600, 2) if total_time else 0,
            "average_daily_usage_gb": round(total_bytes / days / (1024**3), 2) if total_bytes else 0
        }
    
    def aggregate_daily_stats(self, date: datetime) -> List[CustomerStatistics]:
        """Get all daily statistics for a specific date"""
        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)
        
        return self.db.query(self.model).filter(
            and_(
                self.model.period_type == "daily",
                self.model.period_start >= start_of_day,
                self.model.period_start < end_of_day
            )
        ).all()
    
    def create_or_update_stats(self, customer_id: int, period_type: str, 
                             period_start: datetime, period_end: datetime, 
                             stats_data: Dict[str, Any]) -> CustomerStatistics:
        """Create or update statistics record"""
        existing = self.get_by_customer_and_period(customer_id, period_type, period_start, period_end)
        
        if existing:
            # Update existing record
            for key, value in stats_data.items():
                if hasattr(existing, key):
                    setattr(existing, key, value)
            existing.updated_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(existing)
            return existing
        else:
            # Create new record
            stats_data.update({
                "customer_id": customer_id,
                "period_type": period_type,
                "period_start": period_start,
                "period_end": period_end
            })
            return self.create(stats_data)
