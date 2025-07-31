"""Device model for MAC authentication and IoT device management."""

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base


class Device(Base):
    """Device model for MAC-based authentication and IoT device management."""

    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(
        Integer, ForeignKey("customers.id"), nullable=False, index=True
    )
    mac_address = Column(
        String(17), nullable=False, unique=True, index=True
    )  # AA:BB:CC:DD:EE:FF
    name = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    device_type = Column(
        String(50), nullable=True
    )  # router, switch, camera, sensor, etc.

    # Status and lifecycle
    status = Column(
        String(20), nullable=False, default="pending"
    )  # pending, active, blocked, expired
    is_auto_registered = Column(Boolean, default=False)  # Auto-registered via MAC-auth
    is_approved = Column(Boolean, default=False)  # Admin approved

    # Network information
    last_ip_address = Column(String(45), nullable=True)  # IPv4 or IPv6
    last_nas_identifier = Column(
        String(255), nullable=True
    )  # NAS that last saw this device
    last_nas_port = Column(String(50), nullable=True)  # Port/interface on NAS

    # Timestamps
    first_seen = Column(DateTime(timezone=True), server_default=func.now())
    last_seen = Column(DateTime(timezone=True), server_default=func.now())
    approved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Approval tracking
    approved_by = Column(Integer, ForeignKey("administrators.id"), nullable=True)

    # Relationships
    customer = relationship("Customer", back_populates="devices")
    approver = relationship("Administrator", foreign_keys=[approved_by])

    # Indexes for performance
    __table_args__ = (
        Index("idx_device_customer_status", "customer_id", "status"),
        Index("idx_device_mac_status", "mac_address", "status"),
        Index("idx_device_last_seen", "last_seen"),
    )

    def __repr__(self):
        return f"<Device(id={self.id}, mac={self.mac_address}, customer_id={self.customer_id}, status={self.status})>"

    @property
    def is_active(self) -> bool:
        """Check if device is active and approved."""
        return self.status == "active" and self.is_approved

    @property
    def formatted_mac(self) -> str:
        """Return MAC address in standard format."""
        return self.mac_address.upper().replace("-", ":")

    @classmethod
    def normalize_mac(cls, mac: str) -> str:
        """Normalize MAC address to standard format (AA:BB:CC:DD:EE:FF)."""
        # Remove common separators and convert to uppercase
        cleaned = mac.replace(":", "").replace("-", "").replace(".", "").upper()

        # Validate length
        if len(cleaned) != 12:
            raise ValueError(f"Invalid MAC address length: {mac}")

        # Validate hex characters
        try:
            int(cleaned, 16)
        except ValueError:
            raise ValueError(f"Invalid MAC address format: {mac}")

        # Format as AA:BB:CC:DD:EE:FF
        return ":".join([cleaned[i : i + 2] for i in range(0, 12, 2)])


class DeviceGroup(Base):
    """Device groups for organizing and managing devices."""

    __tablename__ = "device_groups"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(
        Integer, ForeignKey("customers.id"), nullable=False, index=True
    )
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Group settings
    auto_approve_devices = Column(Boolean, default=False)
    default_device_status = Column(String(20), default="pending")
    bandwidth_limit_mbps = Column(Integer, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    customer = relationship("Customer")
    devices = relationship(
        "Device", secondary="device_group_members", back_populates="groups"
    )


class DeviceGroupMember(Base):
    """Many-to-many relationship between devices and groups."""

    __tablename__ = "device_group_members"

    id = Column(Integer, primary_key=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False)
    group_id = Column(Integer, ForeignKey("device_groups.id"), nullable=False)
    added_at = Column(DateTime(timezone=True), server_default=func.now())

    # Unique constraint
    __table_args__ = (
        Index("idx_device_group_unique", "device_id", "group_id", unique=True),
    )
