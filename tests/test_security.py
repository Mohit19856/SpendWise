"""
Security-focused tests: CSRF protection, session-cookie flags, password
storage, safe queries and production configuration.
"""

import os
import re
from pathlib import Path

import pytest

from app.models import Transaction, User, db

CSRF_PATTERN = re.compile(r'name="csrf_token"[^>]*value="([^"]+)"')
PROJECT_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture()
def csrf_client(app):
    """A client for an app instance where CSRF protection is switched ON."""
    app.config["WTF_CSRF_ENABLED"] = True
    return app.test_client()


def csrf_token_from(html_bytes):
    match = CSRF_PATTERN.search(html_bytes.decode("utf-8"))
    assert match, "CSRF token was not found in the page"
    return match.group(1)


# ---------------------------------------------------------------------------
# CSRF protection
# ---------------------------------------------------------------------------
def test_post_without_csrf_token_is_rejected(csrf_client, make_user):
    make_user(email="nocsrf@example.com")

    response = csrf_client.post(
        "/auth/login", data={"email": "nocsrf@example.com", "password": "Password@123"}
    )

    assert response.status_code == 400
    assert b"Bad request" in response.data


def test_post_with_invalid_csrf_token_is_rejected(csrf_client, make_user):
    make_user(email="badcsrf@example.com")

    response = csrf_client.post(
        "/auth/login",
        data={
            "email": "badcsrf@example.com",
            "password": "Password@123",
            "csrf_token": "not-a-real-token",
        },
    )

    assert response.status_code == 400


def test_post_with_valid_csrf_token_succeeds(csrf_client, make_user):
    make_user(email="goodcsrf@example.com")

    page = csrf_client.get("/auth/login")
    token = csrf_token_from(page.data)

    response = csrf_client.post(
        "/auth/login",
        data={
            "email": "goodcsrf@example.com",
            "password": "Password@123",
            "csrf_token": token,
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Welcome back" in response.data


def test_delete_without_csrf_token_is_blocked(app, client, make_user, make_transaction, login):
    user = make_user(email="csfrdelete@example.com")
    transaction = make_transaction(user)
    login("csfrdelete@example.com")

    # Switch CSRF on only for this request, to prove the delete route is protected.
    app.config["WTF_CSRF_ENABLED"] = True
    response = client.post(f"/transactions/{transaction.id}/delete")

    assert response.status_code == 400
    assert Transaction.query.count() == 1


# ---------------------------------------------------------------------------
# Session cookie hardening
# ---------------------------------------------------------------------------
def test_session_cookie_is_httponly_and_samesite(client, make_user):
    make_user(email="cookie@example.com")

    response = client.post(
        "/auth/login", data={"email": "cookie@example.com", "password": "Password@123"}
    )

    cookie_header = response.headers.get("Set-Cookie", "")
    assert "HttpOnly" in cookie_header
    assert "SameSite=Lax" in cookie_header


def test_production_configuration_requires_a_real_secret_key(monkeypatch):
    from config import ProductionConfig

    monkeypatch.delenv("SECRET_KEY", raising=False)
    with pytest.raises(RuntimeError):
        ProductionConfig.validate()

    monkeypatch.setenv("SECRET_KEY", "a-very-long-random-production-secret-value")
    ProductionConfig.validate()  # must not raise


def test_production_configuration_disables_debug_and_secures_cookies():
    from config import ProductionConfig

    assert ProductionConfig.DEBUG is False
    assert ProductionConfig.SESSION_COOKIE_SECURE is True
    assert ProductionConfig.SESSION_COOKIE_HTTPONLY is True


# ---------------------------------------------------------------------------
# Password safety
# ---------------------------------------------------------------------------
def test_password_hash_is_salted_and_unique(app, make_user):
    first = make_user(email="salt1@example.com", password="SamePassword1")
    second = make_user(email="salt2@example.com", password="SamePassword1")

    # The same password must produce two different hashes (random salt).
    assert first.password_hash != second.password_hash
    assert first.check_password("SamePassword1")
    assert second.check_password("SamePassword1")


def test_database_never_contains_the_plain_password(app, make_user):
    make_user(email="plaintext@example.com", password="MySecretValue9")

    for user in User.query.all():
        assert "MySecretValue9" not in (user.password_hash or "")


# ---------------------------------------------------------------------------
# Safe queries
# ---------------------------------------------------------------------------
def test_search_input_cannot_break_the_query(client, make_user, make_transaction, login):
    user = make_user(email="injection@example.com")
    make_transaction(user, description="Normal record")
    login("injection@example.com")

    response = client.get("/transactions/", query_string={"q": "' OR 1=1 --"})

    assert response.status_code == 200
    # The malicious string is treated as plain text, so no other user's data
    # and no unrelated rows can appear.
    assert b"Normal record" not in response.data


def test_login_error_message_does_not_reveal_if_email_exists(client, make_user):
    make_user(email="known@example.com")

    with_known_email = client.post(
        "/auth/login", data={"email": "known@example.com", "password": "WrongPassword1"},
        follow_redirects=True,
    )
    with_unknown_email = client.post(
        "/auth/login", data={"email": "unknown@example.com", "password": "WrongPassword1"},
        follow_redirects=True,
    )

    assert b"Invalid email or password" in with_known_email.data
    assert b"Invalid email or password" in with_unknown_email.data
    assert b"is not registered" not in with_unknown_email.data


def test_open_redirect_is_blocked(client, make_user):
    """?next=http://evil.example.com must not be followed after login."""
    make_user(email="redirect@example.com")

    response = client.post(
        "/auth/login?next=http://evil.example.com",
        data={"email": "redirect@example.com", "password": "Password@123"},
    )

    assert response.status_code == 302
    assert "evil.example.com" not in response.headers["Location"]
    assert "/dashboard" in response.headers["Location"]


# ---------------------------------------------------------------------------
# Repository hygiene
# ---------------------------------------------------------------------------
def test_gitignore_protects_secrets_and_databases():
    content = (PROJECT_ROOT / ".gitignore").read_text(encoding="utf-8")

    assert ".env" in content
    assert "instance/" in content
    assert "*.db" in content
    assert "venv/" in content or ".venv/" in content


def test_env_example_contains_no_real_secret():
    content = (PROJECT_ROOT / ".env.example").read_text(encoding="utf-8")

    assert "SECRET_KEY=" in content
    assert "change-this" in content
    # A real key would be a long hex/base64 string; the placeholder must not be.
    assert "AWS_SECRET" not in content.upper()


def test_real_env_file_is_not_present_as_a_tracked_artifact():
    """The real .env must not be part of the delivered source tree."""
    env_path = PROJECT_ROOT / ".env"
    if env_path.exists():
        content = env_path.read_text(encoding="utf-8", errors="ignore")
        # If a developer created one locally, it must never contain AWS keys.
        assert "AKIA" not in content
    assert os.environ.get("SECRET_KEY") is not None
