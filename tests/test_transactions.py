"""Tests for transaction CRUD, validation, filters and ownership protection."""

from datetime import date, timedelta

from app.constants import EXPENSE, INCOME
from app.models import Transaction, db

TODAY = date.today()


def valid_payload(**overrides):
    data = {
        "type": EXPENSE,
        "amount": "250.50",
        "category": "Food",
        "txn_date": TODAY.isoformat(),
        "description": "Lunch at college canteen",
    }
    data.update(overrides)
    return data


# ---------------------------------------------------------------------------
# Creating transactions
# ---------------------------------------------------------------------------
def test_add_page_requires_login(client):
    response = client.get("/transactions/add")
    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]


def test_add_page_loads_for_logged_in_user(client, make_user, login):
    make_user(email="adder@example.com")
    login("adder@example.com")

    response = client.get("/transactions/add")

    assert response.status_code == 200
    assert b"Transaction details" in response.data
    assert b"Expense (money going out)" in response.data


def test_add_expense_saves_correct_amount_in_paise(client, make_user, login):
    user = make_user(email="expense@example.com")
    login("expense@example.com")

    response = client.post("/transactions/add", data=valid_payload(), follow_redirects=True)

    assert b"added successfully" in response.data
    transaction = Transaction.query.filter_by(user_id=user.id).one()
    assert transaction.type == EXPENSE
    assert transaction.amount_paise == 25050          # ₹250.50 -> 25050 paise
    assert str(transaction.amount) == "250.50"
    assert transaction.category == "Food"
    assert transaction.txn_date == TODAY


def test_add_income_uses_income_category(client, make_user, login):
    user = make_user(email="income@example.com")
    login("income@example.com")

    client.post(
        "/transactions/add",
        data=valid_payload(type=INCOME, category="Salary", amount="60000", description="October salary"),
        follow_redirects=True,
    )

    transaction = Transaction.query.filter_by(user_id=user.id).one()
    assert transaction.type == INCOME
    assert transaction.amount_paise == 6000000
    assert transaction.is_income is True


def test_add_sets_owner_from_session_not_form(client, make_user, login):
    """Even if the form sends user_id, the session user must be used."""
    owner = make_user(email="realsession@example.com")
    victim = make_user(email="victim@example.com")
    login("realsession@example.com")

    client.post("/transactions/add", data=valid_payload(user_id=victim.id), follow_redirects=True)

    transaction = Transaction.query.one()
    assert transaction.user_id == owner.id
    assert transaction.user_id != victim.id


def test_transaction_amounts_are_rounded_to_two_decimals(client, make_user, login):
    user = make_user(email="rounding@example.com")
    login("rounding@example.com")

    client.post("/transactions/add", data=valid_payload(amount="99.999"), follow_redirects=True)

    transaction = Transaction.query.filter_by(user_id=user.id).one()
    assert transaction.amount_paise == 10000  # 99.999 rounds to 100.00


# ---------------------------------------------------------------------------
# Server-side validation
# ---------------------------------------------------------------------------
def test_zero_amount_is_rejected(client, make_user, login):
    make_user(email="zero@example.com")
    login("zero@example.com")

    response = client.post("/transactions/add", data=valid_payload(amount="0"), follow_redirects=True)

    assert b"could not be saved" in response.data
    assert Transaction.query.count() == 0


def test_negative_amount_is_rejected(client, make_user, login):
    make_user(email="negative@example.com")
    login("negative@example.com")

    client.post("/transactions/add", data=valid_payload(amount="-500"), follow_redirects=True)

    assert Transaction.query.count() == 0


def test_non_numeric_amount_is_rejected(client, make_user, login):
    make_user(email="text@example.com")
    login("text@example.com")

    client.post("/transactions/add", data=valid_payload(amount="two hundred"), follow_redirects=True)

    assert Transaction.query.count() == 0


def test_invalid_type_is_rejected(client, make_user, login):
    make_user(email="badtype@example.com")
    login("badtype@example.com")

    client.post("/transactions/add", data=valid_payload(type="transfer"), follow_redirects=True)

    assert Transaction.query.count() == 0


def test_invalid_date_is_rejected(client, make_user, login):
    make_user(email="baddate@example.com")
    login("baddate@example.com")

    client.post("/transactions/add", data=valid_payload(txn_date="not-a-date"), follow_redirects=True)

    assert Transaction.query.count() == 0


