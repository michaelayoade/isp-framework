"""
Service Management Repository - ISP Service Management System

Repository layer for service lifecycle management including:
- Service IP assignments (IP address management and tracking)
- Service status history (complete audit trail of status changes)
- Service suspensions (suspension management with grace periods)
- Service usage tracking (bandwidth, sessions, quality metrics)
- Service alerts (real-time alerting and notification system)

Provides database operations for comprehensive service lifecycle management
with advanced querying, filtering, and analytics capabilities.
"""

from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, func, case
from datetime import datetime, timezone, timedelta

from app.repositories.base import BaseRepository
from app.models.services import (
    ServiceIPAssignment, ServiceStatusHistory, ServiceSuspension,
    ServiceUsageTracking, ServiceAlert, ServiceStatus, SuspensionReason,
    IPAssignmentType
)
from app.models.services.instances import CustomerService
from app.models.customer import Customer


class ServiceIPAssignmentRepository(BaseRepository[ServiceIPAssignment]):
    """Repository for service IP assignment operations"""
    
    def __init__(self, db: Session):
        super().__init__(ServiceIPAssignment, db)
    
    def get_by_ip_address(self, ip_address: str) -> Optional[ServiceIPAssignment]:
        """Get IP assignment by IP address"""
        return self.db.query(ServiceIPAssignment).filter(
            ServiceIPAssignment.ip_address == ip_address
        ).first()
    
    def get_by_service(self, service_id: int) -> List[ServiceIPAssignment]:
        """Get all IP assignments for a service"""
        return self.db.query(ServiceIPAssignment).filter(
            ServiceIPAssignment.service_id == service_id
        ).options(
            joinedload(ServiceIPAssignment.service).joinedload(CustomerService.customer)
        ).order_by(ServiceIPAssignment.assigned_at.desc()).all()
    
    def get_active_assignments(
        self,
        network_id: Optional[int] = None,
        assignment_type: Optional[IPAssignmentType] = None
    ) -> List[ServiceIPAssignment]:
        """Get all active IP assignments with optional filtering"""
        query = self.db.query(ServiceIPAssignment).filter(
            ServiceIPAssignment.is_active is True
        )
        
        if network_id:
            query = query.filter(ServiceIPAssignment.network_id == network_id)
        
        if assignment_type:
            query = query.filter(ServiceIPAssignment.assignment_type == assignment_type)
        
        return query.options(
            joinedload(ServiceIPAssignment.service).joinedload(CustomerService.customer)
        ).order_by(ServiceIPAssignment.assigned_at.desc()).all()
    
    def get_by_mac_address(self, mac_address: str) -> List[ServiceIPAssignment]:
        """Get IP assignments by MAC address"""
        return self.db.query(ServiceIPAssignment).filter(
            ServiceIPAssignment.mac_address == mac_address
        ).options(
            joinedload(ServiceIPAssignment.service).joinedload(CustomerService.customer)
        ).order_by(ServiceIPAssignment.assigned_at.desc()).all()
    
    def get_expiring_assignments(self, days_ahead: int = 7) -> List[ServiceIPAssignment]:
        """Get IP assignments expiring within specified days"""
        expiry_date = datetime.now(timezone.utc) + timedelta(days=days_ahead)
        
        return self.db.query(ServiceIPAssignment).filter(
            ServiceIPAssignment.is_active is True,
            ServiceIPAssignment.expires_at.isnot(None),
            ServiceIPAssignment.expires_at <= expiry_date
        ).options(
            joinedload(ServiceIPAssignment.service).joinedload(CustomerService.customer)
        ).order_by(ServiceIPAssignment.expires_at).all()
    
    def get_network_utilization(self, network_id: int) -> Dict[str, Any]:
        """Get IP utilization statistics for a network"""
        stats = {}
        
        # Total assignments in network
        total_assignments = self.db.query(ServiceIPAssignment).filter(
            ServiceIPAssignment.network_id == network_id
        ).count()
        
        # Active assignments
        active_assignments = self.db.query(ServiceIPAssignment).filter(
            ServiceIPAssignment.network_id == network_id,
            ServiceIPAssignment.is_active is True
        ).count()
        
        # Assignments by type
        type_stats = self.db.query(
            ServiceIPAssignment.assignment_type,
            func.count(ServiceIPAssignment.id).label('count')
        ).filter(
            ServiceIPAssignment.network_id == network_id,
            ServiceIPAssignment.is_active is True
        ).group_by(ServiceIPAssignment.assignment_type).all()
        
        stats.update({
            'total_assignments': total_assignments,
            'active_assignments': active_assignments,
            'by_type': {str(type_stat[0]): type_stat[1] for type_stat in type_stats}
        })
        
        return stats
    
    def search_assignments(
        self,
        search_term: Optional[str] = None,
        network_id: Optional[int] = None,
        assignment_type: Optional[IPAssignmentType] = None,
        is_active: Optional[bool] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[ServiceIPAssignment], int]:
        """Search IP assignments with comprehensive filtering"""
        query = self.db.query(ServiceIPAssignment)
        
        # Text search
        if search_term:
            query = query.join(CustomerService).join(Customer).filter(
                or_(
                    ServiceIPAssignment.ip_address.ilike(f"%{search_term}%"),
                    ServiceIPAssignment.mac_address.ilike(f"%{search_term}%"),
                    Customer.first_name.ilike(f"%{search_term}%"),
                    Customer.last_name.ilike(f"%{search_term}%"),
                    Customer.login.ilike(f"%{search_term}%")
                )
            )
        
        # Filter by network
        if network_id:
            query = query.filter(ServiceIPAssignment.network_id == network_id)
        
        # Filter by assignment type
        if assignment_type:
            query = query.filter(ServiceIPAssignment.assignment_type == assignment_type)
        
        # Filter by active status
        if is_active is not None:
            query = query.filter(ServiceIPAssignment.is_active == is_active)
        
        # Filter by date range
        if date_from:
            query = query.filter(ServiceIPAssignment.assigned_at >= date_from)
        
        if date_to:
            query = query.filter(ServiceIPAssignment.assigned_at <= date_to)
        
        # Get total count
        total = query.count()
        
        # Apply pagination and ordering
        assignments = query.options(
            joinedload(ServiceIPAssignment.service).joinedload(CustomerService.customer)
        ).order_by(
            ServiceIPAssignment.assigned_at.desc()
        ).offset(offset).limit(limit).all()
        
        return assignments, total


