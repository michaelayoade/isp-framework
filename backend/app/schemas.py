from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr


# Customer schemas
class CustomerBase(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    category: Optional[str] = "person"  # person or company
    street_1: Optional[str] = None
    street_2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: Optional[str] = "Nigeria"


class CustomerCreate(CustomerBase):
    pass


class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    status: Optional[str] = None
    street_1: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None


class Customer(CustomerBase):
    id: int
    status: str
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# Response schemas
class CustomerList(BaseModel):
    customers: List[Customer]
    total: int
    page: int
    per_page: int


# Token schemas
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


# Service Plan schemas
class ServicePlanBase(BaseModel):
    name: str
    display_name: Optional[str] = None
    service_type: Optional[str] = "internet"
    price: int
    currency: Optional[str] = "NGN"
    billing_cycle: Optional[str] = "monthly"
    download_speed: Optional[int] = None
    upload_speed: Optional[int] = None
    data_limit: Optional[int] = None


class ServicePlanCreate(ServicePlanBase):
    pass


class ServicePlan(ServicePlanBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Customer Service schemas
class CustomerServiceCreate(BaseModel):
    customer_id: int
    service_plan_id: int
    custom_price: Optional[int] = None
    discount_percentage: Optional[int] = 0


class CustomerService(BaseModel):
    id: int
    customer_id: int
    service_plan_id: int
    status: str
    start_date: datetime
    custom_price: Optional[int]
    discount_percentage: int

    class Config:
        from_attributes = True
