"""
Database models (Flask-SQLAlchemy / SQLAlchemy 2.x).

Two tables:
  users        - one row per registered customer
  transactions - income/expense records, every row belongs to exactly one user

Every transaction carries "user_id". All queries in the application filter on
the logged-in user's id, so a user can never read or change another user's data.
"""

from datetime import date, datetime, timezone

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from . import db
from .constants import EXPENSE, INCOME, TRANSACTION_TYPES
from .utils import paise_to_rupees, rupees_to_paise


def utcnow():
    """Timezone-aware UTC timestamp (stored as naive UTC by SQLite)."""
    return datetime.now(timezone.utc)


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    transactions = db.relationship(
        "Transaction",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    # ---------------- password handling ----------------
    def set_password(self, raw_password):
        """Store only a salted hash - the real password is never saved."""
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        """Verify a login attempt against the stored hash."""
        return check_password_hash(self.password_hash, raw_password)

    # ---------------- convenience helpers ----------------
    def display_name(self):
        return self.name.split()[0] if self.name else self.email

    def __repr__(self):  # pragma: no cover - debugging aid
        return f"<User {self.id} {self.email}>"


class Transaction(db.Model):
    __tablename__ = "transactions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    type = db.Column(db.String(10), nullable=False, default=EXPENSE)
    # Amount is stored in paise (integer) to avoid float rounding problems.
    amount_paise = db.Column(db.Integer, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(255), nullable=False, default="")
    txn_date = db.Column(db.Date, nullable=False, default=date.today, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    user = db.relationship("User", back_populates="transactions")

    __table_args__ = (
        db.CheckConstraint("amount_paise > 0", name="ck_transactions_amount_positive"),
        db.CheckConstraint(
            "type IN ('income', 'expense')", name="ck_transactions_type_valid"
        ),
    )

    # ---------------- money helpers ----------------
    @property
    def amount(self):
        """Amount in rupees as a Decimal (read-only convenience)."""
        return paise_to_rupees(self.amount_paise)

    def set_amount(self, rupees):
        self.amount_paise = rupees_to_paise(rupees)

    @property
    def is_income(self):
        return self.type == INCOME

    @property
    def is_expense(self):
        return self.type == EXPENSE

    @property
    def signed_paise(self):
        """+amount for income, -amount for expense (used by balance maths)."""
        return self.amount_paise if self.is_income else -self.amount_paise

    def __repr__(self):  # pragma: no cover - debugging aid
        return f"<Transaction {self.id} user={self.user_id} {self.type} {self.amount_paise}>"


# Guard against a typo in constants.py silently breaking the CHECK constraint.
assert set(TRANSACTION_TYPES) == {"income", "expense"}