class ServiceStatusHistoryRepository(BaseRepository[ServiceStatusHistory]):
    """Repository for service status history operations"""
    
    def __init__(self, db: Session):
        super().__init__(ServiceStatusHistory, db)
    
    def get_service_history(
        self, 
        service_id: int,
        limit: int = 50
    ) -> List[ServiceStatusHistory]:
        """Get status history for a service"""
        return self.db.query(ServiceStatusHistory).filter(
            ServiceStatusHistory.service_id == service_id
        ).options(
            joinedload(ServiceStatusHistory.changed_by)
        ).order_by(ServiceStatusHistory.changed_at.desc()).limit(limit).all()
    
    def get_recent_changes(
        self,
        hours_back: int = 24,
        status_filter: Optional[ServiceStatus] = None
    ) -> List[ServiceStatusHistory]:
        """Get recent status changes across all services"""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours_back)
        
        query = self.db.query(ServiceStatusHistory).filter(
            ServiceStatusHistory.changed_at >= cutoff_time
        )
        
        if status_filter:
            query = query.filter(ServiceStatusHistory.new_status == status_filter)
        
        return query.options(
            joinedload(ServiceStatusHistory.service).joinedload(CustomerService.customer),
            joinedload(ServiceStatusHistory.changed_by)
        ).order_by(ServiceStatusHistory.changed_at.desc()).all()
    
    def get_status_changes_by_admin(
        self,
        admin_id: int,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> List[ServiceStatusHistory]:
        """Get status changes made by a specific administrator"""
        query = self.db.query(ServiceStatusHistory).filter(
            ServiceStatusHistory.changed_by_id == admin_id
        )
        
        if date_from:
            query = query.filter(ServiceStatusHistory.changed_at >= date_from)
        
        if date_to:
            query = query.filter(ServiceStatusHistory.changed_at <= date_to)
        
        return query.options(
            joinedload(ServiceStatusHistory.service).joinedload(CustomerService.customer)
        ).order_by(ServiceStatusHistory.changed_at.desc()).all()
    
    def get_automated_changes(self, hours_back: int = 24) -> List[ServiceStatusHistory]:
        """Get automated status changes"""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours_back)
        
        return self.db.query(ServiceStatusHistory).filter(
            ServiceStatusHistory.changed_at >= cutoff_time,
            ServiceStatusHistory.is_automated is True
        ).options(
            joinedload(ServiceStatusHistory.service).joinedload(CustomerService.customer)
        ).order_by(ServiceStatusHistory.changed_at.desc()).all()
    
    def get_status_statistics(self, days: int = 30) -> Dict[str, Any]:
        """Get status change statistics"""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        stats = {}
        
        # Total status changes
        stats['total_changes'] = self.db.query(ServiceStatusHistory).filter(
            ServiceStatusHistory.changed_at >= cutoff_date
        ).count()
        
        # Changes by status
        status_stats = self.db.query(
            ServiceStatusHistory.new_status,
            func.count(ServiceStatusHistory.id).label('count')
        ).filter(
            ServiceStatusHistory.changed_at >= cutoff_date
        ).group_by(ServiceStatusHistory.new_status).all()
        
        stats['by_status'] = {str(status[0]): status[1] for status in status_stats}
        
        # Automated vs manual changes
        automated_changes = self.db.query(ServiceStatusHistory).filter(
            ServiceStatusHistory.changed_at >= cutoff_date,
            ServiceStatusHistory.is_automated is True
        ).count()
        
        stats['automated_changes'] = automated_changes
        stats['manual_changes'] = stats['total_changes'] - automated_changes
        
        return stats


