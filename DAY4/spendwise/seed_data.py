"""
Seed script to populate realistic sample transactions and budgets for SpendWise.
Run with: python seed_data.py
"""

from datetime import date, timedelta
from app.database import SessionLocal, init_db
from app.models import Transaction, Budget

def seed():
    init_db()
    db = SessionLocal()

    # Check if data already exists
    if db.query(Transaction).count() > 0:
        print("Database already contains transaction data. Skipping seed to prevent duplicate entries.")
        db.close()
        return

    print("Seeding initial realistic financial data for SpendWise...")

    today = date.today()
    current_month_str = today.strftime("%Y-%m")
    
    # Calculate previous month
    first_of_this_month = date(today.year, today.month, 1)
    last_month_date = first_of_this_month - timedelta(days=15)
    last_month_str = last_month_date.strftime("%Y-%m")

    # 1. Seed Budgets
    budgets = [
        # Current month overall & category budgets
        Budget(month=current_month_str, is_overall=True, category=None, amount_paise=5500000), # ₹55,000
        Budget(month=current_month_str, is_overall=False, category="Groceries & Food", amount_paise=1200000), # ₹12,000
        Budget(month=current_month_str, is_overall=False, category="Dining Out & Cafes", amount_paise=500000), # ₹5,000
        Budget(month=current_month_str, is_overall=False, category="Transportation", amount_paise=400000), # ₹4,000
        Budget(month=current_month_str, is_overall=False, category="Entertainment & Leisure", amount_paise=350000), # ₹3,500
        Budget(month=current_month_str, is_overall=False, category="Shopping & Retail", amount_paise=600000), # ₹6,000
        
        # Previous month budgets
        Budget(month=last_month_str, is_overall=True, category=None, amount_paise=5000000), # ₹50,000
        Budget(month=last_month_str, is_overall=False, category="Groceries & Food", amount_paise=1000000),
    ]

    for b in budgets:
        db.add(b)

    # 2. Seed Transactions for Current Month
    txs = [
        # Income
        Transaction(
            amount_paise=7500000, # ₹75,000
            type="income",
            category="Salary",
            description="Monthly Technology Salary",
            date=date(today.year, today.month, 1),
            payment_method="Bank Transfer",
            notes="Company Direct Deposit"
        ),
        Transaction(
            amount_paise=1500000, # ₹15,000
            type="income",
            category="Freelance & Consulting",
            description="UI/UX Redesign Consultation",
            date=date(today.year, today.month, min(today.day, 10)),
            payment_method="UPI",
            notes="Client payment via Razorpay / UPI"
        ),
        Transaction(
            amount_paise=280000, # ₹2,800
            type="income",
            category="Investments & Dividends",
            description="Quarterly Mutual Fund Dividend",
            date=date(today.year, today.month, min(today.day, 14)),
            payment_method="Net Banking",
            notes="Equity fund dividend payout"
        ),

        # Expenses
        Transaction(
            amount_paise=1800000, # ₹18,000
            type="expense",
            category="Housing & Rent",
            description="Apartment Rent",
            date=date(today.year, today.month, 2),
            payment_method="Net Banking",
            notes="Paid landlord for month"
        ),
        Transaction(
            amount_paise=325050, # ₹3,250.50
            type="expense",
            category="Groceries & Food",
            description="Weekly Organic Supermarket Groceries",
            date=date(today.year, today.month, 3),
            payment_method="UPI",
            notes="Nature Basket store purchase"
        ),
        Transaction(
            amount_paise=412000, # ₹4,120.00
            type="expense",
            category="Utilities & Bills",
            description="Electricity & High-speed Broadband",
            date=date(today.year, today.month, 4),
            payment_method="Credit Card",
            notes="Utility autopay bill"
        ),
        Transaction(
            amount_paise=185000, # ₹1,850.00
            type="expense",
            category="Dining Out & Cafes",
            description="Artisan Bistro Dinner with Team",
            date=date(today.year, today.month, 6),
            payment_method="Credit Card",
            notes="Celebration dinner"
        ),
        Transaction(
            amount_paise=120000, # ₹1,200.00
            type="expense",
            category="Transportation",
            description="Fuel & Metro Smartcard Recharge",
            date=date(today.year, today.month, 7),
            payment_method="Debit Card"
        ),
        Transaction(
            amount_paise=349900, # ₹3,499.00
            type="expense",
            category="Entertainment & Leisure",
            description="Annual Streaming & Music Subscriptions",
            date=date(today.year, today.month, 8),
            payment_method="Credit Card"
        ),
        Transaction(
            amount_paise=420000, # ₹4,200.00
            type="expense",
            category="Groceries & Food",
            description="Pantry staples and dairy supplies",
            date=date(today.year, today.month, 11),
            payment_method="UPI"
        ),
        Transaction(
            amount_paise=520000, # ₹5,200.00
            type="expense",
            category="Shopping & Retail",
            description="Ergonomic Desk Keyboard & Mouse",
            date=date(today.year, today.month, min(today.day, 15)),
            payment_method="Credit Card",
            notes="Home office upgrade"
        ),
        Transaction(
            amount_paise=165000, # ₹1,650.00
            type="expense",
            category="Healthcare & Medical",
            description="Annual Health Checkup & Vitamins",
            date=date(today.year, today.month, min(today.day, 16)),
            payment_method="Debit Card"
        ),
        Transaction(
            amount_paise=240000, # ₹2,400.00
            type="expense",
            category="Dining Out & Cafes",
            description="Weekend Cafe Brunch",
            date=date(today.year, today.month, min(today.day, 18)),
            payment_method="UPI"
        ),

        # Previous month sample data for historical analytics
        Transaction(
            amount_paise=7500000,
            type="income",
            category="Salary",
            description="Previous Month Salary",
            date=date(last_month_date.year, last_month_date.month, 1),
            payment_method="Bank Transfer"
        ),
        Transaction(
            amount_paise=1800000,
            type="expense",
            category="Housing & Rent",
            description="Previous Month Rent",
            date=date(last_month_date.year, last_month_date.month, 2),
            payment_method="Net Banking"
        ),
        Transaction(
            amount_paise=850000,
            type="expense",
            category="Groceries & Food",
            description="Previous Month Food & Groceries",
            date=date(last_month_date.year, last_month_date.month, 10),
            payment_method="UPI"
        ),
        Transaction(
            amount_paise=450000,
            type="expense",
            category="Transportation",
            description="Commute & Cabs",
            date=date(last_month_date.year, last_month_date.month, 15),
            payment_method="UPI"
        ),
        Transaction(
            amount_paise=600000,
            type="expense",
            category="Shopping & Retail",
            description="Autumn Apparel Shopping",
            date=date(last_month_date.year, last_month_date.month, 20),
            payment_method="Credit Card"
        ),
    ]

    for t in txs:
        db.add(t)

    db.commit()
    db.close()
    print(f"Successfully seeded {len(budgets)} budgets and {len(txs)} transactions!")

if __name__ == "__main__":
    seed()
