import pytest
from sqlmodel import Session, select
from app.models import User, UserRole
from app.schemas import UserCreate, UserSSOLogin
from app import crud

def test_sso_and_verification_flow(session: Session):
    # Test: Registrazione Standard (is_verified dovrebbe essere False)
    user_data = UserCreate(
        username="test_verify_user",
        email="test_verify@toscanaccio.eu",
        password="testpassword",
        role=UserRole.CUSTOMER,
        privacy_accepted=True
    )
    
    user = crud.create_user(session, user_data)
    assert user.id is not None
    assert user.is_verified is False
    assert user.verification_token is not None
    assert user.privacy_accepted is True
    
    # Verifica che sia presente nel log di notifica la mail di attivazione
    from app.models import NotificationLog
    notif = session.exec(select(NotificationLog).where(NotificationLog.recipient_name == "test_verify_user")).first()
    assert notif is not None
    assert notif.channel == "EMAIL"
    assert "verify?token=" in notif.message_content
    
    # Test: Verifica dell'email
    token = user.verification_token
    verified_user = crud.verify_user_email(session, token)
    assert verified_user is not None
    assert verified_user.is_verified is True
    assert verified_user.verification_token is None
    
    # Test: Login SSO (Google / Apple)
    sso_data = UserSSOLogin(
        email="test_sso@gmail.com",
        username="Test SSO User",
        provider="GOOGLE",
        privacy_accepted=True
    )
    
    sso_user = crud.create_or_get_sso_user(
        session, 
        sso_data.email, 
        sso_data.username, 
        sso_data.provider, 
        sso_data.privacy_accepted
    )
    
    assert sso_user.id is not None
    assert sso_user.is_verified is True
    assert sso_user.privacy_accepted is True
    assert sso_user.email == "test_sso@gmail.com"