class ServiceSuspensionRepository(BaseRepository[ServiceSuspension]):
    """Repository for service suspension operations"""
    
    def __init__(self, db: Session):
        super().__init__(ServiceSuspension, db)
    
    def get_active_suspensions(
        self,
        service_id: Optional[int] = None,
        reason: Optional[SuspensionReason] = None
    ) -> List[ServiceSuspension]:
        """Get all active suspensions with optional filtering"""
        query = self.db.query(ServiceSuspension).filter(
            ServiceSuspension.is_active is True
        )
        
        if service_id:
            query = query.filter(ServiceSuspension.service_id == service_id)
        
        if reason:
            query = query.filter(ServiceSuspension.reason == reason)
        
        return query.options(
            joinedload(ServiceSuspension.service).joinedload(CustomerService.customer),
            joinedload(ServiceSuspension.suspended_by)
        ).order_by(ServiceSuspension.suspended_at.desc()).all()
    
    def get_suspensions_in_grace_period(self) -> List[ServiceSuspension]:
        """Get suspensions currently in grace period"""
        now = datetime.now(timezone.utc)
        
        return self.db.query(ServiceSuspension).filter(
            ServiceSuspension.is_active is True,
            ServiceSuspension.grace_period_until.isnot(None),
            ServiceSuspension.grace_period_until > now
        ).options(
            joinedload(ServiceSuspension.service).joinedload(CustomerService.customer)
        ).order_by(ServiceSuspension.grace_period_until).all()
    
    def get_suspensions_ready_for_escalation(self) -> List[ServiceSuspension]:
        """Get suspensions ready for escalation"""
        now = datetime.now(timezone.utc)
        
        return self.db.query(ServiceSuspension).filter(
            ServiceSuspension.is_active is True,
            ServiceSuspension.escalation_at.isnot(None),
            ServiceSuspension.escalation_at <= now,
            ServiceSuspension.escalated is False
        ).options(
            joinedload(ServiceSuspension.service).joinedload(CustomerService.customer)
        ).order_by(ServiceSuspension.escalation_at).all()
    
    def get_auto_restoration_candidates(self) -> List[ServiceSuspension]:
        """Get suspensions eligible for automatic restoration"""
        now = datetime.now(timezone.utc)
        
        return self.db.query(ServiceSuspension).filter(
            ServiceSuspension.is_active is True,
            ServiceSuspension.auto_restore_at.isnot(None),
            ServiceSuspension.auto_restore_at <= now
        ).options(
            joinedload(ServiceSuspension.service).joinedload(CustomerService.customer)
        ).order_by(ServiceSuspension.auto_restore_at).all()
    
    def get_suspension_history(
        self,
        service_id: int,
        limit: int = 20
    ) -> List[ServiceSuspension]:
        """Get suspension history for a service"""
        return self.db.query(ServiceSuspension).filter(
            ServiceSuspension.service_id == service_id
        ).options(
            joinedload(ServiceSuspension.suspended_by),
            joinedload(ServiceSuspension.restored_by)
        ).order_by(ServiceSuspension.suspended_at.desc()).limit(limit).all()
    
    def get_suspension_statistics(self, days: int = 30) -> Dict[str, Any]:
        """Get suspension statistics"""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        stats = {}
        
        # Total suspensions
        stats['total_suspensions'] = self.db.query(ServiceSuspension).filter(
            ServiceSuspension.suspended_at >= cutoff_date
        ).count()
        
        # Active suspensions
        stats['active_suspensions'] = self.db.query(ServiceSuspension).filter(
            ServiceSuspension.is_active is True
        ).count()
        
        # Suspensions by reason
        reason_stats = self.db.query(
            ServiceSuspension.reason,
            func.count(ServiceSuspension.id).label('count')
        ).filter(
            ServiceSuspension.suspended_at >= cutoff_date
        ).group_by(ServiceSuspension.reason).all()
        
        stats['by_reason'] = {str(reason[0]): reason[1] for reason in reason_stats}
        
        # Average suspension duration for restored services
        avg_duration = self.db.query(
            func.avg(
                func.extract('epoch', ServiceSuspension.restored_at - ServiceSuspension.suspended_at) / 86400
            )
        ).filter(
            ServiceSuspension.restored_at.isnot(None),
            ServiceSuspension.suspended_at >= cutoff_date
        ).scalar()
        
        stats['average_suspension_duration_days'] = float(avg_duration) if avg_duration else 0.0
        
        return stats


