"""Tests for the public pages and the complete authentication flow."""

from app.constants import EXPENSE, INCOME
from app.models import User, db


# ---------------------------------------------------------------------------
# Public pages
# ---------------------------------------------------------------------------
def test_homepage_loads(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"SpendWise" in response.data
    assert b"Create Free Account" in response.data


def test_login_page_loads(client):
    response = client.get("/auth/login")
    assert response.status_code == 200
    assert b"Welcome back" in response.data


def test_register_page_loads(client):
    response = client.get("/auth/register")
    assert response.status_code == 200
    assert b"Create your account" in response.data


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------
def test_register_creates_user_and_logs_in(client, app):
    response = client.post(
        "/auth/register",
        data={
            "name": "Asha Verma",
            "email": "asha@example.com",
            "password": "StrongPass123",
            "confirm_password": "StrongPass123",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Your account is ready" in response.data

    user = User.query.filter_by(email="asha@example.com").first()
    assert user is not None
    assert user.name == "Asha Verma"
    # The plain password must never be stored.
    assert user.password_hash != "StrongPass123"
    assert user.check_password("StrongPass123")


def test_register_duplicate_email_is_rejected(client, app, make_user):
    make_user(email="duplicate@example.com")

    response = client.post(
        "/auth/register",
        data={
            "name": "Second Person",
            "email": "duplicate@example.com",
            "password": "StrongPass123",
            "confirm_password": "StrongPass123",
        },
        follow_redirects=True,
    )

    assert b"already registered" in response.data
    assert User.query.filter_by(email="duplicate@example.com").count() == 1


def test_register_rejects_password_mismatch(client, app):
    response = client.post(
        "/auth/register",
        data={
            "name": "Mismatch User",
            "email": "mismatch@example.com",
            "password": "StrongPass123",
            "confirm_password": "DifferentPass123",
        },
        follow_redirects=True,
    )

    assert b"Both passwords must match" in response.data
    assert User.query.filter_by(email="mismatch@example.com").first() is None


def test_register_rejects_short_password(client, app):
    response = client.post(
        "/auth/register",
        data={
            "name": "Short Pass",
            "email": "short@example.com",
            "password": "abc",
            "confirm_password": "abc",
        },
        follow_redirects=True,
    )

    assert b"at least 8 characters" in response.data
    assert User.query.count() == 0


def test_register_rejects_invalid_email(client, app):
    response = client.post(
        "/auth/register",
        data={
            "name": "Bad Email",
            "email": "not-an-email",
            "password": "StrongPass123",
            "confirm_password": "StrongPass123",
        },
        follow_redirects=True,
    )

    assert b"valid email address" in response.data
    assert User.query.count() == 0


def test_register_normalises_email_case(client, app):
    """EMAIL@Example.COM and email@example.com must be the same account."""
    client.post(
        "/auth/register",
        data={
            "name": "Upper Case",
            "email": "UPPER@Example.COM",
            "password": "StrongPass123",
            "confirm_password": "StrongPass123",
        },
    )
    stored = User.query.first()
    assert stored.email == "upper@example.com"

    client.post("/auth/logout")
    response = client.post(
        "/auth/register",
        data={
            "name": "Lower Case",
            "email": "upper@example.com",
            "password": "StrongPass123",
            "confirm_password": "StrongPass123",
        },
        follow_redirects=True,
    )
    assert b"already registered" in response.data
    assert User.query.count() == 1


# ---------------------------------------------------------------------------
# Login / logout
# ---------------------------------------------------------------------------
def test_login_success(client, make_user):
    make_user(email="login@example.com")

    response = client.post(
        "/auth/login",
        data={"email": "login@example.com", "password": "Password@123"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Welcome back" in response.data
    assert b"Dashboard" in response.data


def test_login_with_wrong_password_fails(client, make_user):
    make_user(email="wrong@example.com")

    response = client.post(
        "/auth/login",
        data={"email": "wrong@example.com", "password": "NotMyPassword"},
        follow_redirects=True,
    )

    assert b"Invalid email or password" in response.data
    # Still anonymous: the dashboard must stay protected.
    assert client.get("/dashboard/", follow_redirects=False).status_code == 302


def test_login_with_unknown_email_fails(client, app):
    response = client.post(
        "/auth/login",
        data={"email": "nobody@example.com", "password": "Password@123"},
        follow_redirects=True,
    )

    assert b"Invalid email or password" in response.data


def test_logout_ends_the_session(client, make_user, login, logout):
    make_user(email="logout@example.com")
    login("logout@example.com")

    response = logout()

    assert b"You have been logged out" in response.data
    assert client.get("/dashboard/", follow_redirects=False).status_code == 302


def test_logout_requires_post(client, make_user, login):
    make_user(email="getlogout@example.com")
    login("getlogout@example.com")

    # GET is not allowed for logout, so a link cannot log the user out.
    assert client.get("/auth/logout").status_code == 405


# ---------------------------------------------------------------------------
# Route protection
# ---------------------------------------------------------------------------
def test_dashboard_redirects_anonymous_user(client):
    response = client.get("/dashboard/")
    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]


def test_all_private_pages_require_login(client):
    private_urls = [
        "/dashboard/",
        "/dashboard/summary",
        "/dashboard/api/chart-data",
        "/transactions/",
        "/transactions/add",
        "/auth/profile",
    ]
    for url in private_urls:
        response = client.get(url)
        assert response.status_code == 302, f"{url} should redirect anonymous users"
        assert "/auth/login" in response.headers["Location"], url


def test_login_page_redirects_authenticated_user(client, make_user, login):
    make_user(email="already@example.com")
    login("already@example.com")

    response = client.get("/auth/login")
    assert response.status_code == 302
    assert "/dashboard" in response.headers["Location"]


# ---------------------------------------------------------------------------
# Profile
# ---------------------------------------------------------------------------
def test_profile_shows_only_own_details(client, make_user, login):
    make_user(name="Owner Person", email="owner@example.com")
    make_user(name="Other Person", email="other@example.com")
    login("owner@example.com")

    response = client.get("/auth/profile")

    assert response.status_code == 200
    assert b"Owner Person" in response.data
    assert b"owner@example.com" in response.data
    assert b"other@example.com" not in response.data


def test_profile_update_changes_name(client, make_user, login):
    make_user(name="Old Name", email="rename@example.com")
    login("rename@example.com")

    response = client.post("/auth/profile", data={"name": "New Name"}, follow_redirects=True)

    assert b"profile has been updated" in response.data
    assert User.query.filter_by(email="rename@example.com").first().name == "New Name"


def test_profile_rejects_empty_name(client, make_user, login):
    make_user(name="Keep Me", email="empty@example.com")
    login("empty@example.com")

    response = client.post("/auth/profile", data={"name": ""}, follow_redirects=True)

    assert b"Could not update your profile" in response.data
    assert User.query.filter_by(email="empty@example.com").first().name == "Keep Me"


def test_change_password_success(client, make_user, login):
    make_user(email="changer@example.com")
    login("changer@example.com")

    response = client.post(
        "/auth/profile/password",
        data={
            "current_password": "Password@123",
            "new_password": "BrandNewPass456",
            "confirm_password": "BrandNewPass456",
        },
        follow_redirects=True,
    )

    assert b"password has been changed" in response.data
    assert User.query.filter_by(email="changer@example.com").first().check_password("BrandNewPass456")


def test_change_password_rejects_wrong_current_password(client, make_user, login):
    make_user(email="wrongpass@example.com")
    login("wrongpass@example.com")

    response = client.post(
        "/auth/profile/password",
        data={
            "current_password": "TotallyWrong",
            "new_password": "BrandNewPass456",
            "confirm_password": "BrandNewPass456",
        },
        follow_redirects=True,
    )

    assert b"current password is incorrect" in response.data
    assert User.query.filter_by(email="wrongpass@example.com").first().check_password("Password@123")


def test_profile_page_requires_login(client):
    response = client.get("/auth/profile")
    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]


# ---------------------------------------------------------------------------
# Password storage
# ---------------------------------------------------------------------------
def test_passwords_are_stored_as_hashes(app, make_user):
    user = make_user(email="hash@example.com", password="SuperSecret1")
    stored = db.session.get(User, user.id)

    assert stored.password_hash != "SuperSecret1"
    assert "SuperSecret1" not in stored.password_hash
    assert stored.password_hash.startswith("pbkdf2") or stored.password_hash.startswith("scrypt")
    assert len(stored.password_hash) > 60
    assert stored.check_password("SuperSecret1")
    assert not stored.check_password("SuperSecret2")


def test_income_and_expense_constants_are_used_by_models():
    assert INCOME == "income"
    assert EXPENSE == "expense"
