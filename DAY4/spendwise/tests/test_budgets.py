"""
Tests for budget management, duplicate prevention, and 80%/100% threshold warnings.
"""


def test_create_overall_and_category_budgets(client):
    month = "2026-11"

    # Create overall budget
    resp = client.post("/api/budgets", json={
        "month": month,
        "is_overall": True,
        "amount": 25000.00
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["is_overall"] is True
    assert data["category"] is None
    assert data["amount"] == 25000.00

    # Create category budget
    resp = client.post("/api/budgets", json={
        "month": month,
        "is_overall": False,
        "category": "Groceries & Food",
        "amount": 6000.00
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["is_overall"] is False
    assert data["category"] == "Groceries & Food"
    assert data["amount"] == 6000.00


def test_prevent_duplicate_budgets(client):
    month = "2026-12"

    # 1. Overall duplicate
    client.post("/api/budgets", json={"month": month, "is_overall": True, "amount": 30000.00})
    dup_resp = client.post("/api/budgets", json={"month": month, "is_overall": True, "amount": 35000.00})
    assert dup_resp.status_code == 400
    assert "already exists" in dup_resp.json()["detail"]

    # 2. Category duplicate
    client.post("/api/budgets", json={"month": month, "is_overall": False, "category": "Rent", "amount": 12000.00})
    dup_cat_resp = client.post("/api/budgets", json={"month": month, "is_overall": False, "category": "Rent", "amount": 14000.00})
    assert dup_cat_resp.status_code == 400
    assert "already exists" in dup_cat_resp.json()["detail"]


def test_budget_warning_thresholds(client):
    month = "2026-09"

    # Set up category budget for 1000
    client.post("/api/budgets", json={
        "month": month,
        "is_overall": False,
        "category": "Entertainment",
        "amount": 1000.00
    })

    # 1. Spend 500 (50% -> ok)
    client.post("/api/transactions", json={
        "amount": 500.00,
        "type": "expense",
        "category": "Entertainment",
        "description": "Cinema",
        "date": "2026-09-05"
    })
    budgets = client.get(f"/api/budgets?month={month}").json()
    ent_b = next(b for b in budgets if b["category"] == "Entertainment")
    assert ent_b["spent_amount"] == 500.00
    assert ent_b["remaining_amount"] == 500.00
    assert ent_b["usage_percentage"] == 50.0
    assert ent_b["warning_level"] == "ok"

    # 2. Spend another 350 (Total 850 / 1000 = 85% -> warning)
    client.post("/api/transactions", json={
        "amount": 350.00,
        "type": "expense",
        "category": "Entertainment",
        "description": "Concert",
        "date": "2026-09-10"
    })
    budgets = client.get(f"/api/budgets?month={month}").json()
    ent_b = next(b for b in budgets if b["category"] == "Entertainment")
    assert ent_b["spent_amount"] == 850.00
    assert ent_b["remaining_amount"] == 150.00
    assert ent_b["usage_percentage"] == 85.0
    assert ent_b["warning_level"] == "warning"

    # 3. Spend another 200 (Total 1050 / 1000 = 105% -> exceeded)
    client.post("/api/transactions", json={
        "amount": 200.00,
        "type": "expense",
        "category": "Entertainment",
        "description": "Gaming subscription",
        "date": "2026-09-15"
    })
    budgets = client.get(f"/api/budgets?month={month}").json()
    ent_b = next(b for b in budgets if b["category"] == "Entertainment")
    assert ent_b["spent_amount"] == 1050.00
    assert ent_b["remaining_amount"] == -50.00
    assert ent_b["usage_percentage"] == 105.0
    assert ent_b["warning_level"] == "exceeded"


def test_budget_update_and_delete(client):
    resp = client.post("/api/budgets", json={
        "month": "2026-08",
        "is_overall": True,
        "amount": 20000.00
    })
    b_id = resp.json()["id"]

    # Update amount
    up_resp = client.put(f"/api/budgets/{b_id}", json={"amount": 28000.00})
    assert up_resp.status_code == 200
    assert up_resp.json()["amount"] == 28000.00

    # Delete
    del_resp = client.delete(f"/api/budgets/{b_id}")
    assert del_resp.status_code == 200

    # Get non-existent
    assert client.get(f"/api/budgets/{b_id}").status_code == 404
