"""Tests for MAC authentication and device management system."""
import pytest
from fastapi import status
from sqlalchemy.orm import Session

from app.models.networking.device import Device, DeviceGroup
from app.models.customer.base import Customer
from app.services.device import DeviceService


@pytest.mark.device
class TestDeviceService:
    """Test device management service layer."""

    def test_create_device(self, db_session: Session, sample_device_data: dict):
        """Test device creation with MAC validation."""
        # Create a test customer first
        customer = Customer(
            name="Test Customer",
            email="test@example.com",
            phone="+1234567890"
        )
        db_session.add(customer)
        db_session.commit()

        device_service = DeviceService(db_session)
        device_data = {**sample_device_data, "customer_id": customer.id}
        
        device = device_service.create_device(device_data)
        
        assert device.mac_address == "00:11:22:33:44:55"
        assert device.customer_id == customer.id
        assert device.status == "pending"
        assert not device.is_approved

    def test_mac_address_normalization(self, db_session: Session):
        """Test MAC address normalization and validation."""
        customer = Customer(
            name="Test Customer",
            email="test@example.com",
            phone="+1234567890"
        )
        db_session.add(customer)
        db_session.commit()

        device_service = DeviceService(db_session)
        
        # Test various MAC address formats
        test_cases = [
            ("00-11-22-33-44-55", "00:11:22:33:44:55"),
            ("0011.2233.4455", "00:11:22:33:44:55"),
            ("001122334455", "00:11:22:33:44:55"),
            ("00:11:22:33:44:55", "00:11:22:33:44:55"),
        ]
        
        for input_mac, expected_mac in test_cases:
            device_data = {
                "customer_id": customer.id,
                "mac_address": input_mac,
                "name": f"Test Device {input_mac}",
                "device_type": "test"
            }
            
            device = device_service.create_device(device_data)
            assert device.mac_address == expected_mac

    def test_device_approval_workflow(self, db_session: Session, super_admin):
        """Test device approval workflow."""
        customer = Customer(
            name="Test Customer",
            email="test@example.com",
            phone="+1234567890"
        )
        db_session.add(customer)
        db_session.commit()

        device_service = DeviceService(db_session)
        device_data = {
            "customer_id": customer.id,
            "mac_address": "00:11:22:33:44:55",
            "name": "Test Device",
            "device_type": "iot_sensor"
        }
        
        device = device_service.create_device(device_data)
        assert not device.is_approved
        
        # Approve device
        approved_device = device_service.approve_device(device.id, super_admin.id)
        assert approved_device.is_approved
        assert approved_device.approved_by == super_admin.id
        assert approved_device.approved_at is not None
        assert approved_device.status == "active"

    def test_radius_authentication(self, db_session: Session):
        """Test RADIUS MAC authentication."""
        customer = Customer(
            name="Test Customer",
            email="test@example.com",
            phone="+1234567890"
        )
        db_session.add(customer)
        db_session.commit()

        # Create approved device
        device = Device(
            customer_id=customer.id,
            mac_address="00:11:22:33:44:55",
            name="Test Device",
            device_type="iot_sensor",
            status="active",
            is_approved=True
        )
        db_session.add(device)
        db_session.commit()

        device_service = DeviceService(db_session)
        
        # Test successful authentication
        auth_result = device_service.authenticate_mac("00:11:22:33:44:55")
        assert auth_result is not None
        assert auth_result["customer_id"] == customer.id
        assert auth_result["device_id"] == device.id
        
        # Test failed authentication for unknown MAC
        auth_result = device_service.authenticate_mac("ff:ff:ff:ff:ff:ff")
        assert auth_result is None


