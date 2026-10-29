"""Tests for the dashboard, reports, chart data and calculation logic."""

from datetime import date, timedelta

from app.constants import EXPENSE, INCOME
from app.models import Transaction, db
from app.services import category_breakdown, get_summary, monthly_series
from app.utils import format_inr, paise_to_rupees, rupees_to_paise

TODAY = date.today()
MONTH_START = TODAY.replace(day=1)
# A date that is definitely outside the current month.
LAST_MONTH_DATE = MONTH_START - timedelta(days=1)


# ---------------------------------------------------------------------------
# Money helpers (foundation of every calculation)
# ---------------------------------------------------------------------------
def test_rupees_to_paise_avoids_floating_point_errors():
    assert rupees_to_paise(0.1) + rupees_to_paise(0.2) == rupees_to_paise(0.3)
    assert rupees_to_paise("1250.75") == 125075
    assert paise_to_rupees(125075) == 1250.75


def test_indian_rupee_formatting():
    assert format_inr(0) == "\u20b90.00"
    assert format_inr(125075) == "\u20b91,250.75"
    assert format_inr(1234567890) == "\u20b91,23,45,678.90"
    assert format_inr(-50000) == "-\u20b9500.00"


# ---------------------------------------------------------------------------
# Empty dashboard
# ---------------------------------------------------------------------------
def test_empty_dashboard_shows_zero_totals(client, make_user, login):
    make_user(email="emptydash@example.com")
    login("emptydash@example.com")

    response = client.get("/dashboard/")

    assert response.status_code == 200
    assert b"No transactions yet" in response.data
    assert b"\xe2\x82\xb90.00" in response.data          # ₹0.00
    assert b"The chart will appear after you add transactions." in response.data


def test_summary_of_user_without_transactions(app, make_user):
    user = make_user(email="notransactions@example.com")

    summary = get_summary(user.id)

    assert summary["total_income"] == 0
    assert summary["total_expense"] == 0
    assert summary["balance"] == 0
    assert summary["has_data"] is False
    assert summary["transaction_count"] == 0


def test_monthly_series_returns_zeros_for_empty_months(app, make_user):
    user = make_user(email="emptyseries@example.com")

    series = monthly_series(user.id, months=6)

    assert len(series) == 6
    assert all(row["income"] == 0 and row["expense"] == 0 for row in series)


# ---------------------------------------------------------------------------
# Calculations
# ---------------------------------------------------------------------------
def test_summary_totals_and_balance(app, make_user, make_transaction):
    user = make_user(email="calc@example.com")
    make_transaction(user, amount=6000000, txn_type=INCOME, category="Salary", txn_date=MONTH_START)
    make_transaction(user, amount=150000, txn_type=EXPENSE, category="Rent", txn_date=MONTH_START)
    make_transaction(user, amount=50000, txn_type=EXPENSE, category="Food", txn_date=MONTH_START)

    summary = get_summary(user.id)

    assert summary["total_income"] == 6000000
    assert summary["total_expense"] == 200000
    assert summary["balance"] == 5800000
    assert summary["transaction_count"] == 3


def test_month_totals_ignore_other_months(app, make_user, make_transaction):
    user = make_user(email="month@example.com")
    make_transaction(user, amount=100000, txn_type=EXPENSE, category="Food", txn_date=LAST_MONTH_DATE)
    make_transaction(user, amount=200000, txn_type=EXPENSE, category="Food", txn_date=MONTH_START)

    summary = get_summary(user.id)

    # All-time total includes both months...
    assert summary["total_expense"] == 300000
    # ...but the current-month figure includes only this month.
    assert summary["month_expense"] == 200000


def test_summary_does_not_double_count_records(app, make_user, make_transaction):
    user = make_user(email="nodouble@example.com")
    for _ in range(3):
        make_transaction(user, amount=10000, txn_type=EXPENSE, category="Food", txn_date=MONTH_START)

    summary = get_summary(user.id)
    breakdown = category_breakdown(user.id, EXPENSE)

    assert summary["total_expense"] == 30000
    assert summary["transaction_count"] == 3
    assert len(breakdown) == 1
    assert breakdown[0]["amount"] == 30000
    assert breakdown[0]["percentage"] == 100.0


def test_category_breakdown_percentages_and_order(app, make_user, make_transaction):
    user = make_user(email="breakdown@example.com")
    make_transaction(user, amount=75000, txn_type=EXPENSE, category="Rent", txn_date=MONTH_START)
    make_transaction(user, amount=25000, txn_type=EXPENSE, category="Food", txn_date=MONTH_START)
    make_transaction(user, amount=500000, txn_type=INCOME, category="Salary", txn_date=MONTH_START)

    breakdown = category_breakdown(user.id, EXPENSE)

    assert [row["category"] for row in breakdown] == ["Rent", "Food"]
    assert breakdown[0]["percentage"] == 75.0
    assert breakdown[1]["percentage"] == 25.0
    # Income must not appear in the expense breakdown.
    assert all(row["category"] != "Salary" for row in breakdown)


def test_monthly_series_counts_each_transaction_once(app, make_user, make_transaction):
    user = make_user(email="series@example.com")
    make_transaction(user, amount=100000, txn_type=INCOME, category="Salary", txn_date=MONTH_START)
    make_transaction(user, amount=20000, txn_type=EXPENSE, category="Food", txn_date=MONTH_START)
    make_transaction(user, amount=30000, txn_type=EXPENSE, category="Transport", txn_date=MONTH_START)
    make_transaction(user, amount=999900, txn_type=EXPENSE, category="Rent", txn_date=LAST_MONTH_DATE)

    series = monthly_series(user.id, months=6)
    current_month = [row for row in series if row["month"] == MONTH_START.month and row["year"] == MONTH_START.year]

    assert len(current_month) == 1
    assert current_month[0]["income"] == 100000
    assert current_month[0]["expense"] == 50000


