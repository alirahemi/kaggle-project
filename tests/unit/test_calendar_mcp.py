"""Unit tests for calendar MCP tool helpers."""

from datetime import date, timedelta


def parse_german_date(text: str) -> date | None:
    """Minimal date parser used by calendar MCP stubs."""
    for fmt in ("%d.%m.%Y", "%Y-%m-%d"):
        try:
            from datetime import datetime

            return datetime.strptime(text.strip(), fmt).date()
        except ValueError:
            continue
    return None


def business_days_until(deadline: date, today: date | None = None) -> int:
    today = today or date.today()
    if deadline <= today:
        return 0
    count = 0
    cursor = today
    while cursor < deadline:
        cursor += timedelta(days=1)
        if cursor.weekday() < 5:
            count += 1
    return count


def test_parse_german_date():
    assert parse_german_date("15.07.2025") == date(2025, 7, 15)
    assert parse_german_date("2025-07-15") == date(2025, 7, 15)
    assert parse_german_date("invalid") is None


def test_business_days_until_weekend_skipped():
    # Monday 2025-06-16 to Friday 2025-06-20 = 4 business days
    start = date(2025, 6, 16)
    end = date(2025, 6, 20)
    assert business_days_until(end, today=start) == 4
