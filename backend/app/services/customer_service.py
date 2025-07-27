from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
from app.repositories.customer_service import CustomerServiceRepository
from app.repositories.service_plan import ServicePlanRepository
from app.repositories.customer import CustomerRepository
from app.schemas.customer_service import (
    CustomerServiceCreate, CustomerServiceUpdate, CustomerServiceSearch,
    ServiceProvisioningRequest, CustomerServicesOverview, ServicePlanAssignments
)
from app.core.exceptions import NotFoundError, DuplicateError, ValidationError
from app.services.webhook_integration_service import WebhookTriggers
import logging

logger = logging.getLogger(__name__)


class CustomerServiceService:
    """Service layer for customer service assignment business logic."""
    
    def __init__(self, db: Session):
        self.db = db
        self.webhook_triggers = WebhookTriggers(db)
        self.customer_service_repo = CustomerServiceRepository(db)
        self.service_plan_repo = ServicePlanRepository(db)
        self.customer_repo = CustomerRepository(db)
    
    def get_customer_service(self, service_id: int):
        """Get a customer service assignment by ID with full details."""
        service = self.customer_service_repo.get_with_details(service_id)
        if not service:
            raise NotFoundError(f"Customer service with id {service_id} not found")
        
        # Calculate effective price
        effective_price = service.custom_price or service.service_plan.price
        if service.discount_percentage:
            effective_price = int(effective_price * (100 - service.discount_percentage) / 100)
        
        # Add calculated fields
        service.effective_price = effective_price
        service.monthly_cost = effective_price  # For monthly billing cycle
        
        logger.info(f"Retrieved customer service: {service_id}")
        return service
    
    def create_customer_service(self, service_data: CustomerServiceCreate, admin_id: int):
        """Create a new customer service assignment with comprehensive validation."""
        try:
            # Validate customer exists
            customer = self.customer_repo.get(service_data.customer_id)
            if not customer:
                raise NotFoundError(f"Customer with id {service_data.customer_id} not found")
            
            # Validate service plan exists and is active
            service_plan = self.service_plan_repo.get(service_data.service_plan_id)
            if not service_plan:
                raise NotFoundError(f"Service plan with id {service_data.service_plan_id} not found")
            
            if not service_plan.is_active:
                raise ValidationError("Cannot assign inactive service plan")
            
            # Check for existing active service (prevent duplicates)
            existing_service = self.customer_service_repo.get_customer_active_service(
                service_data.customer_id, service_data.service_plan_id
            )
            if existing_service:
                raise DuplicateError(
                    f"Customer {service_data.customer_id} already has an active service "
                    f"for plan {service_data.service_plan_id}"
                )
            
            # Prepare service data
            service_dict = service_data.dict()
            
            # Set default start date if not provided
            if not service_dict.get("start_date"):
                service_dict["start_date"] = datetime.now(timezone.utc)
            
            # Create the customer service assignment
            customer_service = self.customer_service_repo.create(service_dict)
            
            # Trigger webhook event
            try:
                self.webhook_triggers.customer_service_created({
                    'id': customer_service.id,
                    'customer_id': customer_service.customer_id,
                    'service_plan_id': customer_service.service_plan_id,
                    'start_date': customer_service.start_date.isoformat(),
                    'custom_price': customer_service.custom_price,
                    'discount_percentage': customer_service.discount_percentage,
                    'status': customer_service.status.value,
                    'created_at': customer_service.created_at.isoformat()
                })
            except Exception as e:
                logger.warning(f"Failed to trigger customer_service.created webhook: {e}")
            
            logger.info(
                f"Customer service created: Customer {service_data.customer_id} "
                f"assigned to plan {service_data.service_plan_id} (ID: {customer_service.id})"
            )
            
            return customer_service
            
        except Exception as e:
            logger.error(f"Error creating customer service: {str(e)}")
            raise
    
    def update_customer_service(self, service_id: int, service_data: CustomerServiceUpdate, admin_id: int):
        """Update an existing customer service assignment."""
        try:
            # Check if service exists
            existing_service = self.customer_service_repo.get(service_id)
            if not existing_service:
                raise NotFoundError(f"Customer service with id {service_id} not found")
            
            # Prepare update data (only non-None values)
            update_dict = {k: v for k, v in service_data.dict().items() if v is not None}
            
            if not update_dict:
                return existing_service
            
            # Update the service
            updated_service = self.customer_service_repo.update(service_id, update_dict)
            
            # Trigger webhook event
            try:
                self.webhook_triggers.customer_service_updated({
                    'id': updated_service.id,
                    'customer_id': updated_service.customer_id,
                    'service_plan_id': updated_service.service_plan_id,
                    'start_date': updated_service.start_date.isoformat(),
                    'custom_price': updated_service.custom_price,
                    'discount_percentage': updated_service.discount_percentage,
                    'status': updated_service.status.value,
                    'updated_at': updated_service.updated_at.isoformat()
                })
            except Exception as e:
                logger.warning(f"Failed to trigger customer_service.updated webhook: {e}")
            
            logger.info(f"Customer service updated: {service_id}")
            return updated_service
            
        except Exception as e:
            logger.error(f"Error updating customer service {service_id}: {str(e)}")
            raise
    
    def search_customer_services(self, search_params: CustomerServiceSearch):
        """Search customer services with comprehensive filtering and pagination."""
        try:
            search_dict = search_params.dict()
            services, total_count = self.customer_service_repo.search_customer_services(search_dict)
            
            # Calculate effective prices for all services
            for service in services:
                effective_price = service.custom_price or service.service_plan.price
                if service.discount_percentage:
                    effective_price = int(effective_price * (100 - service.discount_percentage) / 100)
                service.effective_price = effective_price
                service.monthly_cost = effective_price
            
            has_more = (search_params.offset + len(services)) < total_count
            
            return {
                "services": services,
                "total_count": total_count,
                "limit": search_params.limit,
                "offset": search_params.offset,
                "has_more": has_more
            }
            
        except Exception as e:
            logger.error(f"Error searching customer services: {str(e)}")
            raise
    
    def get_customer_services_overview(self, customer_id: int) -> CustomerServicesOverview:
        """Get comprehensive overview of all customer's services."""
        try:
            # Validate customer exists
            customer = self.customer_repo.get(customer_id)
            if not customer:
                raise NotFoundError(f"Customer with id {customer_id} not found")
            
            overview_data = self.customer_service_repo.get_customer_services_overview(customer_id)
            
            # Trigger webhook event
            try:
                self.webhook_triggers.customer_services_overview({
                    'customer_id': customer_id,
                    'services': overview_data['services'],
                    'total_services': overview_data['total_services'],
                    'total_cost': overview_data['total_cost'],
                    'updated_at': overview_data['updated_at'].isoformat()
                })
            except Exception as e:
                logger.warning(f"Failed to trigger customer_services.overview webhook: {e}")
            
            logger.info(f"Retrieved customer services overview for customer: {customer_id}")
            return CustomerServicesOverview(**overview_data)
            
        except Exception as e:
            logger.error(f"Error getting customer services overview for {customer_id}: {str(e)}")
            raise
    
    def get_service_plan_assignments(self, service_plan_id: int) -> ServicePlanAssignments:
        """Get all customer assignments for a specific service plan."""
        try:
            # Validate service plan exists
            service_plan = self.service_plan_repo.get(service_plan_id)
            if not service_plan:
                raise NotFoundError(f"Service plan with id {service_plan_id} not found")
            
            overview_data = self.customer_service_repo.get_service_plan_assignments_overview(service_plan_id)
            overview_data["service_plan_name"] = service_plan.name
            
            logger.info(f"Retrieved service plan assignments for plan: {service_plan_id}")
            return ServicePlanAssignments(**overview_data)
            
        except Exception as e:
            logger.error(f"Error getting service plan assignments for {service_plan_id}: {str(e)}")
            raise
    
    def provision_service(self, provision_request: ServiceProvisioningRequest, admin_id: int):
        """Provision a new service for a customer with advanced workflow."""
        try:
            # Create the service assignment
            service_data = CustomerServiceCreate(
                customer_id=provision_request.customer_id,
                service_plan_id=provision_request.service_plan_id,
                start_date=provision_request.start_date,
                custom_price=provision_request.custom_price,
                discount_percentage=provision_request.discount_percentage,
                status="pending"  # Start as pending for provisioning workflow
            )
            
            customer_service = self.create_customer_service(service_data, admin_id)
            
            # Simulate provisioning workflow
            provisioning_status = "provisioning_initiated"
            estimated_activation = datetime.now(timezone.utc) + timedelta(hours=2)  # 2 hours for activation
            
            logger.info(
                f"Service provisioning initiated: Customer {provision_request.customer_id} "
                f"for plan {provision_request.service_plan_id}"
            )
            
            return {
                "customer_service": customer_service,
                "provisioning_status": provisioning_status,
                "provisioning_notes": provision_request.notes,
                "estimated_activation": estimated_activation
            }
            
        except Exception as e:
            logger.error(f"Error provisioning service: {str(e)}")
            raise
    
    def activate_service(self, service_id: int, admin_id: int):
        """Activate a customer service."""
        try:
            service = self.customer_service_repo.activate_service(service_id)
            if not service:
                raise NotFoundError(f"Customer service with id {service_id} not found")
            
            logger.info(f"Customer service activated: {service_id} by admin {admin_id}")
            return service
            
        except Exception as e:
            logger.error(f"Error activating customer service {service_id}: {str(e)}")
            raise
    
    def suspend_service(self, service_id: int, admin_id: int):
        """Suspend a customer service."""
        try:
            service = self.customer_service_repo.suspend_service(service_id)
            if not service:
                raise NotFoundError(f"Customer service with id {service_id} not found")
            
            logger.info(f"Customer service suspended: {service_id} by admin {admin_id}")
            return service
            
        except Exception as e:
            logger.error(f"Error suspending customer service {service_id}: {str(e)}")
            raise
    
    def terminate_service(self, service_id: int, admin_id: int, end_date: Optional[datetime] = None):
        """Terminate a customer service."""
        try:
            service = self.customer_service_repo.terminate_service(service_id, end_date)
            if not service:
                raise NotFoundError(f"Customer service with id {service_id} not found")
            
            logger.info(f"Customer service terminated: {service_id} by admin {admin_id}")
            return service
            
        except Exception as e:
            logger.error(f"Error terminating customer service {service_id}: {str(e)}")
            raise
    
    def get_expiring_services(self, days_ahead: int = 30):
        """Get services that will expire within specified days."""
        try:
            services = self.customer_service_repo.get_expiring_services(days_ahead)
            
            logger.info(f"Retrieved {len(services)} services expiring within {days_ahead} days")
            return services
            
        except Exception as e:
            logger.error(f"Error getting expiring services: {str(e)}")
            raise
    
    def get_revenue_analytics(self, service_plan_id: Optional[int] = None):
        """Get revenue analytics by service plan."""
        try:
            revenue_data = self.customer_service_repo.get_revenue_by_service_plan(service_plan_id)
            
            logger.info(f"Retrieved revenue analytics for {'all plans' if not service_plan_id else f'plan {service_plan_id}'}")
            return revenue_data
            
        except Exception as e:
            logger.error(f"Error getting revenue analytics: {str(e)}")
            raise
    
    def bulk_status_update(self, service_ids: List[int], new_status: str, admin_id: int):
        """Update status for multiple customer services."""
        try:
            updated_services = []
            
            for service_id in service_ids:
                if new_status == "active":
                    service = self.activate_service(service_id, admin_id)
                elif new_status == "suspended":
                    service = self.suspend_service(service_id, admin_id)
                elif new_status == "terminated":
                    service = self.terminate_service(service_id, admin_id)
                else:
                    raise ValidationError(f"Invalid status: {new_status}")
                
                updated_services.append(service)
            
            logger.info(f"Bulk status update completed: {len(updated_services)} services updated to {new_status}")
            return updated_services
            
        except Exception as e:
            logger.error(f"Error in bulk status update: {str(e)}")
            raise
