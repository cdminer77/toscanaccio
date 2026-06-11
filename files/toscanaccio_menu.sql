-- ================================================================
-- TOSCANACCIO · Menu Database · v3 · Giugno 2026
-- Ghost Kitchen H24 · Via Tito Speri 28, Livorno
-- Generato automaticamente da menu_data.py
-- ================================================================

SET NAMES utf8mb4;
SET time_zone = '+01:00';

-- ----------------------------------------------------------------
-- CONTENITORI PYREX
-- ----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS contenitori (
    id          INT PRIMARY KEY AUTO_INCREMENT,
    codice      VARCHAR(10)  NOT NULL UNIQUE,
    descrizione VARCHAR(100) NOT NULL,
    volume_ml   SMALLINT     NOT NULL,
    uso         VARCHAR(200),
    tappo       VARCHAR(200)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO contenitori (codice, descrizione, volume_ml, uso, tappo) VALUES
  ('PYR-S', 'Pyrex monoporzione', 500, 'Zuppe, secondi, piatti unici', 'Tappo 3D PLA/PETG con QR + NFC'),
  ('PYR-L', 'Pyrex grande', 900, 'Cacciucco, cinghiale in salmì, porzioni doppie', 'Tappo 3D PLA/PETG con QR + NFC');

-- ----------------------------------------------------------------
-- CATEGORIE
-- ----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS categorie (
    id   INT PRIMARY KEY AUTO_INCREMENT,
    nome VARCHAR(100) NOT NULL UNIQUE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO categorie (nome) VALUES
  ('Dolce'),
  ('Piatto unico'),
  ('Quinto quarto'),
  ('Secondo di carne'),
  ('Street food / territorio'),
  ('Zuppa'),
  ('Zuppa di pesce');

-- ----------------------------------------------------------------
-- ALLERGENI
-- ----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS allergeni (
    id   INT PRIMARY KEY AUTO_INCREMENT,
    nome VARCHAR(80) NOT NULL UNIQUE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO allergeni (nome) VALUES
  ('Crostacei'),
  ('Frutta a guscio'),
  ('Glutine'),
  ('Latte'),
  ('Legumi'),
  ('Molluschi'),
  ('Pesce'),
  ('Sedano'),
  ('Uova');

-- ----------------------------------------------------------------
-- PIATTI
-- ----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS piatti (
    id                    INT PRIMARY KEY,
    codice                VARCHAR(10)  NOT NULL UNIQUE,
    nome                  VARCHAR(150) NOT NULL,
    categoria_id          INT          NOT NULL,
    descrizione           TEXT,
    ingredienti_principali JSON,
    prezzo                DECIMAL(6,2) NOT NULL,
    food_cost_pct         TINYINT      NOT NULL,
    margine_lordo         DECIMAL(6,2) GENERATED ALWAYS AS (prezzo * (1 - food_cost_pct/100)) STORED,
    contenitore_id        INT          NOT NULL,
    canali                JSON,
    disponibilita         VARCHAR(200),
    note_ops              TEXT,
    piatto_firma          TINYINT(1)   DEFAULT 0,
    vegan                 TINYINT(1)   DEFAULT 0,
    attivo                TINYINT(1)   DEFAULT 1,
    created_at            TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_categoria  FOREIGN KEY (categoria_id)  REFERENCES categorie(id),
    CONSTRAINT fk_contenitore FOREIGN KEY (contenitore_id) REFERENCES contenitori(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO piatti
  (id, codice, nome, categoria_id, descrizione, ingredienti_principali,
   prezzo, food_cost_pct, contenitore_id, canali,
   disponibilita, note_ops, piatto_firma, vegan)
VALUES
  (1, 'TOS-001', 'Cacciucco alla livornese', 7, 'Zuppa di pesce povero del Tirreno — scorfano, tracina, palombo, seppie, polpo, vongole — in brodetto di pomodoro speziato con peperoncino e vino rosso. Servita su fette di pane toscano abbrustolito strofinato d\'aglio. Almeno 5 tipi di pesce come da tradizione.', '["Scorfano", "Tracina", "Palombo", "Seppie", "Polpo", "Vongole", "Pomodoro pelato", "Aglio", "Peperoncino", "Vino rosso", "Pane toscano"]', 13.0, 38, 2, '["walk-in"]', 'Quantità limitata giornaliera — esaurito esaurito', 'Preparazione batch ogni mattina. Porzioni fisse: 15–20 pranzo, 10 cena.', 1, 0),
  (2, 'TOS-002', 'Cinghiale in salmì', 4, 'Cinghiale maremmano marinato 24h in vino rosso con ginepro, alloro e chiodi di garofano. Cottura lenta in casseruola. Servito con pane casereccio toscano.', '["Cinghiale", "Vino rosso", "Ginepro", "Alloro", "Chiodi di garofano", "Cipolla", "Carota", "Sedano", "Pane casereccio"]', 9.0, 33, 2, '["walk-in", "delivery"]', 'Tutto l\'anno — stagionalità autunno/inverno privilegiata', 'Marinatura 24h. Batch settimanale. Stagionale: disponibile da settembre.', 1, 0),
  (3, 'TOS-003', 'Peposo dell'Impruneta', 4, 'Spezzatino di manzo al vino rosso e pepe nero in grani, cottura lenta. Ricetta della tradizione dei fornaciai dell\'Impruneta.', '["Manzo", "Vino rosso Chianti", "Pepe nero in grani", "Aglio", "Sale"]', 8.0, 30, 1, '["walk-in", "delivery"]', 'Tutto l\'anno', 'Cottura 3–4h. Batch giornaliero. Ottimo il giorno dopo.', 1, 0),
  (4, 'TOS-004', 'Lampredotto in umido', 3, 'Quarto stomaco del bovino, cottura lunga in brodo aromatico con pomodoro, sedano e prezzemolo. Servito con pane sciocco toscano tostato. Il quinto quarto fiorentino più autentico.', '["Lampredotto bovino", "Pomodoro", "Sedano", "Carota", "Cipolla", "Prezzemolo", "Pane sciocco toscano"]', 7.5, 22, 1, '["walk-in"]', 'Tutto l\'anno — solo walk-in, servito caldo', 'Cottura lenta in brodo. Servire sempre ben caldo. Non adatto al delivery.', 1, 0),
  (5, 'TOS-005', 'Ragù di chianina al cucchiaio', 2, 'Ragù lento di manzo Chianina IGP servito su crostone di pane toscano abbrustolito. Carne toscana tracciata, cottura di almeno 3 ore.', '["Chianina IGP", "Pomodoro", "Cipolla", "Carota", "Sedano", "Vino rosso", "Pane toscano"]', 7.0, 28, 1, '["walk-in", "delivery"]', 'Tutto l\'anno', 'Batch giornaliero. Il sugo migliora il giorno dopo.', 0, 0),
  (6, 'TOS-006', 'Polpette al sugo della mamma', 4, 'Polpette di macinato misto con pane ammollato nel latte, in sugo di pomodoro lungo. Ricetta casalinga, comfort food autentico.', '["Macinato misto bovino/suino", "Pane raffermo", "Latte", "Uovo", "Pomodoro", "Aglio", "Basilico"]', 7.0, 27, 1, '["walk-in", "delivery", "vending"]', 'Tutto l\'anno', 'Batch giornaliero. Reggono bene il trasporto e il vending.', 0, 0),
  (7, 'TOS-007', 'Ribollita della nonna', 6, 'Zuppa povera toscana con cavolo nero, fagioli cannellini e pane raffermo tostato. La ricetta che non cambia da generazioni.', '["Cavolo nero", "Fagioli cannellini", "Pane raffermo", "Cipolla", "Carota", "Sedano", "Pomodoro", "Olio EVO"]', 6.5, 24, 1, '["walk-in", "delivery"]', 'Tutto l\'anno — preferibile autunno/inverno', 'Batch mattutino. Ribollita = riscaldata due volte, migliora.', 1, 1),
  (8, 'TOS-008', 'Fagioli all'uccelletto con salsiccia', 2, 'Cannellini toscani in salsa di pomodoro con salvia e aglio, accompagnati da salsiccia artigianale. Piatto completo, proteico, della tradizione contadina.', '["Fagioli cannellini", "Salsiccia toscana", "Pomodoro", "Salvia", "Aglio", "Olio EVO"]', 6.5, 25, 1, '["walk-in", "delivery", "vending"]', 'Tutto l\'anno', 'Batch giornaliero. Ottimo anche freddo — adatto al vending.', 0, 0),
  (9, 'TOS-009', 'Zuppa di farro della Garfagnana', 6, 'Farro IGP della Garfagnana con legumi misti e verdure di stagione. Vegano, proteico, dal sapore rustico e autentico.', '["Farro IGP Garfagnana", "Lenticchie", "Fagioli borlotti", "Verdure stagionali", "Olio EVO", "Rosmarino"]', 6.0, 21, 1, '["walk-in", "delivery", "vending"]', 'Tutto l\'anno — rotazione verdure stagionali', 'Batch giornaliero. Ingredienti a lunga conservazione.', 0, 1),
  (10, 'TOS-010', 'Pappa al pomodoro', 6, 'Pomodoro fresco (o pelato in inverno), pane sciocco toscano raffermo, basilico fresco, olio EVO toscano. Semplicità assoluta, sapore autentico.', '["Pomodoro", "Pane sciocco toscano", "Basilico", "Aglio", "Olio EVO"]', 5.5, 19, 1, '["walk-in", "delivery", "vending"]', 'Tutto l\'anno — pomodoro fresco estate, pelato inverno', 'Massimo margine del menu. Batch veloce.', 1, 1),
  (11, 'TOS-011', 'Cecìna livornese', 5, 'Torta di ceci livornese cotta in forno a legna. Croccante fuori, morbida dentro. Il biglietto da visita di Livorno — una \'C\' di appartenenza.', '["Farina di ceci", "Acqua", "Olio EVO", "Sale", "Pepe"]', 3.5, 14, 1, '["walk-in", "vending"]', 'Tutto l\'anno', 'Produzione continua. Servire calda al walk-in. Versione confezionata per vending.', 1, 1),
  (12, 'TOS-012', 'Cantucci con Vin Santo', 1, 'Biscotti di Prato al naturale in monoporzione da viaggio, accompagnati da Vin Santo toscano in miniatura. Perfetti per delivery e vending.', '["Farina", "Zucchero", "Mandorle", "Uova", "Burro", "Vin Santo"]', 3.0, 16, 1, '["walk-in", "delivery", "vending"]', 'Tutto l\'anno', 'Monoporzione confezionata. Stock settimanale.', 0, 0);

-- ----------------------------------------------------------------
-- PIATTI_ALLERGENI (junction table)
-- ----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS piatti_allergeni (
    piatto_id   INT NOT NULL,
    allergene_id INT NOT NULL,
    PRIMARY KEY (piatto_id, allergene_id),
    FOREIGN KEY (piatto_id)    REFERENCES piatti(id),
    FOREIGN KEY (allergene_id) REFERENCES allergeni(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO piatti_allergeni (piatto_id, allergene_id) VALUES
  (1, 7),
  (1, 1),
  (1, 6),
  (1, 3),
  (2, 3),
  (2, 8),
  (3, 8),
  (4, 3),
  (4, 8),
  (5, 3),
  (5, 8),
  (6, 3),
  (6, 4),
  (6, 9),
  (7, 3),
  (7, 8),
  (8, 8),
  (9, 3),
  (9, 8),
  (10, 3),
  (11, 5),
  (12, 3),
  (12, 2),
  (12, 9),
  (12, 4);

-- ----------------------------------------------------------------
-- VIEW: piatti_vending (helper per il distributore automatico)
-- ----------------------------------------------------------------
CREATE OR REPLACE VIEW piatti_vending AS
  SELECT p.id, p.codice, p.nome, p.prezzo, p.food_cost_pct,
         p.margine_lordo, c.codice AS contenitore, c.volume_ml
  FROM piatti p
  JOIN contenitori c ON c.id = p.contenitore_id
  WHERE JSON_CONTAINS(p.canali, '"vending"')
    AND p.attivo = 1;

-- ----------------------------------------------------------------
-- QUERY DI VERIFICA
-- ----------------------------------------------------------------
-- Menu completo ordinato per prezzo:
-- SELECT p.codice, p.nome, cat.nome AS categoria, p.prezzo,
--        p.food_cost_pct, p.margine_lordo, cont.codice AS contenitore
-- FROM piatti p
-- JOIN categorie cat  ON cat.id  = p.categoria_id
-- JOIN contenitori cont ON cont.id = p.contenitore_id
-- ORDER BY p.prezzo DESC;

-- Piatti disponibili al vending:
-- SELECT * FROM piatti_vending ORDER BY prezzo;

-- Fine script Toscanaccio menu v3