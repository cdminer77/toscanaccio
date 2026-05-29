from sqlmodel import Session, select
from .models import MenuItem, Order, OrderItem
from .schemas import OrderCreate

def get_menu(session: Session, category: str = None):
    statement = select(MenuItem).where(MenuItem.available == True)
    if category:
        statement = statement.where(MenuItem.category == category)
    return session.exec(statement).all()

def create_order(session: Session, order_data: OrderCreate):
    total = 0
    order = Order(
        order_type=order_data.order_type,
        customer_name=order_data.customer_name,
        customer_phone=order_data.customer_phone,
        address=order_data.address,
        total=0  # verrà calcolato dopo
    )
    session.add(order)
    session.commit()
    session.refresh(order)

    for item in order_data.items:
        menu_item = session.get(MenuItem, item.menu_item_id)
        if menu_item:
            order_item = OrderItem(order_id=order.id, menu_item_id=item.menu_item_id, quantity=item.quantity)
            session.add(order_item)
            total += menu_item.price * item.quantity

    order.total = total
    session.add(order)
    session.commit()
    session.refresh(order)
    return order