def test_category_outside_the_allowed_list_is_rejected(client, make_user, login):
    make_user(email="badcat@example.com")
    login("badcat@example.com")

    client.post("/transactions/add", data=valid_payload(category="Bitcoin"), follow_redirects=True)

    assert Transaction.query.count() == 0


def test_income_category_cannot_be_used_for_an_expense(client, make_user, login):
    make_user(email="mixedcat@example.com")
    login("mixedcat@example.com")

    client.post(
        "/transactions/add",
        data=valid_payload(type=EXPENSE, category="Salary"),
        follow_redirects=True,
    )

    assert Transaction.query.count() == 0


def test_too_long_description_is_rejected(client, make_user, login):
    make_user(email="longdesc@example.com")
    login("longdesc@example.com")

    client.post("/transactions/add", data=valid_payload(description="x" * 300), follow_redirects=True)

    assert Transaction.query.count() == 0


def test_empty_description_is_allowed(client, make_user, login):
    user = make_user(email="nodesc@example.com")
    login("nodesc@example.com")

    client.post("/transactions/add", data=valid_payload(description=""), follow_redirects=True)

    transaction = Transaction.query.filter_by(user_id=user.id).one()
    assert transaction.description == ""


# ---------------------------------------------------------------------------
# Viewing, editing and deleting
# ---------------------------------------------------------------------------
def test_detail_page_shows_transaction(client, make_user, make_transaction, login):
    user = make_user(email="detail@example.com")
    transaction = make_transaction(user, amount=75000, description="Textbook purchase")
    login("detail@example.com")

    response = client.get(f"/transactions/{transaction.id}")

    assert response.status_code == 200
    assert b"Textbook purchase" in response.data
    assert b"Ownership check" in response.data


def test_unknown_transaction_returns_404(client, make_user, login):
    make_user(email="missing@example.com")
    login("missing@example.com")

    response = client.get("/transactions/999999")

    assert response.status_code == 404
    assert b"Page not found" in response.data


def test_edit_transaction_updates_values(client, make_user, make_transaction, login):
    user = make_user(email="editor@example.com")
    transaction = make_transaction(user, amount=50000, description="Old description")
    login("editor@example.com")

    response = client.post(
        f"/transactions/{transaction.id}/edit",
        data=valid_payload(type=INCOME, amount="1500.25", category="Freelance", description="New description"),
        follow_redirects=True,
    )

    assert b"updated successfully" in response.data
    db.session.refresh(transaction)
    assert transaction.type == INCOME
    assert transaction.amount_paise == 150025
    assert transaction.category == "Freelance"
    assert transaction.description == "New description"


def test_edit_rejects_invalid_amount(client, make_user, make_transaction, login):
    user = make_user(email="editbad@example.com")
    transaction = make_transaction(user, amount=50000)
    login("editbad@example.com")

    response = client.post(
        f"/transactions/{transaction.id}/edit",
        data=valid_payload(amount="0"),
        follow_redirects=True,
    )

    assert b"could not be updated" in response.data
    db.session.refresh(transaction)
    assert transaction.amount_paise == 50000  # unchanged


def test_delete_transaction(client, make_user, make_transaction, login):
    user = make_user(email="deleter@example.com")
    transaction = make_transaction(user)
    login("deleter@example.com")

    response = client.post(f"/transactions/{transaction.id}/delete", follow_redirects=True)

    assert b"deleted successfully" in response.data
    assert Transaction.query.count() == 0


def test_delete_requires_post_method(client, make_user, make_transaction, login):
    user = make_user(email="deleteget@example.com")
    transaction = make_transaction(user)
    login("deleteget@example.com")

    assert client.get(f"/transactions/{transaction.id}/delete").status_code == 405
    assert Transaction.query.count() == 1


# ---------------------------------------------------------------------------
# Ownership protection between two users
# ---------------------------------------------------------------------------
def test_user_cannot_view_another_users_transaction(client, make_user, make_transaction, login):
    owner = make_user(email="owner2@example.com")
    make_user(email="intruder@example.com")
    transaction = make_transaction(owner, description="Private record")

    login("intruder@example.com")
    response = client.get(f"/transactions/{transaction.id}")

    assert response.status_code == 403
    assert b"Access denied" in response.data
    assert b"Private record" not in response.data


def test_user_cannot_edit_another_users_transaction(client, make_user, make_transaction, login):
    owner = make_user(email="owner3@example.com")
    make_user(email="intruder2@example.com")
    transaction = make_transaction(owner, amount=99900)

    login("intruder2@example.com")
    response = client.post(
        f"/transactions/{transaction.id}/edit", data=valid_payload(amount="1"), follow_redirects=False
    )

    assert response.status_code == 403
    db.session.refresh(transaction)
    assert transaction.amount_paise == 99900