@pytest.mark.device
@pytest.mark.api
class TestDeviceAPI:
    """Test device management API endpoints."""

    def test_get_devices(self, client, auth_headers, super_admin, db_session):
        """Test GET /api/v1/devices endpoint."""
        response = client.get("/api/v1/devices", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "size" in data

    def test_create_device_api(self, client, auth_headers, db_session):
        """Test POST /api/v1/devices endpoint."""
        # Create customer first
        customer = Customer(
            name="Test Customer",
            email="test@example.com",
            phone="+1234567890"
        )
        db_session.add(customer)
        db_session.commit()

        device_data = {
            "customer_id": customer.id,
            "mac_address": "00:11:22:33:44:55",
            "name": "Test Device",
            "description": "Test IoT Device",
            "device_type": "iot_sensor"
        }
        
        response = client.post("/api/v1/devices", json=device_data, headers=auth_headers)
        assert response.status_code == status.HTTP_201_CREATED
        
        data = response.json()
        assert data["mac_address"] == "00:11:22:33:44:55"
        assert data["customer_id"] == customer.id
        assert data["status"] == "pending"

    def test_approve_device_api(self, client, auth_headers, db_session):
        """Test POST /api/v1/devices/{device_id}/approve endpoint."""
        # Create customer and device
        customer = Customer(
            name="Test Customer",
            email="test@example.com",
            phone="+1234567890"
        )
        db_session.add(customer)
        db_session.commit()

        device = Device(
            customer_id=customer.id,
            mac_address="00:11:22:33:44:55",
            name="Test Device",
            device_type="iot_sensor",
            status="pending",
            is_approved=False
        )
        db_session.add(device)
        db_session.commit()

        response = client.post(
            f"/api/v1/devices/{device.id}/approve",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["is_approved"] is True
        assert data["status"] == "active"

    def test_radius_auth_endpoint(self, client, db_session):
        """Test internal RADIUS authentication endpoint."""
        # Create customer and approved device
        customer = Customer(
            name="Test Customer",
            email="test@example.com",
            phone="+1234567890"
        )
        db_session.add(customer)
        db_session.commit()

        device = Device(
            customer_id=customer.id,
            mac_address="00:11:22:33:44:55",
            name="Test Device",
            device_type="iot_sensor",
            status="active",
            is_approved=True
        )
        db_session.add(device)
        db_session.commit()

        # Test successful authentication
        response = client.post(
            "/api/v1/devices/radius/authenticate",
            json={"mac_address": "00:11:22:33:44:55"}
        )
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["authenticated"] is True
        assert data["customer_id"] == customer.id

        # Test failed authentication
        response = client.post(
            "/api/v1/devices/radius/authenticate",
            json={"mac_address": "ff:ff:ff:ff:ff:ff"}
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.device
@pytest.mark.integration
class TestDeviceIntegration:
    """Integration tests for device management system."""

    def test_device_lifecycle(self, client, auth_headers, db_session):
        """Test complete device lifecycle from creation to approval."""
        # Create customer
        customer = Customer(
            name="Test Customer",
            email="test@example.com",
            phone="+1234567890"
        )
        db_session.add(customer)
        db_session.commit()

        # 1. Create device
        device_data = {
            "customer_id": customer.id,
            "mac_address": "00:11:22:33:44:55",
            "name": "Test Device",
            "device_type": "iot_sensor"
        }
        
        response = client.post("/api/v1/devices", json=device_data, headers=auth_headers)
        assert response.status_code == status.HTTP_201_CREATED
        device_id = response.json()["id"]

        # 2. Verify device is pending
        response = client.get(f"/api/v1/devices/{device_id}", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["status"] == "pending"
        assert response.json()["is_approved"] is False

        # 3. Approve device
        response = client.post(f"/api/v1/devices/{device_id}/approve", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK

        # 4. Verify device is active
        response = client.get(f"/api/v1/devices/{device_id}", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["status"] == "active"
        assert response.json()["is_approved"] is True

        # 5. Test RADIUS authentication
        response = client.post(
            "/api/v1/devices/radius/authenticate",
            json={"mac_address": "00:11:22:33:44:55"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["authenticated"] is True
