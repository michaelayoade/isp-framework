"""
RADIUS Session Management Service Layer

This module contains service classes for RADIUS session tracking,
customer online status, and network usage statistics.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..core.exceptions import DuplicateError, NotFoundError, ValidationError
from ..models.networking.radius import CustomerOnline, CustomerStatistics, RadiusSession
from ..repositories.radius import (
    CustomerOnlineRepository,
    CustomerStatisticsRepository,
    RadiusSessionRepository,
)

logger = logging.getLogger(__name__)


class RadiusSessionService:
    """Service for RADIUS session management"""

    def __init__(self, db: Session):
        self.db = db
        self.repo = RadiusSessionRepository(db)
        self.online_repo = CustomerOnlineRepository(db)

    def start_session(self, session_data: Dict[str, Any]) -> RadiusSession:
        """Start a new RADIUS session"""
        try:
            # Validate required fields
            if not session_data.get("login"):
                raise ValidationError("Login is required for RADIUS session")

            if not session_data.get("start_session"):
                session_data["start_session"] = datetime.now(timezone.utc)

            # Create session record
            session = self.repo.create(session_data)
            logger.info(f"Started RADIUS session: {session.login} (ID: {session.id})")

            # Add to online customers if customer_id is provided
            if session.customer_id:
                self._add_to_online(session)

            return session
        except IntegrityError as e:
            logger.error(f"Failed to start RADIUS session: {e}")
            raise DuplicateError("RADIUS session creation failed due to data conflict")

    def _add_to_online(self, session: RadiusSession):
        """Add customer to online status"""
        online_data = {
            "customer_id": session.customer_id,
            "service_id": session.service_id,
            "tariff_id": session.tariff_id,
            "partner_id": session.partner_id,
            "nas_id": session.nas_id,
            "login": session.login,
            "username_real": session.username_real,
            "in_bytes": session.in_bytes,
            "out_bytes": session.out_bytes,
            "start_session": session.start_session,
            "ipv4": session.ipv4,
            "ipv6": session.ipv6,
            "mac": session.mac,
            "call_to": session.call_to,
            "port": session.port,
            "price": session.price,
            "time_on": session.time_on,
            "type": session.type,
            "login_is": session.login_is,
            "session_id": session.session_id,
        }

        # Remove existing online record for this customer
        self.online_repo.remove_customer(session.customer_id)

        # Add new online record
        self.online_repo.create(online_data)

    def stop_session(
        self, session_id: str, end_time: Optional[datetime] = None
    ) -> bool:
        """Stop a RADIUS session"""
        success = self.repo.stop_session(session_id, end_time)
        if success:
            # Remove from online customers
            self.online_repo.remove_by_session_id(session_id)
            logger.info(f"Stopped RADIUS session: {session_id}")
        return success

    def update_session_usage(
        self, session_id: str, in_bytes: int, out_bytes: int, time_on: int
    ) -> Optional[RadiusSession]:
        """Update session usage statistics"""
        session = self.repo.update_session_usage(
            session_id, in_bytes, out_bytes, time_on
        )

        if session:
            # Update online customer data
            self.online_repo.update_session_data(
                session_id, in_bytes, out_bytes, time_on
            )
            logger.debug(f"Updated session usage: {session_id}")

        return session

    def get_session(self, session_id: int) -> RadiusSession:
        """Get RADIUS session by ID"""
        session = self.repo.get_by_id(session_id)
        if not session:
            raise NotFoundError(f"RADIUS session with ID {session_id} not found")
        return session

    def get_session_by_session_id(self, session_id: str) -> RadiusSession:
        """Get RADIUS session by session ID"""
        session = self.repo.get_by_session_id(session_id)
        if not session:
            raise NotFoundError(
                f"RADIUS session with session ID {session_id} not found"
            )
        return session

    def get_customer_sessions(
        self, customer_id: int, days: int = 30
    ) -> List[RadiusSession]:
        """Get customer sessions for the last N days"""
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)
        return self.repo.get_customer_sessions_by_date(
            customer_id, start_date, end_date
        )

    def get_active_sessions(self) -> List[RadiusSession]:
        """Get all active sessions"""
        return self.repo.get_active_sessions()

    def get_session_analytics(self, days: int = 30) -> Dict[str, Any]:
        """Get session analytics for the last N days"""
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)
        return self.repo.get_session_analytics(start_date, end_date)


class CustomerOnlineService:
    """Service for customer online status management"""

    def __init__(self, db: Session):
        self.db = db
        self.repo = CustomerOnlineRepository(db)

    def get_online_customers(self) -> List[CustomerOnline]:
        """Get all currently online customers"""
        return self.repo.get_all_online()

    def get_online_count(self) -> int:
        """Get count of online customers"""
        return self.repo.get_online_count()

    def get_customer_online_status(self, customer_id: int) -> Optional[CustomerOnline]:
        """Get online status for a specific customer"""
        return self.repo.get_by_customer(customer_id)

    def is_customer_online(self, customer_id: int) -> bool:
        """Check if customer is currently online"""
        return self.repo.get_by_customer(customer_id) is not None

    def get_by_ip(self, ip_address: str) -> Optional[CustomerOnline]:
        """Get online customer by IP address"""
        return self.repo.get_by_ip(ip_address)

    def get_by_login(self, login: str) -> Optional[CustomerOnline]:
        """Get online customer by login"""
        return self.repo.get_by_login(login)

    def disconnect_customer(self, customer_id: int) -> bool:
        """Disconnect a customer (remove from online status)"""
        success = self.repo.remove_customer(customer_id)
        if success:
            logger.info(f"Disconnected customer: {customer_id}")
        return success

    def get_online_summary(self) -> Dict[str, Any]:
        """Get online customers summary"""
        online_customers = self.get_online_customers()

        total_data = sum(c.total_bytes for c in online_customers)
        total_time = sum(c.time_on for c in online_customers if c.time_on)

        return {
            "total_online": len(online_customers),
            "total_data_gb": round(total_data / (1024**3), 2) if total_data else 0,
            "total_session_time_hours": (
                round(total_time / 3600, 2) if total_time else 0
            ),
            "average_session_duration_minutes": (
                round(total_time / len(online_customers) / 60, 2)
                if online_customers and total_time
                else 0
            ),
        }


class CustomerStatisticsService:
    """Service for customer usage statistics"""

    def __init__(self, db: Session):
        self.db = db
        self.repo = CustomerStatisticsRepository(db)
        self.session_repo = RadiusSessionRepository(db)

    def get_customer_statistics(
        self, customer_id: int, days: int = 30
    ) -> List[CustomerStatistics]:
        """Get customer statistics for the last N days"""
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)

        return (
            self.db.query(CustomerStatistics)
            .filter(
                CustomerStatistics.customer_id == customer_id,
                CustomerStatistics.period_start >= start_date,
                CustomerStatistics.period_end <= end_date,
            )
            .all()
        )

    def get_customer_usage_summary(
        self, customer_id: int, days: int = 30
    ) -> Dict[str, Any]:
        """Get customer usage summary"""
        return self.repo.get_customer_usage_summary(customer_id, days)

    def get_top_users_by_usage(
        self, days: int = 30, limit: int = 10
    ) -> List[CustomerStatistics]:
        """Get top users by data usage"""
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)
        return self.repo.get_top_users_by_usage(start_date, end_date, limit)

    def generate_daily_statistics(self, date: datetime) -> int:
        """Generate daily statistics for all customers"""
        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)

        # Get all sessions for the day
        sessions = self.session_repo.get_sessions_by_date_range(
            start_of_day, end_of_day
        )

        # Group by customer
        customer_data = {}
        for session in sessions:
            if session.customer_id:
                if session.customer_id not in customer_data:
                    customer_data[session.customer_id] = {
                        "in_bytes": 0,
                        "out_bytes": 0,
                        "time_on": 0,
                        "sessions": 0,
                        "service_id": session.service_id,
                        "tariff_id": session.tariff_id,
                        "partner_id": session.partner_id,
                        "login": session.login,
                    }

                customer_data[session.customer_id]["in_bytes"] += session.in_bytes or 0
                customer_data[session.customer_id]["out_bytes"] += (
                    session.out_bytes or 0
                )
                customer_data[session.customer_id]["time_on"] += session.time_on or 0
                customer_data[session.customer_id]["sessions"] += 1

        # Create or update statistics records
        created_count = 0
        for customer_id, data in customer_data.items():
            stats_data = {
                "service_id": data["service_id"],
                "tariff_id": data["tariff_id"],
                "partner_id": data["partner_id"],
                "login": data["login"],
                "in_bytes": data["in_bytes"],
                "out_bytes": data["out_bytes"],
                "time_on": data["time_on"],
                "start_date": start_of_day,
                "end_date": end_of_day,
                "period_start": start_of_day,
                "period_end": end_of_day,
            }

            self.repo.create_or_update_stats(
                customer_id, "daily", start_of_day, end_of_day, stats_data
            )
            created_count += 1

        logger.info(
            f"Generated daily statistics for {created_count} customers on {date.date()}"
        )
        return created_count

    def generate_monthly_statistics(self, year: int, month: int) -> int:
        """Generate monthly statistics for all customers"""
        start_of_month = datetime(year, month, 1, tzinfo=timezone.utc)
        if month == 12:
            end_of_month = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
        else:
            end_of_month = datetime(year, month + 1, 1, tzinfo=timezone.utc)

        # Get all daily statistics for the month
        daily_stats = (
            self.db.query(CustomerStatistics)
            .filter(
                CustomerStatistics.period_type == "daily",
                CustomerStatistics.period_start >= start_of_month,
                CustomerStatistics.period_start < end_of_month,
            )
            .all()
        )

        # Group by customer
        customer_data = {}
        for stat in daily_stats:
            if stat.customer_id not in customer_data:
                customer_data[stat.customer_id] = {
                    "in_bytes": 0,
                    "out_bytes": 0,
                    "time_on": 0,
                    "service_id": stat.service_id,
                    "tariff_id": stat.tariff_id,
                    "partner_id": stat.partner_id,
                    "login": stat.login,
                }

            customer_data[stat.customer_id]["in_bytes"] += stat.in_bytes or 0
            customer_data[stat.customer_id]["out_bytes"] += stat.out_bytes or 0
            customer_data[stat.customer_id]["time_on"] += stat.time_on or 0

        # Create or update monthly statistics
        created_count = 0
        for customer_id, data in customer_data.items():
            stats_data = {
                "service_id": data["service_id"],
                "tariff_id": data["tariff_id"],
                "partner_id": data["partner_id"],
                "login": data["login"],
                "in_bytes": data["in_bytes"],
                "out_bytes": data["out_bytes"],
                "time_on": data["time_on"],
                "start_date": start_of_month,
                "end_date": end_of_month,
                "period_start": start_of_month,
                "period_end": end_of_month,
            }

            self.repo.create_or_update_stats(
                customer_id, "monthly", start_of_month, end_of_month, stats_data
            )
            created_count += 1

        logger.info(
            f"Generated monthly statistics for {created_count} customers for {year}-{month:02d}"
        )
        return created_count

    def get_network_utilization(self, days: int = 30) -> Dict[str, Any]:
        """Get network utilization statistics"""
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)

        # Get all statistics for the period
        stats = (
            self.db.query(CustomerStatistics)
            .filter(
                CustomerStatistics.period_start >= start_date,
                CustomerStatistics.period_end <= end_date,
            )
            .all()
        )

        total_data = sum((s.in_bytes or 0) + (s.out_bytes or 0) for s in stats)
        total_time = sum(s.time_on or 0 for s in stats)
        unique_customers = len(set(s.customer_id for s in stats))

        # Get peak concurrent users (this would need to be calculated from online data)
        # For now, we'll estimate based on current online count
        from ..services.radius import CustomerOnlineService

        online_service = CustomerOnlineService(self.db)
        current_online = online_service.get_online_count()

        return {
            "period_start": start_date,
            "period_end": end_date,
            "total_data_gb": round(total_data / (1024**3), 2) if total_data else 0,
            "total_session_time_hours": (
                round(total_time / 3600, 2) if total_time else 0
            ),
            "unique_customers": unique_customers,
            "current_online_users": current_online,
            "average_daily_usage_gb": (
                round(total_data / days / (1024**3), 2) if total_data else 0
            ),
        }
