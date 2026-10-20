"""
Budget business logic service.
Calculates spent vs budget, remaining balances, warning thresholds, and avoids duplicates.
"""

import calendar
from datetime import date
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models import Budget, Transaction
from app.schemas import BudgetCreate, BudgetUpdate, BudgetResponse, BudgetWarningItem


class BudgetService:
    @staticmethod
    def _get_month_date_range(month_str: str) -> Tuple[date, date]:
        """Convert 'YYYY-MM' string to (start_date, end_date)"""
        year, month = map(int, month_str.split("-"))
        _, last_day = calendar.monthrange(year, month)
        start_date = date(year, month, 1)
        end_date = date(year, month, last_day)
        return start_date, end_date

    @classmethod
    def calculate_budget_stats(cls, db: Session, budget: Budget) -> BudgetResponse:
        """Calculate real-time spent amount, remaining balance, usage %, and warning level."""
        start_date, end_date = cls._get_month_date_range(budget.month)

        query = db.query(func.coalesce(func.sum(Transaction.amount_paise), 0)).filter(
            Transaction.type == "expense",
            Transaction.date >= start_date,
            Transaction.date <= end_date
        )

        if not budget.is_overall and budget.category:
            query = query.filter(Transaction.category == budget.category)

        spent_paise = query.scalar() or 0
        spent_amount = round(spent_paise / 100.0, 2)
        budget_amount = round(budget.amount_paise / 100.0, 2)
        remaining_amount = round(budget_amount - spent_amount, 2)

        usage_pct = round((spent_paise / budget.amount_paise) * 100.0, 1) if budget.amount_paise > 0 else 0.0

        if usage_pct >= 100.0:
            warning_level = "exceeded"
        elif usage_pct >= 80.0:
            warning_level = "warning"
        else:
            warning_level = "ok"

        return BudgetResponse(
            id=budget.id,
            month=budget.month,
            is_overall=budget.is_overall,
            category=budget.category,
            amount=budget_amount,
            amount_paise=budget.amount_paise,
            spent_amount=spent_amount,
            spent_paise=spent_paise,
            remaining_amount=remaining_amount,
            usage_percentage=usage_pct,
            warning_level=warning_level,
            created_at=budget.created_at,
            updated_at=budget.updated_at
        )

    @classmethod
    def create_budget(cls, db: Session, data: BudgetCreate) -> Budget:
        # Check for duplicates
        query = db.query(Budget).filter(Budget.month == data.month)
        if data.is_overall:
            existing = query.filter(Budget.is_overall.is_(True)).first()
            if existing:
                raise ValueError(f"An overall budget for {data.month} already exists.")
        else:
            existing = query.filter(
                Budget.is_overall.is_(False),
                Budget.category == data.category
            ).first()
            if existing:
                raise ValueError(f"A budget for category '{data.category}' in {data.month} already exists.")

        amount_paise = int(round(data.amount * 100))
        budget = Budget(
            month=data.month,
            is_overall=data.is_overall,
            category=None if data.is_overall else data.category,
            amount_paise=amount_paise
        )
        db.add(budget)
        db.commit()
        db.refresh(budget)
        return budget

    @classmethod
    def get_budget_by_id(cls, db: Session, budget_id: int) -> Optional[Budget]:
        return db.query(Budget).filter(Budget.id == budget_id).first()

    @classmethod
    def update_budget(cls, db: Session, budget: Budget, data: BudgetUpdate) -> Budget:
        budget.amount_paise = int(round(data.amount * 100))
        db.commit()
        db.refresh(budget)
        return budget

    @classmethod
    def delete_budget(cls, db: Session, budget: Budget) -> bool:
        db.delete(budget)
        db.commit()
        return True

    @classmethod
    def list_budgets_for_month(cls, db: Session, month: str) -> List[BudgetResponse]:
        budgets = db.query(Budget).filter(Budget.month == month).order_by(
            Budget.is_overall.desc(),
            Budget.category.asc()
        ).all()

        return [cls.calculate_budget_stats(db, b) for b in budgets]

    @classmethod
    def get_warnings_for_month(cls, db: Session, month: str) -> List[BudgetWarningItem]:
        budget_responses = cls.list_budgets_for_month(db, month)
        warnings = []
        for b in budget_responses:
            if b.warning_level in ("warning", "exceeded"):
                name = "Overall Monthly Budget" if b.is_overall else f"Budget: {b.category}"
                if b.warning_level == "exceeded":
                    msg = f"{name} has exceeded its limit ({b.usage_percentage}% spent: ₹{b.spent_amount:,.2f} of ₹{b.amount:,.2f})."
                else:
                    msg = f"{name} is at {b.usage_percentage}% of its limit (₹{b.spent_amount:,.2f} of ₹{b.amount:,.2f})."
                
                warnings.append(BudgetWarningItem(
                    budget_id=b.id,
                    name=name,
                    is_overall=b.is_overall,
                    budget_amount=b.amount,
                    spent_amount=b.spent_amount,
                    usage_percentage=b.usage_percentage,
                    status=b.warning_level,
                    message=msg
                ))
        return warnings
