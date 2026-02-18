import re

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"(?:\\+?\\d{1,3})?[\\s.-]?(?:\\(?\\d{2,3}\\)?[\\s.-]?)?\\d{4,5}[\\s.-]?\\d{4}")
URL_RE = re.compile(r"https?://|www\\.", re.IGNORECASE)
HANDLE_RE = re.compile(r"(^|\\s)@[A-Za-z0-9_]{2,}")


def contains_restricted_data(text: str) -> bool:
    candidates = [EMAIL_RE, PHONE_RE, URL_RE, HANDLE_RE]
    return any(pattern.search(text) for pattern in candidates)
