#!/usr/bin/env python3
"""
Modular Network Provisioning Service

This service handles automated network provisioning using the new modular,
vendor-agnostic network architecture. It provides IP allocation, device
assignment, and service provisioning capabilities.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from ..core.exceptions import NotFoundError, ValidationError
from ..models.customer.base import Customer
from ..models.networking.ipam import IPAllocation, IPPool
from ..models.networking.nas_radius import NASDevice

# Using new modular network architecture
from ..models.networking.networks import NetworkDevice, NetworkSite
from ..models.services.instances import CustomerService
from ..models.services.legacy import ServicePlan
from ..repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class ModularNetworkProvisioningService:
    """
    Modular Network Provisioning Service

    Handles automated provisioning of network services using the new
    vendor-agnostic modular architecture.
    """

    def __init__(self, db: Session):
        self.db = db

        # Initialize repositories for modular architecture
        self.network_device_repo = BaseRepository(NetworkDevice, db)
        self.network_site_repo = BaseRepository(NetworkSite, db)
        self.nas_device_repo = BaseRepository(NASDevice, db)
        self.ip_pool_repo = BaseRepository(IPPool, db)
        self.ip_allocation_repo = BaseRepository(IPAllocation, db)
        self.customer_service_repo = BaseRepository(CustomerService, db)

    def provision_customer_service(
        self, customer_id: int, service_plan_id: int, device_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Provision network services for a customer using modular architecture

        Args:
            customer_id: Customer ID
            service_plan_id: Service plan ID
            device_id: Optional specific network device ID

        Returns:
            Dict containing provisioning results
        """
        try:
            logger.info(
                f"Starting modular service provisioning for customer {customer_id}"
            )

            # Get customer and service plan
            customer = (
                self.db.query(Customer).filter(Customer.id == customer_id).first()
            )
            if not customer:
                raise NotFoundError(f"Customer {customer_id} not found")

            service_plan = (
                self.db.query(ServicePlan)
                .filter(ServicePlan.id == service_plan_id)
                .first()
            )
            if not service_plan:
                raise NotFoundError(f"Service plan {service_plan_id} not found")

            # Assign network device
            assigned_device = self._assign_network_device(customer_id, device_id)

            # Allocate IP address
            ip_allocation = self._allocate_ip_address(
                customer_id, assigned_device.get("id")
            )

            # Create customer service record
            customer_service = CustomerService(
                customer_id=customer_id,
                service_plan_id=service_plan_id,
                status="active",
                created_at=datetime.now(timezone.utc),
            )
            self.db.add(customer_service)
            self.db.commit()

            result = {
                "success": True,
                "customer_id": customer_id,
                "service_plan_id": service_plan_id,
                "customer_service_id": customer_service.id,
                "network_device": assigned_device,
                "ip_allocation": ip_allocation,
                "provisioned_at": datetime.now(timezone.utc).isoformat(),
            }

            logger.info(
                f"Modular service provisioning completed for customer {customer_id}"
            )
            return result

        except Exception as e:
            logger.error(
                f"Modular service provisioning failed for customer {customer_id}: {str(e)}"
            )
            self.db.rollback()
            raise ValidationError(f"Service provisioning failed: {str(e)}")

    def _assign_network_device(
        self, customer_id: int, device_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Assign a network device to the customer"""
        try:
            if device_id:
                # Use specific device
                device = self.network_device_repo.get_by_id(device_id)
                if not device:
                    raise NotFoundError(f"Network device {device_id} not found")
            else:
                # Find available device
                devices = self.network_device_repo.get_all()
                if not devices:
                    raise NotFoundError("No network devices available")
                device = devices[0]  # Simple assignment logic

            return {
                "id": device.id,
                "name": device.name,
                "device_type": (
                    device.device_type.value if device.device_type else "unknown"
                ),
                "management_ip": (
                    str(device.management_ip) if device.management_ip else None
                ),
                "site_id": device.site_id,
            }

        except Exception as e:
            logger.error(
                f"Device assignment failed for customer {customer_id}: {str(e)}"
            )
            raise ValidationError(f"Device assignment failed: {str(e)}")

    def _allocate_ip_address(
        self, customer_id: int, device_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Allocate an IP address from available pools"""
        try:
            # Find available IP pool
            pools = self.ip_pool_repo.get_all()
            if not pools:
                raise NotFoundError("No IP pools available")

            pool = pools[0]  # Simple pool selection logic

            # Create IP allocation record
            allocation = IPAllocation(
                pool_id=pool.id,
                customer_id=customer_id,
                device_id=device_id,
                status="allocated",
                allocated_at=datetime.now(timezone.utc),
            )
            self.db.add(allocation)
            self.db.commit()

            return {
                "id": allocation.id,
                "pool_id": pool.id,
                "pool_name": pool.name,
                "network": str(pool.network),
                "customer_id": customer_id,
                "allocated_at": allocation.allocated_at.isoformat(),
            }

        except Exception as e:
            logger.error(f"IP allocation failed for customer {customer_id}: {str(e)}")
            raise ValidationError(f"IP allocation failed: {str(e)}")

    def deprovision_customer_service(self, customer_service_id: int) -> Dict[str, Any]:
        """Deprovision network services for a customer"""
        try:
            logger.info(
                f"Starting service deprovisioning for customer service {customer_service_id}"
            )

            # Get customer service
            customer_service = self.customer_service_repo.get_by_id(customer_service_id)
            if not customer_service:
                raise NotFoundError(f"Customer service {customer_service_id} not found")

            # Release IP allocations
            allocations = (
                self.db.query(IPAllocation)
                .filter(IPAllocation.customer_id == customer_service.customer_id)
                .all()
            )

            for allocation in allocations:
                allocation.status = "released"
                allocation.released_at = datetime.now(timezone.utc)

            # Update customer service status
            customer_service.status = "inactive"
            customer_service.updated_at = datetime.now(timezone.utc)

            self.db.commit()

            result = {
                "success": True,
                "customer_service_id": customer_service_id,
                "customer_id": customer_service.customer_id,
                "released_allocations": len(allocations),
                "deprovisioned_at": datetime.now(timezone.utc).isoformat(),
            }

            logger.info(
                f"Service deprovisioning completed for customer service {customer_service_id}"
            )
            return result

        except Exception as e:
            logger.error(f"Service deprovisioning failed: {str(e)}")
            self.db.rollback()
            raise ValidationError(f"Service deprovisioning failed: {str(e)}")

    def get_customer_network_info(self, customer_id: int) -> Dict[str, Any]:
        """Get comprehensive network information for a customer"""
        try:
            # Get customer services
            services = (
                self.db.query(CustomerService)
                .filter(CustomerService.customer_id == customer_id)
                .all()
            )

            # Get IP allocations
            allocations = (
                self.db.query(IPAllocation)
                .filter(IPAllocation.customer_id == customer_id)
                .all()
            )

            return {
                "customer_id": customer_id,
                "services": [
                    {
                        "id": service.id,
                        "service_plan_id": service.service_plan_id,
                        "status": service.status,
                        "created_at": (
                            service.created_at.isoformat()
                            if service.created_at
                            else None
                        ),
                    }
                    for service in services
                ],
                "ip_allocations": [
                    {
                        "id": allocation.id,
                        "pool_id": allocation.pool_id,
                        "status": allocation.status,
                        "allocated_at": (
                            allocation.allocated_at.isoformat()
                            if allocation.allocated_at
                            else None
                        ),
                    }
                    for allocation in allocations
                ],
                "total_services": len(services),
                "total_allocations": len(allocations),
            }

        except Exception as e:
            logger.error(
                f"Failed to get network info for customer {customer_id}: {str(e)}"
            )
            raise ValidationError(f"Failed to get network info: {str(e)}")
