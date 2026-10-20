"""
Budgets API router.
Supports creating overall and category-specific monthly budgets, tracking limits, and managing entries.
"""

from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import BudgetCreate, BudgetUpdate, BudgetResponse
from app.services.budget_service import BudgetService

router = APIRouter(prefix="/api/budgets", tags=["Budgets"])


@router.post("", response_model=BudgetResponse, status_code=status.HTTP_201_CREATED)
def create_budget(data: BudgetCreate, db: Session = Depends(get_db)):
    """Create a new overall or category-specific budget for a month."""
    try:
        budget = BudgetService.create_budget(db, data)
        return BudgetService.calculate_budget_stats(db, budget)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("", response_model=List[BudgetResponse])
def list_budgets(
    month: str = Query(
        default_factory=lambda: datetime.now().strftime("%Y-%m"),
        pattern=r"^\d{4}-(0[1-9]|1[0-2])$",
        description="Target month (YYYY-MM)"
    ),
    db: Session = Depends(get_db)
):
    """Retrieve all budgets and real-time spending progress for the given month."""
    return BudgetService.list_budgets_for_month(db, month)


@router.get("/{budget_id}", response_model=BudgetResponse)
def get_budget(budget_id: int, db: Session = Depends(get_db)):
    """Get single budget details."""
    budget = BudgetService.get_budget_by_id(db, budget_id)
    if not budget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Budget with ID {budget_id} not found."
        )
    return BudgetService.calculate_budget_stats(db, budget)


@router.put("/{budget_id}", response_model=BudgetResponse)
def update_budget(budget_id: int, data: BudgetUpdate, db: Session = Depends(get_db)):
    """Update budget amount."""
    budget = BudgetService.get_budget_by_id(db, budget_id)
    if not budget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Budget with ID {budget_id} not found."
        )
    updated_b = BudgetService.update_budget(db, budget, data)
    return BudgetService.calculate_budget_stats(db, updated_b)


@router.delete("/{budget_id}", status_code=status.HTTP_200_OK)
def delete_budget(budget_id: int, db: Session = Depends(get_db)):
    """Delete a budget by ID."""
    budget = BudgetService.get_budget_by_id(db, budget_id)
    if not budget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Budget with ID {budget_id} not found."
        )
    BudgetService.delete_budget(db, budget)
    return {"message": f"Budget {budget_id} deleted successfully."}