class ServiceUsageTrackingRepository(BaseRepository[ServiceUsageTracking]):
    """Repository for service usage tracking operations"""
    
    def __init__(self, db: Session):
        super().__init__(ServiceUsageTracking, db)
    
    def get_service_usage(
        self,
        service_id: int,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> List[ServiceUsageTracking]:
        """Get usage records for a service"""
        query = self.db.query(ServiceUsageTracking).filter(
            ServiceUsageTracking.service_id == service_id
        )
        
        if date_from:
            query = query.filter(ServiceUsageTracking.period_start >= date_from)
        
        if date_to:
            query = query.filter(ServiceUsageTracking.period_end <= date_to)
        
        return query.order_by(ServiceUsageTracking.period_start.desc()).all()
    
    def get_high_usage_services(
        self,
        threshold_gb: float = 100.0,
        days_back: int = 7
    ) -> List[ServiceUsageTracking]:
        """Get services with high bandwidth usage"""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_back)
        threshold_bytes = threshold_gb * 1024 * 1024 * 1024  # Convert GB to bytes
        
        return self.db.query(ServiceUsageTracking).filter(
            ServiceUsageTracking.period_start >= cutoff_date,
            ServiceUsageTracking.total_bytes > threshold_bytes
        ).options(
            joinedload(ServiceUsageTracking.service).joinedload(CustomerService.customer)
        ).order_by(ServiceUsageTracking.total_bytes.desc()).all()
    
    def get_usage_summary(
        self,
        service_id: int,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get usage summary for a service"""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        usage_records = self.db.query(ServiceUsageTracking).filter(
            ServiceUsageTracking.service_id == service_id,
            ServiceUsageTracking.period_start >= cutoff_date
        ).all()
        
        if not usage_records:
            return {
                'total_bytes': 0,
                'total_sessions': 0,
                'average_session_duration': 0,
                'peak_bandwidth_mbps': 0,
                'total_cost': 0.0
            }
        
        summary = {
            'total_bytes': sum(record.total_bytes or 0 for record in usage_records),
            'total_sessions': sum(record.session_count or 0 for record in usage_records),
            'peak_bandwidth_mbps': max(record.peak_bandwidth_mbps or 0 for record in usage_records),
            'total_cost': sum(record.cost_amount or 0 for record in usage_records)
        }
        
        # Calculate average session duration
        total_duration = sum(record.total_session_duration or 0 for record in usage_records)
        total_sessions = summary['total_sessions']
        summary['average_session_duration'] = total_duration / total_sessions if total_sessions > 0 else 0
        
        return summary
    
    def get_network_usage_stats(self, days: int = 30) -> Dict[str, Any]:
        """Get network-wide usage statistics"""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        stats = {}
        
        # Total bandwidth usage
        total_bytes = self.db.query(
            func.sum(ServiceUsageTracking.total_bytes)
        ).filter(
            ServiceUsageTracking.period_start >= cutoff_date
        ).scalar()
        
        stats['total_bytes'] = int(total_bytes) if total_bytes else 0
        stats['total_gb'] = stats['total_bytes'] / (1024 * 1024 * 1024)
        
        # Total sessions
        total_sessions = self.db.query(
            func.sum(ServiceUsageTracking.session_count)
        ).filter(
            ServiceUsageTracking.period_start >= cutoff_date
        ).scalar()
        
        stats['total_sessions'] = int(total_sessions) if total_sessions else 0
        
        # Peak bandwidth
        peak_bandwidth = self.db.query(
            func.max(ServiceUsageTracking.peak_bandwidth_mbps)
        ).filter(
            ServiceUsageTracking.period_start >= cutoff_date
        ).scalar()
        
        stats['peak_bandwidth_mbps'] = float(peak_bandwidth) if peak_bandwidth else 0.0
        
        # Total cost
        total_cost = self.db.query(
            func.sum(ServiceUsageTracking.cost_amount)
        ).filter(
            ServiceUsageTracking.period_start >= cutoff_date
        ).scalar()
        
        stats['total_cost'] = float(total_cost) if total_cost else 0.0
        
        return stats


class ServiceAlertRepository(BaseRepository[ServiceAlert]):
    """Repository for service alert operations"""
    
    def __init__(self, db: Session):
        super().__init__(ServiceAlert, db)
    
    def get_active_alerts(
        self,
        service_id: Optional[int] = None,
        severity: Optional[str] = None
    ) -> List[ServiceAlert]:
        """Get all active alerts with optional filtering"""
        query = self.db.query(ServiceAlert).filter(
            ServiceAlert.is_active is True
        )
        
        if service_id:
            query = query.filter(ServiceAlert.service_id == service_id)
        
        if severity:
            query = query.filter(ServiceAlert.severity == severity)
        
        return query.options(
            joinedload(ServiceAlert.service).joinedload(CustomerService.customer)
        ).order_by(
            case(
                (ServiceAlert.severity == 'critical', 1),
                (ServiceAlert.severity == 'high', 2),
                (ServiceAlert.severity == 'medium', 3),
                (ServiceAlert.severity == 'low', 4),
                else_=5
            ),
            ServiceAlert.created_at.desc()
        ).all()
    
    def get_unacknowledged_alerts(self) -> List[ServiceAlert]:
        """Get all unacknowledged alerts"""
        return self.db.query(ServiceAlert).filter(
            ServiceAlert.is_active is True,
            ServiceAlert.acknowledged_at.is_(None)
        ).options(
            joinedload(ServiceAlert.service).joinedload(CustomerService.customer)
        ).order_by(
            case(
                (ServiceAlert.severity == 'critical', 1),
                (ServiceAlert.severity == 'high', 2),
                (ServiceAlert.severity == 'medium', 3),
                (ServiceAlert.severity == 'low', 4),
                else_=5
            ),
            ServiceAlert.created_at.desc()
        ).all()
    
    def get_critical_alerts(self, hours_back: int = 24) -> List[ServiceAlert]:
        """Get critical alerts within specified timeframe"""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours_back)
        
        return self.db.query(ServiceAlert).filter(
            ServiceAlert.severity == 'critical',
            ServiceAlert.created_at >= cutoff_time
        ).options(
            joinedload(ServiceAlert.service).joinedload(CustomerService.customer)
        ).order_by(ServiceAlert.created_at.desc()).all()
    
    def get_alert_statistics(self, days: int = 30) -> Dict[str, Any]:
        """Get alert statistics"""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        stats = {}
        
        # Total alerts
        stats['total_alerts'] = self.db.query(ServiceAlert).filter(
            ServiceAlert.created_at >= cutoff_date
        ).count()
        
        # Active alerts
        stats['active_alerts'] = self.db.query(ServiceAlert).filter(
            ServiceAlert.is_active is True
        ).count()
        
        # Alerts by severity
        severity_stats = self.db.query(
            ServiceAlert.severity,
            func.count(ServiceAlert.id).label('count')
        ).filter(
            ServiceAlert.created_at >= cutoff_date
        ).group_by(ServiceAlert.severity).all()
        
        stats['by_severity'] = {severity[0]: severity[1] for severity in severity_stats}
        
        # Unacknowledged alerts
        stats['unacknowledged_alerts'] = self.db.query(ServiceAlert).filter(
            ServiceAlert.is_active is True,
            ServiceAlert.acknowledged_at.is_(None)
        ).count()
        
        # Average resolution time for resolved alerts
        avg_resolution = self.db.query(
            func.avg(
                func.extract('epoch', ServiceAlert.resolved_at - ServiceAlert.created_at) / 3600
            )
        ).filter(
            ServiceAlert.resolved_at.isnot(None),
            ServiceAlert.created_at >= cutoff_date
        ).scalar()
        
        stats['average_resolution_time_hours'] = float(avg_resolution) if avg_resolution else 0.0
        
        return stats


# Repository factory for service management
class ServiceManagementRepositoryFactory:
    """Factory for creating service management repositories"""
    
    @staticmethod
    def create_ip_assignment_repo(db: Session) -> ServiceIPAssignmentRepository:
        return ServiceIPAssignmentRepository(db)
    
    @staticmethod
    def create_status_history_repo(db: Session) -> ServiceStatusHistoryRepository:
        return ServiceStatusHistoryRepository(db)
    
    @staticmethod
    def create_suspension_repo(db: Session) -> ServiceSuspensionRepository:
        return ServiceSuspensionRepository(db)
    
    @staticmethod
    def create_usage_tracking_repo(db: Session) -> ServiceUsageTrackingRepository:
        return ServiceUsageTrackingRepository(db)
    
    @staticmethod
    def create_alert_repo(db: Session) -> ServiceAlertRepository:
        return ServiceAlertRepository(db)
    
    @staticmethod
    def create_all_repos(db: Session) -> Dict[str, Any]:
        """Create all service management repositories"""
        return {
            'ip_assignment': ServiceIPAssignmentRepository(db),
            'status_history': ServiceStatusHistoryRepository(db),
            'suspension': ServiceSuspensionRepository(db),
            'usage_tracking': ServiceUsageTrackingRepository(db),
            'alert': ServiceAlertRepository(db)
        }
