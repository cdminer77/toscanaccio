from sqlmodel import Session, select
from .models import MenuItem, Category, Stock, VendingSlot, Rider, User, UserRole
from .crud import get_password_hash

def seed_db(session: Session):
    # 1. Popola MenuItem se vuoto
    if session.exec(select(MenuItem)).first():
        print("Menu gia' popolato.")
        return

    items = [
        # Primi Piatti Caldi & Gastronomia
        MenuItem(name="Pappa al Pomodoro", description="Classica toscana con crostini e basilico fresco", price=9.90, category=Category.GASTRONOMIA),
        MenuItem(name="Ribollita Toscana", description="Zuppa tradizionale di pane, fagioli e verdure selvatiche", price=10.50, category=Category.GASTRONOMIA),
        MenuItem(name="Pappardelle al Sugo di Cinghiale", description="Hero product con pasta fresca all'uovo e cinghiale locale", price=13.90, category=Category.GASTRONOMIA),
        MenuItem(name="Lasagne alla Toscana", description="Pasta al forno con ragù toscano cotto a fuoco lento", price=12.90, category=Category.GASTRONOMIA),
        MenuItem(name="Cacciucco Livornese", description="Zuppa di pesce ricca e saporita con pane agliato", price=14.90, category=Category.GASTRONOMIA),
        MenuItem(name="Zuppa di Legumi e Farro", description="Zuppa contadina toscana ad alta digeribilita'", price=9.50, category=Category.GASTRONOMIA),
        MenuItem(name="Peposo dell'Impruneta", description="Spezzatino di manzo toscano stracotto con pepe nero e Chianti", price=15.90, category=Category.GASTRONOMIA),
        MenuItem(name="Trippa alla Fiorentina", description="Trippa classica in umido con pomodoro e spolverata di pecorino", price=11.50, category=Category.GASTRONOMIA),
        MenuItem(name="Cantucci di Prato con Vin Santo", description="Cantucci artigianali alle mandorle serviti con Vin Santo", price=8.00, category=Category.GASTRONOMIA),
        
        # Taglieri, Panini & Prosciutteria
        MenuItem(name="Toscano Classico", description="Salumi misti toscani, finocchiona e pecorino semistagionato", price=18.00, category=Category.PROSCIUTTERIA),
        MenuItem(name="Cinta Senese Experience", description="Tagliere deluxe con Prosciutto DOP di Cinta Senese e salumi rari", price=28.00, category=Category.PROSCIUTTERIA),
        MenuItem(name="Pecorino Tour", description="Selezione di 3 pecorini toscani con confettura di cipolle e miele", price=25.00, category=Category.PROSCIUTTERIA),
        MenuItem(name="Schiacciata Finocchiona & Pecorino", description="Schiacciata toscana ripiena di finocchiona locale e pecorino fresco", price=8.50, category=Category.PROSCIUTTERIA),
        MenuItem(name="Schiacciata Prosciutto DOP & Tartufo", description="Schiacciata con prosciutto crudo toscano e crema al tartufo", price=9.50, category=Category.PROSCIUTTERIA),
        MenuItem(name="Schiacciata Vegetariana Toscana", description="Con verdure grigliate, pecorino fresco e crema di basilico", price=7.50, category=Category.PROSCIUTTERIA),

        # Bevande Locali e Birre (adatte per distributore SandenVendo G-Drink)
        MenuItem(name="Spuma Bionda Toscana", description="La storica bibita gassata toscana, dolce e aromatica (33cl)", price=2.50, category=Category.BEVANDE, version_size="standard"),
        MenuItem(name="Spuma Nera del Valdarno", description="Spuma scura toscana tradizionale con estratto di rabarbaro (33cl)", price=2.50, category=Category.BEVANDE, version_size="standard"),
        MenuItem(name="Chinotto Toscano", description="Bibita analcolica dal sapore piacevolmente amaro (33cl)", price=2.80, category=Category.BEVANDE, version_size="standard"),
        MenuItem(name="Gassosa Lucchese", description="Gassosa locale prodotta secondo ricetta storica (33cl)", price=2.50, category=Category.BEVANDE, version_size="standard"),
        MenuItem(name="Cedrata dei Fiori", description="Cedrata profumata e rinfrescante (33cl)", price=2.80, category=Category.BEVANDE, version_size="standard"),
        MenuItem(name="Acqua Naturale San Felice", description="Acqua minerale toscana in bottiglia di vetro (50cl)", price=1.50, category=Category.BEVANDE, version_size="standard"),
        MenuItem(name="Acqua Frizzante San Felice", description="Acqua gassata toscana in bottiglia di vetro (50cl)", price=1.50, category=Category.BEVANDE, version_size="standard"),
        MenuItem(name="Birra Artigianale Livornese IPA", description="Birra bionda luppolata prodotta a Livorno (33cl)", price=5.50, category=Category.BEVANDE, version_size="standard"),
        MenuItem(name="Birra Artigianale Livornese Rossa", description="Birra ambrata doppio malto, corpo pieno (33cl)", price=5.50, category=Category.BEVANDE, version_size="standard"),
        MenuItem(name="Birra Mastio Bionda", description="Birra artigianale a bassa fermentazione, rinfrescante (33cl)", price=5.00, category=Category.BEVANDE, version_size="standard"),
        MenuItem(name="Chianti Classico DOCG (375ml)", description="Mezza bottiglia di vino rosso Chianti Classico DOCG", price=12.00, category=Category.BEVANDE, version_size="standard"),
        MenuItem(name="Vernaccia di San Gimignano (375ml)", description="Mezza bottiglia di vino bianco Vernaccia DOCG", price=10.00, category=Category.BEVANDE, version_size="standard"),
        MenuItem(name="Bolgheri Rosso DOC (375ml)", description="Mezza bottiglia di vino Bolgheri Rosso strutturato", price=16.00, category=Category.BEVANDE, version_size="standard"),

        # Snack Salati e Cantuccini Monoporzione
        MenuItem(name="Schiacciatine Croccanti", description="Schiacciatine toscane all'olio d'oliva in monoporzione", price=2.50, category=Category.SNACK, version_size="standard"),
        MenuItem(name="Tarallini al Rosmarino", description="Tarallini artigianali aromatizzati al rosmarino", price=2.00, category=Category.SNACK, version_size="standard"),
        MenuItem(name="Cantuccini alle Mandorle (Monoporzione)", description="Due cantucci di Prato artigianali perfetti come snack", price=1.50, category=Category.SNACK, version_size="standard"),

        # Prodotto Artigianale Toscanaccio (Varianti con diverse grammature)
        MenuItem(name="Ragù di Cinghiale Toscanaccio", description="Ragù selvatico artigianale della Garfagnana in vaso di vetro", price=8.90, category=Category.ARTIGIANALE, version_size="250g"),
        MenuItem(name="Ragù di Cinghiale Toscanaccio", description="Ragù selvatico artigianale della Garfagnana in vaso di vetro", price=12.50, category=Category.ARTIGIANALE, version_size="400g"),
        MenuItem(name="Ragù di Cinghiale Toscanaccio", description="Ragù selvatico artigianale della Garfagnana in vaso di vetro", price=24.90, category=Category.ARTIGIANALE, version_size="1kg"),

        MenuItem(name="Pappa al Pomodoro Toscanaccio", description="Pronta da scaldare, ricetta storica con pomodori toscani", price=6.90, category=Category.ARTIGIANALE, version_size="250g"),
        MenuItem(name="Pappa al Pomodoro Toscanaccio", description="Pronta da scaldare, ricetta storica con pomodori toscani", price=9.90, category=Category.ARTIGIANALE, version_size="400g"),
        MenuItem(name="Pappa al Pomodoro Toscanaccio", description="Pronta da scaldare, ricetta storica con pomodori toscani", price=19.90, category=Category.ARTIGIANALE, version_size="1kg"),

        MenuItem(name="Sugo all'Aglione Toscanaccio", description="Sugo tipico della Val di Chiana con aglio gigante toscano", price=5.90, category=Category.ARTIGIANALE, version_size="250g"),
        MenuItem(name="Sugo all'Aglione Toscanaccio", description="Sugo tipico della Val di Chiana con aglio gigante toscano", price=8.50, category=Category.ARTIGIANALE, version_size="400g"),
        MenuItem(name="Sugo all'Aglione Toscanaccio", description="Sugo tipico della Val di Chiana con aglio gigante toscano", price=16.90, category=Category.ARTIGIANALE, version_size="1kg"),
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
    # G-Drink 1: Ripiani A-E (Cibo freddo, piatti caldi pronti, bibite analcoliche) -> 50 slot
    # G-Drink 2: Ripiani F-J (Vini DOP, birre artigianali, taglieri pronti, dolci) -> 50 slot
    slots = []
    
    shelves_machine_1 = ["A", "B", "C", "D", "E"]
    shelves_machine_2 = ["F", "G", "H", "I", "J"]
    
    for shelf in shelves_machine_1:
        for column in range(1, 11):
            pos_code = shelf + str(column)
            if shelf == "A": # Primi piatti caldi
                item_idx = column % 5 
            elif shelf == "B": # Altri piatti caldi e zuppe
                item_idx = 5 + (column % 4)
            elif shelf == "C": # Schiacciate e panini
                item_idx = 12 + (column % 3)
            elif shelf == "D": # Spume e bibite
                item_idx = 15 + (column % 5)
            else: # E: Acque e bibite
                item_idx = 17 + (column % 5)
                
            qty = random_initial_quantity(pos_code)
            slots.append(VendingSlot(position_code=pos_code, menu_item_id=items[item_idx].id, current_quantity=qty, max_capacity=10, status="ACTIVE"))

    for shelf in shelves_machine_2:
        for column in range(1, 11):
            pos_code = shelf + str(column)
            if shelf == "F": # Birre artigianali
                item_idx = 22 + (column % 3)
            elif shelf == "G": # Vini in mezza bottiglia
                item_idx = 25 + (column % 3)
            elif shelf == "H": # Taglieri pronti
                item_idx = 9 + (column % 3)
            elif shelf == "I": # Dolci e schiacciate
                item_idx = 8 + (column % 5)
            else: # J: Assortiti a caso per riempimento
                item_idx = (column * 3) % len(items)

            qty = random_initial_quantity(pos_code)
            slot_item_id = items[item_idx].id
            slot_status = "ACTIVE"
            if pos_code in ["F4", "H9", "J10"]:
                slot_item_id = None
                qty = 0
                slot_status = "EMPTY"
            elif pos_code in ["D8", "G3"]:
                slot_status = "MAINTENANCE"
                qty = 2
                
            slots.append(VendingSlot(position_code=pos_code, menu_item_id=slot_item_id, current_quantity=qty, max_capacity=8 if "H" in pos_code or "G" in pos_code else 10, status=slot_status))

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

def random_initial_quantity(pos_code: str) -> int:
    if pos_code in ["A1", "A3", "F1", "G1", "H2"]:
        return 2
    return random.randint(4, 9)

import random
