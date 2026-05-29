from pydantic import BaseModel
from typing import List, Optional
from .models import Category, OrderType

class MenuItemRead(BaseModel):
    id: int
    name: str
    description: Optional[str]
    price: float
    category: Category
    available: bool

class OrderItemCreate(BaseModel):
    menu_item_id: int
    quantity: int

class OrderCreate(BaseModel):
    order_type: OrderType
    customer_name: str
    customer_phone: Optional[str] = None
    address: Optional[str] = None
    items: List[OrderItemCreate]

class OrderRead(BaseModel):
    id: int
    created_at: datetime
    order_type: OrderType
    customer_name: str
    total: float
    status: str