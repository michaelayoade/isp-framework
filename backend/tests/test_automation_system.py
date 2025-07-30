"""Tests for Ansible automation system."""
import pytest
from fastapi import status
from sqlalchemy.orm import Session
from unittest.mock import MagicMock, patch

from app.models.automation.infrastructure import AutomationSite, AutomationDevice
from app.services.automation import AutomationService, AnsibleInventoryService


@pytest.mark.automation
class TestAutomationService:
    """Test Ansible automation service layer."""

    def test_create_site(self, db_session: Session):
        """Test automation site creation."""
        automation_service = AutomationService(db_session)
        
        site_data = {
            "name": "Test Data Center",
            "code": "TDC01",
            "site_type": "datacenter",
            "address": "123 Test Street",
            "contact_name": "Test Admin",
            "contact_email": "admin@test.com"
        }
        
        site = automation_service.create_site(site_data)
        
        assert site.name == "Test Data Center"
        assert site.code == "TDC01"
        assert site.site_type == "datacenter"
        assert site.is_active is True

    def test_create_device(self, db_session: Session):
        """Test automation device creation."""
        # Create site first
        site = AutomationSite(
            name="Test Site",
            code="TS01",
            site_type="datacenter"
        )
        db_session.add(site)
        db_session.commit()

        automation_service = AutomationService(db_session)
        
        device_data = {
            "site_id": site.id,
            "hostname": "test-router-01",
            "device_type": "router",
            "vendor": "mikrotik",
            "model": "CCR1009",
            "management_ip": "192.168.1.1",
            "ansible_user": "admin",
            "ansible_connection": "network_cli"
        }
        
        device = automation_service.create_device(device_data)
        
        assert device.hostname == "test-router-01"
        assert device.site_id == site.id
        assert device.vendor == "mikrotik"
        assert device.is_active is True

    def test_ansible_inventory_generation(self, db_session: Session):
        """Test dynamic Ansible inventory generation."""
        # Create test infrastructure
        site1 = AutomationSite(name="DC1", code="DC01", site_type="datacenter")
        site2 = AutomationSite(name="POP1", code="POP01", site_type="pop")
        db_session.add_all([site1, site2])
        db_session.commit()

        device1 = AutomationDevice(
            site_id=site1.id,
            hostname="dc1-router-01",
            device_type="router",
            vendor="mikrotik",
            management_ip="192.168.1.1",
            ansible_user="admin",
            ansible_connection="network_cli"
        )
        device2 = AutomationDevice(
            site_id=site2.id,
            hostname="pop1-switch-01",
            device_type="switch",
            vendor="cisco",
            management_ip="192.168.2.1",
            ansible_user="admin",
            ansible_connection="network_cli"
        )
        db_session.add_all([device1, device2])
        db_session.commit()

        inventory_service = AnsibleInventoryService(db_session)
        inventory = inventory_service.generate_inventory()
        
        # Verify inventory structure
        assert "all" in inventory
        assert "children" in inventory["all"]
        
        # Verify site groups
        assert "site_DC01" in inventory["all"]["children"]
        assert "site_POP01" in inventory["all"]["children"]
        
        # Verify device type groups
        assert "routers" in inventory["all"]["children"]
        assert "switches" in inventory["all"]["children"]
        
        # Verify vendor groups
        assert "mikrotik" in inventory["all"]["children"]
        assert "cisco" in inventory["all"]["children"]
        
        # Verify hosts
        assert "dc1-router-01" in inventory["site_DC01"]["hosts"]
        assert "pop1-switch-01" in inventory["site_POP01"]["hosts"]

    @patch('app.services.automation.subprocess.run')
    def test_ansible_playbook_execution(self, mock_subprocess, db_session: Session, mock_ansible_runner):
        """Test Ansible playbook execution."""
        # Mock successful subprocess execution
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stdout = "PLAY RECAP: test-host: ok=1"
        mock_subprocess.return_value.stderr = ""

        automation_service = AutomationService(db_session)
        
        result = automation_service.execute_playbook(
            playbook_path="/opt/ansible/playbooks/router_config.yml",
            inventory_data={"test-host": {"ansible_host": "192.168.1.1"}},
            extra_vars={"config_template": "basic"}
        )
        
        assert result["status"] == "successful"
        assert result["return_code"] == 0
        assert "PLAY RECAP" in result["stdout"]


