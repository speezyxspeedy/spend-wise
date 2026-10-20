"""
Tests for dashboard summary and KPI calculations.
"""


def test_dashboard_summary_calculations(client):
    month = "2026-07"

    # Add income
    client.post("/api/transactions", json={
        "amount": 40000.00,
        "type": "income",
        "category": "Salary",
        "description": "July Paycheck",
        "date": "2026-07-01"
    })
    client.post("/api/transactions", json={
        "amount": 10000.00,
        "type": "income",
        "category": "Freelance & Consulting",
        "description": "Client Design Project",
        "date": "2026-07-15"
    })

    # Add expenses
    client.post("/api/transactions", json={
        "amount": 15000.00,
        "type": "expense",
        "category": "Housing & Rent",
        "description": "July Apartment Rent",
        "date": "2026-07-02"
    })
    client.post("/api/transactions", json={
        "amount": 5000.00,
        "type": "expense",
        "category": "Groceries & Food",
        "description": "Supermarket haul",
        "date": "2026-07-08"
    })

    # Set overall budget of 30,000
    client.post("/api/budgets", json={
        "month": month,
        "is_overall": True,
        "amount": 30000.00
    })

    # Query dashboard
    resp = client.get(f"/api/dashboard?month={month}")
    assert resp.status_code == 200
    data = resp.json()

    assert data["month"] == month
    assert data["total_income"] == 50000.00
    assert data["total_expenses"] == 20000.00
    assert data["remaining_balance"] == 30000.00
    # Savings rate: (50000 - 20000) / 50000 = 60.0%
    assert data["savings_rate"] == 60.0
    assert data["overall_budget"] == 30000.00
    # Budget usage: 20000 / 30000 = 66.7%
    assert data["budget_usage_percent"] == 66.7
    assert len(data["recent_transactions"]) >= 4

    # Check category breakdown
    assert len(data["expense_breakdown"]) == 2
    rent_item = next(i for i in data["expense_breakdown"] if i["category"] == "Housing & Rent")
    assert rent_item["amount"] == 15000.00
    assert rent_item["percentage"] == 75.0
