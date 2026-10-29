"""Shared constants: transaction types and category lists."""

EXPENSE = "expense"
INCOME = "income"

TRANSACTION_TYPES = (INCOME, EXPENSE)

TYPE_LABELS = {
    INCOME: "Income",
    EXPENSE: "Expense",
}

TYPE_BADGES = {
    INCOME: "success",
    EXPENSE: "danger",
}

INCOME_CATEGORIES = (
    "Salary",
    "Freelance",
    "Business",
    "Interest",
    "Rental",
    "Gift",
    "Refund",
    "Other Income",
)

EXPENSE_CATEGORIES = (
    "Food",
    "Groceries",
    "Rent",
    "Utilities",
    "Transport",
    "Education",
    "Health",
    "Shopping",
    "Entertainment",
    "Travel",
    "Savings",
    "Other Expense",
)

# One flat list is used by the database/filters; the add/edit form narrows the
# choice down to the categories that belong to the selected transaction type.
ALL_CATEGORIES = tuple(sorted(set(INCOME_CATEGORIES + EXPENSE_CATEGORIES)))

CATEGORIES_BY_TYPE = {
    INCOME: INCOME_CATEGORIES,
    EXPENSE: EXPENSE_CATEGORIES,
}

# Categories used to pick a colour in the category-wise expense chart.
CHART_COLORS = (
    "#4f46e5", "#0ea5e9", "#10b981", "#f59e0b", "#ef4444",
    "#8b5cf6", "#14b8a6", "#f97316", "#ec4899", "#64748b",
    "#84cc16", "#06b6d4",
)
