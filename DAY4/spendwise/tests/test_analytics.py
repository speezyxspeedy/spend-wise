"""
Tests for analytics and reports endpoint.
"""


def test_analytics_summary(client):
    # Add transactions across two months
    client.post("/api/transactions", json={
        "amount": 25000.00,
        "type": "income",
        "category": "Salary",
        "description": "Salary 1",
        "date": "2026-05-01"
    })
    client.post("/api/transactions", json={
        "amount": 5000.00,
        "type": "expense",
        "category": "Shopping & Retail",
        "description": "Electronics purchase",
        "date": "2026-05-10"
    })
    client.post("/api/transactions", json={
        "amount": 1200.00,
        "type": "expense",
        "category": "Groceries & Food",
        "description": "Weekly food",
        "date": "2026-05-15"
    })

    resp = client.get("/api/analytics?from_date=2026-05-01&to_date=2026-05-31")
    assert resp.status_code == 200
    data = resp.json()

    assert data["total_income"] == 25000.00
    assert data["total_expenses"] == 6200.00
    assert data["net_savings"] == 18800.00
    assert len(data["expense_breakdown"]) == 2
    assert len(data["top_spending_categories"]) == 2
    assert data["top_spending_categories"][0]["category"] == "Shopping & Retail"
    assert len(data["highest_expense_transactions"]) == 2
    assert data["highest_expense_transactions"][0]["amount"] == 5000.00


def test_analytics_invalid_date_range(client):
    resp = client.get("/api/analytics?from_date=2026-06-30&to_date=2026-06-01")
    assert resp.status_code == 400
    assert "cannot be greater than" in resp.json()["detail"]
