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
