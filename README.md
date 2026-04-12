# WhatsApp Bot — Beta v2.0

An automated WhatsApp bot that runs in the background, monitors your groups, and handles several Islamic daily/weekly tasks. No browser or phone required to be online once configured via **Green API**.

---

## What the bot does

| Feature | How it works |
|---|---|
| **Prayer times forwarding** | Polls the source group every 15 seconds. When a message containing the exact Arabic prayer-times phrase appears, it sends the attached image (if any) and text to the destination group via Green API. |
| **Hijri calendar** | On startup, and once per day at midnight, it calls the Aladhan API for Beirut and checks today's Hijri date against 40+ hardcoded Shia Islamic events. Prints the event name to the console. |
| **Dua Kumayl reminder** | Every Thursday at 8:00 PM — prints a reminder to the console (sending will be added). |
| **Dua Tawassul reminder** | Every Tuesday at 8:00 PM — prints a reminder to the console (sending will be added). |

---

## Project structure

```
whatsapp-bot/
│
├── index.py            ← START HERE  — runs the bot
├── config.py           ← EDIT THIS   — your Green API credentials and group names
├── requirements.txt    ← INSTALL     — Python dependencies
│
└── bot/                ← Internal modules (you don't normally touch these)
    ├── __init__.py     — marks the folder as a Python package
    ├── calendar.py     — Hijri date logic + events dictionary
    ├── scheduler.py    — Thursday/Tuesday reminders + daily calendar job
    └── forwarder.py    — API polling and forwarding logic
```

---

## Quick start

### 1. Register for Green API
1. Go to [Green-API.com](https://green-api.com/).
2. Create an account and create an instance.
3. Link your WhatsApp by scanning the QR code in your dashboard.
4. Note your `INSTANCE_ID` and `API_TOKEN`.

### 2. Install Python dependencies
```bash
pip install -r requirements.txt
```

### 3. Edit config.py
Open `config.py` and fill in your credentials and exact group names:
```python
INSTANCE_ID            = '1234567890'
API_TOKEN              = 'abc123def456ghi789jkl'

SOURCE_GROUP_NAME      = 'Prayer Times Group'   # exact group that posts prayer times
DESTINATION_GROUP_NAME = 'Family Group'          # exact group to forward them to
```

### 4. Run the bot
```bash
python index.py
```
- The bot will automatically pull the chat IDs based on the group names you provided.
- Press **Ctrl+C** to stop.

---

## Where to go when you want to change something

| What you want to change | File to open |
|---|---|
| Green API creds, Group names, scan interval, keyword | `config.py` |
| Add/remove Islamic events from the calendar | `bot/calendar.py` → edit the `HIJRI_EVENTS` dict |
| Change when duas are sent, or add new scheduled tasks | `bot/scheduler.py` → edit `setup_schedule()` |
| Change how messages are detected or forwarded | `bot/forwarder.py` → edit `check_source_group()` |
| Change startup order | `index.py` |

---

## Requirements

- Python 3.8+
- Active internet connection
- A linked Green API account (Free or Developer plan should be sufficient)
