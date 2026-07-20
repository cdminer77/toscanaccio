from fastapi import FastAPI, Depends, HTTPException, status, File, UploadFile
import os
import shutil
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session, select
from typing import List, Optional
from app.models import VendingSlot
from datetime import datetime, timedelta
from jose import jwt
from app.database import get_session, create_db_and_tables, engine
from app import crud
from app import schemas
from app.seed import seed_db

# Configurazione JWT
SECRET_KEY = "toscanaccio_segreto_di_stato_toscana"
ALGORITHM = "HS256"

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=1)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

app = FastAPI(
    title="Toscanaccio Backend API",
    description="API Backend per il brand toscano Toscanaccio - Gastronomia & Vending H24",
    version="1.1.0"
)

app.mount("/files", StaticFiles(directory="files"), name="files")

# Abilita CORS per lo sviluppo locale
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    # Inizializza il database e carica i dati di seed all'avvio del server
    create_db_and_tables()
    with Session(engine) as session:
        seed_db(session)

@app.get("/")
def home():
    return {
        "status": "online",
        "messaggio": "✅ Benvenuto sul backend di Toscanaccio! La cucina toscana H24 è pronta.",
        "servizi": ["Asporto / Pick-up (12h)", "Consegna / Delivery (Rider interni)", "Distribuzione Automatica (Vending H24)"]
    }

# --- USER AUTHENTICATION API ---
@app.post("/auth/register", response_model=schemas.UserRead, status_code=201)
def register_user(user_data: schemas.UserCreate, session: Session = Depends(get_session)):
    # Verifica se l'utente esiste già
    existing_user = crud.get_user_by_username(session, user_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nome utente già registrato. Scegline un altro!"
        )
    existing_email = crud.get_user_by_email(session, user_data.email)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email già registrata. Scegline un'altra!"
        )
    return crud.create_user(session, user_data)

@app.post("/auth/login", response_model=schemas.Token)
def login_user(login_data: schemas.UserLogin, session: Session = Depends(get_session)):
    user = crud.get_user_by_username(session, login_data.username)
    if not user or not crud.verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nome utente o password non validi. Riprova!"
        )
    
    if not getattr(user, "is_verified", False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account non verificato! Controlla la tua email per attivare il tuo profilo."
        )
    
    # Genera token di accesso
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role.value}
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

from fastapi.responses import HTMLResponse
import urllib.request
import json

@app.get("/auth/verify", response_class=HTMLResponse)
def verify_email(token: str, session: Session = Depends(get_session)):
    user = crud.verify_user_email(session, token)
    if not user:
        return HTMLResponse(
            status_code=400,
            content="""
            <html>
                <head>
                    <title>Verifica Fallita — Toscanaccio</title>
                    <style>
                        body { font-family: 'Outfit', sans-serif; text-align: center; padding: 50px; background-color: #141916; color: #d1c7bd; }
                        .container { background: #1b221e; padding: 40px; border-radius: 12px; border: 1px solid #2e3b33; max-width: 500px; margin: auto; box-shadow: 0 8px 32px rgba(0,0,0,0.3); }
                        h1 { color: #ba5c33; margin-bottom: 20px; }
                        p { font-size: 1.1rem; line-height: 1.6; }
                        .btn { display: inline-block; margin-top: 30px; padding: 12px 24px; background-color: #ba5c33; color: white; text-decoration: none; border-radius: 6px; font-weight: bold; transition: background 0.2s; }
                        .btn:hover { background-color: #a44f2b; }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h1>Link non valido</h1>
                        <p>Il token di verifica è non valido, scaduto o già utilizzato.</p>
                        <a href="https://www.toscanaccio.eu" class="btn">Torna al Sito</a>
                    </div>
                </body>
            </html>
            """
        )
        
    return HTMLResponse(
        content="""
        <html>
            <head>
                <title>Account Verificato! — Toscanaccio</title>
                <style>
                    body { font-family: 'Outfit', sans-serif; text-align: center; padding: 50px; background-color: #141916; color: #d1c7bd; }
                    .container { background: #1b221e; padding: 40px; border-radius: 12px; border: 1px solid #2e3b33; max-width: 500px; margin: auto; box-shadow: 0 8px 32px rgba(0,0,0,0.3); }
                    h1 { color: #5cb85c; margin-bottom: 20px; }
                    p { font-size: 1.1rem; line-height: 1.6; }
                    .btn { display: inline-block; margin-top: 30px; padding: 12px 24px; background-color: #5cb85c; color: white; text-decoration: none; border-radius: 6px; font-weight: bold; transition: background 0.2s; }
                    .btn:hover { background-color: #4cae4c; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>Account Verificato!</h1>
                    <p>La tua email è stata confermata con successo. Ora puoi effettuare il login dal sito.</p>
                    <a href="https://www.toscanaccio.eu" class="btn">Accedi Ora</a>
                </div>
            </body>
        </html>
        """
    )

