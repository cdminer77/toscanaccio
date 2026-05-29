import pytest
from sqlmodel import SQLModel, create_engine, Session
from sqlmodel.pool import StaticPool
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_session
from app.seed import seed_db

# Configurazione del database SQLite in memoria per i test
@pytest.fixture(name="session")
def session_fixture():
    # Usiamo StaticPool per consentire la condivisione dello stesso db in memoria
    # tra diversi thread se necessario, importante per i test SQLite
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        # Applichiamo il seed iniziale per popolare i dati di test
        seed_db(session)
        yield session
    SQLModel.metadata.drop_all(engine)

# Configurazione del client di test FastAPI con dependency override
@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session
    
    # Sovrascrive la dipendenza get_session per usare il DB di test in memoria
    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()
