import datetime
def get_current_time(timezone: str = "UTC") -> str:
    now = datetime.datetime.now(datetime.timezone.utc)
    return f"Current time: {now.strftime('%H:%M:%S')} (UTC)."
