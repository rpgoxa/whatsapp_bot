"""
Environment-based settings for local runs and Railway deployments.
"""

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
        return int(value.strip())
    except ValueError:
        return default


def _get_csv(name: str) -> list[str]:
    value = os.getenv(name, "")
    return [item.strip() for item in value.split(",") if item.strip()]


# ---- Green API Credentials ----
API_URL = os.getenv("API_URL", "https://api.green-api.com").rstrip("/")
INSTANCE_ID = os.getenv("INSTANCE_ID", "")
API_TOKEN = os.getenv("API_TOKEN", "")

# ---- Groups (pick ONE way: names OR chat ids) ----
SOURCE_GROUP_NAME = os.getenv("SOURCE_GROUP_NAME", "")
DESTINATION_GROUP_NAME = os.getenv("DESTINATION_GROUP_NAME", "")
SOURCE_GROUP_CHAT_ID = os.getenv("SOURCE_GROUP_CHAT_ID", "")
DESTINATION_GROUP_CHAT_ID = os.getenv("DESTINATION_GROUP_CHAT_ID", "")

# Prints each incoming/outgoing event and source chat matching details.
MIRROR_DEBUG = _get_bool("MIRROR_DEBUG", True)

# Remove links from mirrored text/captions (plain text only).
STRIP_LINKS_FROM_TEXT = _get_bool("STRIP_LINKS_FROM_TEXT", True)

# ---- Message branding ----
ENABLE_BRANDING = _get_bool("ENABLE_BRANDING", True)
BRAND_TITLE = os.getenv("BRAND_TITLE", "Shia 12 Lebanon Updates")
BRAND_ICON = os.getenv("BRAND_ICON", "🕌")
BRAND_DETAIL_ICON = os.getenv("BRAND_DETAIL_ICON", "✦")
GROUP_LINK_URL = os.getenv("GROUP_LINK_URL", "")
GROUP_LINK_LABEL = os.getenv("GROUP_LINK_LABEL", "Join group")

# ---- Religious events feed ----
ENABLE_SHIA_EVENTS_FEED = _get_bool("ENABLE_SHIA_EVENTS_FEED", False)
SHIA_EVENTS_FEED_URLS = _get_csv("SHIA_EVENTS_FEED_URLS")
SHIA_EVENTS_POLL_SECONDS = max(60, _get_int("SHIA_EVENTS_POLL_SECONDS", 1800))
SHIA_EVENTS_MAX_ITEMS_PER_POLL = max(1, _get_int("SHIA_EVENTS_MAX_ITEMS_PER_POLL", 2))
SHIA_EVENTS_KEYWORDS = _get_csv(
    "SHIA_EVENTS_KEYWORDS"
) or [
    "shia",
    "shiite",
    "imam",
    "ashura",
    "karbala",
    "husseini",
    "lebanon",
    "martyr",
    "birth",
    "death",
    "majlis",
]
