"""
Health check endpoint.
"""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database import get_db
from app.schemas import HealthCheckResponse

router = APIRouter(prefix="/api/health", tags=["Health"])


@router.get("", response_model=HealthCheckResponse)
def health_check(db: Session = Depends(get_db)):
    """Check API and database health status."""
    try:
        # Simple probe query
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
        raise HTTPException(status_code=503, detail=f"Database unhealthy: {str(e)}")

    return HealthCheckResponse(
        status="ok",
        timestamp=datetime.now(timezone.utc),
        database=db_status,
        app="SpendWise Personal Expense Tracker",
        version="1.0.0"
    )
