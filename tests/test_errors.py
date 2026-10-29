"""Tests for the friendly error pages and the error handling logic."""

from app.models import db


def test_unknown_url_shows_custom_404_page(client):
    response = client.get("/this-page-does-not-exist")

    assert response.status_code == 404
    assert b"404" in response.data
    assert b"Page not found" in response.data
    assert b"Go to homepage" in response.data


def test_404_page_does_not_leak_a_stack_trace(client):
    response = client.get("/another/missing/page")

    assert response.status_code == 404
    assert b"Traceback" not in response.data
    assert b"werkzeug" not in response.data.lower()


def test_forbidden_page_is_shown_for_another_users_record(
    client, make_user, make_transaction, login
):
    owner = make_user(email="err-owner@example.com")
    make_user(email="err-intruder@example.com")
    transaction = make_transaction(owner)

    login("err-intruder@example.com")
    response = client.get(f"/transactions/{transaction.id}")

    assert response.status_code == 403
    assert b"403" in response.data
    assert b"Access denied" in response.data
    assert b"My transactions" in response.data


def test_bad_request_page_exists(app, client):
    """The 400 page is used when a CSRF token is missing or expired."""
    app.config["WTF_CSRF_ENABLED"] = True

    response = client.post("/auth/login", data={"email": "x@example.com", "password": "y"})

    assert response.status_code == 400
    assert b"400" in response.data
    assert b"Bad request" in response.data


def test_internal_error_shows_custom_500_page(app, client):
    @app.route("/force-error")
    def force_error():
        raise RuntimeError("Something broke on purpose (test only)")

    response = client.get("/force-error")

    assert response.status_code == 500
    assert b"500" in response.data
    assert b"Something went wrong" in response.data
    assert b"Something broke on purpose" not in response.data


def test_error_pages_render_for_logged_in_users_too(client, make_user, login):
    make_user(email="erruser@example.com")
    login("erruser@example.com")

    response = client.get("/still/missing")

    assert response.status_code == 404
    assert b"Open dashboard" in response.data
