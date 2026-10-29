"""
WTForms form classes.

Flask-WTF gives us three important things for free:
  1. Server-side validation (a user cannot bypass the HTML form)
  2. CSRF protection on every POST request
  3. Friendly, field-level error messages
"""

from datetime import date

from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    DateField,
    DecimalField,
    PasswordField,
    SelectField,
    StringField,
    SubmitField,
)
from wtforms.validators import (
    DataRequired,
    Email,
    EqualTo,
    Length,
    NumberRange,
    Optional,
    ValidationError,
)

from .constants import ALL_CATEGORIES, CATEGORIES_BY_TYPE, EXPENSE, INCOME, TRANSACTION_TYPES
from .models import User

# Values allowed in the "type" dropdown, labelled for the user interface.
TYPE_CHOICES = [
    (EXPENSE, "Expense (money going out)"),
    (INCOME, "Income (money coming in)"),
]

# All categories in one flat list. The add/edit template groups them into
# "Income" and "Expense" optgroups for a nicer user interface, and
# TransactionForm.validate_category() makes sure the chosen category really
# belongs to the selected transaction type.
CATEGORY_CHOICES = [(name, name) for name in ALL_CATEGORIES]


class RegisterForm(FlaskForm):
    name = StringField(
        "Full name",
        validators=[DataRequired(message="Please enter your name."), Length(min=2, max=80)],
    )
    email = StringField(
        "Email address",
        validators=[DataRequired(message="Please enter your email."), Email(message="Enter a valid email address."), Length(max=120)],
    )
    password = PasswordField(
        "Password",
        validators=[
            DataRequired(message="Please choose a password."),
            Length(min=8, max=128, message="Password must be at least 8 characters long."),
        ],
    )
    confirm_password = PasswordField(
        "Confirm password",
        validators=[
            DataRequired(message="Please confirm your password."),
            EqualTo("password", message="Both passwords must match."),
        ],
    )
    submit = SubmitField("Create account")

    def validate_email(self, field):
        """Reject an email address that is already registered."""
        email = field.data.strip().lower()
        field.data = email
        if User.query.filter_by(email=email).first():
            raise ValidationError("This email is already registered. Please log in instead.")


class LoginForm(FlaskForm):
    email = StringField(
        "Email address",
        validators=[DataRequired(message="Please enter your email."), Email(message="Enter a valid email address.")],
    )
    password = PasswordField(
        "Password", validators=[DataRequired(message="Please enter your password.")]
    )
    remember = BooleanField("Keep me logged in on this device")
    submit = SubmitField("Log in")

    def validate_email(self, field):
        field.data = field.data.strip().lower()


class TransactionForm(FlaskForm):
    """Used for both 'Add transaction' and 'Edit transaction'."""

    type = SelectField("Transaction type", choices=TYPE_CHOICES, validators=[DataRequired()])
    amount = DecimalField(
        "Amount (INR)",
        places=2,
        rounding=None,
        validators=[
            DataRequired(message="Please enter an amount."),
            # Amounts must be positive: zero and negative values are rejected.
            NumberRange(min=0.01, max=100000000, message="Amount must be greater than 0 and below 10,00,00,000."),
        ],
    )
    category = SelectField(
        "Category",
        choices=CATEGORY_CHOICES,
        validators=[DataRequired(message="Please choose a category.")],
    )
    txn_date = DateField(
        "Transaction date",
        validators=[DataRequired(message="Please choose a date.")],
        default=date.today,
    )
    description = StringField(
        "Description",
        validators=[
            Optional(),
            Length(max=255, message="Description cannot be longer than 255 characters."),
        ],
    )
    submit = SubmitField("Save transaction")

    def validate_type(self, field):
        if field.data not in TRANSACTION_TYPES:
            raise ValidationError("Invalid transaction type.")

    def validate_category(self, field):
        # Income and expense categories are kept in separate groups, so the
        # selected category must belong to the selected type.
        allowed = CATEGORIES_BY_TYPE.get(self.type.data, ())
        if field.data not in allowed:
            raise ValidationError(
                "Please choose a category that matches the selected transaction type."
            )

    def validate_amount(self, field):
        # DecimalField accepts "abc"? No - but it can accept "0", so guard again here.
        if field.data is None or field.data <= 0:
            raise ValidationError("Amount must be greater than 0.")

    def validate_txn_date(self, field):
        if field.data is None:
            raise ValidationError("Invalid date.")
        if field.data.year < 2000 or field.data.year > 2100:
            raise ValidationError("Date must be between the years 2000 and 2100.")


class ProfileForm(FlaskForm):
    name = StringField(
        "Full name",
        validators=[DataRequired(message="Please enter your name."), Length(min=2, max=80)],
    )
    submit = SubmitField("Update profile")


class ChangePasswordForm(FlaskForm):
    current_password = PasswordField(
        "Current password", validators=[DataRequired(message="Enter your current password.")]
    )
    new_password = PasswordField(
        "New password",
        validators=[
            DataRequired(message="Enter a new password."),
            Length(min=8, max=128, message="Password must be at least 8 characters long."),
        ],
    )
    confirm_password = PasswordField(
        "Confirm new password",
        validators=[
            DataRequired(message="Please confirm the new password."),
            EqualTo("new_password", message="Both passwords must match."),
        ],
    )
    submit = SubmitField("Change password")

    def validate_current_password(self, field):
        from flask_login import current_user

        if not current_user.check_password(field.data):
            raise ValidationError("Your current password is incorrect.")

    def validate_new_password(self, field):
        from flask_login import current_user

        if current_user.check_password(field.data):
            raise ValidationError("The new password must be different from the current one.")
