from sqlmodel import SQLModel, Field, Relationship
from typing import List, Optional
from enum import Enum
from datetime import datetime

class Category(str, Enum):
    GASTRONOMIA = "GASTRONOMIA"
    PROSCIUTTERIA = "PROSCIUTTERIA"

class OrderType(str, Enum):
    PICKUP = "PICKUP"
    DELIVERY = "DELIVERY"
    VENDING = "VENDING"

class MenuItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    description: Optional[str] = None
    price: float
    category: Category
    available: bool = True
    daily_limit: Optional[int] = None  # per "Piatto del Giorno"

class OrderItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    order_id: int = Field(foreign_key="order.id")
    menu_item_id: int = Field(foreign_key="menuitem.id")
    quantity: int

class Order(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    order_type: OrderType
    customer_name: str
    customer_phone: Optional[str] = None
    address: Optional[str] = None  # solo per delivery
    total: float
    status: str = "PENDING"  # PENDING, CONFIRMED, READY, DELIVERED, COMPLETED
    items: List[OrderItem] = Relationship(back_populates="order")

# Relazione inversa
OrderItem.order = Relationship(back_populates="items")