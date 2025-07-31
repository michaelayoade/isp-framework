"""
Network Service Layer - Modular Architecture

This service provides vendor-agnostic network management capabilities including:
- Network site management
- Device management across multiple vendors
- IP address management (IPAM)
- Network topology discovery and visualization
- Real-time monitoring and alerting
- Network change management
"""

import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from fastapi import Depends

from ..repositories.base import BaseRepository
from ..models.networking.networks import NetworkSite, NetworkDevice, DeviceConnection
from ..models.networking.ipam import IPPool, IPAllocation, DHCPReservation
from ..core.database import get_db
from ..core.exceptions import NotFoundError, ValidationError
from app.services.webhook_integration_service import WebhookTriggers

logger = logging.getLogger(__name__)


class NetworkSiteService:
    """Service for managing network sites and locations"""
    
    def __init__(self, db: Session, webhook_triggers: WebhookTriggers):
        self.db = db
        self.repository = BaseRepository(NetworkSite, db)
        self.webhook_triggers = webhook_triggers
    
    def create_site(self, site_data: Dict[str, Any]) -> NetworkSite:
        """Create a new network site"""
        try:
            site = NetworkSite(**site_data)
            self.db.add(site)
            self.db.commit()
            self.db.refresh(site)
            
            # Trigger webhook event
            try:
                self.webhook_triggers.network_site_created({
                    'id': site.id,
                    'name': site.name,
                    'site_type': site.site_type.value,
                    'address': site.address,
                    'latitude': float(site.latitude) if site.latitude else None,
                    'longitude': float(site.longitude) if site.longitude else None,
                    'status': site.status.value,
                    'created_at': site.created_at.isoformat()
                })
            except Exception as e:
                logger.warning(f"Failed to trigger network_site.created webhook: {e}")
            
            logger.info(f"Created network site {site.name}")
            return site
        except Exception as e:
            logger.error(f"Error creating network site: {e}")
            raise ValidationError(f"Failed to create network site: {str(e)}")
    
    def get_site_with_devices(self, site_id: int) -> Optional[NetworkSite]:
        """Get site with all associated devices"""
        return self.db.query(NetworkSite).filter(
            NetworkSite.id == site_id
        ).first()
    
    def get_sites_by_type(self, site_type: str) -> List[NetworkSite]:
        """Get all sites of a specific type"""
        return self.repository.get_all(filters={"site_type": site_type})
    
    def get_active_sites(self) -> List[NetworkSite]:
        """Get all active network sites"""
        return self.repository.get_all(filters={"is_active": True})


class NetworkDeviceService:
    """Service for managing network devices across all vendors"""
    
    def __init__(self, db: Session, webhook_triggers: WebhookTriggers):
        self.db = db
        self.repository = BaseRepository(NetworkDevice, db)
        self.webhook_triggers = webhook_triggers
    
    def create_device(self, device_data: Dict[str, Any]) -> NetworkDevice:
        """Create a new network device"""
        try:
            device = NetworkDevice(**device_data)
            self.db.add(device)
            self.db.commit()
            self.db.refresh(device)
            
            # Trigger webhook event
            try:
                self.webhook_triggers.network_device_created({
                    'id': device.id,
                    'name': device.name,
                    'device_type': device.device_type.value,
                    'site_id': device.site_id,
                    'ip_address': device.ip_address,
                    'mac_address': device.mac_address,
                    'status': device.status.value,
                    'created_at': device.created_at.isoformat()
                })
            except Exception as e:
                logger.warning(f"Failed to trigger network_device.created webhook: {e}")
            
            logger.info(f"Created network device {device.name} ({device.device_type})")
            return device
        except Exception as e:
            logger.error(f"Error creating network device: {e}")
            raise ValidationError(f"Failed to create network device: {str(e)}")
    
    def get_device_by_ip(self, ip_address: str) -> Optional[NetworkDevice]:
        """Get device by management IP address"""
        return self.repository.get_by_field("management_ip", ip_address)
    
    def get_devices_by_site(self, site_id: int) -> List[NetworkDevice]:
        """Get all devices at a specific site"""
        return self.repository.get_all(filters={"site_id": site_id})
    
    def get_devices_by_type(self, device_type: str) -> List[NetworkDevice]:
        """Get all devices of a specific type"""
        return self.repository.get_all(filters={"device_type": device_type})
    
    def get_devices_by_vendor(self, vendor: str) -> List[NetworkDevice]:
        """Get all devices from a specific vendor"""
        return self.repository.get_all(filters={"vendor": vendor})