def test_dashboard_cards_render_calculated_values(client, make_user, make_transaction, login):
    user = make_user(email="cards@example.com")
    make_transaction(user, amount=5000000, txn_type=INCOME, category="Salary", txn_date=MONTH_START)
    make_transaction(user, amount=125000, txn_type=EXPENSE, category="Rent", txn_date=MONTH_START)
    login("cards@example.com")

    response = client.get("/dashboard/")

    assert response.status_code == 200
    assert b"\xe2\x82\xb948,750.00" in response.data      # ₹48,750.00 balance
    assert b"\xe2\x82\xb91,250.00" in response.data       # ₹1,250.00 expense
    assert b"Rent" in response.data
    assert b"Top expense category" in response.data


def test_dashboard_does_not_show_other_users_data(client, make_user, make_transaction, login):
    mine = make_user(email="dashmine@example.com")
    other = make_user(email="dashother@example.com")
    make_transaction(mine, amount=100000, txn_type=INCOME, category="Salary", txn_date=MONTH_START)
    make_transaction(other, amount=999999, txn_type=EXPENSE, category="Shopping",
                     description="Other user shopping", txn_date=MONTH_START)
    login("dashmine@example.com")

    response = client.get("/dashboard/")

    assert b"Other user shopping" not in response.data
    assert b"\xe2\x82\xb9999,999.00" not in response.data


# ---------------------------------------------------------------------------
# Chart data (JSON API used by Chart.js)
# ---------------------------------------------------------------------------
def test_chart_data_requires_login(client):
    response = client.get("/dashboard/api/chart-data")
    assert response.status_code == 302


def test_chart_data_has_expected_structure(client, make_user, make_transaction, login):
    user = make_user(email="charts@example.com")
    make_transaction(user, amount=400000, txn_type=INCOME, category="Salary", txn_date=MONTH_START)
    make_transaction(user, amount=100000, txn_type=EXPENSE, category="Food", txn_date=MONTH_START)
    login("charts@example.com")

    payload = client.get("/dashboard/api/chart-data").get_json()

    assert set(payload.keys()) == {"monthly", "expense_categories", "income_categories"}
    assert len(payload["monthly"]["labels"]) == 6
    assert payload["monthly"]["income"][-1] == 400000
    assert payload["monthly"]["expense"][-1] == 100000
    assert payload["expense_categories"]["labels"] == ["Food"]
    assert payload["expense_categories"]["values"] == [100000]
    assert payload["income_categories"]["labels"] == ["Salary"]


def test_chart_data_for_empty_user_returns_empty_lists(client, make_user, login):
    make_user(email="emptycharts@example.com")
    login("emptycharts@example.com")

    payload = client.get("/dashboard/api/chart-data").get_json()

    assert payload["expense_categories"]["labels"] == []
    assert payload["expense_categories"]["values"] == []
    assert all(value == 0 for value in payload["monthly"]["income"])


# ---------------------------------------------------------------------------
# Monthly summary view
# ---------------------------------------------------------------------------
def test_monthly_summary_view_current_month(client, make_user, make_transaction, login):
    user = make_user(email="summary@example.com")
    make_transaction(user, amount=300000, txn_type=INCOME, category="Salary", txn_date=MONTH_START)
    make_transaction(user, amount=50000, txn_type=EXPENSE, category="Food", txn_date=MONTH_START)
    login("summary@example.com")

    response = client.get("/dashboard/summary")

    assert response.status_code == 200
    assert b"\xe2\x82\xb93,000.00" in response.data
    assert b"Expense categories" in response.data


def test_monthly_summary_for_month_without_transactions(client, make_user, make_transaction, login):
    user = make_user(email="summaryempty@example.com")
    make_transaction(user, amount=300000, txn_type=INCOME, category="Salary", txn_date=MONTH_START)
    login("summaryempty@example.com")

    old_month = MONTH_START - timedelta(days=200)
    response = client.get(f"/dashboard/summary?year={old_month.year}&month={old_month.month}")

    assert response.status_code == 200
    assert b"No transactions in" in response.data


def test_monthly_summary_rejects_invalid_month_parameters(client, make_user, login):
    make_user(email="badmonth@example.com")
    login("badmonth@example.com")

    response = client.get("/dashboard/summary?year=1800&month=99")

    assert response.status_code == 200   # falls back to the current month

    assert b"Income" in response.data


def test_monthly_summary_only_counts_own_records(app, make_user, make_transaction):
    mine = make_user(email="summarymine@example.com")
    other = make_user(email="summaryother@example.com")
    make_transaction(mine, amount=111100, txn_type=INCOME, category="Salary", txn_date=MONTH_START)
    make_transaction(other, amount=999900, txn_type=INCOME, category="Salary", txn_date=MONTH_START)

    from app.services import get_month_summary

    data = get_month_summary(mine.id, MONTH_START.year, MONTH_START.month)

    assert data["income"] == 111100


def test_dashboard_summary_page_requires_login(client):
    response = client.get("/dashboard/summary")
    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]


def test_transaction_count_helper(app, make_user, make_transaction):
    user = make_user(email="counter@example.com")
    make_transaction(user, txn_type=INCOME, category="Salary")
    make_transaction(user, txn_type=EXPENSE, category="Food")

    assert Transaction.query.filter_by(user_id=user.id).count() == 2
    assert db.session.query(Transaction).count() == 2
