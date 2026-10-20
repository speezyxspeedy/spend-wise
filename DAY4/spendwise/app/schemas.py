"""
Pydantic schemas for SpendWise request and response validation.
Handles currency conversion between decimal values and integer paise.
"""

import datetime as dt
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator


# ==========================================
# TRANSACTION SCHEMAS
# ==========================================

class TransactionBase(BaseModel):
    amount: float = Field(..., gt=0, description="Transaction amount in standard currency (e.g. 150.50)")
    type: str = Field(..., description="Transaction type: 'income' or 'expense'")
    category: str = Field(..., min_length=1, max_length=100, description="Category name")
    description: str = Field(..., min_length=1, max_length=255, description="Brief description")
    date: dt.date = Field(..., description="Date of transaction in YYYY-MM-DD")
    payment_method: Optional[str] = Field(None, max_length=50, description="Payment method used")
    notes: Optional[str] = Field(None, max_length=1000, description="Optional extra notes")

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        v_clean = v.strip().lower()
        if v_clean not in ("income", "expense"):
            raise ValueError("Type must be either 'income' or 'expense'")
        return v_clean

    @field_validator("category", "description")
    @classmethod
    def validate_not_blank(cls, v: str) -> str:
        v_clean = v.strip()
        if not v_clean:
            raise ValueError("Field cannot be empty or blank")
        return v_clean

    @field_validator("amount")
    @classmethod
    def validate_amount_precision(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Amount must be greater than zero")
        return round(v, 2)


class TransactionCreate(TransactionBase):
    pass


class TransactionUpdate(BaseModel):
    amount: Optional[float] = Field(None, gt=0)
    type: Optional[str] = None
    category: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, min_length=1, max_length=255)
    date: Optional[dt.date] = None
    payment_method: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = Field(None, max_length=1000)

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v_clean = v.strip().lower()
            if v_clean not in ("income", "expense"):
                raise ValueError("Type must be either 'income' or 'expense'")
            return v_clean
        return v

    @field_validator("category", "description")
    @classmethod
    def validate_not_blank(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v_clean = v.strip()
            if not v_clean:
                raise ValueError("Field cannot be empty or blank")
            return v_clean
        return v

    @field_validator("amount")
    @classmethod
    def validate_amount_precision(cls, v: Optional[float]) -> Optional[float]:
        if v is not None:
            if v <= 0:
                raise ValueError("Amount must be greater than zero")
            return round(v, 2)
        return v


class TransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    amount: float
    amount_paise: int
    type: str
    category: str
    description: str
    date: dt.date
    payment_method: Optional[str]
    notes: Optional[str]
    created_at: dt.datetime
    updated_at: dt.datetime

    @classmethod
    def from_orm_model(cls, obj) -> "TransactionResponse":
        return cls(
            id=obj.id,
            amount=round(obj.amount_paise / 100.0, 2),
            amount_paise=obj.amount_paise,
            type=obj.type,
            category=obj.category,
            description=obj.description,
            date=obj.date,
            payment_method=obj.payment_method,
            notes=obj.notes,
            created_at=obj.created_at,
            updated_at=obj.updated_at
        )


class PaginatedTransactionsResponse(BaseModel):
    items: List[TransactionResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ==========================================
# BUDGET SCHEMAS
# ==========================================

class BudgetBase(BaseModel):
    month: str = Field(..., pattern=r"^\d{4}-(0[1-9]|1[0-2])$", description="Target month in YYYY-MM")
    is_overall: bool = Field(False, description="Whether this is the overall monthly budget")
    category: Optional[str] = Field(None, max_length=100, description="Target category (required if is_overall=False)")
    amount: float = Field(..., gt=0, description="Budget amount in standard currency")

    @model_validator(mode="after")
    def validate_overall_and_category(self):
        if self.is_overall:
            self.category = None
        else:
            if not self.category or not self.category.strip():
                raise ValueError("Category is required when budget is not overall")
            self.category = self.category.strip()
        self.amount = round(self.amount, 2)
        return self


class BudgetCreate(BudgetBase):
    pass


class BudgetUpdate(BaseModel):
    amount: float = Field(..., gt=0, description="Updated budget amount")

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Amount must be greater than zero")
        return round(v, 2)


class BudgetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    month: str
    is_overall: bool
    category: Optional[str]
    amount: float
    amount_paise: int
    spent_amount: float = 0.0
    spent_paise: int = 0
    remaining_amount: float = 0.0
    usage_percentage: float = 0.0
    warning_level: str = "ok"  # 'ok', 'warning' (>=80%), 'exceeded' (>=100%)
    created_at: dt.datetime
    updated_at: dt.datetime


# ==========================================
# DASHBOARD & ANALYTICS SCHEMAS
# ==========================================

class CategoryBreakdownItem(BaseModel):
    category: str
    amount: float
    percentage: float
    count: int


class MonthlyTrendItem(BaseModel):
    month: str  # YYYY-MM
    income: float
    expense: float
    net: float
    savings_rate: float


class DailySpendingTrendItem(BaseModel):
    date: str  # YYYY-MM-DD
    amount: float


class BudgetWarningItem(BaseModel):
    budget_id: int
    name: str
    is_overall: bool
    budget_amount: float
    spent_amount: float
    usage_percentage: float
    status: str
    message: str


class DashboardSummaryResponse(BaseModel):
    month: str
    total_income: float
    total_expenses: float
    remaining_balance: float
    savings_rate: float
    overall_budget: Optional[float]
    budget_spent: float
    budget_usage_percent: Optional[float]
    budget_warnings: List[BudgetWarningItem]
    recent_transactions: List[TransactionResponse]
    expense_breakdown: List[CategoryBreakdownItem]
    income_breakdown: List[CategoryBreakdownItem]


class AnalyticsSummaryResponse(BaseModel):
    from_date: str
    to_date: str
    total_income: float
    total_expenses: float
    net_savings: float
    savings_rate: float
    expense_breakdown: List[CategoryBreakdownItem]
    income_breakdown: List[CategoryBreakdownItem]
    monthly_trends: List[MonthlyTrendItem]
    daily_spending: List[DailySpendingTrendItem]
    top_spending_categories: List[CategoryBreakdownItem]
    highest_expense_transactions: List[TransactionResponse]


class HealthCheckResponse(BaseModel):
    status: str
    timestamp: dt.datetime
    database: str
    app: str
    version: str
