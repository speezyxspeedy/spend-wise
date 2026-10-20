"""
Main FastAPI application entry point for SpendWise.
Configures CORS, routers, database initialization, error handling, and static file serving.
"""

from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.encoders import jsonable_encoder

from app.database import init_db
from app.routers import (
    health,
    categories,
    transactions,
    budgets,
    dashboard,
    analytics,
    export
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables on startup
    init_db()
    yield


app = FastAPI(
    title="SpendWise — Personal Expense Tracker & Budget Manager",
    description="Production-quality Personal Expense Tracker and Budget Manager API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration - narrow to local origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5500",  # VS Code Live Server
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Exception handlers for clean, consistent error responses
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for err in exc.errors():
        field = " -> ".join(str(loc) for loc in err["loc"] if loc != "body")
        errors.append(f"{field}: {err['msg']}" if field else err["msg"])
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Validation error: " + "; ".join(errors),
            "errors": jsonable_encoder(exc.errors())
        }
    )


# Include API routers
app.include_router(health.router)
app.include_router(categories.router)
app.include_router(transactions.router)
app.include_router(budgets.router)
app.include_router(dashboard.router)
app.include_router(analytics.router)
app.include_router(export.router)

# Mount static files directory for frontend SPA
STATIC_DIR = Path(__file__).resolve().parent / "static"
if STATIC_DIR.exists():
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
