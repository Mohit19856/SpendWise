"""
SpendWise - application configuration.

Configuration is split into three environments:
  * DevelopmentConfig - used on your Windows laptop while developing
  * TestingConfig     - used by pytest (isolated, CSRF off by default)
  * ProductionConfig  - used on the AWS EC2 server with Gunicorn

Secrets are NEVER written in this file. They are read from environment
variables, which you place in the ".env" file (see .env.example).
"""

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent

# Load key=value pairs from ".env" into the process environment (if it exists).
load_dotenv(BASE_DIR / ".env")


class BaseConfig:
    """Settings shared by every environment."""

    # Used to sign session cookies and CSRF tokens.
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Reconnects automatically if the database connection went away.
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

    # ---------- Session / cookie hardening ----------
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = "Lax"

    # CSRF token stays valid for the whole session (no surprise logouts).
    WTF_CSRF_TIME_LIMIT = None

    # ---------- Application settings ----------
    CURRENCY_SYMBOL = "\u20b9"  # Indian Rupee
    TRANSACTIONS_PER_PAGE = 10


class DevelopmentConfig(BaseConfig):
    """Local Windows development: Flask debug server + local SQLite file."""

    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///spendwise.db")


class TestingConfig(BaseConfig):
    """
    Automated tests.

    tests/conftest.py sets TEST_DATABASE_URL to a throw-away file inside the
    operating system's temporary folder, so tests never touch real user data.
    CSRF is disabled by default so that tests can post forms easily;
    tests/test_security.py re-enables it to prove CSRF protection works.
    """

    TESTING = True
    SECRET_KEY = "testing-secret-key"
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = os.environ.get("TEST_DATABASE_URL", "sqlite:///:memory:")
    TRANSACTIONS_PER_PAGE = 10


class ProductionConfig(BaseConfig):
    """AWS EC2 deployment: DEBUG off, secure cookies, real secret required."""

    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///spendwise.db")

    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True

    @staticmethod
    def validate():
        """Refuse to start in production with a missing/placeholder secret key."""
        secret = os.environ.get("SECRET_KEY", "")
        if not secret or secret.startswith("change-this") or secret == "dev-secret-key-change-me":
            raise RuntimeError(
                "SECRET_KEY is not configured. Set a strong SECRET_KEY in the "
                "environment before running SpendWise in production."
            )


config = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}


def get_config(name=None):
    """Return a config class by name, falling back to FLASK_CONFIG / development."""
    name = name or os.environ.get("FLASK_CONFIG", "development")
    return config.get(name, DevelopmentConfig)
