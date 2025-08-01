"""
Complete Service Management Service Layer

This module contains comprehensive business logic for service management operations:
- Service Catalog Management (ServiceTemplate + Tariff creation)
- Service CRUD Operations (Internet, Voice, Bundle, Recurring)
- Service Provisioning Workflows
- Service Validation and Error Handling
- Service Search and Filtering
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.foundation.tariff import (
    InternetTariffConfig,
    Tariff,
    TariffBillingOption,
    TariffPromotion,
    TariffZonePricing,
)
from app.models.services.templates import (
    BundleServiceTemplate,
    InternetServiceTemplate,
    ServiceTemplate,
    VoiceServiceTemplate,
)

from ..core.exceptions import DuplicateError, NotFoundError
from app.schemas.services import (
    BundleServiceCreate,
    BundleServiceUpdate,
    InternetServiceCreate,
    InternetServiceUpdate,
    RecurringServiceCreate,
    RecurringServiceUpdate,
    ServiceOverview,
    ServiceSearchFilters,
    VoiceServiceCreate,
    VoiceServiceUpdate,
)

logger = logging.getLogger(__name__)


class ServiceManagementService:
    """Complete service management operations including catalog, CRUD, and provisioning"""

    def __init__(self, db: Session):
        self.db = db

    # ============================================================================
    # SERVICE CATALOG MANAGEMENT
    # ============================================================================

    async def create_service_catalog_item(
        self, 
        service_type: str,
        name: str,
        description: str,
        base_price: float,
        service_config: dict
    ) -> ServiceTemplate:
        """Create a complete service catalog item with tariff and configuration"""
        try:
            # 1. Create base tariff
            tariff = Tariff(
                name=f"{name} Tariff",
                display_name=f"{name} Service Plan",
                description=f"Tariff for {name} service",
                service_type=service_type,
                base_price=base_price,
                currency="NGN",
                is_active=True,
                is_public=True
            )
            self.db.add(tariff)
            self.db.flush()  # Get tariff ID

            # 2. Create service template
            service_template = ServiceTemplate(
                service_type=service_type,
                name=name,
                display_name=name,
                description=description,
                tariff_id=tariff.id,
                is_active=True,
                is_public=True
            )
            self.db.add(service_template)
            self.db.flush()  # Get service template ID

            # 3. Create service-specific configuration
            if service_type == "INTERNET":
                internet_config = InternetServiceTemplate(
                    service_template_id=service_template.id,
                    download_speed_kbps=service_config.get("download_speed", 1000) * 1000,  # Convert Mbps to kbps
                    upload_speed_kbps=service_config.get("upload_speed", 500) * 1000,
                    monthly_data_limit_gb=service_config.get("data_limit"),
                    fup_enabled=service_config.get("fup_enabled", False),
                    static_ip_required=service_config.get("static_ip", False),
                    burst_enabled=service_config.get("burst_enabled", True)
                )
                self.db.add(internet_config)
                
                # Create internet tariff config
                internet_tariff = InternetTariffConfig(
                    tariff_id=tariff.id,
                    speed_download=service_config.get("download_speed", 1000) * 1000,
                    speed_upload=service_config.get("upload_speed", 500) * 1000,
                    data_limit_bytes=service_config.get("data_limit_bytes"),
                    fup_enabled=service_config.get("fup_enabled", False)
                )
                self.db.add(internet_tariff)

            elif service_type == "VOICE":
                voice_config = VoiceServiceTemplate(
                    service_template_id=service_template.id,
                    included_minutes=service_config.get("included_minutes", 0),
                    per_minute_rate=service_config.get("per_minute_rate", 0.05),
                    caller_id=service_config.get("caller_id", True),
                    voicemail=service_config.get("voicemail", True)
                )
                self.db.add(voice_config)

            elif service_type == "BUNDLE":
                bundle_config = BundleServiceTemplate(
                    service_template_id=service_template.id,
                    included_services=service_config.get("included_services", {}),
                    bundle_discount_percent=service_config.get("discount_percent", 10),
                    minimum_bundle_months=service_config.get("minimum_months", 12)
                )
                self.db.add(bundle_config)

            self.db.commit()
            logger.info(f"Created service catalog item: {name} (Type: {service_type})")
            return service_template

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating service catalog item: {str(e)}")
            raise

    async def get_service_catalog(self, service_type: str = None) -> List[ServiceTemplate]:
        """Get all service catalog items"""
        query = self.db.query(ServiceTemplate).filter(ServiceTemplate.is_active == True)
        if service_type:
            query = query.filter(ServiceTemplate.service_type == service_type)
        return query.all()

    async def get_service_catalog_item(self, service_id: int) -> ServiceTemplate:
        """Get specific service catalog item with full configuration"""
        service = self.db.query(ServiceTemplate).filter(
            ServiceTemplate.id == service_id
        ).first()
        if not service:
            raise NotFoundError(f"Service catalog item with ID {service_id} not found")
        return service

    # ============================================================================
    # SERVICE CATALOG CRUD OPERATIONS
    # ============================================================================

    async def update_service_catalog_item(
        self, service_id: int, update_data: dict
    ) -> ServiceTemplate:
        """Update service catalog item and its configuration"""
        try:
            service = await self.get_service_catalog_item(service_id)
            
            # Update service template
            for key, value in update_data.items():
                if hasattr(service, key):
                    setattr(service, key, value)
            
            # Update tariff if price changed
            if "base_price" in update_data:
                service.tariff.base_price = update_data["base_price"]
            
            self.db.commit()
            logger.info(f"Updated service catalog item: {service.name} (ID: {service_id})")
            return service
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating service catalog item: {str(e)}")
            raise

    async def delete_service_catalog_item(self, service_id: int) -> bool:
        """Delete service catalog item (soft delete)"""
        try:
            service = await self.get_service_catalog_item(service_id)
            service.is_active = False
            service.tariff.is_active = False
            
            self.db.commit()
            logger.info(f"Deleted service catalog item: {service.name} (ID: {service_id})")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting service catalog item: {str(e)}")
            raise

    # ============================================================================
    # SERVICE PROVISIONING WORKFLOWS
    # ============================================================================

    async def provision_service(
        self, customer_id: int, service_template_id: int, provisioning_data: dict
    ) -> dict:
        """Provision a service for a customer"""
        try:
            service_template = await self.get_service_catalog_item(service_template_id)
            
            # Create customer service instance
            from app.models.services.instances import CustomerService
            
            customer_service = CustomerService(
                customer_id=customer_id,
                service_template_id=service_template_id,
                status="PENDING_ACTIVATION",
                monthly_price=service_template.tariff.base_price,
                activation_date=datetime.now(timezone.utc),
                billing_cycle_start=datetime.now(timezone.utc)
            )
            self.db.add(customer_service)
            self.db.flush()
            
            # Create provisioning job
            provisioning_job = {
                "customer_service_id": customer_service.id,
                "service_type": service_template.service_type,
                "status": "QUEUED",
                "provisioning_data": provisioning_data,
                "created_at": datetime.now(timezone.utc)
            }
            
            self.db.commit()
            logger.info(f"Provisioned service for customer {customer_id}: {service_template.name}")
            
            return {
                "customer_service_id": customer_service.id,
                "provisioning_job": provisioning_job,
                "status": "PROVISIONING_STARTED"
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error provisioning service: {str(e)}")
            raise

    async def get_provisioning_status(self, customer_service_id: int) -> dict:
        """Get provisioning status for a customer service"""
        try:
            from app.models.services.instances import CustomerService
            
            customer_service = self.db.query(CustomerService).filter(
                CustomerService.id == customer_service_id
            ).first()
            
            if not customer_service:
                raise NotFoundError(f"Customer service with ID {customer_service_id} not found")
            
            return {
                "customer_service_id": customer_service_id,
                "status": customer_service.status,
                "service_name": customer_service.service_template.name,
                "activation_date": customer_service.activation_date,
                "last_updated": customer_service.updated_at
            }
            
        except Exception as e:
            logger.error(f"Error getting provisioning status: {str(e)}")
            raise

    # ============================================================================
    # SIMPLIFIED SERVICE OPERATIONS (for backward compatibility)
    # ============================================================================

    async def create_internet_service(self, service_data: InternetServiceCreate) -> ServiceTemplate:
        """Create internet service using catalog approach"""
        config = {
            "download_speed": service_data.download_speed,
            "upload_speed": service_data.upload_speed,
            "data_limit": service_data.data_limit,
            "fup_enabled": False,
            "static_ip": False,
            "burst_enabled": True
        }
        
        return await self.create_service_catalog_item(
            service_type="INTERNET",
            name=service_data.name,
            description=service_data.description or "",
            base_price=float(service_data.monthly_price),
            service_config=config
        )

    async def create_voice_service(self, service_data: VoiceServiceCreate) -> ServiceTemplate:
        """Create voice service using catalog approach"""
        config = {
            "included_minutes": service_data.included_minutes,
            "per_minute_rate": float(service_data.per_minute_rate),
            "caller_id": True,
            "voicemail": True
        }
        
        return await self.create_service_catalog_item(
            service_type="VOICE",
            name=service_data.name,
            description=service_data.description or "",
            base_price=float(service_data.monthly_price),
            service_config=config
        )

    async def create_bundle_service(self, service_data: BundleServiceCreate) -> ServiceTemplate:
        """Create bundle service using catalog approach"""
        config = {
            "included_services": {},
            "discount_percent": float(service_data.discount_percentage),
            "minimum_months": service_data.minimum_term_months
        }
        
        return await self.create_service_catalog_item(
            service_type="BUNDLE",
            name=service_data.name,
            description=service_data.description or "",
            base_price=float(service_data.bundle_price),
            service_config=config
        )

    # ============================================================================
    # SERVICE SEARCH AND FILTERING
    # ============================================================================

    async def search_services(
        self, 
        search_term: str = None,
        service_type: str = None,
        is_active: bool = None,
        is_public: bool = None,
        min_price: float = None,
        max_price: float = None
    ) -> List[ServiceTemplate]:
        """Search services with filters"""
        try:
            query = self.db.query(ServiceTemplate)
            
            # Apply filters
            if search_term:
                query = query.filter(
                    ServiceTemplate.name.ilike(f"%{search_term}%") |
                    ServiceTemplate.description.ilike(f"%{search_term}%")
                )
            
            if service_type:
                query = query.filter(ServiceTemplate.service_type == service_type)
            
            if is_active is not None:
                query = query.filter(ServiceTemplate.is_active == is_active)
            
            if is_public is not None:
                query = query.filter(ServiceTemplate.is_public == is_public)
            
            # Price filtering through tariff relationship
            if min_price is not None or max_price is not None:
                query = query.join(Tariff)
                if min_price is not None:
                    query = query.filter(Tariff.base_price >= min_price)
                if max_price is not None:
                    query = query.filter(Tariff.base_price <= max_price)
            
            return query.all()
            
        except Exception as e:
            logger.error(f"Error searching services: {str(e)}")
            raise

    async def get_services_overview(self) -> ServiceOverview:
        """Get overview of all services and statistics"""
        try:
            # Count services by type
            internet_count = self.db.query(ServiceTemplate).filter(
                ServiceTemplate.service_type == "INTERNET",
                ServiceTemplate.is_active == True
            ).count()
            
            voice_count = self.db.query(ServiceTemplate).filter(
                ServiceTemplate.service_type == "VOICE",
                ServiceTemplate.is_active == True
            ).count()
            
            bundle_count = self.db.query(ServiceTemplate).filter(
                ServiceTemplate.service_type == "BUNDLE",
                ServiceTemplate.is_active == True
            ).count()
            
            recurring_count = self.db.query(ServiceTemplate).filter(
                ServiceTemplate.service_type == "RECURRING",
                ServiceTemplate.is_active == True
            ).count()
            
            total_services = internet_count + voice_count + bundle_count + recurring_count
            
            active_services = self.db.query(ServiceTemplate).filter(
                ServiceTemplate.is_active == True
            ).count()
            
            public_services = self.db.query(ServiceTemplate).filter(
                ServiceTemplate.is_public == True,
                ServiceTemplate.is_active == True
            ).count()
            
            return ServiceOverview(
                internet_services=internet_count,
                voice_services=voice_count,
                bundle_services=bundle_count,
                recurring_services=recurring_count,
                total_services=total_services,
                active_services=active_services,
                public_services=public_services
            )
            
        except Exception as e:
            logger.error(f"Error getting services overview: {str(e)}")
            raise

    # ============================================================================
    # SERVICE VALIDATION
    # ============================================================================

    async def validate_service_data(self, service_type: str, service_data: dict) -> dict:
        """Validate service data before creation"""
        errors = []
        
        # Common validations
        if not service_data.get("name"):
            errors.append("Service name is required")
        
        if not service_data.get("base_price") or service_data.get("base_price") <= 0:
            errors.append("Base price must be greater than 0")
        
        # Service-specific validations
        if service_type == "INTERNET":
            config = service_data.get("service_config", {})
            if not config.get("download_speed") or config.get("download_speed") <= 0:
                errors.append("Download speed must be greater than 0")
            if not config.get("upload_speed") or config.get("upload_speed") <= 0:
                errors.append("Upload speed must be greater than 0")
        
        elif service_type == "VOICE":
            config = service_data.get("service_config", {})
            if config.get("per_minute_rate") is not None and config.get("per_minute_rate") < 0:
                errors.append("Per minute rate cannot be negative")
        
        elif service_type == "BUNDLE":
            config = service_data.get("service_config", {})
            if config.get("discount_percent") and (config.get("discount_percent") < 0 or config.get("discount_percent") > 100):
                errors.append("Discount percentage must be between 0 and 100")
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors
        }

    # Legacy methods removed - use service catalog approach instead
    # All service operations now go through the service catalog system

    # Note: All legacy service operations have been replaced by the comprehensive service catalog system
    # Use the following methods instead:
    # - create_service_catalog_item() for creating services
    # - get_service_catalog() for listing services
    # - search_services() for searching services
    # - provision_service() for provisioning services to customers
    
    # ============================================================================
    # END OF SERVICE MANAGEMENT CLASS
    # ============================================================================
        """Update voice service"""
        service = await self.get_voice_service(service_id)

        # Update fields
        update_data = service_data.dict(exclude_unset=True)
        if update_data:
            update_data["updated_at"] = datetime.now(timezone.utc)
            updated_service = self.repo.voice.update(service, update_data)
            logger.info(
                f"Updated voice service: {updated_service.name} (ID: {updated_service.id})"
            )
            return updated_service

        return service

    async def delete_voice_service(self, service_id: int) -> bool:
        """Delete voice service"""
        service = await self.get_voice_service(service_id)
        success = self.repo.voice.delete(service)
        if success:
            logger.info(f"Deleted voice service: {service.name} (ID: {service.id})")
        return success

    async def list_voice_services(
        self, filters: Optional[Dict] = None
    ) -> List[VoiceService]:
        """List voice services with optional filters"""
        return self.repo.voice.get_all(filters or {})

    # Bundle Service Operations
    async def create_bundle_service(
        self, service_data: BundleServiceCreate
    ) -> BundleService:
        """Create a new bundle service"""
        try:
            # Check for duplicate name
            existing = self.repo.bundle.get_all({"name": service_data.name})
            if existing:
                raise DuplicateError(
                    f"Bundle service with name '{service_data.name}' already exists"
                )

            # Validate referenced services exist
            if service_data.internet_service_id:
                internet_service = self.repo.internet.get_by_id(
                    service_data.internet_service_id
                )
                if not internet_service:
                    raise NotFoundError(
                        f"Internet service with ID {service_data.internet_service_id} not found"
                    )

            if service_data.voice_service_id:
                voice_service = self.repo.voice.get_by_id(service_data.voice_service_id)
                if not voice_service:
                    raise NotFoundError(
                        f"Voice service with ID {service_data.voice_service_id} not found"
                    )

            # Create service
            service = BundleService(**service_data.dict())
            service.created_at = datetime.now(timezone.utc)
            service.updated_at = datetime.now(timezone.utc)

            created_service = self.repo.bundle.create(service)
            logger.info(
                f"Created bundle service: {created_service.name} (ID: {created_service.id})"
            )
            return created_service

        except Exception as e:
            logger.error(f"Error creating bundle service: {str(e)}")
            raise

    async def get_bundle_service(self, service_id: int) -> BundleService:
        """Get bundle service by ID"""
        service = self.repo.bundle.get_by_id(service_id)
        if not service:
            raise NotFoundError(f"Bundle service with ID {service_id} not found")
        return service

    async def update_bundle_service(
        self, service_id: int, service_data: BundleServiceUpdate
    ) -> BundleService:
        """Update bundle service"""
        service = await self.get_bundle_service(service_id)

        # Update fields
        update_data = service_data.dict(exclude_unset=True)
        if update_data:
            update_data["updated_at"] = datetime.now(timezone.utc)
            updated_service = self.repo.bundle.update(service, update_data)
            logger.info(
                f"Updated bundle service: {updated_service.name} (ID: {updated_service.id})"
            )
            return updated_service

        return service

    async def delete_bundle_service(self, service_id: int) -> bool:
        """Delete bundle service"""
        service = await self.get_bundle_service(service_id)
        success = self.repo.bundle.delete(service)
        if success:
            logger.info(f"Deleted bundle service: {service.name} (ID: {service.id})")
        return success

    async def list_bundle_services(
        self, filters: Optional[Dict] = None
    ) -> List[BundleService]:
        """List bundle services with optional filters"""
        return self.repo.bundle.get_all(filters or {})

    # Recurring Service Operations
    async def create_recurring_service(
        self, service_data: RecurringServiceCreate
    ) -> RecurringService:
        """Create a new recurring service"""
        try:
            # Check for duplicate name
            existing = self.repo.recurring.get_all({"name": service_data.name})
            if existing:
                raise DuplicateError(
                    f"Recurring service with name '{service_data.name}' already exists"
                )

            # Create service
            service = RecurringService(**service_data.dict())
            service.created_at = datetime.now(timezone.utc)
            service.updated_at = datetime.now(timezone.utc)

            created_service = self.repo.recurring.create(service)
            logger.info(
                f"Created recurring service: {created_service.name} (ID: {created_service.id})"
            )
            return created_service

        except Exception as e:
            logger.error(f"Error creating recurring service: {str(e)}")
            raise

    async def get_recurring_service(self, service_id: int) -> RecurringService:
        """Get recurring service by ID"""
        service = self.repo.recurring.get_by_id(service_id)
        if not service:
            raise NotFoundError(f"Recurring service with ID {service_id} not found")
        return service

    async def update_recurring_service(
        self, service_id: int, service_data: RecurringServiceUpdate
    ) -> RecurringService:
        """Update recurring service"""
        service = await self.get_recurring_service(service_id)

        # Update fields
        update_data = service_data.dict(exclude_unset=True)
        if update_data:
            update_data["updated_at"] = datetime.now(timezone.utc)
            updated_service = self.repo.recurring.update(service, update_data)
            logger.info(
                f"Updated recurring service: {updated_service.name} (ID: {updated_service.id})"
            )
            return updated_service

        return service

    async def delete_recurring_service(self, service_id: int) -> bool:
        """Delete recurring service"""
        service = await self.get_recurring_service(service_id)
        success = self.repo.recurring.delete(service)
        if success:
            logger.info(f"Deleted recurring service: {service.name} (ID: {service.id})")
        return success

    async def list_recurring_services(
        self, filters: Optional[Dict] = None
    ) -> List[RecurringService]:
        """List recurring services with optional filters"""
        return self.repo.recurring.get_all(filters or {})

    # Service Tariff Operations moved to dedicated tariff module
    # Use app.services.tariff for tariff management

    # Service Management Operations
    async def get_service_overview(self) -> ServiceOverview:
        """Get overview of all services"""
        overview_data = self.repo.get_service_overview()
        return ServiceOverview(**overview_data)

    async def search_services(self, filters: ServiceSearchFilters) -> Dict[str, List]:
        """Search services across all types"""
        results = {}

        if filters.search_term:
            results = self.repo.search_all_services(
                filters.search_term, filters.service_type
            )
        else:
            # Apply filters to each service type
            service_filters = {}
            if filters.is_active is not None:
                service_filters["is_active"] = filters.is_active
            if filters.is_public is not None:
                service_filters["is_public"] = filters.is_public

            if not filters.service_type or filters.service_type == "internet":
                internet_filters = service_filters.copy()
                if filters.min_price:
                    internet_filters["monthly_price__gte"] = filters.min_price
                if filters.max_price:
                    internet_filters["monthly_price__lte"] = filters.max_price
                results["internet"] = self.repo.internet.get_all(internet_filters)

            if not filters.service_type or filters.service_type == "voice":
                voice_filters = service_filters.copy()
                if filters.min_price:
                    voice_filters["monthly_price__gte"] = filters.min_price
                if filters.max_price:
                    voice_filters["monthly_price__lte"] = filters.max_price
                results["voice"] = self.repo.voice.get_all(voice_filters)

            if not filters.service_type or filters.service_type == "bundle":
                bundle_filters = service_filters.copy()
                if filters.min_price:
                    bundle_filters["bundle_price__gte"] = filters.min_price
                if filters.max_price:
                    bundle_filters["bundle_price__lte"] = filters.max_price
                results["bundle"] = self.repo.bundle.get_all(bundle_filters)

            if not filters.service_type or filters.service_type == "recurring":
                recurring_filters = service_filters.copy()
                if filters.min_price:
                    recurring_filters["price__gte"] = filters.min_price
                if filters.max_price:
                    recurring_filters["price__lte"] = filters.max_price
                results["recurring"] = self.repo.recurring.get_all(recurring_filters)

        return results

    # RADIUS Integration Methods
    async def get_service_for_radius(
        self, service_id: int, service_type: str
    ) -> Optional[Dict[str, Any]]:
        """Get service configuration for RADIUS integration"""
        try:
            if service_type == "internet":
                service = await self.get_internet_service(service_id)
                return {
                    "id": service.id,
                    "name": service.name,
                    "type": "internet",
                    "download_speed": service.download_speed,
                    "upload_speed": service.upload_speed,
                    "data_limit": service.data_limit,
                    "radius_profile": service.radius_profile,
                    "bandwidth_limit_down": service.bandwidth_limit_down,
                    "bandwidth_limit_up": service.bandwidth_limit_up,
                    "monthly_price": float(service.monthly_price),
                }
            elif service_type == "voice":
                service = await self.get_voice_service(service_id)
                return {
                    "id": service.id,
                    "name": service.name,
                    "type": "voice",
                    "included_minutes": service.included_minutes,
                    "per_minute_rate": float(service.per_minute_rate),
                    "monthly_price": float(service.monthly_price),
                }
            elif service_type == "bundle":
                service = await self.get_bundle_service(service_id)
                return {
                    "id": service.id,
                    "name": service.name,
                    "type": "bundle",
                    "bundle_price": float(service.bundle_price),
                    "internet_service_id": service.internet_service_id,
                    "voice_service_id": service.voice_service_id,
                }

            return None

        except NotFoundError:
            return None
