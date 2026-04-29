from datetime import datetime, timezone
from zoneinfo import ZoneInfo

JST = ZoneInfo("Asia/Tokyo")


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


def is_business_time(business_hours):
    start_text = business_hours.get("start", "08:30")
    end_text = business_hours.get("end", "17:15")

    try:
        start_hour, start_minute = [int(part) for part in start_text.split(":", 1)]
        end_hour, end_minute = [int(part) for part in end_text.split(":", 1)]
    except Exception:
        start_hour, start_minute = 8, 30
        end_hour, end_minute = 17, 15

    now = datetime.now(JST)
    start = now.replace(hour=start_hour, minute=start_minute, second=0, microsecond=0)
    end = now.replace(hour=end_hour, minute=end_minute, second=0, microsecond=0)

    if start <= end:
        return start <= now <= end

    return now >= start or now <= end
