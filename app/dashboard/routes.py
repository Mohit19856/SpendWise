"""
Dashboard + reports routes.

Every number shown on these pages is calculated on the server (app/services.py)
from the logged-in user's own transactions.
"""

from datetime import date

from flask import Blueprint, jsonify, render_template, request
from flask_login import current_user, login_required

from ..constants import CHART_COLORS, EXPENSE, INCOME
from ..models import Transaction
from ..services import (
    MONTH_NAMES,
    available_years,
    category_breakdown,
    get_month_summary,
    get_summary,
    monthly_series,
    recent_transactions,
)

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")


def _chart_payload():
    """Data used by Chart.js on the dashboard (also exposed as JSON)."""
    series = monthly_series(current_user.id, months=6)
    expenses = category_breakdown(current_user.id, EXPENSE)
    income_mix = category_breakdown(current_user.id, INCOME)

    return {
        "monthly": {
            "labels": [row["label"] for row in series],
            "income": [row["income"] for row in series],
            "expense": [row["expense"] for row in series],
        },
        "expense_categories": {
            "labels": [row["category"] for row in expenses],
            "values": [row["amount"] for row in expenses],
            "colors": [row["color"] for row in expenses] or list(CHART_COLORS[:1]),
        },
        "income_categories": {
            "labels": [row["category"] for row in income_mix],
            "values": [row["amount"] for row in income_mix],
        },
    }


@dashboard_bp.route("/")
@login_required
def home():
    """Main dashboard: summary cards, charts and recent transactions."""
    summary = get_summary(current_user.id)
    charts = _chart_payload()
    recent = recent_transactions(current_user.id, limit=5)
    expenses = category_breakdown(current_user.id, EXPENSE)
    top_category = expenses[0] if expenses else None

    return render_template(
        "dashboard/dashboard.html",
        summary=summary,
        charts=charts,
        recent=recent,
        top_category=top_category,
        expense_breakdown=expenses,
        today=date.today(),
    )


@dashboard_bp.route("/summary")
@login_required
def summary():
    """
    Monthly summary view. Without parameters it shows the current month;
    with ?year=&month= it shows any month the user chooses.
    """
    today = date.today()
    year = request.args.get("year", today.year, type=int)
    month = request.args.get("month", today.month, type=int)
    if not 1 <= month <= 12:
        month = today.month
    if not 2000 <= year <= 2100:
        year = today.year

    data = get_month_summary(current_user.id, year, month)
    start, end = data["start"], data["end"]

    # Only this user's transactions, limited to the chosen month.
    transactions = (
        Transaction.query.filter_by(user_id=current_user.id)
        .filter(Transaction.txn_date >= start, Transaction.txn_date <= end)
        .order_by(Transaction.txn_date.asc(), Transaction.id.asc())
        .all()
    )

    breakdown = category_breakdown(current_user.id, EXPENSE, start=start, end=end)
    income_breakdown = category_breakdown(current_user.id, INCOME, start=start, end=end)

    prev_year, prev_month = (year, month - 1) if month > 1 else (year - 1, 12)
    next_year, next_month = (year, month + 1) if month < 12 else (year + 1, 1)

    return render_template(
        "dashboard/summary.html",
        data=data,
        transactions=transactions,
        breakdown=breakdown,
        income_breakdown=income_breakdown,
        years=available_years(current_user.id),
        months=list(enumerate(MONTH_NAMES, start=1)),
        prev={"year": prev_year, "month": prev_month},
        next={"year": next_year, "month": next_month},
        is_current_month=(year == today.year and month == today.month),
    )


@dashboard_bp.route("/api/chart-data")
@login_required
def chart_data():
    """JSON endpoint so the charts can also be loaded/reloaded with JavaScript."""
    return jsonify(_chart_payload())
