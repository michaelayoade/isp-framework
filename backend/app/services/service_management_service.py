"""
Service Management Service Layer - ISP Service Management System

Business logic layer for service lifecycle management including:
- Service IP assignment management (IP allocation, tracking, expiration)
- Service status history (audit trails, change tracking)
- Service suspension management (grace periods, escalation, restoration)
- Service usage tracking (bandwidth monitoring, cost analysis)
- Service alert management (real-time monitoring, notification)

Provides high-level service management operations with automation,
monitoring, and comprehensive lifecycle control.
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session

from app.repositories.service_repository_factory import ServiceRepositoryFactory
from app.models.services import (
    ServiceIPAssignment, ServiceStatusHistory, ServiceSuspension,
    ServiceUsageTracking, ServiceAlert, ServiceStatus, SuspensionReason,
    SuspensionType, IPAssignmentType
)
from app.models.networking.ipam import IPPool as IPv4Network
from app.core.exceptions import ValidationError, NotFoundError, BusinessLogicError

logger = logging.getLogger(__name__)


class ServiceIPAssignmentService:
    """Service layer for service IP assignment operations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.repo_factory = ServiceRepositoryFactory(db)
        self.ip_assignment_repo = self.repo_factory.get_ip_assignment_repo()
        self.service_repo = self.repo_factory.get_customer_service_repo()
    
    async def assign_ip_address(
        self,
        service_id: int,
        ip_address: str,
        network_id: int,
        assignment_type: IPAssignmentType,
        admin_id: int,
        mac_address: Optional[str] = None,
        expires_at: Optional[datetime] = None
    ) -> ServiceIPAssignment:
        """Assign IP address to a service"""
        logger.info(f"Assigning IP {ip_address} to service: {service_id}")
        
        try:
            # Validate service exists and is active
            service = self.service_repo.get_by_id(service_id)
            if not service:
                raise NotFoundError(f"Service {service_id} not found")
            
            if service.status != ServiceStatus.ACTIVE:
                raise ValidationError("Can only assign IP to active services")
            
            # Check if IP is already assigned
            existing_assignment = self.ip_assignment_repo.get_by_ip_address(ip_address)
            if existing_assignment and existing_assignment.is_active:
                raise ValidationError(f"IP address {ip_address} is already assigned")
            
            # Create IP assignment
            assignment_params = {
                'service_id': service_id,
                'network_id': network_id,
                'ip_address': ip_address,
                'assignment_type': assignment_type,
                'mac_address': mac_address,
                'is_active': True,
                'assigned_at': datetime.now(timezone.utc),
                'expires_at': expires_at,
                'assigned_by_id': admin_id,
                'created_at': datetime.now(timezone.utc)
            }
            
            assignment = ServiceIPAssignment(**assignment_params)
            assignment = self.ip_assignment_repo.create(assignment)
            
            logger.info(f"IP address assigned successfully: {ip_address}")
            return assignment
            
        except Exception as e:
            logger.error(f"Error assigning IP address: {str(e)}")
            raise
    
    async def get_network_utilization(self, network_id: int) -> Dict[str, Any]:
        """Get comprehensive network utilization statistics"""
        logger.info(f"Getting network utilization for network: {network_id}")
        
        try:
            basic_stats = self.ip_assignment_repo.get_network_utilization(network_id)
            
            # Add advanced metrics
            network = self.db.query(IPv4Network).filter(IPv4Network.id == network_id).first()
            if not network:
                raise NotFoundError(f"Network {network_id} not found")
            
            total_ips = 254  # Default for /24 network
            utilization_percentage = (basic_stats['active_assignments'] / total_ips * 100) if total_ips > 0 else 0
            
            utilization_stats = {
                **basic_stats,
                'total_available_ips': total_ips,
                'utilization_percentage': utilization_percentage,
                'available_ips': total_ips - basic_stats['active_assignments']
            }
            
            return utilization_stats
            
        except Exception as e:
            logger.error(f"Error getting network utilization: {str(e)}")
            raise BusinessLogicError(f"Failed to get network utilization: {str(e)}")


