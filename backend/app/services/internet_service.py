"""
Internet Service Business Logic

Service layer for Internet service management including:
- Service creation and lifecycle management
- Provisioning queue integration
- RADIUS integration for PPPoE authentication
- IP address allocation and management
- Usage tracking and analytics
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from app.repositories.customer import CustomerRepository
from app.schemas.internet_service import (
    InternetServiceCreate, InternetServiceUpdate, InternetServiceList,
    InternetServiceProvisioningRequest, InternetService, InternetServiceSummary
)
from app.core.exceptions import NotFoundError
from app.services.webhook_integration_service import WebhookTriggers
from app.services.portal_id import PortalIDService
import logging

logger = logging.getLogger(__name__)


class InternetServiceService:
    """Service layer for Internet service business logic."""
    
    def __init__(self, db: Session):
        self.db = db
        self.customer_repo = CustomerRepository(db)
        self.portal_id_service = PortalIDService(db)
        self.webhook_triggers = WebhookTriggers(db)
    
    def create_internet_service(self, customer_id: int, service_data: InternetServiceCreate) -> InternetService:
        """Create a new Internet service for a customer."""
        # Validate customer exists
        customer = self.customer_repo.get(customer_id)
        if not customer:
            raise NotFoundError(f"Customer with id {customer_id} not found")
        
        # Validate tariff plan exists (placeholder - implement when tariff repository is available)
        # tariff_plan = self.tariff_repo.get(service_data.tariff_plan_id)
        # if not tariff_plan:
        #     raise NotFoundError(f"Tariff plan with id {service_data.tariff_plan_id} not found")
        
        try:
            # Generate portal username for PPPoE authentication
            portal_username = self._generate_portal_username(customer_id)
            
            # Create service record
            service_dict = service_data.model_dump()
            service_dict.update({
                "customer_id": customer_id,
                "status": "pending",
                "portal_username": portal_username,
                "created_at": datetime.now(timezone.utc)
            })
            
            # Create service in database (placeholder - implement when service repository is available)
            # service = self.internet_service_repo.create(service_dict)
            
            # For now, return a mock service object
            service = InternetService(
                id=1,  # Mock ID
                customer_id=customer_id,
                **service_dict
            )
            
            # Trigger webhook event
            try:
                self.webhook_triggers.service_created({
                    'service_id': service.id,
                    'customer_id': customer_id,
                    'service_type': 'internet',
                    'status': service.status,
                    'created_at': service.created_at.isoformat()
                })
            except Exception as e:
                logger.warning(f"Failed to trigger service.created webhook: {e}")
            
            logger.info(f"Created Internet service {service.id} for customer {customer_id}")
            return service
            
        except Exception as e:
            logger.error(f"Error creating Internet service: {e}")
            raise
    
    def get_service(self, service_id: int) -> InternetService:
        """Get an Internet service by ID."""
        # Placeholder - implement when service repository is available
        # service = self.internet_service_repo.get(service_id)
        # if not service:
        #     raise NotFoundError(f"Internet service with id {service_id} not found")
        # return service
        
        # Mock implementation
        if service_id <= 0:
            raise NotFoundError(f"Internet service with id {service_id} not found")
        
        return InternetService(
            id=service_id,
            customer_id=1,
            tariff_plan_id=1,
            speed_config={
                "download_mbps": 100,
                "upload_mbps": 10
            },
            status="active",
            portal_username=f"user{service_id}",
            created_at=datetime.now(timezone.utc)
        )
    
    def update_service(self, service_id: int, service_data: InternetServiceUpdate) -> InternetService:
        """Update an existing Internet service."""
        # Get existing service
        service = self.get_service(service_id)
        
        try:
            # Update service fields
            update_dict = service_data.model_dump(exclude_unset=True)
            update_dict["updated_at"] = datetime.now(timezone.utc)
            
            # Placeholder - implement when service repository is available
            # updated_service = self.internet_service_repo.update(service_id, update_dict)
            
            # Mock implementation
            for key, value in update_dict.items():
                if hasattr(service, key):
                    setattr(service, key, value)
            
            # Trigger webhook event if status changed
            if "status" in update_dict:
                try:
                    self.webhook_triggers.service_status_changed({
                        'service_id': service_id,
                        'customer_id': service.customer_id,
                        'service_type': 'internet',
                        'old_status': 'active',  # Placeholder
                        'new_status': update_dict["status"],
                        'updated_at': update_dict["updated_at"].isoformat()
                    })
                except Exception as e:
                    logger.warning(f"Failed to trigger service.status_changed webhook: {e}")
            
            logger.info(f"Updated Internet service {service_id}")
            return service
            
        except Exception as e:
            logger.error(f"Error updating Internet service {service_id}: {e}")
            raise
    
    def list_customer_services(self, customer_id: int, active_only: bool = True) -> List[InternetServiceSummary]:
        """List all Internet services for a specific customer."""
        # Validate customer exists
        customer = self.customer_repo.get(customer_id)
        if not customer:
            raise NotFoundError(f"Customer with id {customer_id} not found")
        
        # Placeholder - implement when service repository is available
        # filters = {"customer_id": customer_id}
        # if active_only:
        #     filters["status"] = "active"
        # services = self.internet_service_repo.get_all(filters=filters)
        
        # Mock implementation
        services = [
            InternetServiceSummary(
                id=1,
                customer_id=customer_id,
                customer_name=customer.name,
                tariff_plan_name="100 Mbps Residential",
                status="active",
                speed_config={
                    "download_mbps": 100,
                    "upload_mbps": 10
                },
                assigned_ip="192.168.1.100",
                monthly_fee=89.99,
                activation_date=datetime.now(timezone.utc),
                created_at=datetime.now(timezone.utc)
            )
        ]
        
        return services
    
    def list_all_services(
        self, 
        page: int = 1, 
        per_page: int = 25,
        status: Optional[str] = None,
        tariff_id: Optional[int] = None
    ) -> InternetServiceList:
        """List all Internet services with pagination and filtering."""
        # Placeholder - implement when service repository is available
        # filters = {}
        # if status:
        #     filters["status"] = status
        # if tariff_id:
        #     filters["tariff_plan_id"] = tariff_id
        
        # skip = (page - 1) * per_page
        # services = self.internet_service_repo.get_all(skip=skip, limit=per_page, filters=filters)
        # total = self.internet_service_repo.count(filters=filters)
        
        # Mock implementation
        services = [
            InternetServiceSummary(
                id=1,
                customer_id=1,
                customer_name="John Doe",
                tariff_plan_name="100 Mbps Residential",
                status="active",
                speed_config={
                    "download_mbps": 100,
                    "upload_mbps": 10
                },
                assigned_ip="192.168.1.100",
                monthly_fee=89.99,
                activation_date=datetime.now(timezone.utc),
                created_at=datetime.now(timezone.utc)
            )
        ]
        
        total = len(services)
        pages = ((total - 1) // per_page) + 1 if total > 0 else 0
        
        return InternetServiceList(
            services=services,
            total=total,
            page=page,
            per_page=per_page,
            pages=pages
        )
    
    def queue_provisioning(self, service_id: int, provision_request: InternetServiceProvisioningRequest) -> Dict[str, Any]:
        """Queue Internet service for provisioning."""
        # Get service
        service = self.get_service(service_id)
        
        try:
            # Create provisioning job
            {
                "service_id": service_id,
                "service_type": "internet",
                "customer_id": service.customer_id,
                "priority": provision_request.priority,
                "scheduled_for": provision_request.scheduled_for or datetime.now(timezone.utc),
                "auto_activate": provision_request.auto_activate,
                "router_id": provision_request.router_id,
                "ip_pool_id": provision_request.ip_pool_id,
                "vlan_id": provision_request.vlan_id,
                "status": "queued",
                "created_at": datetime.now(timezone.utc)
            }
            
            # Placeholder - implement when provisioning queue is available
            # job = self.provisioning_queue.create_job(job_data)
            
            # Update service status to provisioning
            self.update_service(service_id, InternetServiceUpdate(status="provisioning"))
            
            # Mock response
            return {
                "job_id": f"job_{service_id}_{datetime.now().timestamp()}",
                "estimated_completion": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error queuing provisioning for service {service_id}: {e}")
            raise
    
    def suspend_service(self, service_id: int, reason: str, admin_id: int) -> Dict[str, Any]:
        """Suspend an Internet service."""
        # Get service
        service = self.get_service(service_id)
        
        try:
            # Create suspension record
            {
                "service_id": service_id,
                "reason": reason,
                "suspended_by": admin_id,
                "suspended_at": datetime.now(timezone.utc),
                "is_active": True
            }
            
            # Placeholder - implement when suspension repository is available
            # suspension = self.suspension_repo.create(suspension_data)
            
            # Update service status
            self.update_service(service_id, InternetServiceUpdate(
                status="suspended",
                suspension_date=datetime.now(timezone.utc)
            ))
            
            # Trigger webhook event
            try:
                self.webhook_triggers.service_suspended({
                    'service_id': service_id,
                    'customer_id': service.customer_id,
                    'service_type': 'internet',
                    'reason': reason,
                    'suspended_at': datetime.now(timezone.utc).isoformat()
                })
            except Exception as e:
                logger.warning(f"Failed to trigger service.suspended webhook: {e}")
            
            return {"suspension_id": f"susp_{service_id}_{datetime.now().timestamp()}"}
            
        except Exception as e:
            logger.error(f"Error suspending service {service_id}: {e}")
            raise
    
    def reactivate_service(self, service_id: int, admin_id: int) -> Dict[str, Any]:
        """Reactivate a suspended Internet service."""
        # Get service
        service = self.get_service(service_id)
        
        try:
            # Update service status
            self.update_service(service_id, InternetServiceUpdate(
                status="active",
                suspension_date=None
            ))
            
            # Mark suspension as inactive (placeholder)
            # self.suspension_repo.deactivate_by_service_id(service_id)
            
            # Trigger webhook event
            try:
                self.webhook_triggers.service_reactivated({
                    'service_id': service_id,
                    'customer_id': service.customer_id,
                    'service_type': 'internet',
                    'reactivated_at': datetime.now(timezone.utc).isoformat()
                })
            except Exception as e:
                logger.warning(f"Failed to trigger service.reactivated webhook: {e}")
            
            return {"message": "Service reactivated successfully"}
            
        except Exception as e:
            logger.error(f"Error reactivating service {service_id}: {e}")
            raise
    
    def _generate_portal_username(self, customer_id: int) -> str:
        """Generate a unique portal username for PPPoE authentication."""
        # Use customer's portal ID as base for username
        customer = self.customer_repo.get(customer_id)
        if customer and customer.portal_id:
            return customer.portal_id.lower()
        
        # Fallback to customer ID
        return f"user{customer_id}"
