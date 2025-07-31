from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.sql import func

from app.core.database import Base


class Administrator(Base):
    __tablename__ = "administrators"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(255))
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    role = Column(String(50), nullable=False, default="admin")
    permissions = Column(JSON, default=list)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True))


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True)
    phone = Column(String(50))
    category = Column(String(20), default="person")  # person or company
    status = Column(String(20), default="active")  # active, blocked, disabled

    # Address
    street_1 = Column(String(255))
    street_2 = Column(String(255))
    city = Column(String(100))
    state = Column(String(100))
    zip_code = Column(String(20))
    country = Column(String(100), default="Nigeria")

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class ServicePlan(Base):
    __tablename__ = "service_plans"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    display_name = Column(String(255))
    service_type = Column(String(50), default="internet")  # internet, voice, bundle

    # Pricing
    price = Column(Integer, nullable=False)  # in kobo/cents
    currency = Column(String(3), default="NGN")
    billing_cycle = Column(String(20), default="monthly")  # monthly, quarterly, yearly

    # Internet specific
    download_speed = Column(Integer)  # in Mbps
    upload_speed = Column(Integer)  # in Mbps
    data_limit = Column(Integer)  # in GB, null for unlimited

    # Status
    is_active = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class CustomerService(Base):
    __tablename__ = "customer_services"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    service_plan_id = Column(Integer, ForeignKey("service_plans.id"), nullable=False)

    # Service details
    status = Column(String(20), default="active")  # active, suspended, terminated
    start_date = Column(DateTime(timezone=True), server_default=func.now())
    end_date = Column(DateTime(timezone=True))

    # Custom pricing (if different from plan)
    custom_price = Column(Integer)
    discount_percentage = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
