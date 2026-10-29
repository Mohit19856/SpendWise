"""
pytest configuration and shared fixtures for the SpendWise test suite.

IMPORTANT
---------
The tests run against a TEMPORARY database file inside the operating system's
temp folder (never the real instance/spendwise.db), so automated testing can
never damage or read real user financial records.
"""

import itertools
import os
import shutil
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# ---------------------------------------------------------------------------
# Point TestingConfig at a throw-away database BEFORE the app is imported,
# because the configuration class reads this environment variable at import time.
# ---------------------------------------------------------------------------
TEMP_DB_DIR = Path(tempfile.mkdtemp(prefix="spendwise-tests-"))
os.environ["TEST_DATABASE_URL"] = f"sqlite:///{(TEMP_DB_DIR / 'spendwise-test.db').as_posix()}"
os.environ.setdefault("SECRET_KEY", "testing-secret-key")

import pytest  # noqa: E402

from app import create_app, db  # noqa: E402
from app.constants import EXPENSE, INCOME  # noqa: E402
from app.models import Transaction, User  # noqa: E402
from app.utils import rupees_to_paise  # noqa: E402

_email_counter = itertools.count(1)


def pytest_sessionfinish(session, exitstatus):
    """Delete the temporary test database folder when the run is finished."""
    shutil.rmtree(TEMP_DB_DIR, ignore_errors=True)


@pytest.fixture()
def app():
    """A fresh application instance with empty, isolated tables for every test."""
    application = create_app("testing")
    application.config.update(
        SERVER_NAME=None,
        WTF_CSRF_ENABLED=False,
    )

    # Confirm we are really talking to the temporary database.
    assert "spendwise-tests-" in application.config["SQLALCHEMY_DATABASE_URI"]

    with application.app_context():
        db.drop_all()
        db.create_all()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    """Flask test client (keeps cookies/session between requests)."""
    return app.test_client()


@pytest.fixture()
def make_user(app):
    """Factory that creates a user with a properly hashed password."""

    def _make_user(name="Test User", email=None, password="Password@123"):
        email = (email or f"user{next(_email_counter)}@example.com").lower()
        user = User(name=name, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return user

    return _make_user


@pytest.fixture()
def make_transaction(app):
    """Factory that creates a transaction for a given user."""

    def _make_transaction(
        user,
        amount=100000,  # in paise
        txn_type=EXPENSE,
        category=None,
        description="Test transaction",
        txn_date=None,
    ):
        from datetime import date

        transaction = Transaction(
            user_id=user.id,
            type=txn_type,
            category=category or ("Salary" if txn_type == INCOME else "Food"),
            description=description,
            txn_date=txn_date or date.today(),
        )
        transaction.amount_paise = int(amount)
        db.session.add(transaction)
        db.session.commit()
        return transaction

    return _make_transaction


@pytest.fixture()
def login(client):
    """Log a user in through the real login form (no session hacking)."""

    def _login(email, password="Password@123", follow_redirects=True):
        return client.post(
            "/auth/login",
            data={"email": email, "password": password},
            follow_redirects=follow_redirects,
        )

    return _login


@pytest.fixture()
def logout(client):
    def _logout():
        return client.post("/auth/logout", follow_redirects=True)

    return _logout


# ---------------------------------------------------------------------------
# Convenience helpers used by several test modules.
# ---------------------------------------------------------------------------
@pytest.fixture()
def rupees():
    """Convert rupees to paise inside tests: rupees(250.75) -> 25075."""
    return rupees_to_paise
