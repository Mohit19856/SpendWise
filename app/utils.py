"""
Money helpers.

Financial amounts are stored in the database as INTEGER PAISE (1 rupee = 100
paise). Integers avoid the floating-point rounding errors that appear when you
add/subtract values such as 0.1 + 0.2 with the "float" type.

Conversion rule:
    rupees  ->  paise :  Decimal("1250.75") -> 125075
    paise   ->  rupees:  125075             -> Decimal("1250.75")
"""

from decimal import Decimal, ROUND_HALF_UP

PAISE_PER_RUPEE = 100


def rupees_to_paise(amount):
    """Convert a rupee amount (Decimal / int / str) into integer paise."""
    if amount is None:
        return 0
    value = Decimal(str(amount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return int(value * PAISE_PER_RUPEE)


def paise_to_rupees(paise):
    """Convert integer paise into a Decimal rupee amount."""
    return (Decimal(int(paise or 0)) / PAISE_PER_RUPEE).quantize(Decimal("0.01"))


def format_inr(paise, symbol="\u20b9", with_symbol=True):
    """
    Format integer paise using Indian digit grouping.

        125075 paise -> "₹1,250.75"
        1234567890 paise -> "₹1,23,45,678.90"
    """
    amount = paise_to_rupees(paise)
    negative = amount < 0
    whole, _, fraction = f"{abs(amount):.2f}".partition(".")

    # Indian grouping: last 3 digits, then groups of 2 digits.
    if len(whole) > 3:
        head, tail = whole[:-3], whole[-3:]
        head = ",".join(
            [head[max(i - 2, 0):i] for i in range(len(head), 0, -2)][::-1]
        )
        grouped = f"{head},{tail}"
    else:
        grouped = whole

    text = f"{grouped}.{fraction}"
    if with_symbol:
        text = f"{symbol}{text}"
    return f"-{text}" if negative else text