@app.get("/auth/config")
def get_auth_config():
    return {
        "google_client_id": os.getenv("GOOGLE_CLIENT_ID", "")
    }

@app.post("/auth/sso", response_model=schemas.Token)
def sso_login(sso_data: schemas.UserSSOLogin, session: Session = Depends(get_session)):
    user = crud.create_or_get_sso_user(
        session=session,
        email=sso_data.email,
        username=sso_data.username,
        provider=sso_data.provider,
        privacy_accepted=sso_data.privacy_accepted
    )
    
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role.value}
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

@app.post("/auth/google", response_model=schemas.Token)
def google_login(token_data: dict, session: Session = Depends(get_session)):
    id_token = token_data.get("credential")
    if not id_token:
        raise HTTPException(status_code=400, detail="Token Google mancante")
        
    google_client_id = os.getenv("GOOGLE_CLIENT_ID", "")
    
    try:
        url = f"https://oauth2.googleapis.com/tokeninfo?id_token={id_token}"
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode('utf-8'))
            
        aud = data.get("aud")
        if aud != google_client_id and google_client_id != "":
            raise HTTPException(status_code=400, detail="Client ID non corrispondente")
            
        email = data.get("email")
        name = data.get("name", email.split("@")[0] if email else "GoogleUser")
        
        if not email:
            raise HTTPException(status_code=400, detail="Impossibile ottenere l'email da Google")
            
        user = crud.create_or_get_sso_user(
            session=session,
            email=email,
            username=name,
            provider="GOOGLE",
            privacy_accepted=True
        )
        
        access_token = create_access_token(
            data={"sub": user.username, "role": user.role.value}
        )
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": user
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Convalida Google fallita: {str(e)}")

# --- MENU API ---
@app.get("/menu", response_model=List[schemas.MenuItemRead])
def read_menu(category: Optional[str] = None, session: Session = Depends(get_session)):
    return crud.get_menu(session, category)

