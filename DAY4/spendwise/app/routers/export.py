"""
CSV Export API router.
Exports filtered transactions as CSV with spreadsheet formula injection protection.
"""

from datetime import date, datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.transaction_service import TransactionService
from app.services.csv_service import CSVExportService

router = APIRouter(prefix="/api/export", tags=["Export"])


@router.get("/csv")
def export_transactions_csv(
    type: Optional[str] = Query(None, description="Filter by 'income' or 'expense'"),
    category: Optional[str] = Query(None, description="Filter by category"),
    from_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    to_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    search: Optional[str] = Query(None, description="Search query"),
    db: Session = Depends(get_db)
):
    """Export transactions to CSV file with formula injection mitigation."""
    if from_date and to_date and from_date > to_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="from_date cannot be greater than to_date"
        )

    transactions = TransactionService.get_all_for_export(
        db=db,
        type_=type,
        category=category,
        from_date=from_date,
        to_date=to_date,
        search=search
    )

    csv_content = CSVExportService.generate_transactions_csv(transactions)

    # Encode with UTF-8 BOM so Excel on Windows recognizes UTF-8 properly
    encoded_csv = "\ufeff" + csv_content

    filename = f"spendwise_transactions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    return Response(
        content=encoded_csv,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )
