import pytest
import os
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlmodel import Session, select
from app.models import Order, OrderItem, MenuItem, Category, OrderType, AccountingEntry, PaymentDeadline, ArchivedDocument

def test_upload_document(client: TestClient, session: Session):
    # Test file upload
    file_content = b"Mock PDF scanned receipt content"
    filename = "test_receipt.pdf"
    
    response = client.post(
        "/admin/documents/upload",
        params={"category": "UTENZE", "notes": "Fattura luce di test"},
        files={"file": (filename, file_content, "application/pdf")}
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["filename"] == filename
    assert data["category"] == "UTENZE"
    assert "test_receipt.pdf" in data["file_path"]
    
    # Check db record exists
    doc_id = data["id"]
    db_doc = session.get(ArchivedDocument, doc_id)
    assert db_doc is not None
    assert db_doc.filename == filename
    
    # Clean up uploaded file from disk if it was created
    local_path = db_doc.file_path
    if os.path.exists(local_path):
        os.remove(local_path)
        
    # Test deletion
    del_response = client.delete(f"/admin/documents/{doc_id}")
    assert del_response.status_code == 200
    assert session.get(ArchivedDocument, doc_id) is None

def test_order_completion_triggers_accounting(client: TestClient, session: Session):
    # 1. Create a menu item to order
    item = MenuItem(
        code="TEST-001",
        name="Panino test",
        price=10.00,
        category=Category.STREET_FOOD,  # 10% VAT
        available=True
    )
    session.add(item)
    session.commit()
    session.refresh(item)
    
    # 2. Place an order
    order_payload = {
        "order_type": "PICKUP",
        "customer_name": "Test Client",
        "customer_phone": "+39 111 222333",
        "payment_method": "POS",
        "payment_status": "PAID",
        "items": [{"menu_item_id": item.id, "quantity": 2}]
    }
    response = client.post("/orders", json=order_payload)
    assert response.status_code == 201
    order_data = response.json()
    order_id = order_data["id"]
    assert order_data["total"] == 20.00
    
    # Check no accounting entry yet (status is PENDING)
    entries = session.exec(select(AccountingEntry).where(AccountingEntry.description.contains(f"Ordine #{order_id}"))).all()
    assert len(entries) == 0
    
    # 3. Update status to COMPLETED
    patch_response = client.patch(f"/orders/{order_id}?status=COMPLETED")
    assert patch_response.status_code == 200
    
    # Verify accounting entry was generated
    entries = session.exec(select(AccountingEntry).where(AccountingEntry.description.contains(f"Ordine #{order_id}"))).all()
    assert len(entries) == 1
    
    entry = entries[0]
    assert entry.entry_type == "ENTRATA"
    assert entry.category == "VENDITE"
    assert entry.amount_gross == 20.00
    # VAT 10% on food: 20.00 / 1.10 = 18.18 net, 1.82 vat
    assert entry.amount == 18.18
    assert entry.vat_amount == 1.82
    assert entry.vat_rate == 0.10

def test_deadline_payment_triggers_accounting(client: TestClient, session: Session):
    # 1. Create a deadline
    deadline = PaymentDeadline(
        description="Affitto Aprile",
        amount=220.00,
        due_date=datetime.now() + timedelta(days=5),
        status="PENDING",
        category="AFFITTO"  # 0% VAT
    )
    session.add(deadline)
    session.commit()
    session.refresh(deadline)
    
    # 2. Update status to PAID via API
    patch_response = client.patch(
        f"/admin/deadlines/{deadline.id}",
        json={"status": "PAID", "payment_date": datetime.now().isoformat()}
    )
    assert patch_response.status_code == 200
    
    # Check db status
    session.refresh(deadline)
    assert deadline.status == "PAID"
    assert deadline.payment_date is not None
    
    # Verify accounting entry was generated
    entries = session.exec(select(AccountingEntry).where(AccountingEntry.description.contains("Affitto Aprile"))).all()
    assert len(entries) == 1
    entry = entries[0]
    assert entry.entry_type == "USCITA"
    assert entry.category == "AFFITTO"
    assert entry.amount_gross == 220.00
    assert entry.amount == 220.00  # Rent is 0% VAT
    assert entry.vat_amount == 0.00
    assert entry.vat_rate == 0.00
