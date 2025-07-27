"""
Service Instances Repository - ISP Service Management System

Repository layer for customer service instance management including:
- Customer services (active service subscriptions)
- Customer internet services (internet-specific instances)
- Customer voice services (voice service instances)

Provides database operations with advanced querying, filtering, and relationship management.
"""

from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import and_, or_, desc, asc, func, text, case
from datetime import datetime, timezone, timedelta

from app.models.services import (
    ServiceTemplate, InternetServiceTemplate, VoiceServiceTemplate, BundleServiceTemplate,
    CustomerService, CustomerInternetService, CustomerVoiceService,
    ServiceProvisioning, ServiceStatusHistory, ServiceSuspension, ServiceUsageTracking,
    ServiceStatus, ServiceType
)
from app.models.customer import Customer
from app.models.devices import DeviceTemplate
from app.models.networking.networks import NetworkDevice, NetworkSite
from .base import BaseRepository


class CustomerServiceRepository(BaseRepository[CustomerService]):
    """Repository for customer service operations"""
    
    def __init__(self, db: Session):
        super().__init__(CustomerService, db)
    
    def get_customer_services(
        self, 
        customer_id: int,
        status: Optional[ServiceStatus] = None,
        service_type: Optional[ServiceType] = None
    ) -> List[CustomerService]:
        """Get all services for a customer with optional filtering"""
        query = self.db.query(CustomerService).filter(
            CustomerService.customer_id == customer_id
        )
        
        if status:
            query = query.filter(CustomerService.status == status)
        
        if service_type:
            query = query.filter(CustomerService.service_type == service_type)
        
        return query.options(
            joinedload(CustomerService.service_template),
            joinedload(CustomerService.customer)
        ).order_by(CustomerService.created_at.desc()).all()
    
    def get_active_services(self, customer_id: Optional[int] = None) -> List[CustomerService]:
        """Get all active services, optionally for a specific customer"""
        query = self.db.query(CustomerService).filter(
            CustomerService.status == ServiceStatus.ACTIVE
        )
        
        if customer_id:
            query = query.filter(CustomerService.customer_id == customer_id)
        
        return query.options(
            joinedload(CustomerService.service_template),
            joinedload(CustomerService.customer)
        ).all()
    
    def get_services_by_template(self, template_id: int) -> List[CustomerService]:
        """Get all services using a specific template"""
        return self.db.query(CustomerService).filter(
            CustomerService.template_id == template_id
        ).options(
            joinedload(CustomerService.customer)
        ).order_by(CustomerService.created_at.desc()).all()
    
    def get_services_for_billing(
        self,
        billing_cycle_start: datetime,
        billing_cycle_end: datetime,
        status: Optional[ServiceStatus] = None
    ) -> List[CustomerService]:
        """Get services that should be billed in a specific period"""
        query = self.db.query(CustomerService).filter(
            CustomerService.activated_at <= billing_cycle_end,
            or_(
                CustomerService.terminated_at.is_(None),
                CustomerService.terminated_at >= billing_cycle_start
            )
        )
        
        if status:
            query = query.filter(CustomerService.status == status)
        
        return query.options(
            joinedload(CustomerService.customer),
            joinedload(CustomerService.service_template)
        ).all()
    
    def get_expiring_services(self, days_ahead: int = 30) -> List[CustomerService]:
        """Get services expiring within specified days"""
        expiry_date = datetime.now(timezone.utc) + timedelta(days=days_ahead)
        
        return self.db.query(CustomerService).filter(
            CustomerService.expires_at.isnot(None),
            CustomerService.expires_at <= expiry_date,
            CustomerService.status.in_([ServiceStatus.ACTIVE, ServiceStatus.SUSPENDED])
        ).options(
            joinedload(CustomerService.customer),
            joinedload(CustomerService.service_template)
        ).order_by(CustomerService.expires_at).all()
    
    def search_services(
        self,
        search_term: Optional[str] = None,
        customer_id: Optional[int] = None,
        service_type: Optional[ServiceType] = None,
        status: Optional[ServiceStatus] = None,
        router_id: Optional[int] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[CustomerService], int]:
        """Search customer services with comprehensive filtering"""
        query = self.db.query(CustomerService)
        
        # Text search across customer and service details
        if search_term:
            query = query.join(Customer).filter(
                or_(
                    Customer.first_name.ilike(f"%{search_term}%"),
                    Customer.last_name.ilike(f"%{search_term}%"),
                    Customer.login.ilike(f"%{search_term}%"),
                    CustomerService.service_identifier.ilike(f"%{search_term}%")
                )
            )
        
        # Filter by customer
        if customer_id:
            query = query.filter(CustomerService.customer_id == customer_id)
        
        # Filter by service type
        if service_type:
            query = query.filter(CustomerService.service_type == service_type)
        
        # Filter by status
        if status:
            query = query.filter(CustomerService.status == status)
        
        # Filter by router
        if router_id:
            query = query.filter(CustomerService.router_id == router_id)
        
        # Filter by date range
        if date_from:
            query = query.filter(CustomerService.created_at >= date_from)
        
        if date_to:
            query = query.filter(CustomerService.created_at <= date_to)
        
        # Get total count
        total = query.count()
        
        # Apply pagination and ordering
        services = query.options(
            joinedload(CustomerService.customer),
            joinedload(CustomerService.service_template)
        ).order_by(
            CustomerService.created_at.desc()
        ).offset(offset).limit(limit).all()
        
        return services, total
    
    def get_service_statistics(self) -> Dict[str, Any]:
        """Get comprehensive service statistics"""
        stats = {}
        
        # Total services
        stats['total_services'] = self.db.query(CustomerService).count()
        
        # Services by status
        status_stats = self.db.query(
            CustomerService.status,
            func.count(CustomerService.id).label('count')
        ).group_by(CustomerService.status).all()
        
        stats['by_status'] = {str(status[0]): status[1] for status in status_stats}
        
        # Services by type
        type_stats = self.db.query(
            CustomerService.service_type,
            func.count(CustomerService.id).label('count')
        ).group_by(CustomerService.service_type).all()
        
        stats['by_type'] = {str(type_stat[0]): type_stat[1] for type_stat in type_stats}
        
        # Active services
        stats['active_services'] = self.db.query(CustomerService).filter(
            CustomerService.status == ServiceStatus.ACTIVE
        ).count()
        
        # Services activated this month
        month_start = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        stats['activated_this_month'] = self.db.query(CustomerService).filter(
            CustomerService.activated_at >= month_start
        ).count()
        
        # Average service duration for terminated services
        avg_duration = self.db.query(
            func.avg(
                func.extract('epoch', CustomerService.terminated_at - CustomerService.activated_at) / 86400
            )
        ).filter(
            CustomerService.terminated_at.isnot(None)
        ).scalar()
        
        stats['average_service_duration_days'] = float(avg_duration) if avg_duration else 0.0
        
        return stats


