from sqlmodel import Session, select
from .models import MenuItem, Category, Stock, VendingSlot, Rider, User, UserRole
from .crud import get_password_hash

def seed_db(session: Session):
    # 1. Popola MenuItem se vuoto
    if session.exec(select(MenuItem)).first():
        print("Menu gia' popolato.")
        return

    items = [
        MenuItem(
            code="TOS-001",
            name="Cacciucco alla livornese",
            description="Zuppa di pesce povero del Tirreno — scorfano, tracina, palombo, seppie, polpo, vongole — in brodetto di pomodoro speziato con peperoncino e vino rosso. Servita su fette di pane toscano abbrustolito strofinato d'aglio. Almeno 5 tipi di pesce come da tradizione.",
            price=13.0,
            category=Category.ZUPPA_PESCE,
            food_cost_pct=0.38,
            container_code="PYR-L",
            channels='["walk-in"]',
            availability_notes="Quantità limitata giornaliera — esaurito in fretta",
            note_ops="Preparazione batch ogni mattina. Porzioni fisse: 15–20 pranzo, 10 cena.",
            is_signature=True,
            is_vegan=False
        ),
        MenuItem(
            code="TOS-002",
            name="Cinghiale in salmì",
            description="Cinghiale maremmano marinato 24h in vino rosso con ginepro, alloro e chiodi di garofano. Cottura lenta in casseruola. Servito con pane casereccio toscano.",
            price=9.0,
            category=Category.SECONDO_CARNE,
            food_cost_pct=0.33,
            container_code="PYR-L",
            channels='["walk-in", "delivery"]',
            availability_notes="Tutto l'anno — stagionalità autunno/inverno privilegiata",
            note_ops="Marinatura 24h. Batch settimanale. Stagionale: disponibile da settembre.",
            is_signature=True,
            is_vegan=False
        ),
        MenuItem(
            code="TOS-003",
            name="Peposo dell'Impruneta",
            description="Spezzatino di manzo al vino rosso e pepe nero in grani, cottura lenta. Ricetta della tradizione dei fornaciai dell'Impruneta.",
            price=8.0,
            category=Category.SECONDO_CARNE,
            food_cost_pct=0.30,
            container_code="PYR-S",
            channels='["walk-in", "delivery"]',
            availability_notes="Tutto l'anno",
            note_ops="Cottura 3–4h. Batch giornaliero. Ottimo il giorno dopo.",
            is_signature=True,
            is_vegan=False
        ),
        MenuItem(
            code="TOS-004",
            name="Lampredotto in umido",
            description="Quarto stomaco del bovino, cottura lunga in brodo aromatico con pomodoro, sedano e prezzemolo. Servito con pane sciocco toscano tostato. Il quinto quarto fiorentino più autentico.",
            price=7.5,
            category=Category.QUINTO_QUARTO,
            food_cost_pct=0.22,
            container_code="PYR-S",
            channels='["walk-in"]',
            availability_notes="Tutto l'anno — solo walk-in, servito caldo",
            note_ops="Cottura lenta in brodo. Servire sempre ben caldo. Non adatto al delivery.",
            is_signature=True,
            is_vegan=False
        ),
        MenuItem(
            code="TOS-005",
            name="Ragù di chianina al cucchiaio",
            description="Ragù lento di manzo Chianina IGP servito su crostone di pane toscano abbrustolito. Carne toscana tracciata, cottura di almeno 3 ore.",
            price=7.0,
            category=Category.PIATTO_UNICO,
            food_cost_pct=0.28,
            container_code="PYR-S",
            channels='["walk-in", "delivery"]',
            availability_notes="Tutto l'anno",
            note_ops="Batch giornaliero. Il sugo migliora il giorno dopo.",
            is_signature=False,
            is_vegan=False
        ),
        MenuItem(
            code="TOS-006",
            name="Polpette al sugo della mamma",
            description="Polpette di macinato misto con pane ammollato nel latte, in sugo di pomodoro lungo. Ricetta casalinga, comfort food autentico.",
            price=7.0,
            category=Category.SECONDO_CARNE,
            food_cost_pct=0.27,
            container_code="PYR-S",
            channels='["walk-in", "delivery", "vending"]',
            availability_notes="Tutto l'anno",
            note_ops="Batch giornaliero. Reggono bene il trasporto e il vending.",
            is_signature=False,
            is_vegan=False
        ),
        MenuItem(
            code="TOS-007",
            name="Ribollita della nonna",
            description="Zuppa povera toscana con cavolo nero, fagioli cannellini e pane raffermo tostato. La ricetta che non cambia da generazioni.",
            price=6.5,
            category=Category.ZUPPA,
            food_cost_pct=0.24,
            container_code="PYR-S",
            channels='["walk-in", "delivery"]',
            availability_notes="Tutto l'anno — preferibile autunno/inverno",
            note_ops="Batch mattutino. Ribollita = riscaldata due volte, migliora.",
            is_signature=True,
            is_vegan=True
        ),
        MenuItem(
            code="TOS-008",
            name="Fagioli all'uccelletto con salsiccia",
            description="Cannellini toscani in salsa di pomodoro con salvia e aglio, accompagnati da salsiccia artigianale. Piatto completo, proteico, della tradizione contadina.",
            price=6.5,
            category=Category.PIATTO_UNICO,
            food_cost_pct=0.25,
            container_code="PYR-S",
            channels='["walk-in", "delivery", "vending"]',
            availability_notes="Tutto l'anno",
            note_ops="Batch giornaliero. Ottimo anche freddo — adatto al vending.",
            is_signature=False,
            is_vegan=False
        ),
        MenuItem(
            code="TOS-009",
            name="Zuppa di farro della Garfagnana",
            description="Farro IGP della Garfagnana con legumi misti e verdure di stagione. Vegano, proteico, dal sapore rustico e autentico.",
            price=6.0,
            category=Category.ZUPPA,
            food_cost_pct=0.21,
            container_code="PYR-S",
            channels='["walk-in", "delivery", "vending"]',
            availability_notes="Tutto l'anno — rotazione verdure stagionali",
            note_ops="Batch giornaliero. Ingredienti a lunga conservazione.",
            is_signature=False,
            is_vegan=True
        ),
        MenuItem(
            code="TOS-010",
            name="Pappa al pomodoro",
            description="Pomodoro fresco (o pelato in inverno), pane sciocco toscano raffermo, basilico fresco, olio EVO toscano. Semplicità assoluta, sapore autentico.",
            price=5.5,
            category=Category.ZUPPA,
            food_cost_pct=0.19,
            container_code="PYR-S",
            channels='["walk-in", "delivery", "vending"]',
            availability_notes="Tutto l'anno — pomodoro fresco estate, pelato inverno",
            note_ops="Massimo margine del menu. Batch veloce.",
            is_signature=True,
            is_vegan=True
        ),
        MenuItem(
            code="TOS-011",
            name="Cecìna livornese",
            description="Torta di ceci livornese cotta in forno. Croccante fuori, morbida dentro. Il biglietto da visita di Livorno — una 'C' di appartenenza.",
            price=3.5,
            category=Category.STREET_FOOD,
            food_cost_pct=0.14,
            container_code="PYR-S",
            channels='["walk-in", "vending"]',
            availability_notes="Tutto l'anno",
            note_ops="Produzione continua. Servire calda al walk-in. Versione confezionata per vending.",
            is_signature=True,
            is_vegan=True
        ),
        MenuItem(
            code="TOS-012",
            name="Cantucci con Vin Santo",
            description="Biscotti di Prato al naturale in monoporzione da viaggio, accompagnati da Vin Santo toscano in miniatura. Perfetti per delivery e vending.",
            price=3.0,
            category=Category.DOLCE,
            food_cost_pct=0.16,
            container_code="PYR-S",
            channels='["walk-in", "delivery", "vending"]',
            availability_notes="Tutto l'anno",
            note_ops="Monoporzione confezionata. Stock settimanale.",
            is_signature=False,
            is_vegan=False
        ),
        MenuItem(
            code="TOS-013",
            name="Pasta Cup Berruto - Pomodoro",
            description="Pasta istantanea in tazza Berruto. Pronta in 3 minuti aggiungendo acqua calda. Perfetta per uno spuntino rapido.",
            price=2.5,
            category=Category.SNACK,
            food_cost_pct=0.20,
            container_code="CUP",
            channels='["walk-in", "vending"]',
            availability_notes="Tutto l'anno",
            note_ops="Prodotto secco in tazza. Richiede acqua calda.",
            is_signature=False,
            is_vegan=True,
            requires_microwave=False,
            requires_hot_water=True
        ),
        MenuItem(
            code="SRV-001",
            name="Erogazione Acqua Calda (Bicchiere Incluso)",
            description="Servizio di erogazione acqua calda dalla macchina Bianchi Lei 900. Ideale per cup o infusi personali.",
            price=0.10,
            category=Category.SNACK,
            food_cost_pct=0.01,
            container_code="CUP",
            channels='["vending"]',
            availability_notes="Sempre attivo",
            note_ops="Servizio di sblocco erogazione acqua calda.",
            is_signature=False,
            is_vegan=True,
            requires_microwave=False,
            requires_hot_water=True
        ),
        MenuItem(
            code="SRV-002",
            name="Utilizzo Microonde Professionale (Max 3 Min)",
            description="Abilitazione all'uso del microonde per riscaldare i piatti pronti acquistati.",
            price=0.20,
            category=Category.GASTRONOMIA,
            food_cost_pct=0.01,
            container_code="NONE",
            channels='["vending"]',
            availability_notes="Sempre attivo",
            note_ops="Servizio di sblocco presa elettrica e sportello microonde.",
            is_signature=False,
            is_vegan=True,
            requires_microwave=True,
            requires_hot_water=False
        ),
    ]
    
    for item in items:
        session.add(item)
    session.commit()
    
    # Rinfresca gli item per avere i loro ID
    for item in items:
        session.refresh(item)
    print("MenuItem popolati con successo (" + str(len(items)) + " articoli)!")

    # 2. Popola Stock iniziale per magazzino centrale (25 unita per articolo)
    for item in items:
        stock = Stock(menu_item_id=item.id, current_quantity=25, min_alert_threshold=5)
        session.add(stock)
    session.commit()
    print("Stock iniziale popolato (25 unita per articolo)!")

    # 3. Popola 100 Vending Slots per la distribuzione automatica SandenVendo H24
    # Filtriamo solo gli articoli adatti al vending
    vending_items = [item for item in items if ("vending" in item.channels and not item.code.startswith("SRV-")) or item.code in ["TOS-006", "TOS-008", "TOS-009", "TOS-010", "TOS-011", "TOS-012", "TOS-013"]]
    if not vending_items:
        vending_items = items

    slots = []
    
    shelves_machine_1 = ["A", "B", "C", "D", "E"]
    shelves_machine_2 = ["F", "G", "H", "I", "J"]
    
    for shelf in shelves_machine_1:
        for column in range(1, 11):
            pos_code = shelf + str(column)
            # Distribuzione ciclica degli articoli da vending
            v_idx = (ord(shelf) * 7 + column) % len(vending_items)
            item_id = vending_items[v_idx].id
            
            qty = random_initial_quantity(pos_code)
            slot_status = "ACTIVE"
            if pos_code in ["D8"]:
                slot_status = "MAINTENANCE"
                qty = 2
                
            slots.append(VendingSlot(position_code=pos_code, menu_item_id=item_id, current_quantity=qty, max_capacity=10, status=slot_status))

    for shelf in shelves_machine_2:
        for column in range(1, 11):
            pos_code = shelf + str(column)
            v_idx = (ord(shelf) * 11 + column * 3) % len(vending_items)
            item_id = vending_items[v_idx].id
            
            qty = random_initial_quantity(pos_code)
            slot_status = "ACTIVE"
            
            if pos_code in ["F4", "H9", "J10"]:
                item_id = None
                qty = 0
                slot_status = "EMPTY"
            elif pos_code in ["G3"]:
                slot_status = "MAINTENANCE"
                qty = 2
                
            slots.append(VendingSlot(position_code=pos_code, menu_item_id=item_id, current_quantity=qty, max_capacity=8 if "H" in pos_code or "G" in pos_code else 10, status=slot_status))

    for slot in slots:
        session.add(slot)
    session.commit()
    print("SandenVendo G-Drink x 2 (100 Slots totali) inizializzati!")

    # 4. Popola Rider di test
    riders = [
        Rider(
            name="claudio", 
            phone="+39 333 1234567", 
            status="AVAILABLE",
            personal_data="Claudio Rossi, CF: RSSCLD90A01E625X, Email: claudio@toscanaccio.it",
            financial_data="IT99A0123456789012345678901",
            work_area="Centro Storico & Venezia (Livorno)"
        ),
        Rider(
            name="roberto", 
            phone="+39 344 7654321", 
            status="AVAILABLE",
            personal_data="Roberto Bianchi, CF: BNCRBT88M12E625O, Email: roberto@toscanaccio.it",
            financial_data="IT88B0987654321098765432109",
            work_area="Ardenza & Antignano (Livorno)"
        ),
    ]
    for rider in riders:
        session.add(rider)
    session.commit()
    print("Rider di test caricati!")

    # 5. Popola Utenti di test per autenticazione (Fase 2)
    admin_user = User(
        username="admin",
        email="admin@toscanaccio.it",
        hashed_password=get_password_hash("adminpass"),
        role=UserRole.ADMIN
    )
    rider_user = User(
        username="claudio",
        email="claudio@toscanaccio.it",
        hashed_password=get_password_hash("claudiopass"),
        role=UserRole.RIDER
    )
    customer_user = User(
        username="mario",
        email="mario@gmail.com",
        hashed_password=get_password_hash("mariopass"),
        role=UserRole.CUSTOMER
    )
    
    if not session.exec(select(User).where(User.username == "admin")).first():
        session.add(admin_user)
        session.add(rider_user)
        session.add(customer_user)
        session.commit()
        print("Utenti di test registrati (admin, claudio, mario)!")

    # 6. Popola Scadenziario iniziale se vuoto
    from .models import PaymentDeadline, AccountingEntry
    if not session.exec(select(PaymentDeadline)).first():
        from datetime import datetime, timedelta
        deadlines = [
            PaymentDeadline(
                description="Affitto Locale Via Machiavelli 102 (Casalp)",
                amount=220.00,
                due_date=datetime.now() + timedelta(days=20),
                status="PENDING",
                category="AFFITTO"
            ),
            PaymentDeadline(
                description="Bolletta Luce Enel Energia",
                amount=145.30,
                due_date=datetime.now() - timedelta(days=2),
                status="PENDING",
                category="UTENZE"
            ),
            PaymentDeadline(
                description="Acquisto Materie Prime (Fornitore Ortofrutta Livorno)",
                amount=350.00,
                due_date=datetime.now() + timedelta(days=5),
                status="PENDING",
                category="INGREDIENTI"
            ),
            PaymentDeadline(
                description="Tassa Rifiuti TARI Comune di Livorno",
                amount=85.00,
                due_date=datetime.now() - timedelta(days=15),
                status="PAID",
                payment_date=datetime.now() - timedelta(days=15),
                category="FISCALE"
            )
        ]
        for dl in deadlines:
            session.add(dl)
        session.commit()
        print("Scadenziario iniziale popolato!")
        
        # Aggiungiamo anche la Tari pagata in contabilità per iniziare con un movimento di uscita
        tari_dl = deadlines[3]
        session.add(AccountingEntry(
            description=f"Pagamento scadenza: {tari_dl.description}",
            entry_type="USCITA",
            amount=69.67,  # net of 22% vat (TARI is usually a tax but let's assume 22% or whatever for simulation)
            vat_amount=15.33,
            vat_rate=0.22,
            amount_gross=85.00,
            category="FISCALE",
            date=tari_dl.payment_date
        ))
        session.commit()


def random_initial_quantity(pos_code: str) -> int:
    if pos_code in ["A1", "A3", "F1", "G1", "H2"]:
        return 2
    return random.randint(4, 9)

import random
