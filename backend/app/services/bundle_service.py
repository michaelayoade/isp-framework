"""
Bundle Service Management

Service layer for managing bundle services (Internet + Voice combinations).
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import uuid4

from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import ISPFrameworkException
from app.models.customer.base import Customer
from app.models.services import BundleService
from app.schemas.bundle_service import (
    BundleServiceCreate,
    BundleServiceInDB,
    BundleServiceProvisioningRequest,
    BundleServiceProvisioningResponse,
    BundleServiceUpdate,
)
from app.services.provisioning_queue import ProvisioningQueueService


class BundleServiceService:
    """Service layer for bundle service management"""

    def __init__(self, db: Session):
        self.db = db
        self.provisioning_service = ProvisioningQueueService(db)

    def create_bundle_service(
        self, customer_id: int, bundle_data: BundleServiceCreate
    ) -> BundleServiceInDB:
        """Create a new bundle service for a customer"""

        # Verify customer exists
        customer = self.db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            raise ISPFrameworkException(f"Customer {customer_id} not found")

        # Create bundle service record
        bundle_service = BundleService(
            customer_id=customer_id,
            bundle_name=bundle_data.bundle_name,
            internet_speed_mbps=bundle_data.internet_speed_mbps,
            voice_channels=bundle_data.voice_channels,
            monthly_fee=bundle_data.monthly_fee,
            setup_fee=bundle_data.setup_fee or Decimal("0.00"),
            contract_months=bundle_data.contract_months,
            status="pending",
            created_at=datetime.now(timezone.utc),
        )

        self.db.add(bundle_service)
        self.db.commit()
        self.db.refresh(bundle_service)

        return BundleServiceInDB.from_orm(bundle_service)

    def get_bundle_service(self, service_id: int) -> Optional[BundleServiceInDB]:
        """Get bundle service by ID"""
        service = (
            self.db.query(BundleService).filter(BundleService.id == service_id).first()
        )
        if service:
            return BundleServiceInDB.from_orm(service)
        return None

    def get_customer_bundle_services(self, customer_id: int) -> List[BundleServiceInDB]:
        """Get all bundle services for a customer"""
        services = (
            self.db.query(BundleService)
            .filter(BundleService.customer_id == customer_id)
            .all()
        )

        return [BundleServiceInDB.from_orm(service) for service in services]

    def update_bundle_service(
        self, service_id: int, update_data: BundleServiceUpdate
    ) -> Optional[BundleServiceInDB]:
        """Update bundle service"""
        service = (
            self.db.query(BundleService).filter(BundleService.id == service_id).first()
        )
        if not service:
            return None

        # Update fields
        for field, value in update_data.dict(exclude_unset=True).items():
            setattr(service, field, value)

        service.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(service)

        return BundleServiceInDB.from_orm(service)

    def delete_bundle_service(self, service_id: int) -> bool:
        """Delete bundle service"""
        service = (
            self.db.query(BundleService).filter(BundleService.id == service_id).first()
        )
        if not service:
            return False

        self.db.delete(service)
        self.db.commit()
        return True

    def provision_bundle_service(
        self, request: BundleServiceProvisioningRequest
    ) -> BundleServiceProvisioningResponse:
        """Queue bundle service for provisioning"""

        # Create provisioning job
        job_id = uuid4()

        # Add to provisioning queue
        self.provisioning_service.create_provisioning_job(
            job_id=job_id,
            service_type="bundle",
            service_id=str(request.bundle_id),
            customer_id=str(request.customer_id),
            priority="normal",
            provisioning_data={
                "bundle_id": str(request.bundle_id),
                "customer_id": str(request.customer_id),
                "action": "provision",
            },
        )

        return BundleServiceProvisioningResponse(job_id=job_id, status="queued")

    def get_bundle_service_statistics(self) -> Dict[str, Any]:
        """Get bundle service statistics"""
        total_services = self.db.query(BundleService).count()
        active_services = (
            self.db.query(BundleService)
            .filter(BundleService.status == "active")
            .count()
        )
        pending_services = (
            self.db.query(BundleService)
            .filter(BundleService.status == "pending")
            .count()
        )

        return {
            "total_services": total_services,
            "active_services": active_services,
            "pending_services": pending_services,
            "activation_rate": (
                (active_services / total_services * 100) if total_services > 0 else 0
            ),
        }

    def search_bundle_services(
        self,
        customer_id: Optional[int] = None,
        status: Optional[str] = None,
        bundle_name: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[BundleServiceInDB]:
        """Search bundle services with filters"""
        query = self.db.query(BundleService)

        if customer_id:
            query = query.filter(BundleService.customer_id == customer_id)

        if status:
            query = query.filter(BundleService.status == status)

        if bundle_name:
            query = query.filter(BundleService.bundle_name.ilike(f"%{bundle_name}%"))

        services = query.offset(offset).limit(limit).all()
        return [BundleServiceInDB.from_orm(service) for service in services]


def get_bundle_service_service(db: Session = None) -> BundleServiceService:
    """Get bundle service service instance"""
    if db is None:
        db = next(get_db())
    return BundleServiceService(db)
