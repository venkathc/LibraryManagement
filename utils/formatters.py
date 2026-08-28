"""Presentation formatters."""

from decimal import Decimal


def format_inr(amount: Decimal | float | int) -> str:
    """Format an amount in Indian Rupees."""
    return f"₹{Decimal(str(amount)):,.2f}"
