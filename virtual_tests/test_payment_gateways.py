import pytest
from fastapi.testclient import TestClient
from app.main import pack_iso8583, unpack_iso8583

def test_iso8583_pack_unpack():
    """Verifica la corretta serializzazione e deserializzazione del protocollo ISO 8583."""
    mti = "0200"
    fields = {
        3: "000000",
        4: "000000001999",  # € 19.99
        11: "654321",
        41: "POS-TEST",
        42: "MERCHANT-TEST  " # Lunghezza 15
    }
    
    packed = pack_iso8583(mti, fields)
    assert isinstance(packed, str)
    assert len(packed) > 20
    
    unpacked_mti, unpacked_fields = unpack_iso8583(packed)
    assert unpacked_mti == mti
    # Pydantic/FastAPI o le funzioni rimuovono spazi/padding a volte, ma confrontiamo i valori esatti
    assert unpacked_fields[3] == "000000"
    assert unpacked_fields[4] == "000000001999"
    assert unpacked_fields[11] == "654321"
    assert unpacked_fields[41] == "POS-TEST"
    assert unpacked_fields[42] == "MERCHANT-TEST  "

def test_pos_endpoint_approved(client: TestClient):
    """Verifica l'esito APPROVATO dell'emulazione POS con importo positivo."""
    mti = "0200"
    fields = {
        3: "000000",
        4: "000000001550",  # € 15.50
        11: "112233",
        41: "POS-9999",
        42: "TOSCANACCIO-H24"
    }
    packed_msg = pack_iso8583(mti, fields)
    
    response = client.post("/pos/iso8583", json={"iso_message": packed_msg})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "APPROVED"
    assert data["mti_response"] == "0210"
    assert data["response_fields"]["39 (Response Code)"] == "00"
    assert data["parsed_request_fields"]["4 (Amount)"] == "EUR 15.50"
    assert len(data["gateway_logs"]) > 0

def test_pos_endpoint_declined(client: TestClient):
    """Verifica l'esito DECLINED (Rifiutato) dell'emulazione POS con importo nullo o negativo."""
    mti = "0200"
    fields = {
        3: "000000",
        4: "000000000000",  # € 0.00
        11: "112233",
        41: "POS-9999",
        42: "TOSCANACCIO-H24"
    }
    packed_msg = pack_iso8583(mti, fields)
    
    response = client.post("/pos/iso8583", json={"iso_message": packed_msg})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "DECLINED"
    # Il codice 51 indica fondi insufficienti
    assert data["response_fields"]["39 (Response Code)"] == "51"

def test_satispay_flow(client: TestClient):
    """Verifica l'intero ciclo di vita di un pagamento push fittizio con Satispay."""
    # 1. Crea richiesta di pagamento
    req_payload = {
        "phone_number": "+39 347 1234567",
        "amount": 22.90
    }
    response_req = client.post("/payments/satispay/request", json=req_payload)
    assert response_req.status_code == 200
    data_req = response_req.json()
    assert data_req["status"] == "PENDING"
    assert "payment_id" in data_req
    payment_id = data_req["payment_id"]

    # 2. Controlla lo stato (deve essere PENDING)
    response_status = client.get(f"/payments/satispay/status/{payment_id}")
    assert response_status.status_code == 200
    assert response_status.json()["status"] == "PENDING"

    # 3. Simula approvazione da app mobile
    response_approve = client.post(f"/payments/satispay/approve/{payment_id}")
    assert response_approve.status_code == 200
    assert response_approve.json()["status"] == "APPROVED"

    # 4. Verifica stato finale
    response_status_final = client.get(f"/payments/satispay/status/{payment_id}")
    assert response_status_final.status_code == 200
    assert response_status_final.json()["status"] == "APPROVED"

