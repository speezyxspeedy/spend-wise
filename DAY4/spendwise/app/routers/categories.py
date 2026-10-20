"""
Category and payment method endpoints.
"""

from fastapi import APIRouter
from app.constants import EXPENSE_CATEGORIES, INCOME_CATEGORIES, PAYMENT_METHODS

router = APIRouter(prefix="/api/categories", tags=["Categories"])


@router.get("")
def get_categories():
    """Return available categories and payment methods."""
    return {
        "expense": EXPENSE_CATEGORIES,
        "income": INCOME_CATEGORIES,
        "payment_methods": PAYMENT_METHODS
    }
