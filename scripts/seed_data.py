"""
SpendWise - optional demo data seeder.

Run it ONCE after creating the database:

    python scripts/seed_data.py

The script is idempotent: if the demo account already exists it stops without
creating duplicate records. Use --force to build a fresh demo account
(the existing demo transactions of that account are replaced).

Demo login:  demo@spendwise.com  /  Demo@12345

Note: the email validator rejects reserved domains such as ".local", ".test"
or ".invalid", so the demo account uses a normal-looking domain.
"""

import argparse
import os
import random
import sys
from datetime import date, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app import create_app, db  # noqa: E402
from app.constants import EXPENSE, INCOME  # noqa: E402
from app.models import Transaction, User  # noqa: E402
from app.utils import rupees_to_paise  # noqa: E402

DEMO_EMAIL = "demo@spendwise.com"
DEMO_PASSWORD = "Demo@12345"
DEMO_NAME = "Demo Student"

# (type, category, description, min rupees, max rupees, times per month)
DEMO_PATTERN = [
    (INCOME, "Salary", "Monthly salary credited", 25000, 30000, 1),
    (INCOME, "Freelance", "Freelance project payment", 2000, 8000, 1),
    (EXPENSE, "Rent", "Hostel / room rent", 6000, 7000, 1),
    (EXPENSE, "Groceries", "Monthly grocery shopping", 1800, 3200, 2),
    (EXPENSE, "Food", "Canteen and restaurant food", 150, 900, 4),
    (EXPENSE, "Transport", "Bus / auto / metro travel", 60, 600, 3),
    (EXPENSE, "Education", "Books, notes and online course", 300, 1500, 1),
    (EXPENSE, "Utilities", "Mobile recharge and electricity", 250, 900, 1),
    (EXPENSE, "Entertainment", "Movie or streaming subscription", 150, 800, 1),
    (EXPENSE, "Health", "Medicines and doctor visit", 200, 1200, 1),
]


def build_transactions(user, months=4, seed=42):
    """Create a realistic mix of income and expense records."""
    random.seed(seed)
    today = date.today()
    records = []

    for month_index in range(months):
        # Work out the year/month this block belongs to.
        total_months = today.year * 12 + (today.month - 1) - month_index
        year, month = divmod(total_months, 12)
        month += 1
        day_limit = 28 if month == 2 else 30
        if month_index == 0:
            day_limit = max(1, today.day)

        for txn_type, category, description, low, high, times in DEMO_PATTERN:
            for _ in range(times):
                amount = round(random.uniform(low, high), 2)
                txn_date = date(year, month, random.randint(1, day_limit))
                if txn_date > today:
                    txn_date = today
                records.append(
                    Transaction(
                        user_id=user.id,
                        type=txn_type,
                        category=category,
                        description=description,
                        txn_date=txn_date,
                        amount_paise=rupees_to_paise(amount),
                    )
                )

    return records


def seed(force=False):
    app = create_app(os.environ.get("FLASK_CONFIG", "development"))
    with app.app_context():
        db.create_all()

        existing = User.query.filter_by(email=DEMO_EMAIL).first()
        if existing and not force:
            count = Transaction.query.filter_by(user_id=existing.id).count()
            print(
                f"Demo account already exists ({DEMO_EMAIL}) with {count} transactions.\n"
                "Nothing was added, so records were not duplicated.\n"
                "Use 'python scripts/seed_data.py --force' to rebuild the demo data."
            )
            return

        if existing and force:
            print("Removing the previous demo transactions...")
            Transaction.query.filter_by(user_id=existing.id).delete()
            db.session.delete(existing)
            db.session.commit()
            existing = None

        user = User(name=DEMO_NAME, email=DEMO_EMAIL)
        user.set_password(DEMO_PASSWORD)
        db.session.add(user)
        db.session.flush()  # assign user.id

        records = build_transactions(user)
        db.session.add_all(records)
        db.session.commit()

        print("Demo data created successfully.")
        print(f"   Email    : {DEMO_EMAIL}")
        print(f"   Password : {DEMO_PASSWORD}")
        print(f"   Records  : {len(records)} transactions over the last 4 months")
        print("\nStart the app with 'python run.py' and log in to explore the dashboard.")


def main():
    parser = argparse.ArgumentParser(description="Create optional demo data for SpendWise.")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Delete the existing demo data and create it again.",
    )
    args = parser.parse_args()
    seed(force=args.force)


if __name__ == "__main__":
    main()
