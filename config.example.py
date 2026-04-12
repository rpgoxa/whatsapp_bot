# ============================================================
# config.example.py - Central configuration for the WhatsApp bot
# ============================================================
# Rename this file to config.py and set your credentials.

# ---- Green API Credentials ----
# Get these from your dashboard at https://green-api.com
API_URL                = 'https://api.greenapi.com'
INSTANCE_ID            = ''
API_TOKEN              = ''

# ---- Group Names ----
# Enter the group names exactly as they appear in WhatsApp.
SOURCE_GROUP_NAME      = ''   # exact name of the prayer times source group
DESTINATION_GROUP_NAME = ''   # exact name of your group

# ---- Trigger keyword ----
# The bot will forward any message that contains this exact Arabic phrase.
PRAYER_KEYWORD         = 'مواقيت الصلاة بحسب مكتب الوكيل الشرعي'

# ---- Bot behavior ----
# How many seconds to wait between checking for new messages.
# Green API HTTP requests are fast, 15 seconds is a good default.
POLL_INTERVAL          = 15
