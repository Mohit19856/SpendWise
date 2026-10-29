"""
Transaction routes: full CRUD + filters.

Ownership rule used by every route in this file:
  * look the record up by id
  * if it does not exist            -> 404 Not Found
  * if it belongs to another user   -> 403 Forbidden (and a warning is logged)
A transaction id taken from the URL is therefore never trusted on its own.
"""

from datetime import date

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required
from sqlalchemy import or_

from ..constants import ALL_CATEGORIES, EXPENSE, INCOME, TRANSACTION_TYPES
from ..forms import TransactionForm
from ..models import Transaction, db

transactions_bp = Blueprint("transactions", __name__, url_prefix="/transactions")


def get_owned_transaction_or_404(txn_id):
    """Return the transaction only if it belongs to the logged-in user."""
    transaction = db.session.get(Transaction, txn_id)
    if transaction is None:
        abort(404)
    if transaction.user_id != current_user.id:
        current_app.logger.warning(
            "User %s tried to access transaction %s owned by user %s",
            current_user.id,
            txn_id,
            transaction.user_id,
        )
        abort(403)
    return transaction


@transactions_bp.route("/")
@login_required
def index():
    """Transaction history with filters, search and pagination."""
    from ..services import parse_date

    txn_type = request.args.get("type", "").strip().lower()
    date_from = parse_date(request.args.get("date_from"))
    date_to = parse_date(request.args.get("date_to"))
    if date_from and date_to and date_from > date_to:
        date_from, date_to = date_to, date_from

    query = Transaction.query.filter_by(user_id=current_user.id)
    if txn_type in TRANSACTION_TYPES:
        query = query.filter(Transaction.type == txn_type)

    category = request.args.get("category", "").strip()
    if category in ALL_CATEGORIES:
        query = query.filter(Transaction.category == category)

    search = request.args.get("q", "").strip()
    if search:
        like = f"%{search}%"
        query = query.filter(
            or_(Transaction.description.ilike(like), Transaction.category.ilike(like))
        )

    if date_from:
        query = query.filter(Transaction.txn_date >= date_from)
    if date_to:
        query = query.filter(Transaction.txn_date <= date_to)

    page = request.args.get("page", 1, type=int)
    pagination = query.order_by(
        Transaction.txn_date.desc(), Transaction.id.desc()
    ).paginate(
        page=max(page, 1),
        per_page=current_app.config.get("TRANSACTIONS_PER_PAGE", 10),
        error_out=False,
    )

    filtered_income = sum(t.amount_paise for t in pagination.items if t.is_income)
    filtered_expense = sum(t.amount_paise for t in pagination.items if t.is_expense)

    filters = {
        "type": txn_type if txn_type in TRANSACTION_TYPES else "",
        "category": category if category in ALL_CATEGORIES else "",
        "q": search,
        "date_from": date_from.isoformat() if date_from else "",
        "date_to": date_to.isoformat() if date_to else "",
    }
    has_filters = any(filters.values())

    return render_template(
        "transactions/list.html",
        transactions=pagination.items,
        pagination=pagination,
        filters=filters,
        has_filters=has_filters,
        page_income=filtered_income,
        page_expense=filtered_expense,
        categories=ALL_CATEGORIES,
        txn_types=TRANSACTION_TYPES,
    )


@transactions_bp.route("/add", methods=["GET", "POST"])
@login_required
def add():
    """Add a new income or expense record for the logged-in user."""
    form = TransactionForm()
    if request.method == "GET":
        form.txn_date.data = date.today()

    if form.validate_on_submit():
        transaction = Transaction(
            user_id=current_user.id,  # taken from the session, never from a form
            type=form.type.data,
            category=form.category.data.strip(),
            description=(form.description.data or "").strip(),
            txn_date=form.txn_date.data,
        )
        transaction.set_amount(form.amount.data)
        db.session.add(transaction)
        db.session.commit()

        flash(
            f"{form.type.data.capitalize()} of \u20b9{transaction.amount} added successfully.",
            "success",
        )
        return redirect(url_for("transactions.index"))

    if form.errors:
        flash("The transaction could not be saved. Please check the fields below.", "danger")

    return render_template("transactions/form.html", form=form, mode="add", transaction=None)


@transactions_bp.route("/<int:txn_id>")
@login_required
def detail(txn_id):
    """View a single transaction."""
    transaction = get_owned_transaction_or_404(txn_id)
    return render_template("transactions/detail.html", transaction=transaction)


@transactions_bp.route("/<int:txn_id>/edit", methods=["GET", "POST"])
@login_required
def edit(txn_id):
    """Edit a transaction that belongs to the logged-in user."""
    transaction = get_owned_transaction_or_404(txn_id)

    form = TransactionForm(obj=transaction)
    if request.method == "GET":
        form.amount.data = transaction.amount
        form.txn_date.data = transaction.txn_date

    if form.validate_on_submit():
        transaction.type = form.type.data
        transaction.category = form.category.data.strip()
        transaction.description = (form.description.data or "").strip()
        transaction.txn_date = form.txn_date.data
        transaction.set_amount(form.amount.data)
        db.session.commit()

        flash("Transaction updated successfully.", "success")
        return redirect(url_for("transactions.detail", txn_id=transaction.id))

    if form.errors:
        flash("The transaction could not be updated. Please check the fields below.", "danger")

    return render_template("transactions/form.html", form=form, mode="edit", transaction=transaction)


@transactions_bp.route("/<int:txn_id>/delete", methods=["POST"])
@login_required
def delete(txn_id):
    """Delete a transaction (POST only, so a link can never delete data)."""
    transaction = get_owned_transaction_or_404(txn_id)
    db.session.delete(transaction)
    db.session.commit()
    flash("Transaction deleted successfully.", "info")
    return redirect(url_for("transactions.index"))
