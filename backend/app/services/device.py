"""Device management service for MAC authentication and IoT device handling."""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Tuple

from sqlalchemy import asc, desc
from sqlalchemy.orm import Session, joinedload

from app.models.customer.base import Customer
from app.models.networking.device import Device
from app.models.services.instances import CustomerService
from app.schemas.device import (
    DeviceApproval,
    DeviceBulkApproval,
    DeviceBulkResponse,
    DeviceBulkUpdate,
    DeviceCreate,
    DeviceFilters,
    DeviceSort,
    DeviceStats,
    DeviceUpdate,
    RadiusDeviceRequest,
    RadiusDeviceResponse,
)

logger = logging.getLogger(__name__)


class DeviceService:
    """Service for managing devices and MAC authentication."""

    def __init__(self, db: Session):
        self.db = db

    # Device CRUD Operations
    def create_device(
        self, device_data: DeviceCreate, auto_registered: bool = False
    ) -> Device:
        """Create a new device."""
        try:
            # Normalize MAC address
            normalized_mac = Device.normalize_mac(device_data.mac_address)

            # Check if MAC already exists
            existing = (
                self.db.query(Device)
                .filter(Device.mac_address == normalized_mac)
                .first()
            )
            if existing:
                raise ValueError(
                    f"Device with MAC address {normalized_mac} already exists"
                )

            # Verify customer exists
            customer = (
                self.db.query(Customer)
                .filter(Customer.id == device_data.customer_id)
                .first()
            )
            if not customer:
                raise ValueError(
                    f"Customer with ID {device_data.customer_id} not found"
                )

            device = Device(
                customer_id=device_data.customer_id,
                mac_address=normalized_mac,
                name=device_data.name,
                description=device_data.description,
                device_type=device_data.device_type,
                status="pending",
                is_auto_registered=auto_registered,
                is_approved=False,
            )

            self.db.add(device)
            self.db.commit()
            self.db.refresh(device)

            logger.info(
                f"Created device {device.id} with MAC {normalized_mac} for customer {device_data.customer_id}"
            )
            return device

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating device: {str(e)}")
            raise

    def get_device(self, device_id: int) -> Optional[Device]:
        """Get device by ID."""
        return (
            self.db.query(Device)
            .options(joinedload(Device.customer), joinedload(Device.approver))
            .filter(Device.id == device_id)
            .first()
        )

    def get_device_by_mac(self, mac_address: str) -> Optional[Device]:
        """Get device by MAC address."""
        try:
            normalized_mac = Device.normalize_mac(mac_address)
            return (
                self.db.query(Device)
                .options(joinedload(Device.customer))
                .filter(Device.mac_address == normalized_mac)
                .first()
            )
        except ValueError:
            return None

    def update_device(
        self, device_id: int, device_data: DeviceUpdate
    ) -> Optional[Device]:
        """Update device information."""
        try:
            device = self.db.query(Device).filter(Device.id == device_id).first()
            if not device:
                return None

            update_data = device_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(device, field, value)

            device.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(device)

            logger.info(f"Updated device {device_id}")
            return device

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating device {device_id}: {str(e)}")
            raise

    def delete_device(self, device_id: int) -> bool:
        """Delete a device."""
        try:
            device = self.db.query(Device).filter(Device.id == device_id).first()
            if not device:
                return False

            self.db.delete(device)
            self.db.commit()

            logger.info(f"Deleted device {device_id}")
            return True

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting device {device_id}: {str(e)}")
            raise

    def approve_device(
        self, device_id: int, approval_data: DeviceApproval, approved_by: int
    ) -> Optional[Device]:
        """Approve or reject a device."""
        try:
            device = self.db.query(Device).filter(Device.id == device_id).first()
            if not device:
                return None

            device.is_approved = approval_data.is_approved
            device.approved_by = approved_by
            device.approved_at = datetime.utcnow()

            if approval_data.is_approved:
                device.status = "active"
                logger.info(f"Approved device {device_id}")
            else:
                device.status = "blocked"
                logger.info(f"Rejected device {device_id}")

            self.db.commit()
            self.db.refresh(device)
            return device

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error approving device {device_id}: {str(e)}")
            raise

    def list_devices(
        self,
        filters: DeviceFilters,
        sort: DeviceSort,
        page: int = 1,
        per_page: int = 50,
    ) -> Tuple[List[Device], int]:
        """List devices with filtering, sorting, and pagination."""
        query = self.db.query(Device).options(
            joinedload(Device.customer), joinedload(Device.approver)
        )

        # Apply filters
        if filters.customer_id:
            query = query.filter(Device.customer_id == filters.customer_id)
        if filters.status:
            query = query.filter(Device.status == filters.status)
        if filters.device_type:
            query = query.filter(Device.device_type == filters.device_type)
        if filters.is_approved is not None:
            query = query.filter(Device.is_approved == filters.is_approved)
        if filters.is_auto_registered is not None:
            query = query.filter(
                Device.is_auto_registered == filters.is_auto_registered
            )
        if filters.mac_address:
            try:
                normalized_mac = Device.normalize_mac(filters.mac_address)
                query = query.filter(Device.mac_address == normalized_mac)
            except ValueError:
                # Invalid MAC format, return empty results
                return [], 0
        if filters.name:
            query = query.filter(Device.name.ilike(f"%{filters.name}%"))
        if filters.last_seen_after:
            query = query.filter(Device.last_seen >= filters.last_seen_after)
        if filters.last_seen_before:
            query = query.filter(Device.last_seen <= filters.last_seen_before)
        if filters.nas_identifier:
            query = query.filter(Device.last_nas_identifier == filters.nas_identifier)

        # Apply sorting
        sort_column = getattr(Device, sort.field, Device.last_seen)
        if sort.direction == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))

        # Get total count
        total = query.count()

        # Apply pagination
        offset = (page - 1) * per_page
        devices = query.offset(offset).limit(per_page).all()

        return devices, total

    def get_customer_devices(self, customer_id: int) -> List[Device]:
        """Get all devices for a customer."""
        return self.db.query(Device).filter(Device.customer_id == customer_id).all()

    def get_device_stats(self, customer_id: Optional[int] = None) -> DeviceStats:
        """Get device statistics."""
        query = self.db.query(Device)
        if customer_id:
            query = query.filter(Device.customer_id == customer_id)

        total = query.count()
        active = query.filter(Device.status == "active").count()
        pending = query.filter(Device.status == "pending").count()
        blocked = query.filter(Device.status == "blocked").count()
        auto_registered = query.filter(Device.is_auto_registered is True).count()

        # Devices in last 24 hours and 7 days
        now = datetime.utcnow()
        last_24h = query.filter(Device.created_at >= now - timedelta(hours=24)).count()
        last_7d = query.filter(Device.created_at >= now - timedelta(days=7)).count()

        return DeviceStats(
            total_devices=total,
            active_devices=active,
            pending_devices=pending,
            blocked_devices=blocked,
            auto_registered_devices=auto_registered,
            devices_last_24h=last_24h,
            devices_last_7d=last_7d,
        )

    # RADIUS Integration Methods
    def authenticate_device(self, request: RadiusDeviceRequest) -> RadiusDeviceResponse:
        """Authenticate a device via RADIUS MAC-Auth."""
        try:
            # Normalize MAC address
            normalized_mac = Device.normalize_mac(request.mac_address)

            # Find device
            device = self.get_device_by_mac(normalized_mac)

            if not device:
                # Check if any service allows auto-registration
                if request.service_id:
                    service = (
                        self.db.query(CustomerService)
                        .filter(
                            CustomerService.id == request.service_id,
                            CustomerService.auto_register_mac is True,
                        )
                        .first()
                    )

                    if service:
                        # Auto-register the device
                        device_data = DeviceCreate(
                            customer_id=service.customer_id,
                            mac_address=normalized_mac,
                            name=f"Auto-registered {normalized_mac}",
                            device_type="unknown",
                        )
                        device = self.create_device(device_data, auto_registered=True)

                        # Update last seen info
                        self._update_device_session_info(device, request)

                        # Check device limits
                        if self._check_device_limits(
                            service.customer_id, service.max_devices
                        ):
                            device.status = "active"
                            device.is_approved = True
                            self.db.commit()

                            return self._build_radius_response(device, service, True)
                        else:
                            return RadiusDeviceResponse(
                                access_granted=False,
                                rejection_reason="Maximum device limit exceeded",
                            )

                return RadiusDeviceResponse(
                    access_granted=False,
                    rejection_reason="Device not found and auto-registration disabled",
                )

            # Update last seen info
            self._update_device_session_info(device, request)

            # Check if device is active and approved
            if not device.is_active:
                return RadiusDeviceResponse(
                    access_granted=False,
                    device_id=device.id,
                    customer_id=device.customer_id,
                    rejection_reason=f"Device status: {device.status}, approved: {device.is_approved}",
                )

            # Find service with MAC auth enabled
            service = (
                self.db.query(CustomerService)
                .filter(
                    CustomerService.customer_id == device.customer_id,
                    CustomerService.mac_auth_enabled is True,
                )
                .first()
            )

            if not service:
                return RadiusDeviceResponse(
                    access_granted=False,
                    device_id=device.id,
                    customer_id=device.customer_id,
                    rejection_reason="No MAC authentication enabled service found",
                )

            return self._build_radius_response(device, service, True)

        except Exception as e:
            logger.error(f"Error authenticating device {request.mac_address}: {str(e)}")
            return RadiusDeviceResponse(
                access_granted=False, rejection_reason="Internal authentication error"
            )

    def _update_device_session_info(self, device: Device, request: RadiusDeviceRequest):
        """Update device session information."""
        device.last_seen = datetime.utcnow()
        if request.client_ip:
            device.last_ip_address = request.client_ip
        if request.nas_identifier:
            device.last_nas_identifier = request.nas_identifier
        if request.nas_port:
            device.last_nas_port = request.nas_port
        self.db.commit()

    def _check_device_limits(self, customer_id: int, max_devices: int) -> bool:
        """Check if customer is within device limits."""
        active_count = (
            self.db.query(Device)
            .filter(Device.customer_id == customer_id, Device.status == "active")
            .count()
        )
        return active_count < max_devices

    def _build_radius_response(
        self, device: Device, service: CustomerService, access_granted: bool
    ) -> RadiusDeviceResponse:
        """Build RADIUS response with service attributes."""
        if not access_granted:
            return RadiusDeviceResponse(
                access_granted=False,
                device_id=device.id,
                customer_id=device.customer_id,
                service_id=service.id,
            )

        # Get bandwidth limits from service template or tariff
        bandwidth_down = None
        bandwidth_up = None

        if service.internet_config:
            bandwidth_down = service.internet_config.download_speed_kbps
            bandwidth_up = service.internet_config.upload_speed_kbps

        return RadiusDeviceResponse(
            access_granted=True,
            device_id=device.id,
            customer_id=device.customer_id,
            service_id=service.id,
            bandwidth_limit_down=bandwidth_down,
            bandwidth_limit_up=bandwidth_up,
            session_timeout=3600,  # 1 hour default
            vlan_id=(
                service.internet_config.vlan_id if service.internet_config else None
            ),
        )

    # Bulk Operations
    def bulk_approve_devices(
        self, bulk_data: DeviceBulkApproval, approved_by: int
    ) -> DeviceBulkResponse:
        """Bulk approve/reject devices."""
        success_count = 0
        failed_count = 0
        errors = []

        for device_id in bulk_data.device_ids:
            try:
                approval_data = DeviceApproval(
                    is_approved=bulk_data.is_approved,
                    approval_reason=bulk_data.approval_reason,
                )
                result = self.approve_device(device_id, approval_data, approved_by)
                if result:
                    success_count += 1
                else:
                    failed_count += 1
                    errors.append(f"Device {device_id} not found")
            except Exception as e:
                failed_count += 1
                errors.append(f"Device {device_id}: {str(e)}")

        return DeviceBulkResponse(
            success_count=success_count, failed_count=failed_count, errors=errors
        )

    def bulk_update_devices(self, bulk_data: DeviceBulkUpdate) -> DeviceBulkResponse:
        """Bulk update devices."""
        success_count = 0
        failed_count = 0
        errors = []

        update_data = DeviceUpdate(
            status=bulk_data.status, device_type=bulk_data.device_type
        )

        for device_id in bulk_data.device_ids:
            try:
                result = self.update_device(device_id, update_data)
                if result:
                    success_count += 1
                else:
                    failed_count += 1
                    errors.append(f"Device {device_id} not found")
            except Exception as e:
                failed_count += 1
                errors.append(f"Device {device_id}: {str(e)}")

        return DeviceBulkResponse(
            success_count=success_count, failed_count=failed_count, errors=errors
        )
