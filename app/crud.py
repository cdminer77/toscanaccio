import random
import math
from sqlmodel import Session, select
from typing import List, Optional
from datetime import datetime, timedelta

from .models import MenuItem, Order, OrderItem, Stock, VendingSlot, Rider, ProductRecognitionLog, OrderType, User, UserRole, NotificationLog
from .schemas import OrderCreate, MenuItemCreate, ProductRecognitionCreate, UserCreate, StockUpdate, RiderUpdate, MenuItemUpdate, VendingSlotUpdate, UserUpdate, RiderCreate

# Configurazione crittografia password con hashlib (aggira bug bcrypt/passlib su Python 3.12+)
import hashlib

def get_password_hash(password: str) -> str:
    salt = "toscanasalt123"
    db_hash = hashlib.sha256((password + salt).encode('utf-8')).hexdigest()
    return f"{salt}${db_hash}"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        salt, db_hash = hashed_password.split("$")
        check_hash = hashlib.sha256((plain_password + salt).encode('utf-8')).hexdigest()
        return check_hash == db_hash
    except Exception:
        return False

# Stato di simulazione per promozioni dinamiche (meteo e ora)
WEATHER_STATE = "SUNNY"
SIMULATED_LATE_NIGHT = False

# Coordinate della Cucina Centrale (Via Machiavelli 102, Livorno)
KITCHEN_LAT = 43.54877
KITCHEN_LNG = 10.31575

