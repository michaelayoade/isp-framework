"""
Location Models

This module contains SQLAlchemy models for location management.
"""

from sqlalchemy import Column, Integer, String, DECIMAL, DateTime, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from .base import Base


class Location(Base):
    """Locations for organizing network infrastructure and customers"""
    __tablename__ = "locations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    
    # Extended Location Data
    address = Column(String(255))
    city = Column(String(100))
    state_province = Column(String(100))
    postal_code = Column(String(20))
    country = Column(String(100), default="Nigeria")
    
    # Geographic Data
    latitude = Column(DECIMAL(10, 8))
    longitude = Column(DECIMAL(11, 8))
    
    # Framework Integration
    custom_fields = Column(JSONB, default={})  # Dynamic custom fields
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<Location(id={self.id}, name='{self.name}', city='{self.city}')>"