def test_crypto_eurt_payment(client: TestClient):
    """Verifica la simulazione del gateway in stablecoin EURT su Polygon."""
    # 1. Richiesta fattura crypto
    response_inv = client.post("/payments/crypto/invoice", json={"amount": 10.00})
    assert response_inv.status_code == 200
    data_inv = response_inv.json()
    assert data_inv["status"] == "UNPAID"
    assert data_inv["amount"] == 10.00
    assert "0x" in data_inv["merchant_wallet"]

    # 2. Richiesta di verifica transazione fittizia
    tx_hash = "0x" + "a" * 64  # Hash fittizio di 66 caratteri (0x + 64 hex)
    verify_payload = {
        "tx_hash": tx_hash,
        "amount": 10.00
    }
    response_ver = client.post("/payments/crypto/verify", json=verify_payload)
    assert response_ver.status_code == 200
    data_ver = response_ver.json()
    assert data_ver["status"] == "CONFIRMED"
    assert data_ver["confirmations"] == 3

    # Tentativo con hash non valido
    response_invalid_ver = client.post("/payments/crypto/verify", json={"tx_hash": "0x123", "amount": 10.00})
    assert response_invalid_ver.status_code == 400

def test_paypal_authorization(client: TestClient):
    """Verifica l'endpoint fittizio di PayPal."""
    response = client.post("/payments/paypal/authorize", json={"amount": 45.00})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "APPROVED"
    assert "paypal_order_id" in data

def test_iso20022_request_to_pay_flow_approved(client: TestClient):
    """Verifica il flusso completo ISO 20022 pain.013 RTP con settlement approvato pacs.002 e calcolo risparmio fee."""
    payload = {
        "amount": 35.50,
        "creditor_name": "Toscanaccio Bottega H24",
        "creditor_iban": "IT60X0542811101000000123456",
        "remittance_info": "Spesa Vini e Salumi"
    }
    # 1. Creazione Request-to-Pay (pain.013)
    response_req = client.post("/pos/iso20022/request-to-pay", json=payload)
    assert response_req.status_code == 200
    data_req = response_req.json()
    
    assert data_req["status"] == "INITIATED"
    assert data_req["protocol"] == "ISO 20022 (pain.013.001.09)"
    assert "end_to_end_id" in data_req
    assert "epc_qr_payload" in data_req
    assert "BCD\n002" in data_req["epc_qr_payload"]
    assert "EUR35.50" in data_req["epc_qr_payload"]
    assert "<Document xmlns=" in data_req["xml_document"]
    
    # Verifica risparmio di costo calcolato
    savings = data_req["cost_analysis"]
    assert savings["card_interchange_estimate_eur"] > savings["iso20022_a2a_fee_eur"]
    assert savings["net_savings_eur"] > 0
    
    e2e_id = data_req["end_to_end_id"]
    
    # 2. Verifica stato PENDING
    response_st = client.get(f"/pos/iso20022/status/{e2e_id}")
    assert response_st.status_code == 200
    assert response_st.json()["status"] == "PENDING"
    
    # 3. Settlement approvato (pacs.002 ACTC)
    response_settle = client.post("/pos/iso20022/settle", json={"end_to_end_id": e2e_id, "action": "APPROVE"})
    assert response_settle.status_code == 200
    data_settle = response_settle.json()
    assert data_settle["status"] == "SETTLED"
    assert data_settle["iso_status_code"] == "ACTC"
    assert data_settle["savings_realized_eur"] > 0
    assert "<TxSts>ACTC</TxSts>" in data_settle["xml_document"]

def test_iso20022_settlement_rejected(client: TestClient):
    """Verifica il rifiuto del pagamento con codice di reject bancario pacs.002 RJCT."""
    payload = {"amount": 50.00}
    response_req = client.post("/pos/iso20022/request-to-pay", json=payload)
    assert response_req.status_code == 200
    e2e_id = response_req.json()["end_to_end_id"]
    
    # Rifiuto
    response_settle = client.post("/pos/iso20022/settle", json={
        "end_to_end_id": e2e_id,
        "action": "REJECT",
        "reason_code": "AM04",
        "reason_text": "Fondi insufficienti"
    })
    assert response_settle.status_code == 200
    data_settle = response_settle.json()
    assert data_settle["status"] == "DECLINED"
    assert data_settle["iso_status_code"] == "RJCT"
    assert "<TxSts>RJCT</TxSts>" in data_settle["xml_document"]
    assert "<Cd>AM04</Cd>" in data_settle["xml_document"]

