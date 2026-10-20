"""
SQLAlchemy database models for SpendWise.
Normalized schema for Transactions and Budgets with precision-safe monetary storage.
"""

from datetime import datetime, date
from sqlalchemy import (
    Column,
    Integer,
    String,
    Date,
    DateTime,
    Text,
    CheckConstraint,
    Index,
    func,
    Boolean
)
from app.database import Base


class Transaction(Base):
    """
    Transaction model.
    Monetary amounts are stored in integer subunits (paise / cents) to prevent floating-point inaccuracies.
    Example: ₹150.50 is stored as 15050 paise.
    """
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    amount_paise = Column(Integer, nullable=False)
    type = Column(String(20), nullable=False)  # 'income' or 'expense'
    category = Column(String(100), nullable=False, index=True)
    description = Column(String(255), nullable=False)
    date = Column(Date, nullable=False, index=True)
    payment_method = Column(String(50), nullable=True)
    notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        CheckConstraint("amount_paise > 0", name="check_positive_amount"),
        CheckConstraint("type IN ('income', 'expense')", name="check_valid_type"),
        Index("ix_transactions_date_type", "date", "type"),
        Index("ix_transactions_category_date", "category", "date"),
    )

    @property
    def amount(self) -> float:
        """Helper to get decimal amount."""
        return self.amount_paise / 100.0


class Budget(Base):
    """
    Budget model for monthly spending management.
    Supports:
    1. Overall monthly budget (is_overall=True, category is None)
    2. Category-specific monthly budget (is_overall=False, category specifies target)
    """
    __tablename__ = "budgets"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    month = Column(String(7), nullable=False, index=True)  # Format: 'YYYY-MM'
    is_overall = Column(Boolean, default=False, nullable=False)
    category = Column(String(100), nullable=True, index=True)
    amount_paise = Column(Integer, nullable=False)

    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        CheckConstraint("amount_paise > 0", name="check_positive_budget"),
        Index("ix_budgets_month_category", "month", "category"),
        Index("ix_budgets_month_overall", "month", "is_overall"),
    )

    @property
    def amount(self) -> float:
        """Helper to get decimal amount."""
        return self.amount_paise / 100.0