class CustomerInternetServiceRepository(BaseRepository[CustomerInternetService]):
    """Repository for customer internet service operations"""
    
    def __init__(self, db: Session):
        super().__init__(CustomerInternetService, db)
    
    def get_by_pppoe_username(self, username: str) -> Optional[CustomerInternetService]:
        """Get internet service by PPPoE username"""
        return self.db.query(CustomerInternetService).filter(
            CustomerInternetService.pppoe_username == username
        ).first()
    
    def get_by_ip_address(self, ip_address: str) -> Optional[CustomerInternetService]:
        """Get internet service by assigned IP address"""
        return self.db.query(CustomerInternetService).filter(
            CustomerInternetService.assigned_ip == ip_address
        ).first()
    
    def get_services_with_fup_exceeded(self) -> List[CustomerInternetService]:
        """Get internet services that have exceeded FUP limits"""
        return self.db.query(CustomerInternetService).join(CustomerService).filter(
            CustomerService.status == ServiceStatus.ACTIVE,
            CustomerInternetService.fup_exceeded == True
        ).options(
            joinedload(CustomerInternetService.customer_service).joinedload(CustomerService.customer)
        ).all()
    
    def get_services_by_speed_profile(
        self, 
        min_download: Optional[int] = None,
        max_download: Optional[int] = None
    ) -> List[CustomerInternetService]:
        """Get internet services by speed profile"""
        query = self.db.query(CustomerInternetService).join(CustomerService).filter(
            CustomerService.status == ServiceStatus.ACTIVE
        )
        
        if min_download:
            query = query.filter(CustomerInternetService.current_download_speed >= min_download)
        
        if max_download:
            query = query.filter(CustomerInternetService.current_download_speed <= max_download)
        
        return query.options(
            joinedload(CustomerInternetService.customer_service).joinedload(CustomerService.customer)
        ).all()
    
    def get_services_by_router(self, router_id: int) -> List[CustomerInternetService]:
        """Get all internet services on a specific router"""
        return self.db.query(CustomerInternetService).join(CustomerService).filter(
            CustomerService.router_id == router_id,
            CustomerService.status == ServiceStatus.ACTIVE
        ).options(
            joinedload(CustomerInternetService.customer_service).joinedload(CustomerService.customer)
        ).all()
    
    def get_usage_statistics(self, days: int = 30) -> Dict[str, Any]:
        """Get internet service usage statistics"""
        stats = {}
        
        # Total internet services
        stats['total_internet_services'] = self.db.query(CustomerInternetService).count()
        
        # Services with FUP exceeded
        stats['fup_exceeded_services'] = self.db.query(CustomerInternetService).filter(
            CustomerInternetService.fup_exceeded == True
        ).count()
        
        # Average speeds
        avg_download = self.db.query(
            func.avg(CustomerInternetService.current_download_speed)
        ).scalar()
        
        avg_upload = self.db.query(
            func.avg(CustomerInternetService.current_upload_speed)
        ).scalar()
        
        stats['average_download_speed'] = float(avg_download) if avg_download else 0.0
        stats['average_upload_speed'] = float(avg_upload) if avg_upload else 0.0
        
        # Connection types distribution
        connection_stats = self.db.query(
            CustomerInternetService.connection_type,
            func.count(CustomerInternetService.id).label('count')
        ).group_by(CustomerInternetService.connection_type).all()
        
        stats['by_connection_type'] = {str(conn[0]): conn[1] for conn in connection_stats}
        
        return stats


