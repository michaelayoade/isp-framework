"""IPoE (IP over Ethernet) authentication models for fiber networks."""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, JSON, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class OLTProfile(Base):
    """OLT (Optical Line Terminal) configuration profiles."""
    __tablename__ = "olt_profiles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    
    # OLT Connection Details
    olt_type = Column(String(50), nullable=False)  # huawei, zte, nokia, etc.
    management_ip = Column(String(45), nullable=False)
    snmp_community = Column(String(100), nullable=True)
    snmp_version = Column(String(10), default="2c")
    
    # VLAN Configuration
    default_vlan_id = Column(Integer, nullable=True)
    vlan_range_start = Column(Integer, nullable=True)
    vlan_range_end = Column(Integer, nullable=True)
    
    # Speed Templates
    speed_profiles = Column(JSON, default=dict)  # {"profile_name": {"down": 100000, "up": 50000}}
    
    # RADIUS Settings
    radius_nas_identifier = Column(String(255), nullable=True)
    radius_nas_ip = Column(String(45), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    circuits = relationship("AccessCircuit", back_populates="olt_profile")


class AccessCircuit(Base):
    """Access circuits for IPoE authentication (fiber connections)."""
    __tablename__ = "access_circuits"

    id = Column(Integer, primary_key=True, index=True)
    circuit_id = Column(String(255), nullable=False, unique=True, index=True)
    
    # Circuit Information
    olt_profile_id = Column(Integer, ForeignKey("olt_profiles.id"), nullable=False)
    pon_port = Column(String(50), nullable=True)  # PON port on OLT
    onu_id = Column(Integer, nullable=True)  # ONU ID
    onu_serial = Column(String(100), nullable=True, index=True)  # ONU serial number
    
    # Customer Assignment
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True, index=True)
    service_id = Column(Integer, ForeignKey("customer_services.id"), nullable=True, index=True)
    
    # Network Configuration
    vlan_id = Column(Integer, nullable=True)
    inner_vlan_id = Column(Integer, nullable=True)  # For Q-in-Q
    mac_address = Column(String(17), nullable=True, index=True)  # ONU MAC
    
    # Location Information
    address = Column(Text, nullable=True)
    latitude = Column(String(20), nullable=True)
    longitude = Column(String(20), nullable=True)
    
    # Circuit Status
    status = Column(String(20), nullable=False, default="available")  # available, assigned, active, suspended, faulty
    provision_status = Column(String(20), default="pending")  # pending, provisioned, failed
    
    # Technical Details
    fiber_length_meters = Column(Integer, nullable=True)
    signal_level_dbm = Column(String(10), nullable=True)
    last_signal_check = Column(DateTime(timezone=True), nullable=True)
    
    # DHCP Option 82 Information
    agent_circuit_id = Column(String(255), nullable=True, index=True)  # DHCP Option 82 Circuit ID
    agent_remote_id = Column(String(255), nullable=True)  # DHCP Option 82 Remote ID
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    assigned_at = Column(DateTime(timezone=True), nullable=True)
    activated_at = Column(DateTime(timezone=True), nullable=True)
    
    # Assignment tracking
    assigned_by = Column(Integer, ForeignKey("administrators.id"), nullable=True)
    
    # Relationships
    olt_profile = relationship("OLTProfile", back_populates="circuits")
    customer = relationship("Customer")
    service = relationship("CustomerService")
    assigner = relationship("Administrator", foreign_keys=[assigned_by])
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_circuit_customer_status', 'customer_id', 'status'),
        Index('idx_circuit_onu_serial', 'onu_serial'),
        Index('idx_circuit_agent_circuit_id', 'agent_circuit_id'),
        Index('idx_circuit_status', 'status'),
    )
    
    def __repr__(self):
        return f"<AccessCircuit(id={self.id}, circuit_id={self.circuit_id}, customer_id={self.customer_id}, status={self.status})>"
    
    @property
    def is_available(self) -> bool:
        """Check if circuit is available for assignment."""
        return self.status == "available" and self.customer_id is None
    
    @property
    def is_active(self) -> bool:
        """Check if circuit is active and assigned."""
        return self.status == "active" and self.customer_id is not None


class IPoESession(Base):
    """IPoE session tracking for DHCP-based authentication."""
    __tablename__ = "ipoe_sessions"

    id = Column(Integer, primary_key=True, index=True)
    
    # Session Identification
    session_id = Column(String(255), nullable=False, unique=True, index=True)
    circuit_id = Column(String(255), ForeignKey("access_circuits.circuit_id"), nullable=False, index=True)
    
    # Customer and Service
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    service_id = Column(Integer, ForeignKey("customer_services.id"), nullable=False, index=True)
    
    # Network Information
    client_ip = Column(String(45), nullable=True)
    client_mac = Column(String(17), nullable=True, index=True)
    nas_identifier = Column(String(255), nullable=True)
    nas_port = Column(String(50), nullable=True)
    
    # DHCP Option 82 Data
    agent_circuit_id = Column(String(255), nullable=True)
    agent_remote_id = Column(String(255), nullable=True)
    
    # Session Status
    status = Column(String(20), nullable=False, default="active")  # active, terminated, expired
    
    # Bandwidth and Limits
    download_speed_kbps = Column(Integer, nullable=True)
    upload_speed_kbps = Column(Integer, nullable=True)
    session_timeout = Column(Integer, nullable=True)  # seconds
    
    # Usage Tracking
    bytes_in = Column(Integer, default=0)
    bytes_out = Column(Integer, default=0)
    packets_in = Column(Integer, default=0)
    packets_out = Column(Integer, default=0)
    
    # Session Timing
    start_time = Column(DateTime(timezone=True), server_default=func.now())
    last_update = Column(DateTime(timezone=True), server_default=func.now())
    end_time = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    circuit = relationship("AccessCircuit")
    customer = relationship("Customer")
    service = relationship("CustomerService")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_session_customer_status', 'customer_id', 'status'),
        Index('idx_session_circuit_status', 'circuit_id', 'status'),
        Index('idx_session_start_time', 'start_time'),
        Index('idx_session_client_ip', 'client_ip'),
    )
    
    def __repr__(self):
        return f"<IPoESession(id={self.id}, session_id={self.session_id}, customer_id={self.customer_id}, status={self.status})>"
    
    @property
    def duration_seconds(self) -> int:
        """Calculate session duration in seconds."""
        end = self.end_time or func.now()
        return int((end - self.start_time).total_seconds())
    
    @property
    def total_bytes(self) -> int:
        """Calculate total bytes transferred."""
        return self.bytes_in + self.bytes_out


class DHCPRelay(Base):
    """DHCP relay configuration for IPoE authentication."""
    __tablename__ = "dhcp_relays"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    
    # Relay Configuration
    relay_ip = Column(String(45), nullable=False)
    dhcp_server_ip = Column(String(45), nullable=False)
    radius_server_ip = Column(String(45), nullable=False)
    
    # Option 82 Settings
    enable_option82 = Column(Boolean, default=True)
    circuit_id_format = Column(String(255), default="{olt_ip}:{pon_port}:{onu_id}")
    remote_id_format = Column(String(255), default="{onu_serial}")
    
    # RADIUS Integration
    radius_nas_identifier = Column(String(255), nullable=True)
    radius_secret = Column(String(255), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<DHCPRelay(id={self.id}, name={self.name}, relay_ip={self.relay_ip})>"
