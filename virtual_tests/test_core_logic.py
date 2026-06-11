import pytest
from sqlmodel import Session, select
from app import crud
from app.models import MenuItem, Stock, VendingSlot, OrderType, Order
from app.schemas import OrderCreate, OrderItemCreate

def test_calculate_distance_km():
    """Verifica che il calcolo della distanza geodetica con Haversine sia accurato."""
    # Distanza da se stessa deve essere zero
    dist_zero = crud.calculate_distance_km(
        crud.KITCHEN_LAT, crud.KITCHEN_LNG, 
        crud.KITCHEN_LAT, crud.KITCHEN_LNG
    )
    assert dist_zero == 0.0

    # Distanza nota: da Cucina Centrale a Piazza Grande, Livorno (~ 43.551, 10.311)
    dist_piazza_grande = crud.calculate_distance_km(
        crud.KITCHEN_LAT, crud.KITCHEN_LNG,
        43.5512, 10.3114
    )
    # Deve essere una distanza positiva e ragionevole per Livorno centro (meno di 1 km)
    assert 0.1 < dist_piazza_grande < 1.0

def test_delivery_fee_calculation(session: Session):
    """Verifica il calcolo della tariffa di consegna dinamica (Opzione B)."""
    # Recupera un piatto dal database per l'ordine
    item = session.exec(select(MenuItem)).first()
    assert item is not None

    # Caso 1: Consegna esattamente presso la Cucina Centrale (distanza = 0)
    order_data_zero = OrderCreate(
        order_type=OrderType.DELIVERY,
        customer_name="Test Kitchen Delivery",
        customer_phone="+39 300 0000000",
        address="Via Machiavelli 102, Livorno",
        latitude=crud.KITCHEN_LAT,
        longitude=crud.KITCHEN_LNG,
        items=[OrderItemCreate(menu_item_id=item.id, quantity=1)]
    )
    
    order_zero = crud.create_order(session, order_data_zero)
    # Tariffa base = € 2.00. Distanza = 0. Tariffa totale = 2.00 + 0 * 0.50 = 2.00
    assert order_zero.delivery_fee == 2.00
    assert order_zero.total == pytest.approx(item.price + 2.00)

    # Caso 2: Consegna a 10 km di distanza
    # Troviamo delle coordinate a ~10 km di distanza.
    # Spostandosi di 0.09 gradi di latitudine a queste coordinate si fanno circa 10km.
    order_data_far = OrderCreate(
        order_type=OrderType.DELIVERY,
        customer_name="Test Far Delivery",
        customer_phone="+39 300 0000000",
        address="Via Lontana, Livorno",
        latitude=crud.KITCHEN_LAT + 0.09,
        longitude=crud.KITCHEN_LNG,
        items=[OrderItemCreate(menu_item_id=item.id, quantity=1)]
    )
    
    order_far = crud.create_order(session, order_data_far)
    dist = crud.calculate_distance_km(crud.KITCHEN_LAT, crud.KITCHEN_LNG, crud.KITCHEN_LAT + 0.09, crud.KITCHEN_LNG)
    expected_fee = round(2.00 + (dist * 0.50), 2)
    assert order_far.delivery_fee == expected_fee
    assert order_far.total == pytest.approx(item.price + expected_fee)

def test_dynamic_vending_promos(session: Session):
    """Verifica l'applicazione degli sconti dinamici (meteo e ora) su ordini VENDING."""
    item = session.exec(select(MenuItem)).first()
    assert item is not None

    # Assicuriamoci che ci sia stock in un vending slot attivo per questo piatto
    slot = session.exec(select(VendingSlot).where(VendingSlot.menu_item_id == item.id)).first()
    if not slot:
        slot = VendingSlot(position_code="Z1", menu_item_id=item.id, current_quantity=10, status="ACTIVE")
        session.add(slot)
        session.commit()
    else:
        slot.current_quantity = 10
        slot.status = "ACTIVE"
        session.add(slot)
        session.commit()

    order_payload = OrderCreate(
        order_type=OrderType.VENDING,
        customer_name="Vending Promo Tester",
        items=[OrderItemCreate(menu_item_id=item.id, quantity=1)]
    )

    # 1. Stato Normale (Soleggiato, Giorno)
    crud.WEATHER_STATE = "SUNNY"
    crud.SIMULATED_LATE_NIGHT = False
    
    order_normal = crud.create_order(session, order_payload)
    assert order_normal.total == pytest.approx(item.price)

    # Ripristiniamo la quantità dello slot
    slot.current_quantity = 10
    session.add(slot)
    session.commit()

    # 2. Stato Maltempo (RAINY) e Notte Fonda (LATE_NIGHT)
    # Sconto pioggia (10%) + Sconto notte (15%) = 25% di sconto totale
    crud.WEATHER_STATE = "RAINY"
    crud.SIMULATED_LATE_NIGHT = True

    order_discounted = crud.create_order(session, order_payload)
    expected_price = round(item.price * (1 - 0.25), 2)
    assert order_discounted.total == pytest.approx(expected_price)

    # Ripristina lo stato globale di simulazione
    crud.WEATHER_STATE = "SUNNY"
    crud.SIMULATED_LATE_NIGHT = False
