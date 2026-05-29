from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from .models import Category, OrderType, UserRole

# User authentication schemas
class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    role: Optional[UserRole] = UserRole.CUSTOMER

class UserRead(BaseModel):
    id: int
    username: str
    email: str
    role: UserRole
    created_at: datetime

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserRead

# MenuItem schemas
class MenuItemRead(BaseModel):
    id: int
    name: str
    description: Optional[str]
    price: float
    category: Category
    available: bool
    version_size: Optional[str] = None

class MenuItemCreate(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    category: Category
    available: bool = True
    daily_limit: Optional[int] = None
    version_size: Optional[str] = None

# OrderItem schemas
class OrderItemCreate(BaseModel):
    menu_item_id: int
    quantity: int

class OrderItemRead(BaseModel):
    id: int
    menu_item_id: int
    quantity: int

# Order schemas
class OrderCreate(BaseModel):
    order_type: OrderType
    customer_name: str
    customer_phone: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    items: List[OrderItemCreate]

class OrderRead(BaseModel):
    id: int
    created_at: datetime
    order_type: OrderType
    customer_name: str
    customer_phone: Optional[str] = None
    address: Optional[str] = None
    total: float
    status: str
    rider_id: Optional[int] = None
    vending_code: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    delivery_fee: Optional[float] = None
    offer_expires_at: Optional[datetime] = None
    items: List[OrderItemRead]

# VendingSlot schemas
class VendingSlotRead(BaseModel):
    id: int
    position_code: str
    menu_item_id: Optional[int] = None
    current_quantity: int
    max_capacity: int
    status: str

# Rider schemas
class RiderRead(BaseModel):
    id: int
    name: str
    phone: str
    status: str
    personal_data: Optional[str] = None
    financial_data: Optional[str] = None
    work_area: Optional[str] = None

class StockUpdate(BaseModel):
    current_quantity: int
    min_alert_threshold: int

class RiderUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    status: Optional[str] = None
    personal_data: Optional[str] = None
    financial_data: Optional[str] = None
    work_area: Optional[str] = None

# ProductRecognition schemas
class ProductRecognitionCreate(BaseModel):
    recognized_label: str
    confidence: float
    image_url: Optional[str] = None

class ProductRecognitionRead(BaseModel):
    id: int
    timestamp: datetime
    menu_item_id: Optional[int] = None
    recognized_label: str
    confidence: float
    image_url: Optional[str] = None
    result_status: str

class NotificationLogRead(BaseModel):
    id: int
    timestamp: datetime
    recipient_name: str
    channel: str
    phone_number: str
    message_content: str
    event_type: str
    status: str

# CRUD Schemas for Administration
class MenuItemUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    category: Optional[Category] = None
    available: Optional[bool] = None
    daily_limit: Optional[int] = None
    version_size: Optional[str] = None

class VendingSlotUpdate(BaseModel):
    menu_item_id: Optional[int] = None
    current_quantity: Optional[int] = None
    max_capacity: Optional[int] = None
    status: Optional[str] = None

class UserUpdate(BaseModel):
    email: Optional[str] = None
    role: Optional[UserRole] = None

class RiderCreate(BaseModel):
    name: str
    phone: str
    status: Optional[str] = "AVAILABLE"
    personal_data: Optional[str] = None
    financial_data: Optional[str] = None
    work_area: Optional[str] = None
