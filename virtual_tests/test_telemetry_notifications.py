import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select
from app.models import VendingSlot, NotificationLog, MenuItem, OrderType
from app.schemas import OrderCreate, OrderItemCreate
from app import crud

def test_get_telemetry(client: TestClient):
    """Verifica il recupero dei dati telemetrici H24."""
    response = client.get("/vending/telemetry")
    assert response.status_code == 200
    data = response.json()
    assert "gdrink1" in data
    assert "gdrink2" in data
    assert "compressor_status" in data["gdrink1"]

def test_telemetry_fault_jam(client: TestClient, session: Session):
    """Verifica l'iniezione e la risoluzione di un guasto a spirale bloccata (JAM)."""
    # 1. Assicuriamo che esista uno slot C4 nel database per collegarsi all'anomalia
    slot = session.exec(select(VendingSlot).where(VendingSlot.position_code == "C4")).first()
    if not slot:
        slot = VendingSlot(position_code="C4", current_quantity=5, max_capacity=10, status="ACTIVE")
        session.add(slot)
        session.commit()
    else:
        slot.status = "ACTIVE"
        session.add(slot)
        session.commit()

    # 2. Inietta il guasto JAM
    payload_fault = {
        "machine": "gdrink1",
        "fault_type": "JAM"
    }
    response_fault = client.post("/vending/telemetry/fault", json=payload_fault)
    assert response_fault.status_code == 200
    data_fault = response_fault.json()
    assert "Spirale ripiano C bloccata (Slot C4)" in data_fault["telemetry"]["grid_faults"]

    # 3. Verifica che lo slot C4 sia passato a MAINTENANCE nel database
    session.expire_all() # rinfresca la sessione
    slot_db = session.exec(select(VendingSlot).where(VendingSlot.position_code == "C4")).first()
    assert slot_db.status == "MAINTENANCE"

    # 4. Verifica che sia stata generata una notifica WhatsApp per il tecnico Claudio
    notifications = session.exec(select(NotificationLog).where(NotificationLog.recipient_name == "Claudio")).all()
    assert len(notifications) > 0
    assert any("Slot C4" in n.message_content and n.channel == "WHATSAPP" for n in notifications)

    # 5. Esegui il ripristino (CLEAR)
    payload_clear = {
        "machine": "gdrink1",
        "fault_type": "CLEAR"
    }
    response_clear = client.post("/vending/telemetry/fault", json=payload_clear)
    assert response_clear.status_code == 200
    data_clear = response_clear.json()
    assert len(data_clear["telemetry"]["grid_faults"]) == 0

    # 6. Verifica che sia stata generata la notifica di ripristino
    session.expire_all()
    notifications_final = session.exec(select(NotificationLog).where(NotificationLog.event_type == "RESTORE_ALERT")).all()
    assert len(notifications_final) > 0

def test_telemetry_fault_temp_high(client: TestClient, session: Session):
    """Verifica l'allarme di temperatura elevata (TEMP_HIGH) e invio SMS."""
    payload = {
        "machine": "gdrink1",
        "fault_type": "TEMP_HIGH"
    }
    response = client.post("/vending/telemetry/fault", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["telemetry"]["zone1_temp"] == 14.8
    assert data["telemetry"]["compressor_status"] == "OVERHEATED_ALARM"

    # Verifica la presenza della notifica SMS ad alta priorità
    notifications = session.exec(select(NotificationLog).where(
        NotificationLog.event_type == "FAULT_ALERT",
        NotificationLog.channel == "SMS"
    )).all()
    assert len(notifications) > 0
    assert any("temperatura elevata" in n.message_content for n in notifications)

def test_order_notifications(client: TestClient, session: Session):
    """Verifica che la creazione di ordini generi i corretti log di notifica."""
    item = session.exec(select(MenuItem)).first()
    assert item is not None

    # Ordine VENDING -> Notifica WhatsApp a Claudio
    vending_payload = OrderCreate(
        order_type=OrderType.VENDING,
        customer_name="Mario Rossi",
        items=[OrderItemCreate(menu_item_id=item.id, quantity=1)]
    )
    crud.create_order(session, vending_payload)
    notifications_vending = session.exec(select(NotificationLog).where(
        NotificationLog.event_type == "NEW_ORDER",
        NotificationLog.recipient_name == "Claudio"
    )).all()
    assert len(notifications_vending) > 0
    assert any("Vending" in n.message_content for n in notifications_vending)

    # Ordine DELIVERY -> Notifica SMS a Roberto (Rider)
    delivery_payload = OrderCreate(
        order_type=OrderType.DELIVERY,
        customer_name="Luigi Bianchi",
        address="Via delle Vettovaglie 12, Livorno",
        items=[OrderItemCreate(menu_item_id=item.id, quantity=1)]
    )
    crud.create_order(session, delivery_payload)
    notifications_delivery = session.exec(select(NotificationLog).where(
        NotificationLog.event_type == "NEW_ORDER",
        NotificationLog.recipient_name == "Roberto"
    )).all()
    assert len(notifications_delivery) > 0
    assert any("consegna" in n.message_content.lower() for n in notifications_delivery)
