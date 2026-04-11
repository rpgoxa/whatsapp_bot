# ============================================================
# config.py - Central configuration for the WhatsApp bot
# ============================================================
# Edit this file to set your group names and other settings.

# ---- Group Names ----
# Enter the group names exactly as they appear in WhatsApp.
SOURCE_GROUP_NAME      = ''   # The group that posts prayer times  (e.g. 'Prayer Times Group')
DESTINATION_GROUP_NAME = ''   # The group to forward them to        (e.g. 'Family Group')

# ---- Trigger keyword ----
# The bot will forward any message that contains this exact Arabic phrase.
PRAYER_KEYWORD = 'مواقيت الصلاة بحسب مكتب الوكيل الشرعي'

# ---- Bot behavior ----
# How many seconds to wait between each scan of the source group.
CHECK_INTERVAL_SECONDS = 15

# How many of the most-recent messages to inspect on each scan.
# Keep this small (5-10) so the bot runs fast.
MESSAGES_TO_CHECK = 10

# ---- Chrome session ----
# Chrome will save your WhatsApp login here so you only scan the QR code once.
SESSION_FOLDER = './session'

# ---- URLs & timeouts ----
WHATSAPP_WEB_URL = 'https://web.whatsapp.com'

# Maximum seconds to wait for WhatsApp to finish loading after opening the browser.
PAGE_LOAD_TIMEOUT = 90

# Maximum seconds to wait for a single page element to appear.
ELEMENT_TIMEOUT = 20
