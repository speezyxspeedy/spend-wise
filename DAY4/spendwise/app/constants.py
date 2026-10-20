"""
Constants for SpendWise application.
Predefined categories, payment methods, transaction types, and budget rules.
"""

from enum import Enum

class TransactionType(str, Enum):
    INCOME = "income"
    EXPENSE = "expense"

EXPENSE_CATEGORIES = [
    "Housing & Rent",
    "Groceries & Food",
    "Transportation",
    "Utilities & Bills",
    "Healthcare & Medical",
    "Entertainment & Leisure",
    "Shopping & Retail",
    "Dining Out & Cafes",
    "Education & Courses",
    "Personal Care",
    "Travel & Vacation",
    "Investments & Savings",
    "Debt & Loan Repayments",
    "Gifts & Donations",
    "Other Expense"
]

INCOME_CATEGORIES = [
    "Salary",
    "Freelance & Consulting",
    "Business & Sales",
    "Investments & Dividends",
    "Rental Income",
    "Refunds & Reimbursements",
    "Grants & Gifts",
    "Other Income"
]

PAYMENT_METHODS = [
    "Cash",
    "Credit Card",
    "Debit Card",
    "UPI",
    "Net Banking",
    "Bank Transfer",
    "Cheque",
    "Digital Wallet",
    "Other"
]

ALL_CATEGORIES = {
    TransactionType.EXPENSE.value: EXPENSE_CATEGORIES,
    TransactionType.INCOME.value: INCOME_CATEGORIES
}