def test_user_cannot_delete_another_users_transaction(client, make_user, make_transaction, login):
    owner = make_user(email="owner4@example.com")
    make_user(email="intruder3@example.com")
    transaction = make_transaction(owner)

    login("intruder3@example.com")
    response = client.post(f"/transactions/{transaction.id}/delete")

    assert response.status_code == 403
    assert Transaction.query.count() == 1


def test_history_shows_only_own_transactions(client, make_user, make_transaction, login):
    mine = make_user(email="mine@example.com")
    theirs = make_user(email="theirs@example.com")
    make_transaction(mine, description="My own record")
    make_transaction(theirs, description="Somebody else record")

    login("mine@example.com")
    response = client.get("/transactions/")

    assert response.status_code == 200
    assert b"My own record" in response.data
    assert b"Somebody else record" not in response.data


# ---------------------------------------------------------------------------
# Filters and search
# ---------------------------------------------------------------------------
def test_filter_by_type(client, make_user, make_transaction, login):
    user = make_user(email="filtertype@example.com")
    make_transaction(user, txn_type=INCOME, category="Salary", description="Monthly salary")
    make_transaction(user, txn_type=EXPENSE, category="Food", description="Dinner")
    login("filtertype@example.com")

    response = client.get("/transactions/?type=income")

    assert b"Monthly salary" in response.data
    assert b"Dinner" not in response.data


def test_filter_by_category(client, make_user, make_transaction, login):
    user = make_user(email="filtercat@example.com")
    make_transaction(user, category="Transport", description="Metro card recharge")
    make_transaction(user, category="Health", description="Pharmacy bill")
    login("filtercat@example.com")

    response = client.get("/transactions/?category=Transport")

    assert b"Metro card recharge" in response.data
    assert b"Pharmacy bill" not in response.data


def test_filter_by_date_range(client, make_user, make_transaction, login):
    user = make_user(email="filterdate@example.com")
    make_transaction(user, description="Old record", txn_date=TODAY - timedelta(days=60))
    make_transaction(user, description="Recent record", txn_date=TODAY - timedelta(days=2))
    login("filterdate@example.com")

    response = client.get(
        f"/transactions/?date_from={(TODAY - timedelta(days=7)).isoformat()}"
        f"&date_to={TODAY.isoformat()}"
    )

    assert b"Recent record" in response.data
    assert b"Old record" not in response.data


def test_swapped_date_range_still_returns_results(client, make_user, make_transaction, login):
    user = make_user(email="swap@example.com")
    make_transaction(user, description="Inside range", txn_date=TODAY)
    login("swap@example.com")

    response = client.get(
        f"/transactions/?date_from={TODAY.isoformat()}"
        f"&date_to={(TODAY - timedelta(days=5)).isoformat()}"
    )

    assert b"Inside range" in response.data


def test_search_by_description(client, make_user, make_transaction, login):
    user = make_user(email="search@example.com")
    make_transaction(user, description="Electricity bill payment")
    make_transaction(user, description="Movie tickets")
    login("search@example.com")

    response = client.get("/transactions/?q=electricity")

    assert b"Electricity bill payment" in response.data
    assert b"Movie tickets" not in response.data


def test_empty_filter_result_shows_empty_state(client, make_user, make_transaction, login):
    user = make_user(email="emptyfilter@example.com")
    make_transaction(user, category="Food", description="Only food")
    login("emptyfilter@example.com")

    response = client.get("/transactions/?q=zzzz-nothing-matches")

    assert response.status_code == 200
    assert b"No transactions match your filters" in response.data


# ---------------------------------------------------------------------------
# Pagination
# ---------------------------------------------------------------------------
def test_history_is_paginated(client, make_user, make_transaction, login):
    user = make_user(email="paging@example.com")
    for index in range(13):
        make_transaction(user, description=f"Paged record {index}", txn_date=TODAY - timedelta(days=index))
    login("paging@example.com")

    first_page = client.get("/transactions/")
    second_page = client.get("/transactions/?page=2")

    assert first_page.status_code == 200
    assert second_page.status_code == 200
    assert b"page 2 of 2" in second_page.data
    assert b"Paged record 0" in first_page.data       # newest first
    assert b"Paged record 0" not in second_page.data
