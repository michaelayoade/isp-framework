"""
Service Management Service Layer

This module contains business logic for service management operations:
Internet services, Voice services, Bundle services, and Recurring services.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.services import CustomerInternetService as InternetService
from app.models.services import CustomerService as BundleService
from app.models.services import CustomerVoiceService as VoiceService
from app.models.services import ServiceTemplate as RecurringService

from ..core.exceptions import DuplicateError, NotFoundError
from ..repositories.services import ServiceManagementRepository
from ..schemas.services import (
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
    """Service layer for all service management operations"""

    def __init__(self, db: Session):
        self.db = db
        self.repo = ServiceManagementRepository(db)

    # Internet Service Operations
    async def create_internet_service(
        self, service_data: InternetServiceCreate
    ) -> InternetService:
        """Create a new internet service"""
        try:
            # Check for duplicate name
            existing = self.repo.internet.get_all({"name": service_data.name})
            if existing:
                raise DuplicateError(
                    f"Internet service with name '{service_data.name}' already exists"
                )

            # Create service
            service = InternetService(**service_data.dict())
            service.created_at = datetime.now(timezone.utc)
            service.updated_at = datetime.now(timezone.utc)

            created_service = self.repo.internet.create(service)
            logger.info(
                f"Created internet service: {created_service.name} (ID: {created_service.id})"
            )
            return created_service

        except Exception as e:
            logger.error(f"Error creating internet service: {str(e)}")
            raise

    async def get_internet_service(self, service_id: int) -> InternetService:
        """Get internet service by ID"""
        service = self.repo.internet.get_by_id(service_id)
        if not service:
            raise NotFoundError(f"Internet service with ID {service_id} not found")
        return service

    async def update_internet_service(
        self, service_id: int, service_data: InternetServiceUpdate
    ) -> InternetService:
        """Update internet service"""
        service = await self.get_internet_service(service_id)

        # Update fields
        update_data = service_data.dict(exclude_unset=True)
        if update_data:
            update_data["updated_at"] = datetime.now(timezone.utc)
            updated_service = self.repo.internet.update(service, update_data)
            logger.info(
                f"Updated internet service: {updated_service.name} (ID: {updated_service.id})"
            )
            return updated_service

        return service

    async def delete_internet_service(self, service_id: int) -> bool:
        """Delete internet service"""
        service = await self.get_internet_service(service_id)
        success = self.repo.internet.delete(service)
        if success:
            logger.info(f"Deleted internet service: {service.name} (ID: {service.id})")
        return success

    def list_internet_services(
        self, filters: Optional[Dict] = None
    ) -> List[InternetService]:
        """List internet services with optional filters"""
        # Convert filters to proper BaseRepository format
        if filters:
            return self.repo.internet.get_all(filters=filters)
        else:
            return self.repo.internet.get_all()

    async def get_public_internet_services(self) -> List[InternetService]:
        """Get public internet services"""
        return self.repo.internet.get_public_services()

    # Voice Service Operations
    async def create_voice_service(
        self, service_data: VoiceServiceCreate
    ) -> VoiceService:
        """Create a new voice service"""
        try:
            # Check for duplicate name
            existing = self.repo.voice.get_all({"name": service_data.name})
            if existing:
                raise DuplicateError(
                    f"Voice service with name '{service_data.name}' already exists"
                )

            # Create service
            service = VoiceService(**service_data.dict())
            service.created_at = datetime.now(timezone.utc)
            service.updated_at = datetime.now(timezone.utc)

            created_service = self.repo.voice.create(service)
            logger.info(
                f"Created voice service: {created_service.name} (ID: {created_service.id})"
            )
            return created_service

        except Exception as e:
            logger.error(f"Error creating voice service: {str(e)}")
            raise

    async def get_voice_service(self, service_id: int) -> VoiceService:
        """Get voice service by ID"""
        service = self.repo.voice.get_by_id(service_id)
        if not service:
            raise NotFoundError(f"Voice service with ID {service_id} not found")
        return service

    async def update_voice_service(
        self, service_id: int, service_data: VoiceServiceUpdate
    ) -> VoiceService:
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
