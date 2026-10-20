"""
Transaction business logic service.
Provides querying, filtering, pagination, and CRUD operations.
"""

from datetime import date
from typing import Optional, Tuple, List
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, asc

from app.models import Transaction
from app.schemas import TransactionCreate, TransactionUpdate, TransactionResponse, PaginatedTransactionsResponse


class TransactionService:
    @staticmethod
    def create_transaction(db: Session, data: TransactionCreate) -> Transaction:
        amount_paise = int(round(data.amount * 100))
        transaction = Transaction(
            amount_paise=amount_paise,
            type=data.type,
            category=data.category,
            description=data.description,
            date=data.date,
            payment_method=data.payment_method,
            notes=data.notes
        )
        db.add(transaction)
        db.commit()
        db.refresh(transaction)
        return transaction

    @staticmethod
    def get_transaction_by_id(db: Session, transaction_id: int) -> Optional[Transaction]:
        return db.query(Transaction).filter(Transaction.id == transaction_id).first()

    @staticmethod
    def update_transaction(db: Session, transaction: Transaction, data: TransactionUpdate) -> Transaction:
        if data.amount is not None:
            transaction.amount_paise = int(round(data.amount * 100))
        if data.type is not None:
            transaction.type = data.type
        if data.category is not None:
            transaction.category = data.category
        if data.description is not None:
            transaction.description = data.description
        if data.date is not None:
            transaction.date = data.date
        if data.payment_method is not None:
            transaction.payment_method = data.payment_method
        if data.notes is not None:
            transaction.notes = data.notes

        db.commit()
        db.refresh(transaction)
        return transaction

    @staticmethod
    def delete_transaction(db: Session, transaction: Transaction) -> bool:
        db.delete(transaction)
        db.commit()
        return True

    @staticmethod
    def list_transactions(
        db: Session,
        page: int = 1,
        page_size: int = 10,
        type_: Optional[str] = None,
        category: Optional[str] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        search: Optional[str] = None,
        sort_by: str = "date",
        sort_order: str = "desc"
    ) -> PaginatedTransactionsResponse:
        query = db.query(Transaction)

        if type_:
            query = query.filter(Transaction.type == type_.lower().strip())
        if category:
            query = query.filter(Transaction.category == category.strip())
        if from_date:
            query = query.filter(Transaction.date >= from_date)
        if to_date:
            query = query.filter(Transaction.date <= to_date)
        if search:
            search_pattern = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    Transaction.description.ilike(search_pattern),
                    Transaction.category.ilike(search_pattern),
                    Transaction.notes.ilike(search_pattern),
                    Transaction.payment_method.ilike(search_pattern)
                )
            )

        # Total count before pagination
        total = query.count()

        # Sorting
        sort_column = Transaction.date
        if sort_by == "amount":
            sort_column = Transaction.amount_paise
        elif sort_by == "created_at":
            sort_column = Transaction.created_at
        elif sort_by == "category":
            sort_column = Transaction.category

        if sort_order.lower() == "asc":
            query = query.order_by(asc(sort_column), asc(Transaction.id))
        else:
            query = query.order_by(desc(sort_column), desc(Transaction.id))

        # Pagination calculation
        page = max(1, page)
        page_size = max(1, min(page_size, 100))  # limit max 100 per page
        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()
        total_pages = (total + page_size - 1) // page_size if total > 0 else 1

        return PaginatedTransactionsResponse(
            items=[TransactionResponse.from_orm_model(item) for item in items],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )

    @staticmethod
    def get_all_for_export(
        db: Session,
        type_: Optional[str] = None,
        category: Optional[str] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        search: Optional[str] = None
    ) -> List[Transaction]:
        query = db.query(Transaction)

        if type_:
            query = query.filter(Transaction.type == type_.lower().strip())
        if category:
            query = query.filter(Transaction.category == category.strip())
        if from_date:
            query = query.filter(Transaction.date >= from_date)
        if to_date:
            query = query.filter(Transaction.date <= to_date)
        if search:
            search_pattern = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    Transaction.description.ilike(search_pattern),
                    Transaction.category.ilike(search_pattern),
                    Transaction.notes.ilike(search_pattern)
                )
            )

        return query.order_by(desc(Transaction.date), desc(Transaction.id)).all()
