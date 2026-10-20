"""
Tests for CSV export and spreadsheet formula injection security.
"""

from app.services.csv_service import CSVExportService


def test_csv_formula_injection_sanitization():
    # Dangerous values starting with formula operators
    assert CSVExportService.sanitize_field("=cmd|' /C calc'!A0") == "'=cmd|' /C calc'!A0"
    assert CSVExportService.sanitize_field("+1+2") == "'+1+2"
    assert CSVExportService.sanitize_field("-5+5") == "'-5+5"
    assert CSVExportService.sanitize_field("@SUM(A1:A10)") == "'@SUM(A1:A10)"
    assert CSVExportService.sanitize_field("\talert()") == "'\talert()"
    # Safe value remains unchanged
    assert CSVExportService.sanitize_field("Standard groceries") == "Standard groceries"
    assert CSVExportService.sanitize_field(None) == ""


def test_export_transactions_csv_endpoint(client):
    # Add a transaction with potential formula injection string
    client.post("/api/transactions", json={
        "amount": 250.00,
        "type": "expense",
        "category": "Shopping & Retail",
        "description": "=SUM(1+1)",
        "date": "2026-04-10",
        "notes": "@HYPERLINK('http://malicious.example.com')"
    })

    resp = client.get("/api/export/csv?from_date=2026-04-01&to_date=2026-04-30")
    assert resp.status_code == 200
    assert "text/csv" in resp.headers["content-type"]
    assert "attachment; filename=" in resp.headers["content-disposition"]

    content = resp.text
    # Verify header line
    assert "ID,Date,Type,Category,Description,Amount,Payment Method,Notes" in content
    # Verify formula injection mitigation: escaped with leading single quote
    assert "'=SUM(1+1)" in content
    assert "'@HYPERLINK" in content
