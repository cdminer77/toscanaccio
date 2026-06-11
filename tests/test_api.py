import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select
from app.models import MenuItem, VendingSlot, Order, Rider, NotificationLog
from app.main import pack_iso8583

def test_read_root(client: TestClient):
    """Verifica che l'endpoint home funzioni correttamente."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "Toscanaccio" in data["messaggio"]
    assert "servizi" in data

def test_auth_login_success(client: TestClient):
    """Verifica che il login degli utenti pre-caricati funzioni con le credenziali corrette."""
    login_payload = {
        "username": "mario",
        "password": "mariopass"
    }
    response = client.post("/auth/login", json=login_payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["username"] == "mario"
    assert data["user"]["role"] == "CUSTOMER"

def test_auth_login_invalid(client: TestClient):
    """Verifica che il login fallisca con credenziali errate."""
    login_payload = {
        "username": "mario",
        "password": "password_sbagliata"
    }
    response = client.post("/auth/login", json=login_payload)
    assert response.status_code == 401
    assert "non validi" in response.json()["detail"]

def test_auth_register_new_user(client: TestClient):
    """Verifica la registrazione di un nuovo cliente."""
    register_payload = {
        "username": "toscano99",
        "email": "toscano99@gmail.com",
        "password": "miapasswordsegreta"
    }
    response = client.post("/auth/register", json=register_payload)
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "toscano99"
    assert data["email"] == "toscano99@gmail.com"
    assert data["role"] == "CUSTOMER"
    assert "hashed_password" not in data  # Importante: non esporre la password hashata!

def test_get_menu(client: TestClient):
    """Verifica la lista del menu e i filtri per categoria."""
    response = client.get("/menu")
    assert response.status_code == 200
    menu = response.json()
    assert len(menu) > 0
    # Verifica che gli oggetti abbiano le chiavi corrette
    first_item = menu[0]
    assert "name" in first_item
    assert "price" in first_item
    assert "category" in first_item

    # Test filtraggio categoria
    response_gastronomia = client.get("/menu?category=GASTRONOMIA")
    assert response_gastronomia.status_code == 200
    for item in response_gastronomia.json():
        assert item["category"] == "GASTRONOMIA"

def test_create_order_pickup(client: TestClient, session: Session):
    """Verifica la creazione di un ordine in modalità PICK-UP."""
    # Recupera un piatto dal DB per l'ordine
    item = session.exec(select(MenuItem)).first()
    assert item is not None

    order_payload = {
        "order_type": "PICKUP",
        "customer_name": "Gino Ginori",
        "customer_phone": "+39 333 9876543",
        "items": [
            {"menu_item_id": item.id, "quantity": 2}
        ]
    }
    
    response = client.post("/orders", json=order_payload)
    assert response.status_code == 201
    data = response.json()
    assert data["customer_name"] == "Gino Ginori"
    assert data["order_type"] == "PICKUP"
    assert data["total"] == pytest.approx(item.price * 2)
    assert data["status"] == "PENDING"
    assert data["vending_code"] is None  # Nessun codice ritiro per asporto standard

def test_create_order_vending(client: TestClient, session: Session):
    """Verifica la creazione di un ordine in modalità VENDING H24."""
    # Recupera un piatto dal DB per l'ordine
    item = session.exec(select(MenuItem)).first()
    assert item is not None

    order_payload = {
        "order_type": "VENDING",
        "customer_name": "KioskTouchscreenShop",
        "customer_phone": None,
        "items": [
            {"menu_item_id": item.id, "quantity": 1}
        ]
    }
    
    response = client.post("/orders", json=order_payload)
    assert response.status_code == 201
    data = response.json()
    assert data["customer_name"] == "KioskTouchscreenShop"
    assert data["order_type"] == "VENDING"
    assert data["vending_code"] is not None  # Codice ritiro autogenerato per vending H24
    assert len(data["vending_code"]) == 6


def test_vending_telemetry_get(client: TestClient):
    """Verifica il recupero dei dati telemetrici H24 dei distributori SandenVendo."""
    response = client.get("/vending/telemetry")
    assert response.status_code == 200
    telemetry = response.json()
    assert "gdrink1" in telemetry
    assert "gdrink2" in telemetry
    assert telemetry["gdrink1"]["compressor_status"] == "RUNNING"
    assert telemetry["gdrink1"]["zone1_temp"] == 4.2
    assert telemetry["gdrink1"]["gettoniera"]["status"] == "OPERATIONAL"

def test_vending_telemetry_fault_jam(client: TestClient, session: Session):
    """Verifica la simulazione di un guasto a una spirale bloccata."""
    fault_payload = {
        "machine": "gdrink1",
        "fault_type": "JAM"
    }
    response = client.post("/vending/telemetry/fault", json=fault_payload)
    assert response.status_code == 200
    data = response.json()
    assert "Spirale ripiano C bloccata (Slot C4)" in data["telemetry"]["grid_faults"]
    
    # Verifica che sia stata creata una notifica WhatsApp per il tecnico
    notifications_resp = client.get("/notifications")
    assert notifications_resp.status_code == 200
    notifications = notifications_resp.json()
    assert any(n["event_type"] == "FAULT_ALERT" and "C4" in n["message_content"] for n in notifications)

def test_pos_iso8583_payment_emulator(client: TestClient):
    """Verifica l'emulatore POS e il protocollo di interscambio bancario ISO 8583."""
    # Impacchetta un messaggio finanziario ISO 8583 (0200 = Richiesta Addebito)
    # Campi: 3 (Processing Code = 000000), 4 (Amount = 00000001390 -> 13.90€), 11 (STAN = 123456), 41 (Terminal ID = POS-0001), 42 (Merchant ID = TOSCANACCIO-H24)
    mti = "0200"
    fields = {
        3: "000000",
        4: "000000001390",
        11: "123456",
        41: "POS-0001",
        42: "TOSCANACCIO-H24"
    }
    raw_iso_msg = pack_iso8583(mti, fields)
    
    payload = {"iso_message": raw_iso_msg}
    response = client.post("/pos/iso8583", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "APPROVED"
    assert data["mti_response"] == "0210"  # Risposta finanziaria approvata
    assert data["response_fields"]["39 (Response Code)"] == "00"  # 00 = Approvato
    assert data["parsed_request_fields"]["4 (Amount)"] == "EUR 13.90"
    assert "APPROVED" in data["status"]
    assert len(data["gateway_logs"]) > 0

def test_vending_promos_weather_simulation(client: TestClient):
    """Verifica il calcolo delle promozioni basato su meteo e ora simulati."""
    # Imposta lo stato a piovoso (RAINY) e notte fonda (true)
    sim_payload = {
        "weather": "RAINY",
        "simulated_late_night": True
    }
    response_update = client.post("/vending/simulation", json=sim_payload)
    assert response_update.status_code == 200
    assert response_update.json()["weather"] == "RAINY"
    
    # Recupera le promozioni
    response_promos = client.get("/vending/promos")
    assert response_promos.status_code == 200
    data = response_promos.json()
    assert data["weather"] == "RAINY"
    assert data["simulated_late_night"] is True
    
    # Dovrebbero esserci due promozioni attive
    promo_names = [p["name"] for p in data["promos"]]
    assert any("Sconto Pioggia" in name for name in promo_names)
    assert any("Spuntino Notturno" in name for name in promo_names)

def test_admin_crud_menu_item(client: TestClient):
    """Verifica le operazioni CRUD su un piatto del menu (creazione, aggiornamento, cancellazione)."""
    # 1. Creazione
    item_payload = {
        "name": "Tortelli Maremmani Nuovi",
        "description": "Tortelli ripieni di ricotta e spinaci freschi, con ragù toscano",
        "price": 12.00,
        "category": "GASTRONOMIA",
        "available": True
    }
    response_create = client.post("/menu", json=item_payload)
    assert response_create.status_code == 201
    new_item = response_create.json()
    assert new_item["name"] == "Tortelli Maremmani Nuovi"
    assert new_item["price"] == 12.00
    new_item_id = new_item["id"]
    
    # 2. Aggiornamento (Patch)
    update_payload = {
        "price": 13.50,
        "description": "Descrizione aggiornata con dettagli extra"
    }
    response_patch = client.get("/menu")
    response_update = client.patch(f"/menu/{new_item_id}", json=update_payload)
    assert response_update.status_code == 200
    updated_item = response_update.json()
    assert updated_item["price"] == 13.50
    assert updated_item["description"] == "Descrizione aggiornata con dettagli extra"
    
    # 3. Eliminazione
    response_delete = client.delete(f"/menu/{new_item_id}")
    assert response_delete.status_code == 200
    assert response_delete.json()["status"] == "DELETED"
    
    # Verifica che sia stato effettivamente eliminato
    response_get = client.get("/menu")
    all_items = response_get.json()
    assert not any(item["id"] == new_item_id for item in all_items)

def test_create_order_with_new_payments(client: TestClient, session: Session):
    """Verifica la creazione di un ordine specificando un metodo di pagamento personalizzato (es: Satispay)."""
    item = session.exec(select(MenuItem)).first()
    assert item is not None

    order_payload = {
        "order_type": "DELIVERY",
        "customer_name": "Claudio Bianchi",
        "customer_phone": "+39 333 7776655",
        "address": "Via della Fortezza 4, Livorno",
        "payment_method": "SATISPAY",
        "payment_status": "PAID",
        "payment_tx_id": "MOCK-SATISPAY-TX-999",
        "items": [
            {"menu_item_id": item.id, "quantity": 1}
        ]
    }
    
    response = client.post("/orders", json=order_payload)
    assert response.status_code == 201
    data = response.json()
    assert data["customer_name"] == "Claudio Bianchi"
    assert data["payment_method"] == "SATISPAY"
    assert data["payment_status"] == "PAID"
    assert data["payment_tx_id"] == "MOCK-SATISPAY-TX-999"

def test_satispay_simulation_endpoints(client: TestClient):
    """Verifica gli endpoint di simulazione di Satispay (richiesta push ed approvazione)."""
    payload = {
        "phone_number": "+39 333 1122334",
        "amount": 18.50
    }
    response_req = client.post("/payments/satispay/request", json=payload)
    assert response_req.status_code == 200
    data_req = response_req.json()
    assert data_req["status"] == "PENDING"
    assert "payment_id" in data_req
    
    payment_id = data_req["payment_id"]
    
    # Verifica stato pending
    response_status = client.get(f"/payments/satispay/status/{payment_id}")
    assert response_status.status_code == 200
    assert response_status.json()["status"] == "PENDING"
    
    # Simula approvazione
    response_approve = client.post(f"/payments/satispay/approve/{payment_id}")
    assert response_approve.status_code == 200
    assert response_approve.json()["status"] == "APPROVED"

def test_crypto_simulation_endpoints(client: TestClient):
    """Verifica la simulazione del gateway in stablecoin EURT su Polygon."""
    payload = {"amount": 25.50}
    response_inv = client.post("/payments/crypto/invoice", json=payload)
    assert response_inv.status_code == 200
    data_inv = response_inv.json()
    assert data_inv["status"] == "UNPAID"
    assert data_inv["network"] == "Polygon Mainnet"
    assert data_inv["amount"] == 25.50
    
    # Verifica validazione fittizia transazione
    verify_payload = {
        "tx_hash": "0x8a92b7c4d5e6f3a1c890124354675869faebcd01ab2c3d4e5f60718293a4b5c6",
        "amount": 25.50
    }
    response_ver = client.post("/payments/crypto/verify", json=verify_payload)
    assert response_ver.status_code == 200
    data_ver = response_ver.json()
    assert data_ver["status"] == "CONFIRMED"
    assert data_ver["confirmations"] == 3

def test_paypal_simulation_endpoints(client: TestClient):
    """Verifica la simulazione dell'autorizzazione PayPal."""
    payload = {"amount": 12.00}
    response = client.post("/payments/paypal/authorize", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "APPROVED"
    assert "paypal_order_id" in data