class IPAMService:
    """Service for IP Address Management (IPAM)"""
    
    def __init__(self, db: Session):
        self.db = db
        self.pool_repo = BaseRepository(IPPool, db)
        self.allocation_repo = BaseRepository(IPAllocation, db)
        self.reservation_repo = BaseRepository(DHCPReservation, db)
    
    def create_pool(self, pool_data: Dict[str, Any]) -> IPPool:
        """Create a new IP pool"""
        try:
            pool = IPPool(**pool_data)
            return self.pool_repo.create(pool)
        except Exception as e:
            logger.error(f"Error creating IP pool: {e}")
            raise ValidationError(f"Failed to create IP pool: {str(e)}")
    
    def allocate_ip(self, allocation_data: Dict[str, Any]) -> IPAllocation:
        """Allocate an IP address from a pool"""
        try:
            allocation = IPAllocation(**allocation_data)
            return self.allocation_repo.create(allocation)
        except Exception as e:
            logger.error(f"Error allocating IP: {e}")
            raise ValidationError(f"Failed to allocate IP: {str(e)}")
    
    def get_pool_utilization(self, pool_id: int) -> Dict[str, Any]:
        """Get utilization statistics for an IP pool"""
        pool = self.pool_repo.get_by_id(pool_id)
        if not pool:
            raise NotFoundError(f"IP pool {pool_id} not found")
        
        total_ips = pool.total_ips
        allocated_count = self.allocation_repo.count(filters={"pool_id": pool_id})
        
        return {
            "pool_id": pool_id,
            "pool_name": pool.name,
            "total_ips": total_ips,
            "allocated_ips": allocated_count,
            "available_ips": total_ips - allocated_count,
            "utilization_percentage": (allocated_count / total_ips) * 100 if total_ips > 0 else 0
        }
    
    def get_available_ips(self, pool_id: int) -> List[str]:
        """Get available IP addresses in a pool"""
        pool = self.pool_repo.get_by_id(pool_id)
        if not pool:
            raise NotFoundError(f"IP pool {pool_id} not found")
        
        # This would need to be implemented based on your IP range logic
        # For now, return empty list as placeholder
        return []


class NetworkTopologyService:
    """Service for network topology discovery and visualization"""
    
    def __init__(self, db: Session):
        self.db = db
        self.device_repo = BaseRepository(NetworkDevice, db)
        self.connection_repo = BaseRepository(DeviceConnection, db)
    
    def get_network_topology(self, site_id: Optional[int] = None) -> Dict[str, Any]:
        """Get complete network topology"""
        try:
            query = self.db.query(NetworkDevice)
            if site_id:
                query = query.filter(NetworkDevice.site_id == site_id)
            
            devices = query.all()
            connections = self.connection_repo.get_all()
            
            return {
                "devices": devices,
                "connections": connections,
                "total_devices": len(devices),
                "total_connections": len(connections)
            }
        except Exception as e:
            logger.error(f"Error getting network topology: {e}")
            raise ValidationError(f"Failed to get network topology: {str(e)}")
    
    def get_device_neighbors(self, device_id: int) -> List[NetworkDevice]:
        """Get all devices connected to a specific device"""
        connections = self.connection_repo.get_all(
            filters={"from_device_id": device_id}
        )
        neighbor_ids = [conn.to_device_id for conn in connections]
        
        return self.device_repo.get_all(filters={"id": neighbor_ids})


class NetworkMonitoringService:
    """Service for network monitoring and alerting"""
    
    def __init__(self, db: Session, webhook_triggers: WebhookTriggers):
        self.db = db
        self.device_repo = BaseRepository(NetworkDevice, db)
        self.webhook_triggers = webhook_triggers
    
    def get_device_health(self, device_id: int) -> Dict[str, Any]:
        """Get health status of a specific device"""
        device = self.device_repo.get_by_id(device_id)
        if not device:
            raise NotFoundError(f"Device {device_id} not found")
        
        # Placeholder for actual monitoring logic
        return {
            "device_id": device_id,
            "device_name": device.name,
            "status": device.status,
            "last_seen": device.last_seen,
            "uptime": getattr(device, 'uptime', None),
            "health_score": 100 if device.status == "online" else 0
        }
    
    def get_network_overview(self) -> Dict[str, Any]:
        """Get high-level network overview"""
        try:
            total_devices = self.device_repo.count()
            online_devices = self.device_repo.count(filters={"status": "online"})
            offline_devices = self.device_repo.count(filters={"status": "offline"})
            
            return {
                "total_devices": total_devices,
                "online_devices": online_devices,
                "offline_devices": offline_devices,
                "uptime_percentage": (online_devices / total_devices * 100) if total_devices > 0 else 0,
                "last_updated": "2024-01-01T00:00:00Z"  # Placeholder
            }
        except Exception as e:
            logger.error(f"Error getting network overview: {e}")
            raise ValidationError(f"Failed to get network overview: {str(e)}")


# Factory function for dependency injection
def get_network_services(db: Session, webhook_triggers: WebhookTriggers) -> Dict[str, Any]:
    """
    Factory function to get all network services
    
    Args:
        db: Database session
        
    Returns:
        Dictionary of network services
    """
    return {
        "site_service": NetworkSiteService(db),
        "device_service": NetworkDeviceService(db),
        "ipam_service": IPAMService(db),
        "topology_service": NetworkTopologyService(db),
        "monitoring_service": NetworkMonitoringService(db)
    }


# Dependency injection helpers for FastAPI
def get_network_site_service(db: Session = Depends(get_db)) -> NetworkSiteService:
    """Get network site service instance"""
    return NetworkSiteService(db)


def get_network_device_service(db: Session = Depends(get_db)) -> NetworkDeviceService:
    """Get network device service instance"""
    return NetworkDeviceService(db)


def get_ipam_service(db: Session = Depends(get_db)) -> IPAMService:
    """Get IPAM service instance"""
    return IPAMService(db)


def get_network_topology_service(db: Session = Depends(get_db)) -> NetworkTopologyService:
    """Get network topology service instance"""
    return NetworkTopologyService(db)


def get_network_monitoring_service(db: Session = Depends(get_db)) -> NetworkMonitoringService:
    """Get network monitoring service instance"""
    return NetworkMonitoringService(db)