class CustomerVoiceServiceRepository(BaseRepository[CustomerVoiceService]):
    """Repository for customer voice service operations"""
    
    def __init__(self, db: Session):
        super().__init__(CustomerVoiceService, db)
    
    def get_by_phone_number(self, phone_number: str) -> Optional[CustomerVoiceService]:
        """Get voice service by phone number"""
        return self.db.query(CustomerVoiceService).filter(
            CustomerVoiceService.phone_numbers.contains([phone_number])
        ).first()
    
    def get_by_sip_username(self, sip_username: str) -> Optional[CustomerVoiceService]:
        """Get voice service by SIP username"""
        return self.db.query(CustomerVoiceService).filter(
            CustomerVoiceService.sip_username == sip_username
        ).first()
    
    def get_services_with_low_balance(self, threshold: float = 5.0) -> List[CustomerVoiceService]:
        """Get voice services with balance below threshold"""
        return self.db.query(CustomerVoiceService).join(CustomerService).filter(
            CustomerService.status == ServiceStatus.ACTIVE,
            CustomerVoiceService.current_balance < threshold
        ).options(
            joinedload(CustomerVoiceService.customer_service).joinedload(CustomerService.customer)
        ).all()
    
    def get_services_with_exceeded_minutes(self) -> List[CustomerVoiceService]:
        """Get voice services that have exceeded included minutes"""
        return self.db.query(CustomerVoiceService).join(CustomerService).filter(
            CustomerService.status == ServiceStatus.ACTIVE,
            CustomerVoiceService.used_minutes > CustomerVoiceService.included_minutes
        ).options(
            joinedload(CustomerVoiceService.customer_service).joinedload(CustomerService.customer)
        ).all()
    
    def get_call_statistics(self, days: int = 30) -> Dict[str, Any]:
        """Get voice service call statistics"""
        stats = {}
        
        # Total voice services
        stats['total_voice_services'] = self.db.query(CustomerVoiceService).count()
        
        # Total minutes used
        total_minutes = self.db.query(
            func.sum(CustomerVoiceService.used_minutes)
        ).scalar()
        
        stats['total_minutes_used'] = float(total_minutes) if total_minutes else 0.0
        
        # Average minutes per service
        avg_minutes = self.db.query(
            func.avg(CustomerVoiceService.used_minutes)
        ).scalar()
        
        stats['average_minutes_per_service'] = float(avg_minutes) if avg_minutes else 0.0
        
        # Services exceeding included minutes
        stats['services_exceeding_minutes'] = self.db.query(CustomerVoiceService).filter(
            CustomerVoiceService.used_minutes > CustomerVoiceService.included_minutes
        ).count()
        
        # Total balance across all services
        total_balance = self.db.query(
            func.sum(CustomerVoiceService.current_balance)
        ).scalar()
        
        stats['total_balance'] = float(total_balance) if total_balance else 0.0
        
        return stats


# Repository factory for service instances
class ServiceInstanceRepositoryFactory:
    """Factory for creating service instance repositories"""
    
    @staticmethod
    def create_customer_service_repo(db: Session) -> CustomerServiceRepository:
        return CustomerServiceRepository(db)
    
    @staticmethod
    def create_internet_service_repo(db: Session) -> CustomerInternetServiceRepository:
        return CustomerInternetServiceRepository(db)
    
    @staticmethod
    def create_voice_service_repo(db: Session) -> CustomerVoiceServiceRepository:
        return CustomerVoiceServiceRepository(db)
    
    @staticmethod
    def create_all_repos(db: Session) -> Dict[str, Any]:
        """Create all service instance repositories"""
        return {
            'customer_service': CustomerServiceRepository(db),
            'internet_service': CustomerInternetServiceRepository(db),
            'voice_service': CustomerVoiceServiceRepository(db)
        }


# Utility functions for service instance operations
class ServiceInstanceUtils:
    """Utility functions for service instance operations"""
    
    @staticmethod
    def generate_service_identifier(service_type: ServiceType, customer_id: int) -> str:
        """Generate unique service identifier"""
        timestamp = int(datetime.now(timezone.utc).timestamp())
        return f"{service_type.value.upper()}-{customer_id:06d}-{timestamp}"
    
    @staticmethod
    def generate_pppoe_username(customer_login: str, service_id: int) -> str:
        """Generate PPPoE username for internet service"""
        return f"{customer_login}-inet-{service_id}"
    
    @staticmethod
    def generate_sip_username(customer_login: str, service_id: int) -> str:
        """Generate SIP username for voice service"""
        return f"{customer_login}-voice-{service_id}"
    
    @staticmethod
    def calculate_prorated_amount(
        monthly_amount: float,
        start_date: datetime,
        end_date: datetime
    ) -> float:
        """Calculate prorated amount for partial billing period"""
        days_in_period = (end_date - start_date).days + 1
        days_in_month = 30  # Standard ISP billing month
        
        return (monthly_amount / days_in_month) * days_in_period
