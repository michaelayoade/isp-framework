"""
Router and RouterSector Models

Core router models based on ISP Framework database schema.
These models represent network routers and their sectors for service provisioning.
"""

from sqlalchemy import (
    ARRAY,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import INET
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Router(Base):
    """Network router model matching ISP Framework database schema"""

    __tablename__ = "routers"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), unique=True, nullable=False)
    model = Column(String(255))
    partners_ids = Column(ARRAY(Integer), nullable=False, default=list)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    address = Column(Text)
    ip = Column(INET, nullable=False, unique=True)
    gps = Column(Text)  # area coordinates
    gps_point = Column(String(100))  # point coordinates
    authorization_method = Column(String(50), default="none")
    accounting_method = Column(String(50), default="none")
    nas_type = Column(Integer, nullable=False)
    nas_ip = Column(INET)
    radius_secret = Column(String(255))
    status = Column(
        String(20), default="unknown"
    )  # ok, api_error, error, disabled, unknown
    pool_ids = Column(ARRAY(Integer), default=list)

    # MikroTik API Configuration
    api_login = Column(String(100))
    api_password = Column(String(255))
    api_port = Column(Integer, default=8728)
    api_enable = Column(Boolean, default=False)
    api_status = Column(String(20), default="unknown")
    shaper = Column(Boolean, default=False)
    shaper_id = Column(Integer)
    shaping_type = Column(String(20), default="simple")

    # Status tracking
    last_status = Column(DateTime(timezone=True))
    cpu_usage = Column(Integer, default=0)
    platform = Column(String(100))
    board_name = Column(String(100))
    version = Column(String(100))
    connection_error = Column(Integer, default=0)
    last_api_error = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    location = relationship("Location", back_populates="routers")
    sectors = relationship(
        "RouterSector", back_populates="router", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Router(id={self.id}, title='{self.title}', ip='{self.ip}', status='{self.status}')>"


class RouterSector(Base):
    """Router sector model for network segmentation"""

    __tablename__ = "router_sectors"

    id = Column(Integer, primary_key=True, index=True)
    router_id = Column(
        Integer, ForeignKey("routers.id", ondelete="CASCADE"), nullable=False
    )
    title = Column(String(255), nullable=False)
    speed_down = Column(Integer, nullable=False)  # kbps
    speed_up = Column(Integer, nullable=False)  # kbps
    limit_at = Column(Integer, default=95)  # percentage

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    router = relationship("Router", back_populates="sectors")

    def __repr__(self):
        return f"<RouterSector(id={self.id}, title='{self.title}', router_id={self.router_id})>"
