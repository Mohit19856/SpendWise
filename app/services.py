"""
Reporting / statistics helpers.

All numbers are calculated on the server from the AUTHENTICATED user's own
records. Every query starts from "filter_by(user_id=user_id)", so results can
never leak between users.

Definitions used everywhere in the app:
  * total_income   -> sum of ALL income transactions of the user (all time)
  * total_expense  -> sum of ALL expense transactions of the user (all time)
  * balance        -> total_income - total_expense
  * month_*        -> same sums, but limited to one calendar month
Amounts are always returned in integer PAISE (see app/utils.py).
"""

from calendar import monthrange
from datetime import date, timedelta

from sqlalchemy import func

from .constants import CHART_COLORS, EXPENSE, INCOME
from .models import Transaction, db

MONTH_NAMES = (
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
)


def month_bounds(year, month):
    """Return (first_day, last_day) of the given month."""
    last_day = monthrange(year, month)[1]
    return date(year, month, 1), date(year, month, last_day)


def add_months(year, month, delta):
    """Shift a (year, month) pair by delta months (delta may be negative)."""
    index = (year * 12 + (month - 1)) + delta
    return index // 12, index % 12 + 1


def _user_totals(user_id, start=None, end=None):
    """Sum income and expense of one user, optionally inside a date range."""
    query = db.session.query(
        Transaction.type, func.coalesce(func.sum(Transaction.amount_paise), 0)
    ).filter(Transaction.user_id == user_id)
    if start is not None:
        query = query.filter(Transaction.txn_date >= start)
    if end is not None:
        query = query.filter(Transaction.txn_date <= end)

    totals = {INCOME: 0, EXPENSE: 0}
    for txn_type, total in query.group_by(Transaction.type).all():
        totals[txn_type] = int(total or 0)
    return totals[INCOME], totals[EXPENSE]


def get_summary(user_id, today=None):
    """All-time and current-month summary for the dashboard cards."""
    today = today or date.today()
    total_income, total_expense = _user_totals(user_id)

    start, end = month_bounds(today.year, today.month)
    month_income, month_expense = _user_totals(user_id, start, end)

    count = db.session.query(func.count(Transaction.id)).filter(
        Transaction.user_id == user_id
    ).scalar() or 0

    return {
        "total_income": total_income,
        "total_expense": total_expense,
        "balance": total_income - total_expense,
        "month_income": month_income,
        "month_expense": month_expense,
        "month_balance": month_income - month_expense,
        "month_label": f"{MONTH_NAMES[today.month - 1]} {today.year}",
        "transaction_count": int(count),
        "has_data": int(count) > 0,
    }


def get_month_summary(user_id, year, month):
    """Summary for one specific month (used by the monthly summary view)."""
    start, end = month_bounds(year, month)
    income, expense = _user_totals(user_id, start, end)
    return {
        "year": year,
        "month": month,
        "month_label": f"{MONTH_NAMES[month - 1]} {year}",
        "start": start,
        "end": end,
        "income": income,
        "expense": expense,
        "balance": income - expense,
    }


def monthly_series(user_id, months=6, today=None):
    """
    Income vs expense for the last N months (oldest month first).
    Months without transactions are returned with zeros, and each transaction is
    counted exactly once because it is grouped by its year-month key.
    """
    today = today or date.today()
    first_year, first_month = add_months(today.year, today.month, -(months - 1))
    start = date(first_year, first_month, 1)
    end = date(today.year, today.month, monthrange(today.year, today.month)[1])

    rows = db.session.query(
        Transaction.txn_date, Transaction.type, Transaction.amount_paise
    ).filter(
        Transaction.user_id == user_id,
        Transaction.txn_date >= start,
        Transaction.txn_date <= end,
    ).all()

    buckets = {}
    for year, month in (
        add_months(first_year, first_month, i) for i in range(months)
    ):
        buckets[(year, month)] = {"income": 0, "expense": 0}

    for txn_date, txn_type, amount_paise in rows:
        key = (txn_date.year, txn_date.month)
        if key in buckets and txn_type in buckets[key]:
            buckets[key][txn_type] += int(amount_paise or 0)

    series = []
    for (year, month), values in buckets.items():
        series.append(
            {
                "year": year,
                "month": month,
                "label": f"{MONTH_NAMES[month - 1][:3]} {str(year)[2:]}",
                "income": values["income"],
                "expense": values["expense"],
            }
        )
    return series


def category_breakdown(user_id, txn_type=EXPENSE, limit=None, start=None, end=None):
    """Grouped totals per category, biggest first, with a chart colour."""
    query = db.session.query(
        Transaction.category, func.coalesce(func.sum(Transaction.amount_paise), 0)
    ).filter(Transaction.user_id == user_id, Transaction.type == txn_type)
    if start is not None:
        query = query.filter(Transaction.txn_date >= start)
    if end is not None:
        query = query.filter(Transaction.txn_date <= end)

    rows = query.group_by(Transaction.category).order_by(
        func.sum(Transaction.amount_paise).desc()
    ).all()

    total = sum(int(amount or 0) for _, amount in rows)
    items = []
    for index, (category, amount) in enumerate(rows):
        amount = int(amount or 0)
        items.append(
            {
                "category": category,
                "amount": amount,
                "percentage": round(amount * 100 / total, 1) if total else 0.0,
                "color": CHART_COLORS[index % len(CHART_COLORS)],
            }
        )
    if limit:
        items = items[:limit]
    return items


def recent_transactions(user_id, limit=5):
    """Most recent transactions first (by date, then by id)."""
    return (
        Transaction.query.filter_by(user_id=user_id)
        .order_by(Transaction.txn_date.desc(), Transaction.id.desc())
        .limit(limit)
        .all()
    )


def available_years(user_id, today=None):
    """Distinct years that contain transactions, newest first."""
    rows = db.session.query(
        func.strftime("%Y", Transaction.txn_date)
    ).filter(Transaction.user_id == user_id).distinct().all()

    years = set()
    for (value,) in rows:
        try:
            years.add(int(value))
        except (TypeError, ValueError):
            continue

    today = today or date.today()
    years.add(today.year)
    return sorted(years, reverse=True)


def parse_date(value):
    """Parse an ISO yyyy-mm-dd string from a filter query parameter."""
    if not value:
        return None
    try:
        return date.fromisoformat(value.strip())
    except (ValueError, AttributeError):
        return None


def default_date_range(today=None):
    """Default filter range: last 30 days (used when filters are empty)."""
    today = today or date.today()
    return today - timedelta(days=30), today