# --- ORDERS API ---
@app.post("/orders", response_model=schemas.OrderRead, status_code=201)
def create_order(order_data: schemas.OrderCreate, session: Session = Depends(get_session)):
    try:
        return crud.create_order(session, order_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/orders", response_model=List[schemas.OrderRead])
def read_orders(
    order_type: Optional[str] = None,
    status: Optional[str] = None,
    session: Session = Depends(get_session)
):
    return crud.get_orders(session, order_type, status)

@app.patch("/orders/{order_id}", response_model=schemas.OrderRead)
def update_order_status(
    order_id: int,
    status: str,
    rider_id: Optional[int] = None,
    session: Session = Depends(get_session)
):
    updated_order = crud.update_order_status(session, order_id, status, rider_id)
    if not updated_order:
        raise HTTPException(status_code=404, detail="Ordine non trovato")
    return updated_order

# --- USERS API ---
@app.get("/users", response_model=List[schemas.UserRead])
def get_all_users(session: Session = Depends(get_session)):
    return crud.get_users(session)

# --- WAREHOUSE & STOCK API ---
@app.get("/stock")
def get_warehouse_stock(session: Session = Depends(get_session)):
    return crud.get_stock(session)

@app.patch("/stock/{stock_id}")
def update_warehouse_stock(stock_id: int, stock_data: schemas.StockUpdate, session: Session = Depends(get_session)):
    updated_stock = crud.update_stock(session, stock_id, stock_data.current_quantity, stock_data.min_alert_threshold)
    if not updated_stock:
        raise HTTPException(status_code=404, detail="Stock item non trovato")
    return updated_stock

@app.get("/vending", response_model=List[schemas.VendingSlotRead])
def get_vending_slots(session: Session = Depends(get_session)):
    return crud.get_vending_slots(session)

# --- RIDERS API ---
@app.get("/riders", response_model=List[schemas.RiderRead])
def get_riders(session: Session = Depends(get_session)):
    return crud.get_riders(session)

@app.patch("/riders/{rider_id}", response_model=schemas.RiderRead)
def update_rider_details(rider_id: int, rider_data: schemas.RiderUpdate, session: Session = Depends(get_session)):
    updated_rider = crud.update_rider(session, rider_id, rider_data)
    if not updated_rider:
        raise HTTPException(status_code=404, detail="Rider non trovato")
    return updated_rider

# --- PRODUCT RECOGNITION (I.A.) API ---
@app.post("/recognition", response_model=schemas.ProductRecognitionRead)
def log_recognition(log_data: schemas.ProductRecognitionCreate, session: Session = Depends(get_session)):
    return crud.log_product_recognition(session, log_data)

@app.get("/recognition", response_model=List[schemas.ProductRecognitionRead])
def get_recognition_logs(session: Session = Depends(get_session)):
    return crud.get_recognition_logs(session)

# --- PREDICTIVE I.A. API ---
@app.get("/predict")
def get_predictions(session: Session = Depends(get_session)):
    return crud.get_production_forecast(session)

# --- ISO 8583 BANK INTERCHANGE EMULATOR & PAYMENT API ---
def unpack_iso8583(msg: str):
    """Decodifica un messaggio ISO 8583 in formato ASCII stringa (MTI + Bitmap 16 char + Campi)"""
    if len(msg) < 20:
        raise ValueError("Messaggio troppo corto per essere uno standard ISO 8583 valido")
    
    mti = msg[0:4]
    bitmap_hex = msg[4:20]
    
    # Conversione bitmap esadecimale in binario a 64 bit
    bitmap_bin = bin(int(bitmap_hex, 16))[2:].zfill(64)
    
    fields = {}
    idx = 20
    
    # Mappatura lunghezze fisse dei campi supportati nella nostra simulazione
    field_lens = {
        3: 6,   # Processing Code (es: 000000 per acquisti)
        4: 12,  # Amount, Transaction (in centesimi, es: 00000001390 = 13.90 EUR)
        11: 6,  # STAN (Systems Trace Audit Number)
        12: 6,  # Local Transaction Time (hhmmss)
        13: 4,  # Local Transaction Date (MMDD)
        37: 12, # RRN (Retrieval Reference Number)
        39: 2,  # Response Code (es: 00 = Approvato)
        41: 8,  # Card Acceptor Terminal ID
        42: 15, # Card Acceptor Identification Code (Merchant ID)
    }
    
    for f_num in sorted(field_lens.keys()):
        # Il bitmap e' 1-indexed, quindi f_num - 1
        bit_idx = f_num - 1
        if bit_idx < len(bitmap_bin) and bitmap_bin[bit_idx] == '1':
            length = field_lens[f_num]
            if idx + length <= len(msg):
                fields[f_num] = msg[idx : idx + length]
                idx += length
                
    return mti, fields

def pack_iso8583(mti: str, fields: dict):
    """Codifica un dizionario di campi in un messaggio ISO 8583 formattato in stringa ASCII"""
    bitmap_bin = ['0'] * 64
    field_lens = {
        3: 6, 4: 12, 11: 6, 12: 6, 13: 4, 37: 12, 39: 2, 41: 8, 42: 15
    }
    
    for f_num in fields.keys():
        if f_num in field_lens:
            bitmap_bin[f_num - 1] = '1'
        
    bitmap_str = "".join(bitmap_bin)
    bitmap_hex = hex(int(bitmap_str, 2))[2:].upper().zfill(16)
    
    msg = mti + bitmap_hex
    for f_num in sorted(field_lens.keys()):
        if f_num in fields:
            val = str(fields[f_num])
            length = field_lens[f_num]
            # Pad con zeri a sinistra per rispettare la lunghezza
            val = val.zfill(length)[:length]
            msg += val
            
    return msg

@app.post("/pos/iso8583")
def process_pos_transaction(payload: dict, session: Session = Depends(get_session)):
    """
    Riceve un messaggio POS ISO 8583 grezzo (MTI 0200), lo analizza, esegue l'addebito
    e restituisce il messaggio di approvazione della banca (MTI 0210, Field 39 = '00')
    """
    iso_request = payload.get("iso_message")
    if not iso_request:
        raise HTTPException(status_code=400, detail="Messaggio ISO 8583 non fornito!")
        
    try:
        mti_req, fields_req = unpack_iso8583(iso_request)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Errore di parsing ISO 8583: {str(e)}")
        
    if mti_req != "0200":
        raise HTTPException(status_code=400, detail="MTI non supportato. Inviare una richiesta finanziaria 0200")
        
    # Estrae dettagli
    terminal_id = fields_req.get(41, "UNKNOWN ")
    amount_cents = int(fields_req.get(4, "0"))
    amount_eur = amount_cents / 100.0
    stan = fields_req.get(11, "000000")
    
    # Genera i campi di risposta finanziaria
    rrn = f"9381{stan.zfill(6)}03"  # RRN sintetico basato su STAN
    local_time = datetime.now().strftime("%H%M%S")
    local_date = datetime.now().strftime("%m%d")
    
    # Esegue l'approvazione bancaria (approvato al 100% se importo > 0)
    response_code = "00"  # 00 = Transazione Approvata con Successo
    if amount_cents <= 0:
        response_code = "51"  # 51 = Fondi insufficienti (per test)
        
    fields_res = fields_req.copy()
    fields_res[37] = rrn           # Field 37: RRN
    fields_res[39] = response_code # Field 39: Response Code
    fields_res[12] = local_time
    fields_res[13] = local_date
    
    # Genera pacchetto ISO 8583 di risposta
    iso_response = pack_iso8583("0210", fields_res)
    
    # Log nel database se la transazione e' associata a un ordine (opzionale)
    return {
        "status": "APPROVED" if response_code == "00" else "DECLINED",
        "mti_request": mti_req,
        "mti_response": "0210",
        "parsed_request_fields": {
            "3 (Processing Code)": fields_req.get(3),
            "4 (Amount)": f"EUR {amount_eur:.2f}",
            "11 (STAN)": stan,
            "41 (Terminal ID)": terminal_id,
            "42 (Merchant ID)": fields_req.get(42)
        },
        "response_fields": {
            "37 (RRN)": rrn,
            "39 (Response Code)": response_code,
            "12 (Local Time)": local_time,
            "13 (Local Date)": local_date
        },
        "raw_request": iso_request,
        "raw_response": iso_response,
        "gateway_logs": [
            f"[BANK HOST] Connection established from POS terminal {terminal_id.strip()}",
            f"[BANK HOST] Processing Financial Request (MTI 0200) for EUR {amount_eur:.2f}",
            f"[BANK HOST] ISO8583 Primary Bitmap decoded: {iso_request[4:20]}",
            f"[BANK HOST] Card authorized. STAN: {stan}, Generating RRN: {rrn}",
            f"[BANK HOST] Transaction Approved. Packing Response Message (MTI 0210)",
            f"[BANK HOST] Dispatching response packet to POS terminal"
        ]
    }

# --- SIMULATORE GATEWAY FINANZIARI DI PAGAMENTO (Satispay, PayPal, Crypto stablecoin Polygon) ---
import uuid

# Dizionario in-memory per tracciare lo stato dei pagamenti Satispay simulati
SATISPAY_PAYMENTS = {}

@app.post("/payments/satispay/request")
def create_satispay_payment(payload: dict, session: Session = Depends(get_session)):
    """Simula l'avvio di una richiesta di pagamento push su Satispay"""
    phone = payload.get("phone_number")
    amount = payload.get("amount", 0.0)
    
    if not phone:
        raise HTTPException(status_code=400, detail="Numero di telefono Satispay richiesto!")
        
    payment_id = str(uuid.uuid4())
    SATISPAY_PAYMENTS[payment_id] = {
        "payment_id": payment_id,
        "phone_number": phone,
        "amount": amount,
        "status": "PENDING",
        "timestamp": datetime.now().isoformat()
    }
    
    # Crea notifica WhatsApp di notifica push simulata
    crud.create_notification_log(
        session=session,
        recipient_name="Cliente Satispay",
        channel="WHATSAPP",
        phone_number=phone,
        message_content=f"[Satispay App] Toscanaccio ti ha inviato una richiesta di addebito di € {amount:.2f}. Clicca qui per autorizzare sul tuo smartphone.",
        event_type="FAULT_ALERT"
    )
    
    return {
        "payment_id": payment_id,
        "status": "PENDING",
        "qr_code_url": "https://raw.githubusercontent.com/satispay/brand/master/satispay-logo.png",
        "message": "Richiesta push inviata con successo allo smartphone dell'utente!"
    }

@app.get("/payments/satispay/status/{payment_id}")
def check_satispay_status(payment_id: str):
    """Controlla lo stato corrente della transazione Satispay"""
    payment = SATISPAY_PAYMENTS.get(payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Pagamento non trovato!")
    return payment

@app.post("/payments/satispay/approve/{payment_id}")
def approve_satispay_payment(payment_id: str, session: Session = Depends(get_session)):
    """Simula l'approvazione del pagamento dall'app Satispay dell'utente"""
    payment = SATISPAY_PAYMENTS.get(payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Pagamento non trovato!")
        
    payment["status"] = "APPROVED"
    
    crud.create_notification_log(
        session=session,
        recipient_name="Claudio",
        channel="WHATSAPP",
        phone_number="+39 333 1234567",
        message_content=f"[Satispay API] Incasso autorizzato di € {payment['amount']:.2f} da {payment['phone_number']}. Transazione Satispay completata.",
        event_type="DELIVERY_ASSIGNED"
    )
    
    return {"status": "APPROVED", "message": "Pagamento approvato con successo via app!"}

@app.post("/payments/crypto/invoice")
def create_crypto_invoice(payload: dict):
    """Genera i dettagli per un pagamento in stablecoin EURT su rete Polygon"""
    amount_eur = payload.get("amount", 0.0)
    amount_eurt = amount_eur
    
    wallet_address = "0x705ca927d3B31660cBF1Cc53De9Ce8bB97A4a721"
    token_address = "0xE11A168FCc20D0F266e56876399047b532187569"
    
    return {
        "status": "UNPAID",
        "network": "Polygon Mainnet",
        "currency": "EURT (Tether Euro)",
        "amount": amount_eurt,
        "merchant_wallet": wallet_address,
        "token_contract_address": token_address,
        "payment_qr_code": f"ethereum:{token_address}@137/transfer?address={wallet_address}&uint256={int(amount_eurt * 1e6)}"
    }

@app.post("/payments/crypto/verify")
def verify_crypto_payment(payload: dict, session: Session = Depends(get_session)):
    """Verifica un hash transazione fittizio e simula block mining per EURT Polygon"""
    tx_hash = payload.get("tx_hash")
    amount = payload.get("amount", 0.0)
    
    if not tx_hash or not tx_hash.startswith("0x") or len(tx_hash) != 66:
        raise HTTPException(status_code=400, detail="Hash transazione EVM non valido! Deve iniziare con 0x ed essere di 66 caratteri.")
        
    crud.create_notification_log(
        session=session,
        recipient_name="Claudio",
        channel="WHATSAPP",
        phone_number="+39 333 1234567",
        message_content=f"[Polygon Web3] Rilevato trasferimento EURT di {amount:.2f} al wallet merchant. Tx: {tx_hash[:10]}...",
        event_type="DELIVERY_ASSIGNED"
    )
    
    return {
        "status": "CONFIRMED",
        "tx_hash": tx_hash,
        "block_number": 8943152,
        "confirmations": 3,
        "gas_used": 65120,
        "message": "Transazione stablecoin confermata su Polygon Blockchain!"
    }

@app.post("/payments/paypal/authorize")
def authorize_paypal_payment(payload: dict, session: Session = Depends(get_session)):
    """Simula l'approvazione immediata a un click dell'ordine PayPal"""
    amount = payload.get("amount", 0.0)
    paypal_order_id = f"PAYID-{str(uuid.uuid4())[:20].upper()}"
    
    crud.create_notification_log(
        session=session,
        recipient_name="Claudio",
        channel="WHATSAPP",
        phone_number="+39 333 1234567",
        message_content=f"[PayPal API] Addebito completato di € {amount:.2f}. PayPal Order ID: {paypal_order_id}",
        event_type="DELIVERY_ASSIGNED"
    )
    
    return {
        "status": "APPROVED",
        "paypal_order_id": paypal_order_id,
        "message": "Autorizzazione PayPal eseguita con successo!"
    }

# --- SANDENVENDO G-DRINK TELEMETRY & DIAGNOSTICS API ---
# Stato allarmi dei distributori modificabile a runtime per simulazioni
VENDING_TELEMETRY_STATE = {
    "gdrink1": {
        "name": "SandenVendo G-Drink 1 H24 (Cibo & Spume)",
        "zone1_temp": 4.2,      # Temperatura zona bassa (4°C ideale per bibite)
        "zone2_temp": 5.5,      # Temperatura zona alta (6°C ideale per cibo freddo)
        "compressor_status": "RUNNING",
        "door_open": False,
        "grid_faults": [],
        "gettoniera": {
            "model": "MEI Cashflow 7900 (MDB 5-Tubi)",
            "connection": "MDB Protocol (RS232-Adapter)",
            "tubes": [
                {"coin": "2.00 EUR", "count": 45, "status": "OK"},
                {"coin": "1.00 EUR", "count": 52, "status": "OK"},
                {"coin": "0.50 EUR", "count": 12, "status": "LOW"},  # Stato basso per allerta
                {"coin": "0.20 EUR", "count": 85, "status": "OK"},
                {"coin": "0.10 EUR", "count": 120, "status": "OK"}
            ],
            "total_cash_in_changer": 178.00,
            "status": "OPERATIONAL"
        }
    },
    "gdrink2": {
        "name": "SandenVendo G-Drink 2 H24 (Birre & Vini Premium)",
        "zone1_temp": 11.5,     # Temperatura vini bianchi/rossi (12°C ideale)
        "zone2_temp": 12.8,
        "compressor_status": "RUNNING",
        "door_open": False,
        "grid_faults": [],
        "gettoniera": {
            "model": "CPI Gryphon (MDB 6-Tubi USB)",
            "connection": "USB-Serial MDB Direct Connection",
            "tubes": [
                {"coin": "2.00 EUR", "count": 80, "status": "OK"},
                {"coin": "1.00 EUR", "count": 95, "status": "OK"},
                {"coin": "0.50 EUR", "count": 64, "status": "OK"},
                {"coin": "0.20 EUR", "count": 110, "status": "OK"},
                {"coin": "0.10 EUR", "count": 150, "status": "OK"},
                {"coin": "0.05 EUR", "count": 200, "status": "OK"}
            ],
            "total_cash_in_changer": 310.50,
            "status": "OPERATIONAL"
        }
    }
}

@app.get("/vending/telemetry")
def get_vending_telemetry():
    """Restituisce la telemetria H24 dei due distributori SandenVendo G-Drink e gettoniere"""
    return VENDING_TELEMETRY_STATE

@app.post("/vending/telemetry/fault")
def trigger_vending_fault(payload: dict, session: Session = Depends(get_session)):
    """Simula o risolve anomalie sul distributore (temperatura alta, allarme spirale bloccata, cassa vuota)"""
    machine = payload.get("machine") # gdrink1 o gdrink2
    fault_type = payload.get("fault_type") # e.g. "C4_JAM", "TEMP_HIGH", "COIN_LOW", "CLEAR"
    
    if machine not in VENDING_TELEMETRY_STATE:
        raise HTTPException(status_code=400, detail="Macchina non valida. Scegli gdrink1 o gdrink2")
        
    m_state = VENDING_TELEMETRY_STATE[machine]
    
    if fault_type == "CLEAR":
        m_state["grid_faults"] = []
        if machine == "gdrink1":
            m_state["zone1_temp"] = 4.2
            m_state["compressor_status"] = "RUNNING"
            m_state["gettoniera"]["tubes"][2]["status"] = "OK"
        else:
            m_state["zone1_temp"] = 11.5
            m_state["compressor_status"] = "RUNNING"
        crud.create_notification_log(
            session=session,
            recipient_name="Claudio",
            channel="WHATSAPP",
            phone_number="+39 333 1234567",
            message_content="[WhatsApp] RIPRISTINO TELEMETRIA: Stato distributori automatici H24 tornato alla normalità (CLEAR). Tutti i sistemi operativi.",
            event_type="RESTORE_ALERT"
        )
    elif fault_type == "JAM":
        m_state["grid_faults"].append("Spirale ripiano C bloccata (Slot C4)")
        # Aggiorna lo stato anche nel DB per coerenza
        slot = session.exec(select(VendingSlot).where(VendingSlot.position_code == "C4")).first()
        if slot:
            slot.status = "MAINTENANCE"
            session.add(slot)
            session.commit()
        crud.create_notification_log(
            session=session,
            recipient_name="Claudio",
            channel="WHATSAPP",
            phone_number="+39 333 1234567",
            message_content="[WhatsApp] ALLEGATO TELEMETRIA: Guasto rilevato presso G-Drink 1! Spirale ripiano C bloccata (Slot C4). Stato impostato a MANUTENZIONE nel DB.",
            event_type="FAULT_ALERT"
        )
    elif fault_type == "TEMP_HIGH":
        m_state["zone1_temp"] = 14.8
        m_state["compressor_status"] = "OVERHEATED_ALARM"
        crud.create_notification_log(
            session=session,
            recipient_name="Claudio",
            channel="SMS",
            phone_number="+39 333 1234567",
            message_content="[SMS] EMERGENZA TELEMETRIA: Allarme temperatura elevata presso G-Drink 1! Rilevato: 14.8°C. Compressore in allarme termico.",
            event_type="FAULT_ALERT"
        )
    elif fault_type == "COIN_LOW":
        if machine == "gdrink1":
            m_state["gettoniera"]["tubes"][2]["count"] = 2
            m_state["gettoniera"]["tubes"][2]["status"] = "EMPTY_WARNING"
        crud.create_notification_log(
            session=session,
            recipient_name="Claudio",
            channel="WHATSAPP",
            phone_number="+39 333 1234567",
            message_content="[WhatsApp] ATTENZIONE CASSA: Livello monete da 0.50 EUR basso (count: 2) presso gettoniera MEI 7900 di G-Drink 1. Rifornire per evitare resto basso.",
            event_type="FAULT_ALERT"
        )
            
    return {"status": "UPDATED", "telemetry": m_state}

# --- PROMOTIONS & SIMULATION API ---

@app.get("/notifications", response_model=List[schemas.NotificationLogRead])
def get_notifications(session: Session = Depends(get_session)):
    """Restituisce tutti i log dei messaggi inviati simulati (SMS / WhatsApp)"""
    return crud.get_notification_logs(session)

@app.get("/vending/promos")
def get_active_promos():
    """Restituisce le promozioni attive in base a meteo e ora simulati"""
    promos = []
    if crud.WEATHER_STATE == "RAINY":
        promos.append({
            "name": "Sconto Pioggia ☔",
            "discount": 0.10,
            "description": "Sconto Maltempo H24: 10% di sconto su tutti gli articoli gastronomici!"
        })
    elif crud.WEATHER_STATE == "STORMY":
        promos.append({
            "name": "Sconto Tempesta ⚡",
            "discount": 0.20,
            "description": "Sconto Shock Maltempo: 20% di sconto per farti coraggio ed uscire!"
        })
        
    if crud.SIMULATED_LATE_NIGHT:
        promos.append({
            "name": "Spuntino Notturno 🌙",
            "discount": 0.15,
            "description": "Promozione Fame Notturna: 15% di sconto su tutto il menu tra le 00:00 e le 04:00!"
        })
        
    return {
        "weather": crud.WEATHER_STATE,
        "simulated_late_night": crud.SIMULATED_LATE_NIGHT,
        "promos": promos
    }

@app.post("/vending/simulation")
def update_simulation_state(payload: dict):
    """Aggiorna lo stato di simulazione di meteo e ore per testare le promozioni dinamiche"""
    if "weather" in payload:
        crud.WEATHER_STATE = payload["weather"]
    if "simulated_late_night" in payload:
        crud.SIMULATED_LATE_NIGHT = payload["simulated_late_night"]
    return {
        "status": "UPDATED",
        "weather": crud.WEATHER_STATE,
        "simulated_late_night": crud.SIMULATED_LATE_NIGHT
    }

# --- ADMIN FULL CRUD ENDPOINTS ---

@app.post("/menu", response_model=schemas.MenuItemRead, status_code=201)
def create_menu_item(item_data: schemas.MenuItemCreate, session: Session = Depends(get_session)):
    """Crea un nuovo prodotto nel menu"""
    try:
        return crud.create_menu_item(session, item_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.patch("/menu/{item_id}", response_model=schemas.MenuItemRead)
def update_menu_item(item_id: int, item_data: schemas.MenuItemUpdate, session: Session = Depends(get_session)):
    """Aggiorna le informazioni di un prodotto nel menu"""
    updated_item = crud.update_menu_item(session, item_id, item_data)
    if not updated_item:
        raise HTTPException(status_code=404, detail="Prodotto non trovato")
    return updated_item

@app.delete("/menu/{item_id}", status_code=200)
def delete_menu_item(item_id: int, session: Session = Depends(get_session)):
    """Rimuove un prodotto dal menu"""
    success = crud.delete_menu_item(session, item_id)
    if not success:
        raise HTTPException(status_code=404, detail="Prodotto non trovato")
    return {"status": "DELETED", "message": f"Prodotto {item_id} eliminato con successo."}

@app.patch("/vending/{slot_id}", response_model=schemas.VendingSlotRead)
def update_vending_slot(slot_id: int, slot_data: schemas.VendingSlotUpdate, session: Session = Depends(get_session)):
    """Aggiorna le informazioni e il prodotto assegnato a uno slot del distributore automatico"""
    updated_slot = crud.update_vending_slot(session, slot_id, slot_data)
    if not updated_slot:
        raise HTTPException(status_code=404, detail="Slot non trovato")
    return updated_slot

@app.patch("/users/{user_id}", response_model=schemas.UserRead)
def update_user_details(user_id: int, user_data: schemas.UserUpdate, session: Session = Depends(get_session)):
    """Modifica i dati o il ruolo di un utente"""
    updated_user = crud.update_user(session, user_id, user_data)
    if not updated_user:
        raise HTTPException(status_code=404, detail="Utente non trovato")
    return updated_user

@app.delete("/users/{user_id}", status_code=200)
def delete_user(user_id: int, session: Session = Depends(get_session)):
    """Rimuove un utente dal sistema"""
    success = crud.delete_user(session, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Utente non trovato")
    return {"status": "DELETED", "message": f"Utente {user_id} eliminato con successo."}

@app.post("/riders", response_model=schemas.RiderRead, status_code=201)
def create_rider(rider_data: schemas.RiderCreate, session: Session = Depends(get_session)):
    """Registra un nuovo Rider nel sistema"""
    try:
        return crud.create_rider(session, rider_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/riders/{rider_id}", status_code=200)
def delete_rider(rider_id: int, session: Session = Depends(get_session)):
    """Rimuove un Rider dal sistema"""
    success = crud.delete_rider(session, rider_id)
    if not success:
        raise HTTPException(status_code=404, detail="Rider non trovato")
    return {"status": "DELETED", "message": f"Rider {rider_id} rimosso con successo."}

# --- ACCOUNTING, DEADLINES & DOCUMENT VAULT API ---

@app.get("/admin/accounting", response_model=List[schemas.AccountingEntryRead])
def get_accounting_entries(
    category: Optional[str] = None,
    entry_type: Optional[str] = None,
    session: Session = Depends(get_session)
):
    return crud.get_accounting_entries(session, category, entry_type)

@app.post("/admin/accounting", response_model=schemas.AccountingEntryRead, status_code=201)
def create_accounting_entry(
    entry_data: schemas.AccountingEntryCreate,
    session: Session = Depends(get_session)
):
    try:
        return crud.create_accounting_entry(session, entry_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/admin/deadlines", response_model=List[schemas.PaymentDeadlineRead])
def get_payment_deadlines(session: Session = Depends(get_session)):
    return crud.get_payment_deadlines(session)

@app.post("/admin/deadlines", response_model=schemas.PaymentDeadlineRead, status_code=201)
def create_payment_deadline(
    deadline_data: schemas.PaymentDeadlineCreate,
    session: Session = Depends(get_session)
):
    try:
        return crud.create_payment_deadline(session, deadline_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.patch("/admin/deadlines/{deadline_id}", response_model=schemas.PaymentDeadlineRead)
def update_payment_deadline(
    deadline_id: int,
    deadline_data: schemas.PaymentDeadlineUpdate,
    session: Session = Depends(get_session)
):
    updated = crud.update_payment_deadline(session, deadline_id, deadline_data)
    if not updated:
        raise HTTPException(status_code=404, detail="Scadenza non trovata")
    return updated

@app.get("/admin/documents", response_model=List[schemas.ArchivedDocumentRead])
def get_archived_documents(session: Session = Depends(get_session)):
    return crud.get_archived_documents(session)

@app.post("/admin/documents/upload", response_model=schemas.ArchivedDocumentRead, status_code=201)
def upload_document(
    category: str,
    notes: Optional[str] = None,
    file: UploadFile = File(...),
    session: Session = Depends(get_session)
):
    upload_dir = os.path.join("files", "archive")
    os.makedirs(upload_dir, exist_ok=True)
    
    # Generate a safe, unique filename
    base_name, ext = os.path.splitext(file.filename)
    safe_base = "".join([c if c.isalnum() or c in ".-_" else "_" for c in base_name])
    safe_filename = f"{safe_base}{ext}"
    file_path = os.path.join(upload_dir, safe_filename)
    
    # Counter if file already exists
    counter = 1
    while os.path.exists(file_path):
        file_path = os.path.join(upload_dir, f"{safe_base}_{counter}{ext}")
        safe_filename = f"{safe_base}_{counter}{ext}"
        counter += 1
        
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore salvataggio file: {str(e)}")
        
    web_file_path = file_path.replace("\\", "/")
    doc = crud.create_archived_document(session, safe_filename, web_file_path, category, notes)
    return doc

@app.delete("/admin/documents/{doc_id}")
def delete_document(doc_id: int, session: Session = Depends(get_session)):
    doc = session.get(crud.ArchivedDocument, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Documento non trovato")
        
    if os.path.exists(doc.file_path):
        try:
            os.remove(doc.file_path)
        except Exception as e:
            print(f"Errore rimozione file fisico {doc.file_path}: {str(e)}")
            
    success = crud.delete_archived_document(session, doc_id)
    if not success:
        raise HTTPException(status_code=404, detail="Documento non trovato")
    return {"status": "DELETED", "message": "Documento eliminato con successo."}

# --- AUTOMATED DOORS & HARDWARE API ---

@app.get("/admin/hardware/status")
def get_hardware_status():
    """Restituisce lo stato attuale di tutti e 3 gli sportelli e il modulo seriale"""
    from app.hardware import hardware_manager
    return {
        "connection_status": hardware_manager.connection_status,
        "com_port": hardware_manager.com_port,
        "door_states": hardware_manager.door_states,
        "microwave_relay": hardware_manager.microwave_relay,
        "microwave_time_left": hardware_manager.microwave_time_left
    }

@app.post("/admin/hardware/door/{door_id}/open")
def open_hardware_door(door_id: int):
    """Forza l'apertura remota dello sportello selezionato"""
    from app.hardware import hardware_manager
    if door_id not in [1, 2, 3]:
        raise HTTPException(status_code=400, detail="ID sportello non valido. Scegli 1, 2 o 3.")
    hardware_manager.open_door(door_id)
    return {"status": "SUCCESS", "message": f"Inviato comando di sblocco per lo sportello {door_id}"}

@app.post("/admin/hardware/door/{door_id}/close")
def close_hardware_door(door_id: int):
    """Forza la chiusura ed il blocco dello sportello selezionato"""
    from app.hardware import hardware_manager
    if door_id not in [1, 2, 3]:
        raise HTTPException(status_code=400, detail="ID sportello non valido. Scegli 1, 2 o 3.")
    hardware_manager.close_door(door_id)
    return {"status": "SUCCESS", "message": f"Inviato comando di chiusura per lo sportello {door_id}"}

@app.post("/admin/hardware/reset")
def reset_hardware_connection():
    """Ripristina la connessione seriale ad Arduino e azzera gli stati"""
    from app.hardware import hardware_manager
    hardware_manager.reset_connection()
    return {"status": "SUCCESS", "message": "Connessione Arduino ripristinata con successo."}

@app.post("/vending/returns")
def process_pyrex_return_endpoint(payload: dict, session: Session = Depends(get_session)):
    """Gestisce il reso di un contenitore Pyrex (scansione NFC e accredito cauzione)"""
    username = payload.get("username")
    nfc_tag_id = payload.get("nfc_tag_id")
    if not username or not nfc_tag_id:
        raise HTTPException(status_code=400, detail="Username e nfc_tag_id sono richiesti.")
        
    from app.hardware import hardware_manager
    # Apriamo lo sportello resi (Sportello 3)
    hardware_manager.open_door(3)
    
    result = crud.process_pyrex_return(session, username, nfc_tag_id)
    if not result:
        # Se l'utente non esiste, chiudiamo subito lo sportello
        hardware_manager.close_door(3)
        raise HTTPException(status_code=404, detail=f"Utente '{username}' non trovato.")
        
    # Avvia la chiusura automatica dopo 10 secondi dall'accettazione
    import threading
    threading.Timer(10.0, lambda: hardware_manager.close_door(3)).start()
    
    return result



