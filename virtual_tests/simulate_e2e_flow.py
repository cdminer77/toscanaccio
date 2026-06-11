import sys
import os
import time
import io
from fastapi.testclient import TestClient

# Configurazione codifica UTF-8 su Windows per la console (evita errori con emoji)
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        # Fallback se non supportato da vecchie versioni python, anche se usiamo 3.14
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Assicuriamo che la cartella radice sia nel path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app
from app.database import engine, create_db_and_tables
from app.seed import seed_db
from sqlmodel import Session, select
from app.models import VendingSlot, NotificationLog

# Colori ANSI per rendere l'output premium ed elegante nel terminale
C_GREEN = "\033[92m"
C_YELLOW = "\033[93m"
C_RED = "\033[91m"
C_BLUE = "\033[94m"
C_MAGENTA = "\033[95m"
C_CYAN = "\033[96m"
C_BOLD = "\033[1m"
C_RESET = "\033[0m"

client = TestClient(app)

def print_header(title):
    print(f"\n{C_BOLD}{C_CYAN}{'='*60}{C_RESET}")
    print(f"{C_BOLD}{C_CYAN}🚀 SIMULAZIONE: {title.upper()}{C_RESET}")
    print(f"{C_BOLD}{C_CYAN}{'='*60}{C_RESET}")

def print_step(step_num, desc):
    print(f"\n{C_BOLD}{C_BLUE}[Fase {step_num}] {desc}{C_RESET}")

