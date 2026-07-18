from sqlmodel import SQLModel, Field, Relationship
from typing import List, Optional
from enum import Enum
from datetime import datetime

class Category(str, Enum):
    DOLCE = "Dolce"
    PIATTO_UNICO = "Piatto unico"
    QUINTO_QUARTO = "Quinto quarto"
    SECONDO_CARNE = "Secondo di carne"
    STREET_FOOD = "Street food / territorio"
    ZUPPA = "Zuppa"
    ZUPPA_PESCE = "Zuppa di pesce"
    GASTRONOMIA = "GASTRONOMIA"
    PROSCIUTTERIA = "PROSCIUTTERIA"
    SNACK = "SNACK"
    BEVANDE = "BEVANDE"
    ARTIGIANALE = "ARTIGIANALE"

class OrderType(str, Enum):
    PICKUP = "PICKUP"
    DELIVERY = "DELIVERY"
    VENDING = "VENDING"

class UserRole(str, Enum):
    CUSTOMER = "CUSTOMER"
    RIDER = "RIDER"
    ADMIN = "ADMIN"

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str
    role: UserRole = Field(default=UserRole.CUSTOMER)
    balance: float = Field(default=0.0)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class MenuItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    description: Optional[str] = None
    price: float
    category: Category
    available: bool = True
    daily_limit: Optional[int] = None  # per "Piatto del Giorno"
    version_size: Optional[str] = Field(default=None)  # "250g", "400g", "1kg", "standard"
    code: str = Field(default="")
    food_cost_pct: float = Field(default=0.0)
    container_code: str = Field(default="PYR-S")
    channels: str = Field(default="[]")
    availability_notes: Optional[str] = None
    note_ops: Optional[str] = None
    is_signature: bool = Field(default=False)
    is_vegan: bool = Field(default=False)
    requires_microwave: bool = Field(default=False)
    requires_hot_water: bool = Field(default=False)

class Stock(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    menu_item_id: int = Field(foreign_key="menuitem.id")
    current_quantity: int
    min_alert_threshold: int = Field(default=5)

class VendingSlot(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    position_code: str  # Esempio: "A1", "A2", "B1", "B2"
    menu_item_id: Optional[int] = Field(default=None, foreign_key="menuitem.id")
    current_quantity: int
    max_capacity: int = Field(default=10)
    status: str = Field(default="ACTIVE")  # ACTIVE, MAINTENANCE, EMPTY

class Rider(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    phone: str
    status: str = Field(default="AVAILABLE")  # AVAILABLE, DELIVERING, OFFLINE
    personal_data: Optional[str] = Field(default=None)  # Nome completo, CF, Email
    financial_data: Optional[str] = Field(default=None)  # IBAN, Dettagli pagamento
    work_area: Optional[str] = Field(default=None)  # Area geografica a Livorno

class Order(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    order_type: OrderType
    customer_name: str
    customer_phone: Optional[str] = None
    address: Optional[str] = None  # solo per delivery
    total: float
    status: str = "PENDING"  # PENDING, CONFIRMED, READY, DELIVERED, COMPLETED
    rider_id: Optional[int] = Field(default=None, foreign_key="rider.id")
    vending_code: Optional[str] = None  # Codice per ritiro da distributore
    
    # Nuovi campi per tracciabilità pagamenti
    payment_method: str = Field(default="POS")  # CASH, POS, PAYPAL, SATISPAY, CRYPTO_EURT
    payment_status: str = Field(default="PAID")  # UNPAID, PAID, REFUNDED, FAILED
    payment_tx_id: Optional[str] = Field(default=None)  # ID transazione (Paypal, Satispay o Blockchain hash)
    
    # Campi geografici e tariffari (Fase 2)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    delivery_fee: Optional[float] = None
    offer_expires_at: Optional[datetime] = None  # Scadenza dell'offerta per i rider (5/10 min)
    
    items: List["OrderItem"] = Relationship(back_populates="order")

class OrderItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    order_id: int = Field(foreign_key="order.id")
    menu_item_id: int = Field(foreign_key="menuitem.id")
    quantity: int

    order: "Order" = Relationship(back_populates="items")

class ProductRecognitionLog(SQLModel, table=True):
    """Log per tenere traccia dei riconoscimenti I.A. degli articoli venduti (Teachable Machine)"""
    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    menu_item_id: Optional[int] = Field(default=None, foreign_key="menuitem.id")
    recognized_label: str
    confidence: float
    image_url: Optional[str] = None
    result_status: str = "VERIFIED"  # VERIFIED, MISMATCH, MANUAL_CHECK

class NotificationLog(SQLModel, table=True):
    """Log per tenere traccia dei messaggi di notifica SMS / WhatsApp simulati"""
    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    recipient_name: str  # es: "Claudio", "Roberto", "Mario"
    channel: str  # "SMS" o "WHATSAPP"
    phone_number: str
    message_content: str
    event_type: str  # "FAULT_ALERT", "NEW_ORDER", "DELIVERY_ASSIGNED", "RESTORE_ALERT"
    status: str = "DELIVERED"

class ArchivedDocument(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    filename: str
    file_path: str
    category: str  # AFFITTI, FISCALE, HARDWARE, CONTRATTI, UTENZE, INGREDIENTI
    notes: Optional[str] = None
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)

class AccountingEntry(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    date: datetime = Field(default_factory=datetime.utcnow)
    description: str
    entry_type: str  # ENTRATA / USCITA
    amount: float  # Net amount
    vat_amount: float
    vat_rate: float  # 0.10 or 0.22
    amount_gross: float  # amount + vat_amount
    category: str  # VENDITE, ACQUISTI, AFFITTO, UTENZE, PERSONALE, FISCALE
    related_document_id: Optional[int] = Field(default=None, foreign_key="archiveddocument.id")

class PaymentDeadline(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    description: str
    amount: float  # Total gross amount
    due_date: datetime
    status: str = Field(default="PENDING")  # PENDING, PAID
    payment_date: Optional[datetime] = None
    category: str = Field(default="UTENZE")  # AFFITTI, FISCALE, UTENZE, etc.

