"""
Tests for transaction CRUD, filtering, pagination, sorting, and validation.
"""


def test_create_income_transaction(client):
    payload = {
        "amount": 50000.00,
        "type": "income",
        "category": "Salary",
        "description": "Monthly Tech Salary",
        "date": "2026-10-01",
        "payment_method": "Bank Transfer",
        "notes": "Direct deposit"
    }
    response = client.post("/api/transactions", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["id"] is not None
    assert data["amount"] == 50000.00
    assert data["amount_paise"] == 5000000
    assert data["type"] == "income"
    assert data["category"] == "Salary"
    assert data["description"] == "Monthly Tech Salary"
    assert data["payment_method"] == "Bank Transfer"


def test_create_expense_transaction(client):
    payload = {
        "amount": 1450.75,
        "type": "expense",
        "category": "Groceries & Food",
        "description": "Supermarket essentials",
        "date": "2026-10-05",
        "payment_method": "UPI"
    }
    response = client.post("/api/transactions", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["amount"] == 1450.75
    assert data["amount_paise"] == 145075
    assert data["type"] == "expense"


def test_transaction_validation_errors(client):
    # Negative amount
    resp = client.post("/api/transactions", json={
        "amount": -50.0,
        "type": "expense",
        "category": "Food",
        "description": "Lunch",
        "date": "2026-10-05"
    })
    assert resp.status_code == 422

    # Zero amount
    resp = client.post("/api/transactions", json={
        "amount": 0,
        "type": "expense",
        "category": "Food",
        "description": "Lunch",
        "date": "2026-10-05"
    })
    assert resp.status_code == 422

    # Invalid type
    resp = client.post("/api/transactions", json={
        "amount": 100,
        "type": "crypto",
        "category": "Food",
        "description": "Lunch",
        "date": "2026-10-05"
    })
    assert resp.status_code == 422

    # Empty category
    resp = client.post("/api/transactions", json={
        "amount": 100,
        "type": "expense",
        "category": "   ",
        "description": "Lunch",
        "date": "2026-10-05"
    })
    assert resp.status_code == 422


def test_transaction_crud_flow(client):
    # 1. Create
    resp = client.post("/api/transactions", json={
        "amount": 350.00,
        "type": "expense",
        "category": "Transportation",
        "description": "Metro card recharge",
        "date": "2026-10-07",
        "payment_method": "UPI"
    })
    assert resp.status_code == 201
    tx_id = resp.json()["id"]

    # 2. Read single
    resp = client.get(f"/api/transactions/{tx_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == tx_id

    # 3. Update
    resp = client.put(f"/api/transactions/{tx_id}", json={
        "amount": 400.00,
        "description": "Metro card recharge & ticket"
    })
    assert resp.status_code == 200
    assert resp.json()["amount"] == 400.00
    assert resp.json()["description"] == "Metro card recharge & ticket"

    # 4. Delete
    resp = client.delete(f"/api/transactions/{tx_id}")
    assert resp.status_code == 200

    # 5. Read again -> 404
    resp = client.get(f"/api/transactions/{tx_id}")
    assert resp.status_code == 404


def test_transaction_filtering_and_pagination(client):
    # Seed multiple items
    client.post("/api/transactions", json={"amount": 1000, "type": "income", "category": "Salary", "description": "Bonus", "date": "2026-10-01"})
    client.post("/api/transactions", json={"amount": 200, "type": "expense", "category": "Food", "description": "Coffee shop", "date": "2026-10-02"})
    client.post("/api/transactions", json={"amount": 800, "type": "expense", "category": "Food", "description": "Groceries bill", "date": "2026-10-03"})
    client.post("/api/transactions", json={"amount": 450, "type": "expense", "category": "Utilities", "description": "Water bill", "date": "2026-10-04"})

    # Filter by type=expense
    resp = client.get("/api/transactions?type=expense")
    assert resp.status_code == 200
    data = resp.json()
    assert all(item["type"] == "expense" for item in data["items"])

    # Filter by category=Food
    resp = client.get("/api/transactions?category=Food")
    assert resp.status_code == 200
    data = resp.json()
    assert all(item["category"] == "Food" for item in data["items"])

    # Search keyword
    resp = client.get("/api/transactions?search=coffee")
    assert resp.status_code == 200
    assert len(resp.json()["items"]) == 1
    assert resp.json()["items"][0]["description"] == "Coffee shop"

    # Pagination
    resp = client.get("/api/transactions?page=1&page_size=2")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) == 2
    assert data["page"] == 1
    assert data["page_size"] == 2
    assert data["total"] >= 4
