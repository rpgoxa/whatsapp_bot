"""Environment-based settings for local runs and Railway deployments."""

import os

from dotenv import load_dotenv

load_dotenv()


def _get_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _get_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _get_stripped(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


# ---- Green API Credentials ----
API_URL_RAW = os.getenv("API_URL", "https://api.green-api.com")
INSTANCE_ID_RAW = os.getenv("INSTANCE_ID", "")
API_TOKEN_RAW = os.getenv("API_TOKEN", "")

API_URL = API_URL_RAW.strip().rstrip("/")
INSTANCE_ID = INSTANCE_ID_RAW.strip()
API_TOKEN = API_TOKEN_RAW.strip()

API_URL_HAD_WHITESPACE = API_URL_RAW != API_URL
INSTANCE_ID_HAD_WHITESPACE = INSTANCE_ID_RAW != INSTANCE_ID
API_TOKEN_HAD_WHITESPACE = API_TOKEN_RAW != API_TOKEN

# ---- Groups (pick ONE way: names OR chat ids) ----
SOURCE_GROUP_NAME = _get_stripped("SOURCE_GROUP_NAME")
DESTINATION_GROUP_NAME = _get_stripped("DESTINATION_GROUP_NAME")
SOURCE_GROUP_CHAT_ID = _get_stripped("SOURCE_GROUP_CHAT_ID")
DESTINATION_GROUP_CHAT_ID = _get_stripped("DESTINATION_GROUP_CHAT_ID")
GROUP_LINK_URL = _get_stripped("GROUP_LINK_URL")

# ---- Runtime ----
MIRROR_DEBUG = _get_bool("MIRROR_DEBUG", True)
STRIP_LINKS_FROM_TEXT = _get_bool("STRIP_LINKS_FROM_TEXT", True)
APPEND_GROUP_LINK_TO_MESSAGES = _get_bool("APPEND_GROUP_LINK_TO_MESSAGES", True)
ENABLE_OUTGOING_DEDUP = _get_bool("ENABLE_OUTGOING_DEDUP", True)
DEDUPE_WINDOW_SECONDS = _get_int("DEDUPE_WINDOW_SECONDS", 10800)
SCHEDULE_TIMEZONE = os.getenv("SCHEDULE_TIMEZONE", "Asia/Beirut")
SCHEDULE_DB_PATH = _get_stripped("SCHEDULE_DB_PATH", "data/schedules.db")

# ---- Panel auth (sensitive) ----
PANEL_SECRET_KEY = _get_stripped("PANEL_SECRET_KEY", "change-me-before-production")
ADMIN_EMAIL = _get_stripped("ADMIN_EMAIL")
ADMIN_PASSWORD = _get_stripped("ADMIN_PASSWORD")