def calculate_distance_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calcola la distanza in chilometri tra due punti geografici con la formula di Haversine"""
    R = 6371.0  # Raggio terrestre medio in km
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

# --- USER AUTENTICAZIONE CRUD ---
def get_user_by_username(session: Session, username: str) -> Optional[User]:
    return session.exec(select(User).where(User.username == username)).first()

def get_user_by_email(session: Session, email: str) -> Optional[User]:
    return session.exec(select(User).where(User.email == email)).first()

def create_user(session: Session, user_data: UserCreate) -> User:
    hashed_pwd = get_password_hash(user_data.password)
    user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_pwd,
        role=user_data.role
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    
    # Se il ruolo è RIDER, lo aggiungiamo automaticamente anche alla tabella Rider per le consegne
    if user_data.role == UserRole.RIDER:
        rider = Rider(name=user_data.username, phone="+39 000 0000000", status="AVAILABLE")
        session.add(rider)
        session.commit()
        
    return user

# --- MENU ITEMS CRUD ---
def get_menu(session: Session, category: Optional[str] = None) -> List[MenuItem]:
    statement = select(MenuItem).where(MenuItem.available == True)
    if category:
        statement = statement.where(MenuItem.category == category)
    return session.exec(statement).all()

def create_menu_item(session: Session, item_data: MenuItemCreate) -> MenuItem:
    menu_item = MenuItem(**item_data.model_dump())
    session.add(menu_item)
    session.commit()
    session.refresh(menu_item)
    return menu_item

# --- STOCK & VENDING CRUD ---
def get_stock(session: Session) -> List[Stock]:
    return session.exec(select(Stock)).all()

def get_vending_slots(session: Session) -> List[VendingSlot]:
    return session.exec(select(VendingSlot)).all()

def get_riders(session: Session) -> List[Rider]:
    return session.exec(select(Rider)).all()

def get_users(session: Session) -> List[User]:
    return session.exec(select(User)).all()

def update_stock(session: Session, stock_id: int, current_quantity: int, min_alert_threshold: int) -> Optional[Stock]:
    stock = session.get(Stock, stock_id)
    if not stock:
        return None
    stock.current_quantity = current_quantity
    stock.min_alert_threshold = min_alert_threshold
    session.add(stock)
    session.commit()
    session.refresh(stock)
    return stock

def update_rider(session: Session, rider_id: int, rider_update: RiderUpdate) -> Optional[Rider]:
    rider = session.get(Rider, rider_id)
    if not rider:
        return None
    update_data = rider_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(rider, key, value)
    session.add(rider)
    session.commit()
    session.refresh(rider)
    return rider

# --- ORDERS CRUD (Con Calcolo Tariffa Dinamica Opzione B) ---
def create_order(session: Session, order_data: OrderCreate) -> Order:
    vending_code = None
    if order_data.order_type == OrderType.VENDING:
        # Genera un codice casuale di 6 cifre per lo sblocco del distributore automatico
        vending_code = str(random.randint(100000, 999999))

    delivery_fee = 0.0
    latitude = order_data.latitude
    longitude = order_data.longitude
    offer_expires_at = None

    if order_data.order_type == OrderType.DELIVERY:
        # Se non fornite, genera coordinate casuali stabili su Livorno
        if latitude is None or longitude is None:
            # Confini stabili Livorno: Lat 43.51 - 43.56, Lng 10.30 - 10.34
            latitude = 43.51 + random.random() * 0.05
            longitude = 10.30 + random.random() * 0.04
        
        # Calcola distanza geodetica reale
        distance = calculate_distance_km(KITCHEN_LAT, KITCHEN_LNG, latitude, longitude)
        
        # OPZIONE B: € 2.00 quota base + € 0.50 al km
        delivery_fee = round(2.00 + (distance * 0.50), 2)
        
        # Imposta scadenza dell'offerta di accettazione per i rider a 10 minuti
        offer_expires_at = datetime.utcnow() + timedelta(minutes=10)

    order = Order(
        order_type=order_data.order_type,
        customer_name=order_data.customer_name,
        customer_phone=order_data.customer_phone,
        address=order_data.address,
        vending_code=vending_code,
        latitude=latitude,
        longitude=longitude,
        delivery_fee=delivery_fee,
        offer_expires_at=offer_expires_at,
        payment_method=order_data.payment_method or "POS",
        payment_status=order_data.payment_status or "PAID",
        payment_tx_id=order_data.payment_tx_id,
        total=0.0
    )
    session.add(order)
    session.commit()
    session.refresh(order)

    # Aggiunge i singoli articoli e calcola il totale piatti
    total = 0.0
    for item in order_data.items:
        menu_item = session.get(MenuItem, item.menu_item_id)
        if menu_item:
            order_item = OrderItem(
                order_id=order.id,
                menu_item_id=item.menu_item_id,
                quantity=item.quantity
            )
            session.add(order_item)
            
            # Calcola prezzo promozionale se di tipo VENDING
            discount = 0.0
            if order_data.order_type == OrderType.VENDING:
                if WEATHER_STATE == "RAINY":
                    discount += 0.10
                elif WEATHER_STATE == "STORMY":
                    discount += 0.20
                if SIMULATED_LATE_NIGHT:
                    discount += 0.15
            
            discounted_price = round(menu_item.price * (1 - discount), 2)
            total += discounted_price * item.quantity

            # Decrementa scorte
            if order_data.order_type == OrderType.VENDING:
                slot_statement = select(VendingSlot).where(
                    VendingSlot.menu_item_id == item.menu_item_id,
                    VendingSlot.current_quantity >= item.quantity,
                    VendingSlot.status == "ACTIVE"
                )
                slot = session.exec(slot_statement).first()
                if slot:
                    slot.current_quantity -= item.quantity
                    session.add(slot)
            else:
                stock_statement = select(Stock).where(Stock.menu_item_id == item.menu_item_id)
                stock_item = session.exec(stock_statement).first()
                if stock_item:
                    stock_item.current_quantity = max(0, stock_item.current_quantity - item.quantity)
                    session.add(stock_item)

    # Il totale dell'ordine include anche il costo di consegna dinamico per la delivery
    order.total = round(total + delivery_fee, 2)
    session.add(order)
    session.commit()
    session.refresh(order)

    # --- TRIGGER NOTIFICATIONS ON NEW ORDER ---
    method_labels = {
        "CASH": "Contanti in Loco",
        "POS": "POS Carta di Credito",
        "PAYPAL": "PayPal",
        "SATISPAY": "Satispay Mobile",
        "CRYPTO_EURT": "Stablecoin EURT (Polygon)"
    }
    method_name = method_labels.get(order.payment_method, order.payment_method)

    if order.order_type == OrderType.VENDING:
        msg = f"Nuova vendita Vending H24! Metodo: {method_name}. Totale: € {order.total:.2f}. Codice sblocco generato: {order.vending_code}. Ritiro immediato presso SandenVendo."
        create_notification_log(
            session=session,
            recipient_name="Claudio",
            channel="WHATSAPP",
            phone_number="+39 333 1234567",
            message_content=msg,
            event_type="NEW_ORDER"
        )
    elif order.order_type == OrderType.DELIVERY:
        pay_info = "PAGAMENTO GIA' EFFETTUATO ONLINE. NON INCASSARE CONTANTI!" if order.payment_method != "CASH" else "RISCUOTERE CONTANTI ALLA CONSEGNA!"
        msg = f"Nuova consegna! Indirizzo: {order.address or 'Livorno'}. Cliente: {order.customer_name}. Pagamento: {method_name}. {pay_info} Compenso: € {order.delivery_fee:.2f}."
        create_notification_log(
            session=session,
            recipient_name="Roberto",
            channel="SMS",
            phone_number="+39 344 7654321",
            message_content=msg,
            event_type="NEW_ORDER"
        )

    return order

def get_orders(session: Session, order_type: Optional[str] = None, status: Optional[str] = None) -> List[Order]:
    statement = select(Order)
    if order_type:
        statement = statement.where(Order.order_type == order_type)
    if status:
        statement = statement.where(Order.status == status)
    return session.exec(statement).all()

def update_order_status(session: Session, order_id: int, status: str, rider_id: Optional[int] = None) -> Optional[Order]:
    order = session.get(Order, order_id)
    if not order:
        return None
    
    old_status = order.status
    order.status = status
    if rider_id is not None:
        order.rider_id = rider_id
        
    session.add(order)
    session.commit()
    session.refresh(order)
    
    # --- TRIGGER NOTIFICATIONS ON STATUS UPDATE ---
    if old_status != status:
        if status == "DELIVERING" and order.rider_id:
            # Rider accepts delivery
            rider = session.get(Rider, order.rider_id)
            rider_name = rider.name if rider else "Rider"
            msg = f"Consegna accettata dal Rider {rider_name}! Ordine #{order.id} per {order.customer_name} è in transito."
            create_notification_log(
                session=session,
                recipient_name="Claudio",
                channel="WHATSAPP",
                phone_number="+39 333 1234567",
                message_content=msg,
                event_type="DELIVERY_ASSIGNED"
            )
        elif status == "COMPLETED":
            # Order completed
            msg = f"Consegna completata per l'Ordine #{order.id}! Totale incassato: € {order.total:.2f}."
            create_notification_log(
                session=session,
                recipient_name="Claudio",
                channel="WHATSAPP",
                phone_number="+39 333 1234567",
                message_content=msg,
                event_type="DELIVERY_ASSIGNED"
            )
            
    return order

# --- PRODUCT RECOGNITION CRUD ---
def log_product_recognition(session: Session, log_data: ProductRecognitionCreate) -> ProductRecognitionLog:
    menu_item_statement = select(MenuItem).where(MenuItem.name == log_data.recognized_label)
    menu_item = session.exec(menu_item_statement).first()
    
    menu_item_id = menu_item.id if menu_item else None
    
    result_status = "VERIFIED"
    if not menu_item:
        result_status = "MISMATCH"
    elif log_data.confidence < 0.70:
        result_status = "MANUAL_CHECK"

    log = ProductRecognitionLog(
        menu_item_id=menu_item_id,
        recognized_label=log_data.recognized_label,
        confidence=log_data.confidence,
        image_url=log_data.image_url,
        result_status=result_status
    )
    session.add(log)
    session.commit()
    session.refresh(log)
    return log

def get_recognition_logs(session: Session) -> List[ProductRecognitionLog]:
    statement = select(ProductRecognitionLog).order_by(ProductRecognitionLog.timestamp.desc())
    return session.exec(statement).all()

# --- PREDICTION FORECAST CRUD ---
def get_production_forecast(session: Session):
    statement = select(MenuItem).where(MenuItem.available == True)
    items = session.exec(statement).all()
    
    today = datetime.now()
    weekday = today.weekday()
    
    day_multiplier = 1.0
    if weekday in [4, 5, 6]:
        day_multiplier = 1.45
        day_reason = "Elevata richiesta nel fine settimana per asporto e H24"
    else:
        day_multiplier = 0.95
        day_reason = "Feriale standard, flusso stabile"
        
    predictions = []
    from .models import Category
    for item in items:
        base_qty = 15
        if item.category in [Category.ZUPPA, Category.ZUPPA_PESCE, Category.SECONDO_CARNE, Category.QUINTO_QUARTO, Category.PIATTO_UNICO]:
            if item.price > 12.0:
                base_qty = 12
            else:
                base_qty = 18
        else:
            base_qty = 8
            
        recommended = int(base_qty * day_multiplier)
        
        reason = f"{day_reason}."
        if item.name == "Cinghiale in salmì":
            reason = f"Hero Product: {day_reason} (consigliato aumento del 20% per la marinatura)."
        elif item.name == "Cacciucco alla livornese":
            reason = "Preparazione fresca di mare consigliata per massimo 12 porzioni giornaliere."
            recommended = min(12, recommended)
        elif item.name == "Cecìna livornese":
            reason = f"Specialità Territorio: Consigliata preparazione per il vending H24 di {recommended} unità."

        predictions.append({
            "menu_item_id": item.id,
            "name": item.name,
            "category": item.category.value,
            "recommended_quantity": recommended,
            "reason": reason
        })
        
    return predictions

# --- NOTIFICATIONS CRUD ---
def create_notification_log(
    session: Session,
    recipient_name: str,
    channel: str,
    phone_number: str,
    message_content: str,
    event_type: str
) -> NotificationLog:
    log = NotificationLog(
        recipient_name=recipient_name,
        channel=channel,
        phone_number=phone_number,
        message_content=message_content,
        event_type=event_type
    )
    session.add(log)
    session.commit()
    session.refresh(log)
    return log

def get_notification_logs(session: Session) -> List[NotificationLog]:
    return session.exec(select(NotificationLog).order_by(NotificationLog.timestamp.desc())).all()

# --- ADMIN PRODUCT (MENU & SLOTS) CRUD ---
def update_menu_item(session: Session, item_id: int, item_data: MenuItemUpdate) -> Optional[MenuItem]:
    item = session.get(MenuItem, item_id)
    if not item:
        return None
    update_dict = item_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(item, key, value)
    session.add(item)
    session.commit()
    session.refresh(item)
    return item

def delete_menu_item(session: Session, item_id: int) -> bool:
    item = session.get(MenuItem, item_id)
    if not item:
        return False
    
    # Rimuove referenze in vending slot ed evita crash
    slots = session.exec(select(VendingSlot).where(VendingSlot.menu_item_id == item_id)).all()
    for slot in slots:
        slot.menu_item_id = None
        slot.status = "EMPTY"
        session.add(slot)
        
    stocks = session.exec(select(Stock).where(Stock.menu_item_id == item_id)).all()
    for stock in stocks:
        session.delete(stock)
        
    session.delete(item)
    session.commit()
    return True

def update_vending_slot(session: Session, slot_id: int, slot_data: VendingSlotUpdate) -> Optional[VendingSlot]:
    slot = session.get(VendingSlot, slot_id)
    if not slot:
        return None
    update_dict = slot_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(slot, key, value)
    session.add(slot)
    session.commit()
    session.refresh(slot)
    return slot

# --- ADMIN USER CRUD ---
def update_user(session: Session, user_id: int, user_data: UserUpdate) -> Optional[User]:
    user = session.get(User, user_id)
    if not user:
        return None
    
    old_role = user.role
    update_dict = user_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(user, key, value)
        
    session.add(user)
    session.commit()
    session.refresh(user)
    
    # Se l'utente è stato promosso a RIDER, creiamo automaticamente l'anagrafica RIDER se non esiste
    if old_role != UserRole.RIDER and user.role == UserRole.RIDER:
        existing_rider = session.exec(select(Rider).where(Rider.name == user.username)).first()
        if not existing_rider:
            new_rider = Rider(name=user.username, phone="+39 000 0000000", status="AVAILABLE")
            session.add(new_rider)
            session.commit()
            
    return user

def delete_user(session: Session, user_id: int) -> bool:
    user = session.get(User, user_id)
    if not user:
        return False
        
    # Rimuove rider collegato se presente
    if user.role == UserRole.RIDER:
        rider = session.exec(select(Rider).where(Rider.name == user.username)).first()
        if rider:
            session.delete(rider)
            
    session.delete(user)
    session.commit()
    return True

# --- ADMIN RIDER CRUD ---
def create_rider(session: Session, rider_data: RiderCreate) -> Rider:
    rider = Rider(**rider_data.model_dump())
    session.add(rider)
    session.commit()
    session.refresh(rider)
    return rider

def delete_rider(session: Session, rider_id: int) -> bool:
    rider = session.get(Rider, rider_id)
    if not rider:
        return False
    session.delete(rider)
    session.commit()
    return True