class ServiceStatusHistoryService:
    """Service layer for service status history operations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.repo_factory = ServiceRepositoryFactory(db)
        self.status_history_repo = self.repo_factory.get_status_history_repo()
    
    async def record_status_change(
        self,
        service_id: int,
        old_status: ServiceStatus,
        new_status: ServiceStatus,
        admin_id: Optional[int] = None,
        change_reason: Optional[str] = None,
        is_automated: bool = False
    ) -> ServiceStatusHistory:
        """Record a service status change"""
        logger.info(f"Recording status change for service {service_id}: {old_status} -> {new_status}")
        
        try:
            history_params = {
                'service_id': service_id,
                'old_status': old_status,
                'new_status': new_status,
                'changed_by_id': admin_id,
                'change_reason': change_reason,
                'is_automated': is_automated,
                'changed_at': datetime.now(timezone.utc)
            }
            
            history = ServiceStatusHistory(**history_params)
            history = self.status_history_repo.create(history)
            
            logger.info(f"Status change recorded: {history.id}")
            return history
            
        except Exception as e:
            logger.error(f"Error recording status change: {str(e)}")
            raise


class ServiceSuspensionService:
    """Service layer for service suspension operations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.repo_factory = ServiceRepositoryFactory(db)
        self.suspension_repo = self.repo_factory.get_suspension_repo()
        self.service_repo = self.repo_factory.get_customer_service_repo()
    
    async def suspend_service(
        self,
        service_id: int,
        reason: SuspensionReason,
        suspension_type: SuspensionType,
        admin_id: int,
        grace_period_hours: Optional[int] = None,
        suspension_notes: Optional[str] = None
    ) -> ServiceSuspension:
        """Suspend a service with comprehensive suspension management"""
        logger.info(f"Suspending service {service_id} for reason: {reason}")
        
        try:
            service = self.service_repo.get_by_id(service_id)
            if not service:
                raise NotFoundError(f"Service {service_id} not found")
            
            if service.status != ServiceStatus.ACTIVE:
                raise ValidationError("Can only suspend active services")
            
            # Calculate suspension dates
            now = datetime.now(timezone.utc)
            grace_period_until = now + timedelta(hours=grace_period_hours) if grace_period_hours else None
            
            # Create suspension record
            suspension_params = {
                'service_id': service_id,
                'reason': reason,
                'suspension_type': suspension_type,
                'is_active': True,
                'suspended_at': now,
                'suspended_by_id': admin_id,
                'grace_period_until': grace_period_until,
                'suspension_notes': suspension_notes,
                'created_at': now
            }
            
            suspension = ServiceSuspension(**suspension_params)
            suspension = self.suspension_repo.create(suspension)
            
            # Update service status
            self.service_repo.update(service, {
                'status': ServiceStatus.SUSPENDED,
                'suspended_at': now,
                'updated_at': now
            })
            
            logger.info(f"Service suspended successfully: {suspension.id}")
            return suspension
            
        except Exception as e:
            logger.error(f"Error suspending service: {str(e)}")
            raise
    
    async def restore_service(
        self,
        suspension_id: int,
        admin_id: int,
        restoration_notes: Optional[str] = None
    ) -> ServiceSuspension:
        """Restore a suspended service"""
        logger.info(f"Restoring suspended service: {suspension_id}")
        
        try:
            suspension = self.suspension_repo.get_by_id(suspension_id)
            if not suspension:
                raise NotFoundError(f"Suspension {suspension_id} not found")
            
            if not suspension.is_active:
                raise ValidationError("Suspension is already inactive")
            
            # Restore suspension
            now = datetime.now(timezone.utc)
            suspension = self.suspension_repo.update(suspension, {
                'is_active': False,
                'restored_at': now,
                'restored_by_id': admin_id,
                'restoration_notes': restoration_notes,
                'updated_at': now
            })
            
            # Update service status
            service = self.service_repo.get_by_id(suspension.service_id)
            if service:
                self.service_repo.update(service, {
                    'status': ServiceStatus.ACTIVE,
                    'suspended_at': None,
                    'updated_at': now
                })
            
            logger.info(f"Service restored successfully: {suspension.service_id}")
            return suspension
            
        except Exception as e:
            logger.error(f"Error restoring service: {str(e)}")
            raise


