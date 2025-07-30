from sqlalchemy import Column, Integer, ForeignKey, DateTime, Boolean, func, UniqueConstraint
from sqlalchemy.orm import relationship
from app.models.foundation.base import Base


class UserRole(Base):
    """Many-to-many relationship between users and roles"""
    __tablename__ = "user_roles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("administrators.id"), nullable=False)  # References administrators table
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    
    # Assignment properties
    is_active = Column(Boolean, default=True)  # Can temporarily disable role assignment
    assigned_by = Column(Integer, ForeignKey("administrators.id"))  # Who assigned this role
    expires_at = Column(DateTime(timezone=True))  # Optional expiration date
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("Administrator", foreign_keys=[user_id], back_populates="user_roles")
    role = relationship("Role", back_populates="user_roles")
    assigned_by_user = relationship("Administrator", foreign_keys=[assigned_by])
    
    # Ensure unique user-role combinations (but allow reactivation)
    __table_args__ = (
        UniqueConstraint('user_id', 'role_id', name='uq_user_role'),
    )
