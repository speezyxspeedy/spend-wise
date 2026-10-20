"""
Dashboard API router.
Aggregates summary metrics, budget usage, category breakdown, and alerts.
"""

from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import DashboardSummaryResponse
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("", response_model=DashboardSummaryResponse)
def get_dashboard(
    month: str = Query(
        default_factory=lambda: datetime.now().strftime("%Y-%m"),
        pattern=r"^\d{4}-(0[1-9]|1[0-2])$",
        description="Month in YYYY-MM format"
    ),
    db: Session = Depends(get_db)
):
    """Get complete dashboard overview for the selected month."""
    return AnalyticsService.get_dashboard_summary(db, month)
