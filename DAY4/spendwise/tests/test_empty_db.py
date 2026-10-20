"""
Tests verifying graceful behavior on an empty database.
"""


def test_empty_database_dashboard(client):
    resp = client.get("/api/dashboard?month=2026-01")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_income"] == 0.0
    assert data["total_expenses"] == 0.0
    assert data["remaining_balance"] == 0.0
    assert data["savings_rate"] == 0.0
    assert data["overall_budget"] is None
    assert data["budget_spent"] == 0.0
    assert data["budget_usage_percent"] is None
    assert data["budget_warnings"] == []
    assert data["recent_transactions"] == []
    assert data["expense_breakdown"] == []
    assert data["income_breakdown"] == []


def test_empty_database_transactions(client):
    resp = client.get("/api/transactions")
    assert resp.status_code == 200
    data = resp.json()
    assert data["items"] == []
    assert data["total"] == 0
    assert data["page"] == 1
    assert data["total_pages"] == 1


def test_empty_database_budgets(client):
    resp = client.get("/api/budgets?month=2026-01")
    assert resp.status_code == 200
    assert resp.json() == []


def test_empty_database_analytics(client):
    resp = client.get("/api/analytics?from_date=2026-01-01&to_date=2026-01-31")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_income"] == 0.0
    assert data["total_expenses"] == 0.0
    assert data["net_savings"] == 0.0
    assert data["savings_rate"] == 0.0
    assert data["expense_breakdown"] == []
    assert data["income_breakdown"] == []
    assert data["monthly_trends"] == []
    assert data["daily_spending"] == []
    assert data["top_spending_categories"] == []
    assert data["highest_expense_transactions"] == []


def test_empty_database_csv_export(client):
    resp = client.get("/api/export/csv?from_date=2026-01-01&to_date=2026-01-31")
    assert resp.status_code == 200
    assert "ID,Date,Type,Category,Description,Amount,Payment Method,Notes" in resp.text
