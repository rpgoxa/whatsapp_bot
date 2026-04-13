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
