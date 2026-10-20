"""
Transactions API router.
Supports complete CRUD operations, pagination, filtering, and sorting.
"""

from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import (
    TransactionCreate,
    TransactionUpdate,
    TransactionResponse,
    PaginatedTransactionsResponse
)
from app.services.transaction_service import TransactionService

router = APIRouter(prefix="/api/transactions", tags=["Transactions"])


@router.post("", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
def create_transaction(data: TransactionCreate, db: Session = Depends(get_db)):
    """Create a new income or expense transaction."""
    tx = TransactionService.create_transaction(db, data)
    return TransactionResponse.from_orm_model(tx)


@router.get("", response_model=PaginatedTransactionsResponse)
def list_transactions(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    type: Optional[str] = Query(None, description="Filter by 'income' or 'expense'"),
    category: Optional[str] = Query(None, description="Filter by category"),
    from_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    to_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    search: Optional[str] = Query(None, description="Search keyword in description or notes"),
    sort_by: str = Query("date", pattern="^(date|amount|created_at|category)$", description="Sort field"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="Sort order"),
    db: Session = Depends(get_db)
):
    """List transactions with filtering, search, sorting, and pagination."""
    if from_date and to_date and from_date > to_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="from_date cannot be greater than to_date"
        )

    return TransactionService.list_transactions(
        db=db,
        page=page,
        page_size=page_size,
        type_=type,
        category=category,
        from_date=from_date,
        to_date=to_date,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order
    )


@router.get("/{transaction_id}", response_model=TransactionResponse)
def get_transaction(transaction_id: int, db: Session = Depends(get_db)):
    """Retrieve details of a single transaction by ID."""
    tx = TransactionService.get_transaction_by_id(db, transaction_id)
    if not tx:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction with ID {transaction_id} not found."
        )
    return TransactionResponse.from_orm_model(tx)


@router.put("/{transaction_id}", response_model=TransactionResponse)
def update_transaction(transaction_id: int, data: TransactionUpdate, db: Session = Depends(get_db)):
    """Update an existing transaction."""
    tx = TransactionService.get_transaction_by_id(db, transaction_id)
    if not tx:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction with ID {transaction_id} not found."
        )
    updated_tx = TransactionService.update_transaction(db, tx, data)
    return TransactionResponse.from_orm_model(updated_tx)


@router.delete("/{transaction_id}", status_code=status.HTTP_200_OK)
def delete_transaction(transaction_id: int, db: Session = Depends(get_db)):
    """Delete a transaction by ID."""
    tx = TransactionService.get_transaction_by_id(db, transaction_id)
    if not tx:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction with ID {transaction_id} not found."
        )
    TransactionService.delete_transaction(db, tx)
    return {"message": f"Transaction {transaction_id} deleted successfully."}
