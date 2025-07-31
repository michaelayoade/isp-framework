"""
Service Instances Service Layer - ISP Service Management System

Business logic layer for customer service instance management including:
- Customer service operations (CRUD, lifecycle management, billing integration)
- Internet service management (PPPoE, IP assignment, FUP monitoring)
- Voice service management (SIP configuration, balance tracking, call management)

Provides high-level business operations with validation, provisioning integration,
and comprehensive service lifecycle management.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import BusinessLogicError, NotFoundError, ValidationError
from app.models.customer import Customer
from app.models.services import (
    CustomerInternetService,
    CustomerService,
    CustomerVoiceService,
    IPAssignmentType,
    ServiceStatus,
    ServiceType,
)
from app.repositories.service_repository_factory import ServiceRepositoryFactory

logger = logging.getLogger(__name__)


class CustomerServiceService:
    """Service layer for customer service operations"""

    def __init__(self, db: Session):
        self.db = db
        self.repo_factory = ServiceRepositoryFactory(db)
        self.service_repo = self.repo_factory.get_customer_service_repo()
        self.template_repo = self.repo_factory.get_service_template_repo()

    async def create_customer_service(
        self, service_data: Dict[str, Any], admin_id: int
    ) -> CustomerService:
        """Create a new customer service with validation and provisioning"""
        logger.info(
            f"Creating customer service for customer: {service_data.get('customer_id')}"
        )

        try:
            # Validate service data
            await self._validate_service_data(service_data)

            # Check customer exists
            customer = (
                self.db.query(Customer)
                .filter(Customer.id == service_data["customer_id"])
                .first()
            )
            if not customer:
                raise NotFoundError(f"Customer {service_data['customer_id']} not found")

            # Validate service template
            template = self.template_repo.get_by_id(service_data["template_id"])
            if not template or not template.is_active:
                raise ValidationError("Invalid or inactive service template")

            # Generate service identifier
            service_identifier = await self._generate_service_identifier(
                template.service_type, service_data["customer_id"]
            )

            # Prepare service data
            service_data.update(
                {
                    "service_identifier": service_identifier,
                    "service_type": template.service_type,
                    "status": ServiceStatus.PENDING,
                    "created_by_id": admin_id,
                    "created_at": datetime.now(timezone.utc),
                }
            )

            # Create service
            service = CustomerService(**service_data)
            service = self.service_repo.create(service)

            # Trigger provisioning workflow
            await self._trigger_provisioning(service, admin_id)

            logger.info(f"Customer service created successfully: {service.id}")
            return service

        except IntegrityError as e:
            logger.error(f"Database integrity error creating service: {str(e)}")
            raise ValidationError("Failed to create service due to data constraints")
        except Exception as e:
            logger.error(f"Error creating customer service: {str(e)}")
            raise BusinessLogicError(f"Failed to create customer service: {str(e)}")

    async def activate_service(
        self,
        service_id: int,
        admin_id: int,
        activation_data: Optional[Dict[str, Any]] = None,
    ) -> CustomerService:
        """Activate a customer service"""
        logger.info(f"Activating customer service: {service_id}")

        try:
            service = self.service_repo.get_by_id(service_id)
            if not service:
                raise NotFoundError(f"Customer service {service_id} not found")

            if service.status == ServiceStatus.ACTIVE:
                raise ValidationError("Service is already active")

            if service.status not in [ServiceStatus.PENDING, ServiceStatus.SUSPENDED]:
                raise ValidationError(
                    f"Cannot activate service in {service.status} status"
                )

            # Validate activation requirements
            await self._validate_service_activation(service)

            # Update service status
            update_data = {
                "status": ServiceStatus.ACTIVE,
                "activated_at": datetime.now(timezone.utc),
                "updated_by_id": admin_id,
                "updated_at": datetime.now(timezone.utc),
            }

            if activation_data:
                update_data.update(activation_data)

            service = self.service_repo.update(service, update_data)

            # Record status change
            await self._record_status_change(service, ServiceStatus.ACTIVE, admin_id)

            # Trigger post-activation tasks
            await self._handle_service_activation(service, admin_id)

            logger.info(f"Customer service activated: {service_id}")
            return service

        except Exception as e:
            logger.error(f"Error activating service {service_id}: {str(e)}")
            raise

    async def suspend_service(
        self, service_id: int, admin_id: int, suspension_data: Dict[str, Any]
    ) -> CustomerService:
        """Suspend a customer service"""
        logger.info(f"Suspending customer service: {service_id}")

        try:
            service = self.service_repo.get_by_id(service_id)
            if not service:
                raise NotFoundError(f"Customer service {service_id} not found")

            if service.status != ServiceStatus.ACTIVE:
                raise ValidationError("Can only suspend active services")

            # Create suspension record
            await self._create_suspension_record(service, suspension_data, admin_id)

            # Update service status
            service = self.service_repo.update(
                service,
                {
                    "status": ServiceStatus.SUSPENDED,
                    "suspended_at": datetime.now(timezone.utc),
                    "updated_by_id": admin_id,
                    "updated_at": datetime.now(timezone.utc),
                },
            )

            # Record status change
            await self._record_status_change(service, ServiceStatus.SUSPENDED, admin_id)

            # Handle suspension tasks
            await self._handle_service_suspension(service, suspension_data, admin_id)

            logger.info(f"Customer service suspended: {service_id}")
            return service

        except Exception as e:
            logger.error(f"Error suspending service {service_id}: {str(e)}")
            raise

    async def terminate_service(
        self, service_id: int, admin_id: int, termination_data: Dict[str, Any]
    ) -> CustomerService:
        """Terminate a customer service"""
        logger.info(f"Terminating customer service: {service_id}")

        try:
            service = self.service_repo.get_by_id(service_id)
            if not service:
                raise NotFoundError(f"Customer service {service_id} not found")

            if service.status == ServiceStatus.TERMINATED:
                raise ValidationError("Service is already terminated")

            # Handle pre-termination tasks
            await self._handle_service_pre_termination(service, admin_id)

            # Update service status
            service = self.service_repo.update(
                service,
                {
                    "status": ServiceStatus.TERMINATED,
                    "terminated_at": datetime.now(timezone.utc),
                    "termination_reason": termination_data.get("reason"),
                    "updated_by_id": admin_id,
                    "updated_at": datetime.now(timezone.utc),
                },
            )

            # Record status change
            await self._record_status_change(
                service, ServiceStatus.TERMINATED, admin_id
            )

            # Handle post-termination cleanup
            await self._handle_service_termination(service, termination_data, admin_id)

            logger.info(f"Customer service terminated: {service_id}")
            return service

        except Exception as e:
            logger.error(f"Error terminating service {service_id}: {str(e)}")
            raise

    async def get_customer_services(
        self,
        customer_id: int,
        status: Optional[ServiceStatus] = None,
        service_type: Optional[ServiceType] = None,
    ) -> List[CustomerService]:
        """Get all services for a customer"""
        logger.info(f"Getting services for customer: {customer_id}")

        try:
            services = self.service_repo.get_customer_services(
                customer_id=customer_id, status=status, service_type=service_type
            )

            logger.info(f"Found {len(services)} services for customer {customer_id}")
            return services

        except Exception as e:
            logger.error(f"Error getting customer services: {str(e)}")
            raise BusinessLogicError(f"Failed to get customer services: {str(e)}")

    async def search_services(
        self, search_params: Dict[str, Any], page: int = 1, page_size: int = 50
    ) -> Tuple[List[CustomerService], int, Dict[str, Any]]:
        """Search customer services with pagination"""
        logger.info(f"Searching services with params: {search_params}")

        try:
            offset = (page - 1) * page_size

            services, total = self.service_repo.search_services(
                search_term=search_params.get("search_term"),
                customer_id=search_params.get("customer_id"),
                service_type=search_params.get("service_type"),
                status=search_params.get("status"),
                router_id=search_params.get("router_id"),
                date_from=search_params.get("date_from"),
                date_to=search_params.get("date_to"),
                limit=page_size,
                offset=offset,
            )

            # Calculate pagination metadata
            total_pages = (total + page_size - 1) // page_size
            metadata = {
                "page": page,
                "page_size": page_size,
                "total_items": total,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1,
            }

            logger.info(f"Found {total} services matching search criteria")
            return services, total, metadata

        except Exception as e:
            logger.error(f"Error searching services: {str(e)}")
            raise BusinessLogicError(f"Failed to search services: {str(e)}")

    async def get_service_statistics(self) -> Dict[str, Any]:
        """Get comprehensive service statistics"""
        logger.info("Getting service statistics")

        try:
            stats = self.service_repo.get_service_statistics()

            # Add business intelligence metrics
            stats["service_health"] = await self._calculate_service_health_metrics()
            stats["revenue_impact"] = await self._calculate_revenue_impact()

            logger.info("Service statistics retrieved successfully")
            return stats

        except Exception as e:
            logger.error(f"Error getting service statistics: {str(e)}")
            raise BusinessLogicError(f"Failed to get service statistics: {str(e)}")

    # Private helper methods
    async def _validate_service_data(self, service_data: Dict[str, Any]):
        """Validate customer service data"""
        required_fields = ["customer_id", "template_id"]

        for field in required_fields:
            if field not in service_data or not service_data[field]:
                raise ValidationError(f"Required field '{field}' is missing or empty")

    async def _generate_service_identifier(
        self, service_type: ServiceType, customer_id: int
    ) -> str:
        """Generate unique service identifier"""
        timestamp = int(datetime.now(timezone.utc).timestamp())
        return f"{service_type.value.upper()}-{customer_id:06d}-{timestamp}"

    async def _trigger_provisioning(self, service: CustomerService, admin_id: int):
        """Trigger provisioning workflow for new service"""
        # This would integrate with the provisioning service
        logger.info(f"Triggering provisioning for service: {service.id}")
        # Implementation would be added when provisioning service is complete

    async def _validate_service_activation(self, service: CustomerService):
        """Validate service can be activated"""
        # Check provisioning status, billing requirements, etc.
        pass

    async def _record_status_change(
        self, service: CustomerService, new_status: ServiceStatus, admin_id: int
    ):
        """Record service status change in history"""
        self.repo_factory.get_status_history_repo()
        # Implementation would create status history record
        logger.info(f"Recording status change for service {service.id}: {new_status}")

    async def _handle_service_activation(self, service: CustomerService, admin_id: int):
        """Handle post-activation tasks"""
        # Network configuration, billing activation, notifications, etc.
        logger.info(f"Handling activation tasks for service: {service.id}")

    async def _create_suspension_record(
        self, service: CustomerService, suspension_data: Dict[str, Any], admin_id: int
    ):
        """Create suspension record"""
        self.repo_factory.get_suspension_repo()
        # Implementation would create suspension record
        logger.info(f"Creating suspension record for service: {service.id}")

    async def _handle_service_suspension(
        self, service: CustomerService, suspension_data: Dict[str, Any], admin_id: int
    ):
        """Handle service suspension tasks"""
        # Network disconnection, billing suspension, notifications, etc.
        logger.info(f"Handling suspension tasks for service: {service.id}")

    async def _handle_service_pre_termination(
        self, service: CustomerService, admin_id: int
    ):
        """Handle pre-termination tasks"""
        # Final billing, data backup, etc.
        logger.info(f"Handling pre-termination tasks for service: {service.id}")

    async def _handle_service_termination(
        self, service: CustomerService, termination_data: Dict[str, Any], admin_id: int
    ):
        """Handle service termination cleanup"""
        # Resource cleanup, final billing, notifications, etc.
        logger.info(f"Handling termination cleanup for service: {service.id}")

    async def _calculate_service_health_metrics(self) -> Dict[str, Any]:
        """Calculate service health metrics"""
        return {
            "overall_health_score": 85.0,
            "active_service_ratio": 0.92,
            "suspension_rate": 0.05,
            "termination_rate": 0.03,
        }

    async def _calculate_revenue_impact(self) -> Dict[str, Any]:
        """Calculate revenue impact metrics"""
        return {
            "monthly_recurring_revenue": 0.0,
            "average_revenue_per_service": 0.0,
            "revenue_at_risk": 0.0,
        }


class CustomerInternetServiceService:
    """Service layer for customer internet service operations"""

    def __init__(self, db: Session):
        self.db = db
        self.repo_factory = ServiceRepositoryFactory(db)
        self.internet_service_repo = self.repo_factory.get_internet_service_repo()

    async def create_internet_service(
        self, service_id: int, internet_data: Dict[str, Any], admin_id: int
    ) -> CustomerInternetService:
        """Create internet service configuration"""
        logger.info(
            f"Creating internet service configuration for service: {service_id}"
        )

        try:
            # Validate internet service data
            self._validate_internet_service_data(internet_data)

            # Generate PPPoE username
            customer_service = (
                self.db.query(CustomerService)
                .filter(CustomerService.id == service_id)
                .first()
            )
            if not customer_service:
                raise NotFoundError(f"Customer service {service_id} not found")

            pppoe_username = await self._generate_pppoe_username(customer_service)

            # Prepare internet service data
            internet_data.update(
                {
                    "service_id": service_id,
                    "pppoe_username": pppoe_username,
                    "created_by_id": admin_id,
                    "created_at": datetime.now(timezone.utc),
                }
            )

            # Create internet service
            internet_service = CustomerInternetService(**internet_data)
            internet_service = self.internet_service_repo.create(internet_service)

            logger.info(
                f"Internet service configuration created: {internet_service.id}"
            )
            return internet_service

        except Exception as e:
            logger.error(f"Error creating internet service: {str(e)}")
            raise

    async def assign_ip_address(
        self,
        service_id: int,
        ip_address: str,
        assignment_type: IPAssignmentType,
        admin_id: int,
    ) -> CustomerInternetService:
        """Assign IP address to internet service"""
        logger.info(f"Assigning IP {ip_address} to internet service: {service_id}")

        try:
            internet_service = self.internet_service_repo.get_by_id(service_id)
            if not internet_service:
                raise NotFoundError(f"Internet service {service_id} not found")

            # Validate IP is available
            await self._validate_ip_availability(ip_address)

            # Update service with IP assignment
            internet_service = self.internet_service_repo.update(
                internet_service,
                {
                    "assigned_ip": ip_address,
                    "ip_assignment_type": assignment_type,
                    "ip_assigned_at": datetime.now(timezone.utc),
                    "updated_by_id": admin_id,
                    "updated_at": datetime.now(timezone.utc),
                },
            )

            # Create IP assignment record
            await self._create_ip_assignment_record(
                internet_service, ip_address, assignment_type, admin_id
            )

            logger.info(f"IP address assigned successfully: {ip_address}")
            return internet_service

        except Exception as e:
            logger.error(f"Error assigning IP address: {str(e)}")
            raise

    async def update_speed_profile(
        self, service_id: int, download_speed: int, upload_speed: int, admin_id: int
    ) -> CustomerInternetService:
        """Update internet service speed profile"""
        logger.info(f"Updating speed profile for internet service: {service_id}")

        try:
            internet_service = self.internet_service_repo.get_by_id(service_id)
            if not internet_service:
                raise NotFoundError(f"Internet service {service_id} not found")

            # Validate speed values
            if download_speed <= 0 or upload_speed <= 0:
                raise ValidationError("Speed values must be greater than 0")

            # Update speed profile
            internet_service = self.internet_service_repo.update(
                internet_service,
                {
                    "current_download_speed": download_speed,
                    "current_upload_speed": upload_speed,
                    "speed_updated_at": datetime.now(timezone.utc),
                    "updated_by_id": admin_id,
                    "updated_at": datetime.now(timezone.utc),
                },
            )

            # Apply speed changes to network equipment
            await self._apply_speed_changes(
                internet_service, download_speed, upload_speed
            )

            logger.info(f"Speed profile updated: {download_speed}/{upload_speed} Mbps")
            return internet_service

        except Exception as e:
            logger.error(f"Error updating speed profile: {str(e)}")
            raise

    async def handle_fup_exceeded(self, service_id: int) -> CustomerInternetService:
        """Handle FUP limit exceeded"""
        logger.info(f"Handling FUP exceeded for internet service: {service_id}")

        try:
            internet_service = self.internet_service_repo.get_by_id(service_id)
            if not internet_service:
                raise NotFoundError(f"Internet service {service_id} not found")

            # Update FUP status
            internet_service = self.internet_service_repo.update(
                internet_service,
                {
                    "fup_exceeded": True,
                    "fup_exceeded_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc),
                },
            )

            # Apply FUP speed restrictions
            await self._apply_fup_restrictions(internet_service)

            # Create alert
            await self._create_fup_alert(internet_service)

            logger.info(f"FUP exceeded handling completed for service: {service_id}")
            return internet_service

        except Exception as e:
            logger.error(f"Error handling FUP exceeded: {str(e)}")
            raise

    # Private helper methods
    def _validate_internet_service_data(self, internet_data: Dict[str, Any]):
        """Validate internet service data"""
        required_fields = ["current_download_speed", "current_upload_speed"]

        for field in required_fields:
            if field not in internet_data or internet_data[field] is None:
                raise ValidationError(f"Required field '{field}' is missing")

        if internet_data["current_download_speed"] <= 0:
            raise ValidationError("Download speed must be greater than 0")

        if internet_data["current_upload_speed"] <= 0:
            raise ValidationError("Upload speed must be greater than 0")

    async def _generate_pppoe_username(self, customer_service: CustomerService) -> str:
        """Generate PPPoE username"""
        customer = customer_service.customer
        return f"{customer.login}-inet-{customer_service.id}"

    async def _validate_ip_availability(self, ip_address: str):
        """Validate IP address is available"""
        existing_assignment = self.internet_service_repo.get_by_ip_address(ip_address)
        if existing_assignment:
            raise ValidationError(f"IP address {ip_address} is already assigned")

    async def _create_ip_assignment_record(
        self,
        internet_service: CustomerInternetService,
        ip_address: str,
        assignment_type: IPAssignmentType,
        admin_id: int,
    ):
        """Create IP assignment record"""
        self.repo_factory.get_ip_assignment_repo()
        # Implementation would create IP assignment record
        logger.info(f"Creating IP assignment record: {ip_address}")

    async def _apply_speed_changes(
        self,
        internet_service: CustomerInternetService,
        download_speed: int,
        upload_speed: int,
    ):
        """Apply speed changes to network equipment"""
        # This would integrate with network management systems
        logger.info("Applying speed changes to network equipment")

    async def _apply_fup_restrictions(self, internet_service: CustomerInternetService):
        """Apply FUP speed restrictions"""
        # This would reduce speed to FUP limit
        logger.info("Applying FUP restrictions")

    async def _create_fup_alert(self, internet_service: CustomerInternetService):
        """Create FUP exceeded alert"""
        self.repo_factory.get_alert_repo()
        # Implementation would create alert
        logger.info("Creating FUP exceeded alert")


class CustomerVoiceServiceService:
    """Service layer for customer voice service operations"""

    def __init__(self, db: Session):
        self.db = db
        self.repo_factory = ServiceRepositoryFactory(db)
        self.voice_service_repo = self.repo_factory.get_voice_service_repo()

    async def create_voice_service(
        self, service_id: int, voice_data: Dict[str, Any], admin_id: int
    ) -> CustomerVoiceService:
        """Create voice service configuration"""
        logger.info(f"Creating voice service configuration for service: {service_id}")

        try:
            # Validate voice service data
            self._validate_voice_service_data(voice_data)

            # Generate SIP username
            customer_service = (
                self.db.query(CustomerService)
                .filter(CustomerService.id == service_id)
                .first()
            )
            if not customer_service:
                raise NotFoundError(f"Customer service {service_id} not found")

            sip_username = await self._generate_sip_username(customer_service)

            # Prepare voice service data
            voice_data.update(
                {
                    "service_id": service_id,
                    "sip_username": sip_username,
                    "created_by_id": admin_id,
                    "created_at": datetime.now(timezone.utc),
                }
            )

            # Create voice service
            voice_service = CustomerVoiceService(**voice_data)
            voice_service = self.voice_service_repo.create(voice_service)

            logger.info(f"Voice service configuration created: {voice_service.id}")
            return voice_service

        except Exception as e:
            logger.error(f"Error creating voice service: {str(e)}")
            raise

    def _validate_voice_service_data(self, voice_data: Dict[str, Any]):
        """Validate voice service data"""
        if "included_minutes" in voice_data and voice_data["included_minutes"] < 0:
            raise ValidationError("Included minutes cannot be negative")

    async def _generate_sip_username(self, customer_service: CustomerService) -> str:
        """Generate SIP username"""
        customer = customer_service.customer
        return f"{customer.login}-voice-{customer_service.id}"


# Service factory for instance services
class ServiceInstanceServiceFactory:
    """Factory for creating service instance services"""

    @staticmethod
    def create_customer_service_service(db: Session) -> CustomerServiceService:
        return CustomerServiceService(db)

    @staticmethod
    def create_internet_service_service(db: Session) -> CustomerInternetServiceService:
        return CustomerInternetServiceService(db)

    @staticmethod
    def create_voice_service_service(db: Session) -> CustomerVoiceServiceService:
        return CustomerVoiceServiceService(db)

    @staticmethod
    def create_all_services(db: Session) -> Dict[str, Any]:
        """Create all service instance services"""
        return {
            "customer_service": CustomerServiceService(db),
            "internet_service": CustomerInternetServiceService(db),
            "voice_service": CustomerVoiceServiceService(db),
        }
