"""
Analytics and Reports API router.
Provides deep financial analytics, trend comparisons, and category insights.
"""

from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import AnalyticsSummaryResponse
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.get("", response_model=AnalyticsSummaryResponse)
def get_analytics(
    from_date: date = Query(
        default_factory=lambda: date.today() - timedelta(days=90),
        description="Start date (YYYY-MM-DD)"
    ),
    to_date: date = Query(
        default_factory=date.today,
        description="End date (YYYY-MM-DD)"
    ),
    db: Session = Depends(get_db)
):
    """Retrieve financial analytics, trend graphs, and category statistics."""
    if from_date > to_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="from_date cannot be greater than to_date"
        )

    return AnalyticsService.get_analytics_summary(db, from_date, to_date)