@pytest.mark.automation
@pytest.mark.api
class TestAutomationAPI:
    """Test automation API endpoints."""

    def test_get_inventory(self, client, auth_headers):
        """Test GET /api/v1/automation/inventory endpoint."""
        response = client.get("/api/v1/automation/inventory", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "all" in data
        assert "children" in data["all"]

    def test_get_sites(self, client, auth_headers):
        """Test GET /api/v1/automation/sites endpoint."""
        response = client.get("/api/v1/automation/sites", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "items" in data
        assert "total" in data

    def test_create_site(self, client, auth_headers):
        """Test POST /api/v1/automation/sites endpoint."""
        site_data = {
            "name": "Test Data Center",
            "code": "TDC01",
            "site_type": "datacenter",
            "address": "123 Test Street",
            "contact_name": "Test Admin",
            "contact_email": "admin@test.com"
        }
        
        response = client.post("/api/v1/automation/sites", json=site_data, headers=auth_headers)
        assert response.status_code == status.HTTP_201_CREATED
        
        data = response.json()
        assert data["name"] == "Test Data Center"
        assert data["code"] == "TDC01"

    def test_create_device(self, client, auth_headers, db_session):
        """Test POST /api/v1/automation/devices endpoint."""
        # Create site first
        site = AutomationSite(
            name="Test Site",
            code="TS01",
            site_type="datacenter"
        )
        db_session.add(site)
        db_session.commit()

        device_data = {
            "site_id": site.id,
            "hostname": "test-router-01",
            "device_type": "router",
            "vendor": "mikrotik",
            "model": "CCR1009",
            "management_ip": "192.168.1.1",
            "ansible_user": "admin",
            "ansible_connection": "network_cli"
        }
        
        response = client.post("/api/v1/automation/devices", json=device_data, headers=auth_headers)
        assert response.status_code == status.HTTP_201_CREATED
        
        data = response.json()
        assert data["hostname"] == "test-router-01"
        assert data["site_id"] == site.id

    @patch('app.services.automation.subprocess.run')
    def test_execute_provisioning_task(self, mock_subprocess, client, auth_headers, db_session):
        """Test POST /api/v1/automation/tasks/provision endpoint."""
        # Mock successful execution
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stdout = "Task completed successfully"
        mock_subprocess.return_value.stderr = ""

        # Create test infrastructure
        site = AutomationSite(name="Test Site", code="TS01", site_type="datacenter")
        db_session.add(site)
        db_session.commit()

        device = AutomationDevice(
            site_id=site.id,
            hostname="test-router-01",
            device_type="router",
            vendor="mikrotik",
            management_ip="192.168.1.1"
        )
        db_session.add(device)
        db_session.commit()

        task_data = {
            "device_ids": [device.id],
            "playbook": "router_provision",
            "variables": {"config_template": "basic"}
        }
        
        response = client.post("/api/v1/automation/tasks/provision", json=task_data, headers=auth_headers)
        assert response.status_code == status.HTTP_202_ACCEPTED
        
        data = response.json()
        assert "task_id" in data
        assert data["status"] == "pending"


@pytest.mark.automation
@pytest.mark.integration
class TestAutomationIntegration:
    """Integration tests for automation system."""

    def test_complete_automation_workflow(self, client, auth_headers, db_session):
        """Test complete automation workflow from site creation to task execution."""
        # 1. Create site
        site_data = {
            "name": "Integration Test DC",
            "code": "ITDC01",
            "site_type": "datacenter",
            "address": "123 Integration Street"
        }
        
        response = client.post("/api/v1/automation/sites", json=site_data, headers=auth_headers)
        assert response.status_code == status.HTTP_201_CREATED
        site_id = response.json()["id"]

        # 2. Create device
        device_data = {
            "site_id": site_id,
            "hostname": "itdc01-router-01",
            "device_type": "router",
            "vendor": "mikrotik",
            "management_ip": "192.168.100.1",
            "ansible_user": "admin",
            "ansible_connection": "network_cli"
        }
        
        response = client.post("/api/v1/automation/devices", json=device_data, headers=auth_headers)
        assert response.status_code == status.HTTP_201_CREATED
        device_id = response.json()["id"]

        # 3. Verify inventory includes new infrastructure
        response = client.get("/api/v1/automation/inventory", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        inventory = response.json()
        
        assert "site_ITDC01" in inventory["all"]["children"]
        assert "routers" in inventory["all"]["children"]
        assert "mikrotik" in inventory["all"]["children"]

        # 4. Get dashboard stats
        response = client.get("/api/v1/automation/dashboard", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        stats = response.json()
        
        assert stats["total_sites"] >= 1
        assert stats["total_devices"] >= 1
        assert "sites_by_type" in stats
        assert "devices_by_vendor" in stats

    @patch('app.services.automation.subprocess.run')
    def test_device_backup_workflow(self, mock_subprocess, client, auth_headers, db_session):
        """Test device backup automation workflow."""
        # Mock successful backup execution
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stdout = "Backup completed successfully"
        mock_subprocess.return_value.stderr = ""

        # Create test infrastructure
        site = AutomationSite(name="Backup Test Site", code="BTS01", site_type="datacenter")
        db_session.add(site)
        db_session.commit()

        device = AutomationDevice(
            site_id=site.id,
            hostname="bts01-router-01",
            device_type="router",
            vendor="mikrotik",
            management_ip="192.168.200.1"
        )
        db_session.add(device)
        db_session.commit()

        # Execute backup task
        response = client.post(
            f"/api/v1/automation/devices/{device.id}/backup",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_202_ACCEPTED
        
        data = response.json()
        assert "task_id" in data
        assert data["message"] == "Backup task started"
