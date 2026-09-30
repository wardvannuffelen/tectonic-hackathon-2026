"""Small stdlib-only month arithmetic helpers (avoids adding dateutil)."""
from calendar import monthrange
from datetime import date


def first_of_month(d: date) -> date:
    return d.replace(day=1)


def add_months(d: date, n: int) -> date:
    month_index = d.month - 1 + n
    year = d.year + month_index // 12
    month = month_index % 12 + 1
    day = min(d.day, monthrange(year, month)[1])
    return date(year, month, day)


def month_diff(start: date, end: date) -> int:
    """Whole calendar months between two dates (end - start), can be negative."""
    return (end.year - start.year) * 12 + (end.month - start.month)
