# WhatsApp Bot — Beta v1.0

An automated WhatsApp bot that runs in the background, monitors your groups, and handles several Islamic daily/weekly tasks.

---

## What the bot does

| Feature | How it works |
|---|---|
| **Prayer times forwarding** | Watches the source group every 15 seconds. When a message containing the exact Arabic prayer-times phrase appears, it downloads the attached image (if any) and forwards it to the destination group — image first, then text, matching the original layout. |
| **Hijri calendar** | On startup, and once per day at midnight, it calls the Aladhan API for Beirut and checks today's Hijri date against 40+ hardcoded Shia Islamic events (all 12 Imam birthdays & martyrdoms, Ashura, Arbaeen, Mab'ath, Eid al-Ghadir, Eid al-Fitr, Eid al-Adha, Laylat al-Qadr nights, Mid-Sha'ban). Prints the event name to the console. |
| **Dua Kumayl reminder** | Every Thursday at 8:00 PM — prints a reminder to the console (sending will be added in v2). |
| **Dua Tawassul reminder** | Every Tuesday at 8:00 PM — prints a reminder to the console (sending will be added in v2). |
| **Session saving** | Chrome saves your WhatsApp login to the `session/` folder so you only scan the QR code once. |

---

## Project structure

```
whatsapp-bot/
│
├── index.py            ← START HERE  — runs the bot
├── config.py           ← EDIT THIS   — your group names and settings
├── get_groups.py       ← RUN ONCE    — lists your WhatsApp group names
├── requirements.txt    ← INSTALL     — Python dependencies
│
├── bot/                ← Internal modules (you don't normally touch these)
│   ├── __init__.py     — marks the folder as a Python package
│   ├── calendar.py     — Hijri date logic + events dictionary
│   ├── scheduler.py    — Thursday/Tuesday reminders + daily calendar job
│   └── forwarder.py    — all Selenium / WhatsApp Web automation
│
└── session/            ← Auto-created on first run — Chrome login is saved here
                           Do not delete this folder or you'll need to re-scan QR
```

---

## Quick start

### 1. Install Python dependencies
```bash
pip install -r requirements.txt
```

### 2. Find your group names (first time only)
```bash
python get_groups.py
```
- Chrome opens and shows WhatsApp Web — scan the QR code with your phone.
- The script prints a numbered list of every group and contact.
- Note the exact names of the two groups you need.

### 3. Edit config.py
Open `config.py` and fill in the group names exactly as they appear in WhatsApp:
```python
SOURCE_GROUP_NAME      = 'Prayer Times Group'   # group that posts prayer times
DESTINATION_GROUP_NAME = 'Family Group'          # group to forward them to
```

### 4. Run the bot
```bash
python index.py
```
- On the first run it will ask you to scan a QR code.
- On every run after that it restores the saved session automatically.
- Press **Ctrl+C** to stop.

---

## Where to go when you want to change something

| What you want to change | File to open |
|---|---|
| Group names, scan interval, keyword | `config.py` |
| Add/remove Islamic events from the calendar | `bot/calendar.py` → edit the `HIJRI_EVENTS` dict |
| Change when duas are sent, or add new scheduled tasks | `bot/scheduler.py` → edit `setup_schedule()` |
| Change how messages are detected or forwarded | `bot/forwarder.py` → edit `check_source_group()` or `forward_to_destination()` |
| Change startup order | `index.py` |

---

## Planned upgrades (v2)

- [ ] **Send** Dua Kumayl and Dua Tawassul text to the group (not just print)
- [ ] Send a greeting message on special Hijri occasions
- [ ] Monitor **all groups** at once instead of only the source group
- [ ] Web dashboard to configure everything without editing code

---

## Requirements

- Python 3.8+
- Google Chrome installed on this computer
- Active internet connection
- A WhatsApp account that can scan QR codes
