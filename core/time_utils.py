from datetime import datetime, timezone
from zoneinfo import ZoneInfo

JST = ZoneInfo("Asia/Tokyo")
FIXED_JAPANESE_HOLIDAYS = {
    (1, 1),
    (2, 11),
    (2, 23),
    (4, 29),
    (5, 3),
    (5, 4),
    (5, 5),
    (8, 11),
    (11, 3),
    (11, 23),
}


def now_jst_iso():
    return datetime.now(JST).isoformat(timespec="seconds")


def format_jst_timestamp(value):
    text = str(value or "").strip()
    if not text or text == "未回答":
        return text or "未回答"

    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return text

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)

    return parsed.astimezone(JST).strftime("%Y-%m-%d %H:%M:%S")


def _nth_weekday(year, month, weekday, n):
    first = datetime(year, month, 1, tzinfo=JST)
    offset = (weekday - first.weekday()) % 7
    return first.day + offset + 7 * (n - 1)


def _vernal_equinox_day(year):
    return int(20.8431 + 0.242194 * (year - 1980) - int((year - 1980) / 4))


def _autumnal_equinox_day(year):
    return int(23.2488 + 0.242194 * (year - 1980) - int((year - 1980) / 4))


def is_japanese_public_holiday(day):
    month_day = (day.month, day.day)
    if month_day in FIXED_JAPANESE_HOLIDAYS:
        return True

    if day.month == 1 and day.day == _nth_weekday(day.year, 1, 0, 2):
        return True
    if day.month == 7 and day.day == _nth_weekday(day.year, 7, 0, 3):
        return True
    if day.month == 9 and day.day == _nth_weekday(day.year, 9, 0, 3):
        return True
    if day.month == 10 and day.day == _nth_weekday(day.year, 10, 0, 2):
        return True
    if day.month == 3 and day.day == _vernal_equinox_day(day.year):
        return True
    if day.month == 9 and day.day == _autumnal_equinox_day(day.year):
        return True

    return False


def is_configured_holiday(day, holidays):
    today = day.date().isoformat()
    month_day = day.strftime("%m-%d")
    return today in holidays or month_day in holidays


def is_business_time(business_hours, holidays=None):
    now = datetime.now(JST)
    holidays = holidays or []

    if now.weekday() >= 5:
        return False
    if is_japanese_public_holiday(now):
        return False
    if is_configured_holiday(now, holidays):
        return False

    start_text = business_hours.get("start", "08:30")
    end_text = business_hours.get("end", "17:15")

    try:
        start_hour, start_minute = [int(part) for part in start_text.split(":", 1)]
        end_hour, end_minute = [int(part) for part in end_text.split(":", 1)]
    except Exception:
        start_hour, start_minute = 8, 30
        end_hour, end_minute = 17, 15

    start = now.replace(hour=start_hour, minute=start_minute, second=0, microsecond=0)
    end = now.replace(hour=end_hour, minute=end_minute, second=0, microsecond=0)

    if start <= end:
        return start <= now <= end

    return now >= start or now <= end
