from sqlmodel import SQLModel, create_engine, Session
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///toscanaccio.db")

engine = create_engine(DATABASE_URL, echo=False)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
    if DATABASE_URL.startswith("sqlite"):
        try:
            import sqlite3
            db_path = DATABASE_URL.replace("sqlite:///", "")
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info('user');")
            cols = [col[1] for col in cursor.fetchall()]
            
            if "is_verified" not in cols:
                cursor.execute("ALTER TABLE 'user' ADD COLUMN is_verified BOOLEAN DEFAULT 0;")
                print("Migrazione: Aggiunta colonna is_verified alla tabella user")
            if "verification_token" not in cols:
                cursor.execute("ALTER TABLE 'user' ADD COLUMN verification_token VARCHAR;")
                print("Migrazione: Aggiunta colonna verification_token alla tabella user")
            if "privacy_accepted" not in cols:
                cursor.execute("ALTER TABLE 'user' ADD COLUMN privacy_accepted BOOLEAN DEFAULT 0;")
                print("Migrazione: Aggiunta colonna privacy_accepted alla tabella user")
                
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Errore durante la migrazione automatica SQLite: {e}")

def get_session():
    with Session(engine) as session:
        yield session