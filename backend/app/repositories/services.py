"""
Service Management Repositories

This module contains repository classes for service management operations:
Internet services, Voice services, Bundle services, and Recurring services.
"""

from typing import Any, Dict, List, Optional

from sqlalchemy import and_, asc, desc, or_
from sqlalchemy.orm import Session

from app.models.services.templates import (
    BundleServiceTemplate as BundleService,
    InternetServiceTemplate as InternetService,
    ServiceTemplate as RecurringService,
    VoiceServiceTemplate as VoiceService,
)

from .base import BaseRepository


class InternetServiceRepository(BaseRepository[InternetService]):
    """Repository for Internet service operations"""

    def __init__(self, db: Session):
        super().__init__(InternetService, db)

    def get_by_speed_range(
        self, min_speed: int, max_speed: int
    ) -> List[InternetService]:
        """Get internet services by speed range"""
        return (
            self.db.query(self.model)
            .filter(
                and_(
                    self.model.download_speed >= min_speed,
                    self.model.download_speed <= max_speed,
                    self.model.is_active is True,
                )
            )
            .all()
        )

    def get_by_price_range(
        self, min_price: float, max_price: float
    ) -> List[InternetService]:
        """Get internet services by price range"""
        return (
            self.db.query(self.model)
            .filter(
                and_(
                    self.model.monthly_price >= min_price,
                    self.model.monthly_price <= max_price,
                    self.model.is_active is True,
                )
            )
            .all()
        )

    def get_public_services(self) -> List[InternetService]:
        """Get all public internet services"""
        return (
            self.db.query(self.model)
            .filter(and_(self.model.is_public is True, self.model.is_active is True))
            .order_by(asc(self.model.priority), asc(self.model.monthly_price))
            .all()
        )

    def get_by_router(self, router_id: int) -> List[InternetService]:
        """Get internet services by router"""
        return (
            self.db.query(self.model)
            .filter(
                and_(self.model.router_id == router_id, self.model.is_active is True)
            )
            .all()
        )

    def search_services(self, search_term: str) -> List[InternetService]:
        """Search internet services by name or description"""
        return (
            self.db.query(self.model)
            .filter(
                and_(
                    or_(
                        self.model.name.ilike(f"%{search_term}%"),
                        self.model.description.ilike(f"%{search_term}%"),
                    ),
                    self.model.is_active is True,
                )
            )
            .all()
        )


class VoiceServiceRepository(BaseRepository[VoiceService]):
    """Repository for Voice service operations"""

    def __init__(self, db: Session):
        super().__init__(VoiceService, db)

    def get_by_rate_range(self, min_rate: float, max_rate: float) -> List[VoiceService]:
        """Get voice services by per-minute rate range"""
        return (
            self.db.query(self.model)
            .filter(
                and_(
                    self.model.per_minute_rate >= min_rate,
                    self.model.per_minute_rate <= max_rate,
                    self.model.is_active is True,
                )
            )
            .all()
        )

    def get_with_included_minutes(self) -> List[VoiceService]:
        """Get voice services that include minutes"""
        return (
            self.db.query(self.model)
            .filter(and_(self.model.included_minutes > 0, self.model.is_active is True))
            .all()
        )

    def get_public_services(self) -> List[VoiceService]:
        """Get all public voice services"""
        return (
            self.db.query(self.model)
            .filter(and_(self.model.is_public is True, self.model.is_active is True))
            .order_by(asc(self.model.priority), asc(self.model.monthly_price))
            .all()
        )