class ServiceUsageTrackingService:
    """Service layer for service usage tracking operations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.repo_factory = ServiceRepositoryFactory(db)
        self.usage_tracking_repo = self.repo_factory.get_usage_tracking_repo()
    
    async def record_usage_data(
        self,
        service_id: int,
        period_start: datetime,
        period_end: datetime,
        usage_data: Dict[str, Any]
    ) -> ServiceUsageTracking:
        """Record usage data for a service"""
        logger.info(f"Recording usage data for service: {service_id}")
        
        try:
            tracking_params = {
                'service_id': service_id,
                'period_start': period_start,
                'period_end': period_end,
                'total_bytes': usage_data.get('total_bytes', 0),
                'download_bytes': usage_data.get('download_bytes', 0),
                'upload_bytes': usage_data.get('upload_bytes', 0),
                'session_count': usage_data.get('session_count', 0),
                'total_session_duration': usage_data.get('total_session_duration', 0),
                'peak_bandwidth_mbps': usage_data.get('peak_bandwidth_mbps', 0),
                'created_at': datetime.now(timezone.utc)
            }
            
            tracking = ServiceUsageTracking(**tracking_params)
            tracking = self.usage_tracking_repo.create(tracking)
            
            logger.info(f"Usage data recorded: {tracking.id}")
            return tracking
            
        except Exception as e:
            logger.error(f"Error recording usage data: {str(e)}")
            raise


class ServiceAlertService:
    """Service layer for service alert operations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.repo_factory = ServiceRepositoryFactory(db)
        self.alert_repo = self.repo_factory.get_alert_repo()
    
    async def create_alert(
        self,
        service_id: int,
        alert_type: str,
        severity: str,
        title: str,
        description: str,
        alert_data: Optional[Dict[str, Any]] = None
    ) -> ServiceAlert:
        """Create a new service alert"""
        logger.info(f"Creating alert for service {service_id}: {title}")
        
        try:
            alert_params = {
                'service_id': service_id,
                'alert_type': alert_type,
                'severity': severity,
                'title': title,
                'description': description,
                'is_active': True,
                'alert_data': alert_data or {},
                'created_at': datetime.now(timezone.utc)
            }
            
            alert = ServiceAlert(**alert_params)
            alert = self.alert_repo.create(alert)
            
            logger.info(f"Alert created: {alert.id}")
            return alert
            
        except Exception as e:
            logger.error(f"Error creating alert: {str(e)}")
            raise


# Service factory for management services
class ServiceManagementServiceFactory:
    """Factory for creating service management services"""
    
    @staticmethod
    def create_ip_assignment_service(db: Session) -> ServiceIPAssignmentService:
        return ServiceIPAssignmentService(db)
    
    @staticmethod
    def create_status_history_service(db: Session) -> ServiceStatusHistoryService:
        return ServiceStatusHistoryService(db)
    
    @staticmethod
    def create_suspension_service(db: Session) -> ServiceSuspensionService:
        return ServiceSuspensionService(db)
    
    @staticmethod
    def create_usage_tracking_service(db: Session) -> ServiceUsageTrackingService:
        return ServiceUsageTrackingService(db)
    
    @staticmethod
    def create_alert_service(db: Session) -> ServiceAlertService:
        return ServiceAlertService(db)
    
    @staticmethod
    def create_all_services(db: Session) -> Dict[str, Any]:
        """Create all service management services"""
        return {
            'ip_assignment': ServiceIPAssignmentService(db),
            'status_history': ServiceStatusHistoryService(db),
            'suspension': ServiceSuspensionService(db),
            'usage_tracking': ServiceUsageTrackingService(db),
            'alert': ServiceAlertService(db)
        }
