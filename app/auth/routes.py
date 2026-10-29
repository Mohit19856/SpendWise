"""
Authentication routes: register, login, logout, profile.

Security notes
--------------
* Passwords are hashed with Werkzeug before they touch the database.
* Every form is a Flask-WTF form, therefore CSRF-protected.
* Private pages use @login_required, so an anonymous visitor is redirected to
  the login page instead of seeing data.
* The "next" redirect parameter is validated, so it cannot be used for an
  open-redirect attack.
"""

from urllib.parse import urljoin, urlparse

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from ..forms import ChangePasswordForm, LoginForm, ProfileForm, RegisterForm
from ..models import User, db
from ..services import get_summary

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


def is_safe_redirect(target):
    """Only allow redirects that stay inside this website."""
    if not target:
        return False
    reference = urlparse(request.host_url)
    test = urlparse(urljoin(request.host_url, target))
    return test.scheme in ("http", "https") and reference.netloc == test.netloc


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.home"))

    form = RegisterForm()
    if form.validate_on_submit():
        user = User(name=form.name.data.strip(), email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()

        login_user(user)
        flash(f"Welcome to SpendWise, {user.display_name()}! Your account is ready.", "success")
        return redirect(url_for("dashboard.home"))

    if form.errors:
        flash("Please check the highlighted fields and try again.", "danger")

    return render_template("auth/register.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.home"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        # Same message for "unknown email" and "wrong password" so that an
        # attacker cannot discover which emails are registered.
        if user is None or not user.check_password(form.password.data):
            flash("Invalid email or password. Please try again.", "danger")
        else:
            login_user(user, remember=form.remember.data)
            flash(f"Welcome back, {user.display_name()}!", "success")
            next_page = request.args.get("next")
            if is_safe_redirect(next_page):
                return redirect(next_page)
            return redirect(url_for("dashboard.home"))

    return render_template("auth/login.html", form=form)


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    """Logout is a POST request so it is protected by the CSRF token."""
    logout_user()
    flash("You have been logged out successfully.", "info")
    return redirect(url_for("index"))


@auth_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    """Show the logged-in user's own profile. No user id comes from the URL."""
    form = ProfileForm(obj=current_user)

    if form.validate_on_submit():
        current_user.name = form.name.data.strip()
        db.session.commit()
        flash("Your profile has been updated.", "success")
        return redirect(url_for("auth.profile"))

    if form.errors:
        flash("Could not update your profile. Please check the name field.", "danger")

    summary = get_summary(current_user.id)
    return render_template(
        "auth/profile.html",
        form=form,
        password_form=ChangePasswordForm(),
        summary=summary,
        transaction_count=current_user.transactions.count(),
    )


@auth_bp.route("/profile/password", methods=["POST"])
@login_required
def change_password():
    """Change the password of the logged-in user after verifying the old one."""
    form = ChangePasswordForm()
    if form.validate_on_submit():
        current_user.set_password(form.new_password.data)
        db.session.commit()
        flash("Your password has been changed successfully.", "success")
        return redirect(url_for("auth.profile"))

    flash("Could not change your password. Please check the fields below.", "danger")
    summary = get_summary(current_user.id)
    return render_template(
        "auth/profile.html",
        form=ProfileForm(obj=current_user),
        password_form=form,
        summary=summary,
        transaction_count=current_user.transactions.count(),
    )
