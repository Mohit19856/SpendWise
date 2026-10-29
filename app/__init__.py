"""
SpendWise application factory.

Everything is created inside create_app() - that makes the app easy to test
(tests build their own app instance with a temporary database) and easy to run
with Gunicorn on AWS EC2 (see run.py).
"""

import logging
import os

from flask import Flask, flash, redirect, render_template, request, url_for
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFError, CSRFProtect
from werkzeug.exceptions import HTTPException

from config import get_config

# ---------------------------------------------------------------------------
# Shared extension objects (created once, bound to the app in create_app()).
# ---------------------------------------------------------------------------
db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()


def create_app(config_name=None):
    app = Flask(__name__)
    app.config.from_object(get_config(config_name))

    # In production, refuse to start with a missing/placeholder secret key.
    if config_name == "production" or os.environ.get("FLASK_CONFIG") == "production":
        from config import ProductionConfig

        ProductionConfig.validate()

    _init_extensions(app)
    _register_blueprints(app)
    _register_error_handlers(app)
    _register_template_helpers(app)
    _configure_logging(app)
    _register_cli(app)

    return app


def _init_extensions(app):
    db.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please log in to open that page."
    login_manager.login_message_category = "warning"

    # Import models so that the user loader can find the User class.
    from . import models  # noqa: F401

    @login_manager.user_loader
    def load_user(user_id):
        try:
            return db.session.get(models.User, int(user_id))
        except (TypeError, ValueError):
            return None


def _register_blueprints(app):
    from .auth.routes import auth_bp
    from .dashboard.routes import dashboard_bp
    from .transactions.routes import transactions_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(transactions_bp)

    @app.route("/")
    def index():
        """Public landing page (redirects logged-in users to the dashboard)."""
        from flask_login import current_user

        if current_user.is_authenticated:
            return redirect(url_for("dashboard.home"))
        return render_template("index.html")


def _register_error_handlers(app):
    @app.errorhandler(400)
    def bad_request(error):
        return render_template("errors/400.html"), 400

    @app.errorhandler(CSRFError)
    def handle_csrf_error(error):
        """Expired/missing CSRF token - show a friendly explanation."""
        return render_template("errors/400.html", reason=error.description), 400

    @app.errorhandler(403)
    def forbidden(error):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def page_not_found(error):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def internal_server_error(error):
        db.session.rollback()
        app.logger.exception("Unhandled server error on %s", request.path)
        return render_template("errors/500.html"), 500

    @app.errorhandler(Exception)
    def unhandled_exception(error):
        """Catch-all so users see the friendly 500 page instead of a stack trace."""
        if isinstance(error, HTTPException):
            return error
        db.session.rollback()
        app.logger.exception("Unhandled exception on %s", request.path)
        return render_template("errors/500.html"), 500


def _register_template_helpers(app):
    from .utils import format_inr

    @app.template_filter("inr")
    def inr_filter(paise):
        return format_inr(paise)

    @app.context_processor
    def inject_globals():
        from .constants import CATEGORIES_BY_TYPE, EXPENSE_CATEGORIES, INCOME_CATEGORIES, TYPE_BADGES, TYPE_LABELS

        return {
            "APP_NAME": "SpendWise",
            "APP_TAGLINE": "Personal Expense Tracker",
            "CURRENCY_SYMBOL": app.config.get("CURRENCY_SYMBOL", "\u20b9"),
            "CATEGORIES_BY_TYPE": CATEGORIES_BY_TYPE,
            "INCOME_CATEGORIES": INCOME_CATEGORIES,
            "EXPENSE_CATEGORIES": EXPENSE_CATEGORIES,
            "TYPE_LABELS": TYPE_LABELS,
            "TYPE_BADGES": TYPE_BADGES,
        }

    def flash_errors(form, prefix="Please fix the following"):
        messages = [f"{field.label.text}: {msg}" for field, errors in form.errors.items() for msg in errors]
        if messages:
            flash(f"{prefix} - " + " | ".join(messages), "danger")

    app.jinja_env.globals["flash_errors"] = flash_errors


def _configure_logging(app):
    """
    Safe logging: log application events, never passwords or secret keys.
    Logging levels default to INFO locally and can be raised for production.
    """
    level = logging.DEBUG if app.config.get("DEBUG") else logging.INFO
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter("[%(asctime)s] %(levelname)s in %(module)s: %(message)s")
    )
    app.logger.handlers = [handler]
    app.logger.setLevel(level)
    app.logger.info("SpendWise started (debug=%s)", app.config.get("DEBUG"))


def _register_cli(app):
    """Custom "flask" commands: flask init-db  /  flask create-user"""

    import click

    from .models import User

    @app.cli.command("init-db")
    def init_db():
        """Create all database tables (safe to run more than once)."""
        with app.app_context():
            db.create_all()
        click.echo("Database tables created.")

    @app.cli.command("create-user")
    @click.option("--name", prompt=True)
    @click.option("--email", prompt=True)
    @click.option("--password", prompt=True, hide_input=True, confirmation_prompt=True)
    def create_user(name, email, password):
        """Create a single user from the command line."""
        with app.app_context():
            email = email.strip().lower()
            if User.query.filter_by(email=email).first():
                click.echo("A user with that email already exists.")
                return
            user = User(name=name.strip(), email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            click.echo(f"Created user {email} (id={user.id})")