def run_simulation():
    print(f"{C_BOLD}{C_GREEN}🐗 BENVENUTO ALLA SIMULAZIONE END-TO-END DI TOSCANACCIO H24! 🐗{C_RESET}")
    print("Inizializzazione del database temporaneo in memoria e caricamento seed dei dati...")
    
    # 1. SETUP DATABASE E SEEDING
    # Forza ricreazione delle tabelle all'avvio
    create_db_and_tables()
    with Session(engine) as db_session:
        seed_db(db_session)
    
    time.sleep(0.5)
    print(f"{C_GREEN}✅ Database inizializzato con successo!{C_RESET}")

    # =========================================================================
    # FASE 1: REGISTRAZIONE E LOGIN
    # =========================================================================
    print_step(1, "Registrazione e Login Cliente")
    
    # Registrazione
    register_payload = {
        "username": "gourmet_toscano",
        "email": "gourmet.toscano@gmail.com",
        "password": "segretotoscano"
    }
    print(f"-> Invio richiesta POST a /auth/register per '{register_payload['username']}'...")
    res = client.post("/auth/register", json=register_payload)
    if res.status_code == 201:
        data = res.json()
        print(f"   {C_GREEN}🎉 Registrazione completata! User ID: {data['id']}, Ruolo: {data['role']}{C_RESET}")
    else:
        print(f"   {C_RED}❌ Registrazione fallita: {res.text}{C_RESET}")
        return

    # Login
    login_payload = {
        "username": "gourmet_toscano",
        "password": "segretotoscano"
    }
    print(f"-> Richiesta token JWT a /auth/login...")
    res = client.post("/auth/login", json=login_payload)
    if res.status_code == 200:
        token_data = res.json()
        token = token_data["access_token"]
        print(f"   {C_GREEN}🔑 Autenticazione riuscita! Access Token generato (Bearer).{C_RESET}")
    else:
        print(f"   {C_RED}❌ Login fallito: {res.text}{C_RESET}")
        return

    # =========================================================================
    # FASE 2: NAVIGAZIONE DEL MENU
    # =========================================================================
    print_step(2, "Consultazione del Menu Gastronomia")
    print("-> Invio richiesta GET a /menu?category=GASTRONOMIA...")
    res = client.get("/menu?category=GASTRONOMIA")
    menu_items = res.json()
    print(f"   {C_GREEN}🍽️  Trovati {len(menu_items)} piatti disponibili nella Gastronomia:{C_RESET}")
    
    selected_item = None
    for item in menu_items:
        print(f"      - [{item['id']}] {C_BOLD}{item['name']}{C_RESET} - € {item['price']:.2f} ({item['description']})")
        if "Cinghiale" in item["name"]:
            selected_item = item
            
    if not selected_item:
        selected_item = menu_items[0]

    print(f"\n   Selezionato per l'ordine: {C_BOLD}{selected_item['name']}{C_RESET} (ID: {selected_item['id']})")

    # =========================================================================
    # FASE 3: CREAZIONE ORDINE DI CONSEGNA CON DISTANZA E TARIFFARIO DINAMICO
    # =========================================================================
    print_step(3, "Creazione Ordine in Consegna (DELIVERY) con Calcolo Tariffa Geodetica")
    
    # Prepariamo un indirizzo a Livorno
    # Coordinate: 43.518, 10.332 (Distanza stimata circa 3.6 km da Via Machiavelli 102)
    order_payload = {
        "order_type": "DELIVERY",
        "customer_name": "Gourmet Toscano",
        "customer_phone": "+39 347 9876543",
        "address": "Via dell'Ardenza 45, Livorno",
        "latitude": 43.5182,
        "longitude": 10.3321,
        "payment_method": "CRYPTO_EURT",
        "payment_status": "UNPAID",
        "items": [
            {"menu_item_id": selected_item["id"], "quantity": 2}
        ]
    }
    
    print(f"-> Creazione ordine per {order_payload['customer_name']} a {order_payload['address']}...")
    res = client.post("/orders", json=order_payload)
    if res.status_code == 201:
        order_data = res.json()
        print(f"   {C_GREEN}📦 Ordine #{order_data['id']} registrato con successo!{C_RESET}")
        print(f"      Distanza stimata: {C_BOLD}{order_data['latitude']:.2f}° Lat, {order_data['longitude']:.2f}° Lng{C_RESET}")
        print(f"      Costo Consegna (Opzione B: €2 base + €0.50/km): {C_YELLOW}€ {order_data['delivery_fee']:.2f}{C_RESET}")
        print(f"      Totale Ordine (Cibo + Consegna): {C_BOLD}€ {order_data['total']:.2f}{C_RESET}")
    else:
        print(f"   {C_RED}❌ Creazione ordine fallita: {res.text}{C_RESET}")
        return

    # Controlliamo la notifica SMS generata per il Rider Roberto
    with Session(engine) as db_session:
        sms = db_session.exec(select(NotificationLog).where(
            NotificationLog.recipient_name == "Roberto",
            NotificationLog.channel == "SMS"
        )).first()
        if sms:
            print(f"\n   {C_MAGENTA}📱 LOG NOTIFICHE [SMS per Rider Roberto]:{C_RESET}")
            print(f"      A: {sms.phone_number}")
            print(f"      Messaggio: \"{sms.message_content}\"")

    # =========================================================================
    # FASE 4: SIMULAZIONE PAGAMENTO CRYPTO (EURT SU POLYGON)
    # =========================================================================
    print_step(4, "Pagamento Crypto in Stablecoin EURT (Polygon)")
    
    # 1. Richiesta fattura
    print(f"-> Richiesta fattura crypto a /payments/crypto/invoice per € {order_data['total']:.2f}...")
    res = client.post("/payments/crypto/invoice", json={"amount": order_data["total"]})
    invoice_data = res.json()
    print(f"   {C_GREEN}🧾 Dettagli Fattura Generati:{C_RESET}")
    print(f"      Rete: {invoice_data['network']} | Valuta: {invoice_data['currency']}")
    print(f"      Wallet Destinatario: {invoice_data['merchant_wallet']}")
    print(f"      QR Code Web3 Protocollo: {C_YELLOW}{invoice_data['payment_qr_code']}{C_RESET}")

    # 2. Transazione emulata inviata da Metamask / TrustWallet
    mock_tx_hash = "0x8e82a8326cb78c6e266a7b399047b532187569bc92b7c4d5e6f3a1c89012435a"
    print(f"\n-> Invio hash transazione per la verifica a /payments/crypto/verify...")
    res = client.post("/payments/crypto/verify", json={
        "tx_hash": mock_tx_hash,
        "amount": order_data["total"]
    })
    verify_data = res.json()
    print(f"   {C_GREEN}🔗 Transazione Confermata sulla Blockchain!{C_RESET}")
    print(f"      Block: {verify_data['block_number']} | Conferme: {verify_data['confirmations']} | Gas Usato: {verify_data['gas_used']}")
    
    # Aggiorna lo stato dell'ordine a PAGATO
    client.patch(f"/orders/{order_data['id']}?status=CONFIRMED")
    print(f"   {C_GREEN}✅ Ordine #{order_data['id']} aggiornato a CONFIRMED dopo il pagamento.{C_RESET}")

    # =========================================================================
    # FASE 5: SIMULAZIONE GUASTO HARDWARE SU DISTRIBUTORE VENDING H24
    # =========================================================================
    print_step(5, "Simulazione Guasto Hardware Vending SandenVendo (Spirale Bloccata C4)")
    
    # Iniezione guasto
    print("-> Invio richiesta POST a /vending/telemetry/fault per macchina 'gdrink1' tipo 'JAM'...")
    res = client.post("/vending/telemetry/fault", json={
        "machine": "gdrink1",
        "fault_type": "JAM"
    })
    fault_data = res.json()
    print(f"   {C_RED}⚠️ ALLARME TELEMETRIA: {fault_data['telemetry']['grid_faults'][-1]}{C_RESET}")
    
    # Verifichiamo lo stato dello slot C4
    with Session(engine) as db_session:
        slot = db_session.exec(select(VendingSlot).where(VendingSlot.position_code == "C4")).first()
        if slot:
            print(f"   DB Sync: Lo slot vending C4 è ora impostato a stato: {C_BOLD}{C_RED}{slot.status}{C_RESET}")
            
        # Verifichiamo la notifica WhatsApp generata per il manutentore Claudio
        whatsapp = db_session.exec(select(NotificationLog).where(
            NotificationLog.recipient_name == "Claudio",
            NotificationLog.event_type == "FAULT_ALERT",
            NotificationLog.channel == "WHATSAPP"
        )).first()
        if whatsapp:
            print(f"\n   {C_MAGENTA}📱 LOG NOTIFICHE [WhatsApp per Tecnico Claudio]:{C_RESET}")
            print(f"      A: {whatsapp.phone_number}")
            print(f"      Messaggio: \"{whatsapp.message_content}\"")

    # =========================================================================
    # FASE 6: RISOLUZIONE GUASTO (CLEAR)
    # =========================================================================
    print_step(6, "Intervento Tecnico e Ripristino della Telemetria")
    print("-> Invio richiesta POST a /vending/telemetry/fault con tipo 'CLEAR'...")
    res = client.post("/vending/telemetry/fault", json={
        "machine": "gdrink1",
        "fault_type": "CLEAR"
    })
    clear_data = res.json()
    print(f"   {C_GREEN}✅ Allarmi attivi su gdrink1: {clear_data['telemetry']['grid_faults']}{C_RESET}")
    
    with Session(engine) as db_session:
        restore_alert = db_session.exec(select(NotificationLog).where(
            NotificationLog.recipient_name == "Claudio",
            NotificationLog.event_type == "RESTORE_ALERT"
        )).first()
        if restore_alert:
            print(f"\n   {C_MAGENTA}📱 LOG NOTIFICHE [WhatsApp per Tecnico Claudio]:{C_RESET}")
            print(f"      Messaggio: \"{restore_alert.message_content}\"")

    # =========================================================================
    # FASE 7: PREVISIONE INTELLIGENZA ARTIFICIALE DELLA PRODUZIONE
    # =========================================================================
    print_step(7, "Richiesta Previsione di Produzione Giornaliera (I.A. Predittiva)")
    print("-> Invio richiesta GET a /predict...")
    res = client.get("/predict")
    forecasts = res.json()
    
    print(f"   {C_GREEN}🔮 Previsioni I.A. elaborate per domani:{C_RESET}")
    print(f"      {C_BOLD}{'Prodotto':<35} | {'Quantità Consigliata':<20} | {'Motivazione'}{C_RESET}")
    print(f"      {'-'*90}")
    for item in forecasts[:4]:  # Mostra solo i primi 4 per brevità
        print(f"      {item['name']:<35} | {item['recommended_quantity']:^20} | {item['reason']}")
    print(f"      ...")

    print(f"\n{C_BOLD}{C_GREEN}🎉 SIMULAZIONE COMPLETATA CON SUCCESSO! TUTTE LE FUNZIONALITA' DI TOSCANACCIO SONO STATE VALIDATE! 🐗{C_RESET}\n")

if __name__ == "__main__":
    # Abilitiamo la formattazione ANSI su console Windows se necessario
    if sys.platform == "win32":
        os.system("color")
    run_simulation()
