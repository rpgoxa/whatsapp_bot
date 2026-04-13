# WhatsApp group mirror

Re-sends every new message from a **source** WhatsApp group to a **destination** group using [Green API](https://green-api.com/). Messages look like normal sends from your linked number (not "Forwarded"). It can also add branded headers/icons + your group link to outgoing content and post filtered Shia event digests from RSS/Atom feeds.

---

## Setup

1. Create a Green API instance, link WhatsApp, copy `INSTANCE_ID`, `apiTokenInstance`, and host URL from the console.
2. `pip install -r requirements.txt`
3. Copy `.env.example` → `.env` and fill in credentials and **exact** group names as shown in WhatsApp.
4. In the Green API console: enable **incoming messages and files**, and **messages sent from the phone** (otherwise your own test messages in the source group never appear in the queue). **Do not** set a custom webhook if you use this script’s polling.
5. Run: `python index.py`

---

## Files

| File | Role |
|------|------|
| `index.py` | Starts the bot |
| `settings.py` | Reads env vars and exposes runtime config |
| `.env` | Your secrets and group names (not in git) |
| `bot/forwarder.py` | Green API queue + mirror logic |
| `bot/shia_events.py` | RSS/Atom polling + event filtering |

**Python 3.10+**

---

## If it “doesn’t work”

- Turn on **incoming messages and files** in the Green API console (required for other people’s messages).
- The linked WhatsApp account must be in **both** groups.
- Run with `MIRROR_DEBUG=true` in env vars: you should see `[debug] queue: incomingMessageReceived ...` when someone writes in the source group. If you see **nothing**, the queue is empty (wrong instance, custom webhook set, or webhooks disabled).
- If you see `match=False`, the chat id from WhatsApp does not match the resolved source id: set **`SOURCE_GROUP_CHAT_ID`** / **`DESTINATION_GROUP_CHAT_ID`** to the exact `@g.us` values from the Green API group info.
- Watch lines starting with `[API Error]` or `[Mirror]`.

---

## Branding and group link

Set these env vars to add a styled header and invite link to mirrored messages:

- `ENABLE_BRANDING=true`
- `BRAND_TITLE=Shia 12 Lebanon Updates`
- `BRAND_ICON=🕌`
- `BRAND_DETAIL_ICON=✦`
- `GROUP_LINK_URL=https://chat.whatsapp.com/your-link`
- `GROUP_LINK_LABEL=Join group`

---

## Shia events digest (RSS/Atom)

The bot can periodically pull event/news feeds and send a short update into the destination group.

- `ENABLE_SHIA_EVENTS_FEED=true`
- `SHIA_EVENTS_FEED_URLS=https://example1/rss.xml,https://example2/feed`
- `SHIA_EVENTS_POLL_SECONDS=1800`
- `SHIA_EVENTS_MAX_ITEMS_PER_POLL=2`
- `SHIA_EVENTS_KEYWORDS=shia,shiite,imam,ashura,karbala,husseini,lebanon,martyr,birth,death,majlis`

Tip: Use trusted sources focused on Lebanon and Twelver-Shia community updates.

---

## Deploy on Railway

1. Push this repository to GitHub.
2. In Railway, create a new project from the GitHub repo.
3. In Railway Variables, set:
   - `API_URL` (usually `https://api.green-api.com`)
   - `INSTANCE_ID`
   - `API_TOKEN`
   - `SOURCE_GROUP_NAME` and `DESTINATION_GROUP_NAME` (or use chat ids instead)
   - Optional: `SOURCE_GROUP_CHAT_ID`, `DESTINATION_GROUP_CHAT_ID`, `MIRROR_DEBUG`, `STRIP_LINKS_FROM_TEXT`
   - Branding: `ENABLE_BRANDING`, `BRAND_TITLE`, `BRAND_ICON`, `BRAND_DETAIL_ICON`, `GROUP_LINK_URL`, `GROUP_LINK_LABEL`
   - Events: `ENABLE_SHIA_EVENTS_FEED`, `SHIA_EVENTS_FEED_URLS`, `SHIA_EVENTS_POLL_SECONDS`, `SHIA_EVENTS_MAX_ITEMS_PER_POLL`, `SHIA_EVENTS_KEYWORDS`
4. Deploy. Railway uses `railway.toml` and starts the bot with `python index.py`.