class BundleServiceRepository(BaseRepository[BundleService]):
    """Repository for Bundle service operations"""

    def __init__(self, db: Session):
        super().__init__(BundleService, db)

    def get_bundle_services(self, customer_id: int) -> List[BundleService]:
        """Get bundle services for a customer"""
        return (
            self.db.query(self.model)
            .filter(
                and_(
                    self.model.customer_id == customer_id, self.model.status == "active"
                )
            )
            .all()
        )

    def get_best_savings(self, limit: int = 10) -> List[BundleService]:
        """Get bundles with best savings percentage"""
        return (
            self.db.query(self.model)
            .filter(self.model.is_active is True)
            .order_by(desc(self.model.discount_percentage))
            .limit(limit)
            .all()
        )

    def get_public_services(self) -> List[BundleService]:
        """Get all public bundle services"""
        return (
            self.db.query(self.model)
            .filter(and_(self.model.is_public is True, self.model.is_active is True))
            .order_by(asc(self.model.priority), asc(self.model.bundle_price))
            .all()
        )


class RecurringServiceRepository(BaseRepository[RecurringService]):
    """Repository for Recurring service operations"""

    def __init__(self, db: Session):
        super().__init__(RecurringService, db)

    def get_by_type(self, service_type: str) -> List[RecurringService]:
        """Get recurring services by type"""
        return (
            self.db.query(self.model)
            .filter(
                and_(
                    self.model.service_type == service_type,
                    self.model.is_active is True,
                )
            )
            .all()
        )

    def get_addons(self) -> List[RecurringService]:
        """Get services that can be added as addons"""
        return (
            self.db.query(self.model)
            .filter(and_(self.model.is_addon is True, self.model.is_active is True))
            .all()
        )

    def get_auto_provision_services(self) -> List[RecurringService]:
        """Get services with auto-provisioning enabled"""
        return (
            self.db.query(self.model)
            .filter(
                and_(self.model.auto_provision is True, self.model.is_active is True)
            )
            .all()
        )

    def get_public_services(self) -> List[RecurringService]:
        """Get all public recurring services"""
        return (
            self.db.query(self.model)
            .filter(and_(self.model.is_public is True, self.model.is_active is True))
            .order_by(asc(self.model.service_type), asc(self.model.price))
            .all()
        )


# ServiceTariffRepository moved to dedicated tariff module
# Use app.repositories.tariff for tariff operations


class ServiceManagementRepository:
    """Unified repository for all service management operations"""

    def __init__(self, db: Session):
        self.db = db
        self.internet = InternetServiceRepository(db)
        self.voice = VoiceServiceRepository(db)
        self.bundle = BundleServiceRepository(db)
        self.recurring = RecurringServiceRepository(db)
        # self.tariff = ServiceTariffRepository(db)  # Moved to dedicated tariff module

    def get_service_overview(self) -> Dict[str, Any]:
        """Get overview of all services"""
        return {
            "internet_services": self.internet.count(),
            "voice_services": self.voice.count(),
            "bundle_services": self.bundle.count(),
            "recurring_services": self.recurring.count(),
            "total_services": (
                self.internet.count()
                + self.voice.count()
                + self.bundle.count()
                + self.recurring.count()
            ),
            "active_services": (
                self.internet.count({"is_active": True})
                + self.voice.count({"is_active": True})
                + self.bundle.count({"is_active": True})
                + self.recurring.count({"is_active": True})
            ),
            "public_services": (
                self.internet.count({"is_public": True, "is_active": True})
                + self.voice.count({"is_public": True, "is_active": True})
                + self.bundle.count({"is_public": True, "is_active": True})
                + self.recurring.count({"is_public": True, "is_active": True})
            ),
        }

    def search_all_services(
        self, search_term: str, service_type: Optional[str] = None
    ) -> Dict[str, List]:
        """Search across all service types"""
        results = {}

        if not service_type or service_type == "internet":
            results["internet"] = self.internet.search_services(search_term)

        if not service_type or service_type == "voice":
            results["voice"] = self.voice.get_all(
                {"name__ilike": f"%{search_term}%", "is_active": True}
            )

        if not service_type or service_type == "bundle":
            results["bundle"] = self.bundle.get_all(
                {"name__ilike": f"%{search_term}%", "is_active": True}
            )

        if not service_type or service_type == "recurring":
            results["recurring"] = self.recurring.get_all(
                {"name__ilike": f"%{search_term}%", "is_active": True}
            )

        return results
