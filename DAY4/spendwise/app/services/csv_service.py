"""
CSV export service with formula injection mitigation and RFC 4180 compliance.
"""

import csv
import io
from typing import List
from app.models import Transaction


class CSVExportService:
    @staticmethod
    def sanitize_field(value: any) -> str:
        """
        Sanitize field against spreadsheet formula injection (CSV Injection).
        Prepends a single quote if string starts with dangerous characters: =, +, -, @, tab, or carriage return.
        """
        if value is None:
            return ""
        s = str(value)
        if s and s[0] in ("=", "+", "-", "@", "\t", "\r"):
            return f"'{s}"
        return s

    @classmethod
    def generate_transactions_csv(cls, transactions: List[Transaction]) -> str:
        """
        Generate CSV content with proper escaping and formula injection protection.
        """
        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)

        # Header row
        writer.writerow([
            "ID",
            "Date",
            "Type",
            "Category",
            "Description",
            "Amount",
            "Payment Method",
            "Notes"
        ])

        # Data rows
        for t in transactions:
            writer.writerow([
                cls.sanitize_field(t.id),
                cls.sanitize_field(t.date.isoformat()),
                cls.sanitize_field(t.type.capitalize()),
                cls.sanitize_field(t.category),
                cls.sanitize_field(t.description),
                f"{round(t.amount_paise / 100.0, 2):.2f}",
                cls.sanitize_field(t.payment_method or ""),
                cls.sanitize_field(t.notes or "")
            ])

        return output.getvalue()
