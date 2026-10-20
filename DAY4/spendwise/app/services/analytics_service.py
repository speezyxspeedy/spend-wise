"""
Analytics and Dashboard business logic service.
Performs data aggregations, category breakdowns, spending trends, and KPI calculations.
"""

import calendar
from datetime import date, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.models import Transaction, Budget
from app.schemas import (
    DashboardSummaryResponse,
    AnalyticsSummaryResponse,
    CategoryBreakdownItem,
    MonthlyTrendItem,
    DailySpendingTrendItem,
    TransactionResponse
)
from app.services.budget_service import BudgetService


class AnalyticsService:
    @staticmethod
    def _month_range(month_str: str):
        year, month = map(int, month_str.split("-"))
        _, last_day = calendar.monthrange(year, month)
        return date(year, month, 1), date(year, month, last_day)

    @classmethod
    def get_dashboard_summary(cls, db: Session, month_str: str) -> DashboardSummaryResponse:
        start_date, end_date = cls._month_range(month_str)

        # 1. Total income in month
        income_paise = db.query(func.coalesce(func.sum(Transaction.amount_paise), 0)).filter(
            Transaction.type == "income",
            Transaction.date >= start_date,
            Transaction.date <= end_date
        ).scalar() or 0
        total_income = round(income_paise / 100.0, 2)

        # 2. Total expenses in month
        expense_paise = db.query(func.coalesce(func.sum(Transaction.amount_paise), 0)).filter(
            Transaction.type == "expense",
            Transaction.date >= start_date,
            Transaction.date <= end_date
        ).scalar() or 0
        total_expenses = round(expense_paise / 100.0, 2)

        # 3. Remaining balance & savings rate
        remaining_balance = round(total_income - total_expenses, 2)
        if total_income > 0:
            savings_rate = round(((total_income - total_expenses) / total_income) * 100.0, 1)
        else:
            savings_rate = 0.0

        # 4. Overall monthly budget
        overall_budget_obj = db.query(Budget).filter(
            Budget.month == month_str,
            Budget.is_overall.is_(True)
        ).first()

        overall_budget_val = None
        budget_spent = total_expenses
        budget_usage_pct = None

        if overall_budget_obj:
            overall_budget_val = round(overall_budget_obj.amount_paise / 100.0, 2)
            if overall_budget_obj.amount_paise > 0:
                budget_usage_pct = round((expense_paise / overall_budget_obj.amount_paise) * 100.0, 1)

        # 5. Budget warnings
        budget_warnings = BudgetService.get_warnings_for_month(db, month_str)

        # 6. Recent transactions (latest 6 in this month or general recent)
        recent_txs = db.query(Transaction).filter(
            Transaction.date >= start_date,
            Transaction.date <= end_date
        ).order_by(desc(Transaction.date), desc(Transaction.id)).limit(6).all()

        # If no transactions in this month, show up to 6 overall latest
        if not recent_txs:
            recent_txs = db.query(Transaction).order_by(desc(Transaction.date), desc(Transaction.id)).limit(6).all()

        recent_tx_responses = [TransactionResponse.from_orm_model(t) for t in recent_txs]

        # 7. Category breakdown for expenses
        expense_category_rows = db.query(
            Transaction.category,
            func.sum(Transaction.amount_paise).label("cat_paise"),
            func.count(Transaction.id).label("cat_count")
        ).filter(
            Transaction.type == "expense",
            Transaction.date >= start_date,
            Transaction.date <= end_date
        ).group_by(Transaction.category).order_by(desc("cat_paise")).all()

        expense_breakdown = []
        for cat, cat_paise, cat_count in expense_category_rows:
            cat_amt = round(cat_paise / 100.0, 2)
            cat_pct = round((cat_paise / expense_paise) * 100.0, 1) if expense_paise > 0 else 0.0
            expense_breakdown.append(CategoryBreakdownItem(
                category=cat,
                amount=cat_amt,
                percentage=cat_pct,
                count=cat_count
            ))

        # 8. Category breakdown for income
        income_category_rows = db.query(
            Transaction.category,
            func.sum(Transaction.amount_paise).label("cat_paise"),
            func.count(Transaction.id).label("cat_count")
        ).filter(
            Transaction.type == "income",
            Transaction.date >= start_date,
            Transaction.date <= end_date
        ).group_by(Transaction.category).order_by(desc("cat_paise")).all()

        income_breakdown = []
        for cat, cat_paise, cat_count in income_category_rows:
            cat_amt = round(cat_paise / 100.0, 2)
            cat_pct = round((cat_paise / income_paise) * 100.0, 1) if income_paise > 0 else 0.0
            income_breakdown.append(CategoryBreakdownItem(
                category=cat,
                amount=cat_amt,
                percentage=cat_pct,
                count=cat_count
            ))

        return DashboardSummaryResponse(
            month=month_str,
            total_income=total_income,
            total_expenses=total_expenses,
            remaining_balance=remaining_balance,
            savings_rate=savings_rate,
            overall_budget=overall_budget_val,
            budget_spent=budget_spent,
            budget_usage_percent=budget_usage_pct,
            budget_warnings=budget_warnings,
            recent_transactions=recent_tx_responses,
            expense_breakdown=expense_breakdown,
            income_breakdown=income_breakdown
        )

    @classmethod
    def get_analytics_summary(cls, db: Session, from_date: date, to_date: date) -> AnalyticsSummaryResponse:
        # Totals in window
        income_paise = db.query(func.coalesce(func.sum(Transaction.amount_paise), 0)).filter(
            Transaction.type == "income",
            Transaction.date >= from_date,
            Transaction.date <= to_date
        ).scalar() or 0
        total_income = round(income_paise / 100.0, 2)

        expense_paise = db.query(func.coalesce(func.sum(Transaction.amount_paise), 0)).filter(
            Transaction.type == "expense",
            Transaction.date >= from_date,
            Transaction.date <= to_date
        ).scalar() or 0
        total_expenses = round(expense_paise / 100.0, 2)

        net_savings = round(total_income - total_expenses, 2)
        savings_rate = round(((total_income - total_expenses) / total_income) * 100.0, 1) if total_income > 0 else 0.0

        # Expense breakdown
        expense_rows = db.query(
            Transaction.category,
            func.sum(Transaction.amount_paise).label("cat_paise"),
            func.count(Transaction.id).label("cat_count")
        ).filter(
            Transaction.type == "expense",
            Transaction.date >= from_date,
            Transaction.date <= to_date
        ).group_by(Transaction.category).order_by(desc("cat_paise")).all()

        expense_breakdown = [
            CategoryBreakdownItem(
                category=cat,
                amount=round(cat_p / 100.0, 2),
                percentage=round((cat_p / expense_paise) * 100.0, 1) if expense_paise > 0 else 0.0,
                count=cat_c
            ) for cat, cat_p, cat_c in expense_rows
        ]

        # Income breakdown
        income_rows = db.query(
            Transaction.category,
            func.sum(Transaction.amount_paise).label("cat_paise"),
            func.count(Transaction.id).label("cat_count")
        ).filter(
            Transaction.type == "income",
            Transaction.date >= from_date,
            Transaction.date <= to_date
        ).group_by(Transaction.category).order_by(desc("cat_paise")).all()

        income_breakdown = [
            CategoryBreakdownItem(
                category=cat,
                amount=round(cat_p / 100.0, 2),
                percentage=round((cat_p / income_paise) * 100.0, 1) if income_paise > 0 else 0.0,
                count=cat_c
            ) for cat, cat_p, cat_c in income_rows
        ]

        # Top 5 spending categories
        top_spending_categories = expense_breakdown[:5]

        # Highest expense transactions (top 5)
        highest_expenses = db.query(Transaction).filter(
            Transaction.type == "expense",
            Transaction.date >= from_date,
            Transaction.date <= to_date
        ).order_by(desc(Transaction.amount_paise), desc(Transaction.date)).limit(5).all()

        highest_expense_responses = [TransactionResponse.from_orm_model(t) for t in highest_expenses]

        # Monthly trends (Income vs Expense grouped by YYYY-MM)
        # Using SQLite strftime('%Y-%m', date)
        monthly_rows = db.query(
            func.strftime("%Y-%m", Transaction.date).label("m_str"),
            Transaction.type,
            func.sum(Transaction.amount_paise).label("m_paise")
        ).filter(
            Transaction.date >= from_date,
            Transaction.date <= to_date
        ).group_by("m_str", Transaction.type).order_by("m_str").all()

        monthly_dict: Dict[str, Dict[str, float]] = {}
        for m_str, t_type, m_paise in monthly_rows:
            if m_str not in monthly_dict:
                monthly_dict[m_str] = {"income": 0.0, "expense": 0.0}
            monthly_dict[m_str][t_type] = round(m_paise / 100.0, 2)

        monthly_trends = []
        for m_str in sorted(monthly_dict.keys()):
            inc = monthly_dict[m_str]["income"]
            exp = monthly_dict[m_str]["expense"]
            net = round(inc - exp, 2)
            sr = round(((inc - exp) / inc) * 100.0, 1) if inc > 0 else 0.0
            monthly_trends.append(MonthlyTrendItem(
                month=m_str,
                income=inc,
                expense=exp,
                net=net,
                savings_rate=sr
            ))

        # Daily spending trends (expenses per day in date range)
        daily_rows = db.query(
            Transaction.date,
            func.sum(Transaction.amount_paise).label("d_paise")
        ).filter(
            Transaction.type == "expense",
            Transaction.date >= from_date,
            Transaction.date <= to_date
        ).group_by(Transaction.date).order_by(Transaction.date).all()

        daily_spending = [
            DailySpendingTrendItem(
                date=d.isoformat(),
                amount=round(d_paise / 100.0, 2)
            ) for d, d_paise in daily_rows
        ]

        return AnalyticsSummaryResponse(
            from_date=from_date.isoformat(),
            to_date=to_date.isoformat(),
            total_income=total_income,
            total_expenses=total_expenses,
            net_savings=net_savings,
            savings_rate=savings_rate,
            expense_breakdown=expense_breakdown,
            income_breakdown=income_breakdown,
            monthly_trends=monthly_trends,
            daily_spending=daily_spending,
            top_spending_categories=top_spending_categories,
            highest_expense_transactions=highest_expense_responses
        )
