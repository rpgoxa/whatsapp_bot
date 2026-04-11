# ============================================================
# bot/calendar.py - Hijri date checker using the Aladhan API
# ============================================================
# Fetches today's Hijri date from the internet and checks it
# against a hardcoded dictionary of Shia Islamic events.

import requests  # pip install requests

# ============================================================
# Hijri Events Dictionary
# ============================================================
# Key   : (day, month_number)  — Hijri calendar
# Value : Human-readable event name
#
# Month numbers:
#  1 = Muharram       2 = Safar           3 = Rabi' al-Awwal
#  4 = Rabi' al-Thani 5 = Jumada al-Ula   6 = Jumada al-Akhira
#  7 = Rajab           8 = Sha'ban         9 = Ramadan
# 10 = Shawwal        11 = Dhu al-Qi'da  12 = Dhu al-Hijja

HIJRI_EVENTS = {

    # ── Muharram ────────────────────────────────────────────
    (1,  1):  "Islamic New Year (1 Muharram)",
    (1,  10): "Ashura — Martyrdom of Imam Hussain ibn Ali (3rd Imam)",
    (1,  25): "Martyrdom of Imam Ali ibn Husayn al-Sajjad / Zayn al-Abidin (4th Imam)",

    # ── Safar ───────────────────────────────────────────────
    (2,  7):  "Birthday of Imam Musa al-Kazim (7th Imam)",
    (2,  20): "Arbaeen — 40th Day After Ashura",
    (2,  28): "Martyrdom of Prophet Muhammad (PBUH) & Imam Hasan ibn Ali (2nd Imam)",
    (2,  29): "Martyrdom of Imam Ali al-Ridha (8th Imam)",

    # ── Rabi' al-Awwal ──────────────────────────────────────
    (3,  8):  "Martyrdom of Imam Hasan al-Askari (11th Imam)",
    (3,  17): "Birthday of Prophet Muhammad (PBUH) & Imam Ja'far al-Sadiq (6th Imam)",

    # ── Rabi' al-Thani ──────────────────────────────────────
    (4,  8):  "Birthday of Imam Hasan al-Askari (11th Imam)",

    # ── Jumada al-Ula ───────────────────────────────────────
    (5,  13): "Martyrdom of Sayyida Fatima al-Zahra (narration 1)",

    # ── Jumada al-Akhira ────────────────────────────────────
    (6,  3):  "Martyrdom of Sayyida Fatima al-Zahra (narration 2 — most common)",

    # ── Rajab ───────────────────────────────────────────────
    (7,  1):  "Birthday of Imam Muhammad al-Baqir (5th Imam)",
    (7,  3):  "Martyrdom of Imam Ali al-Hadi (10th Imam)",
    (7,  10): "Birthday of Imam Muhammad al-Jawad (9th Imam)",
    (7,  13): "Birthday of Imam Ali ibn Abi Talib (1st Imam)",
    (7,  25): "Martyrdom of Imam Musa al-Kazim (7th Imam)",
    (7,  27): "Mab'ath — Night of the Prophet's First Divine Revelation",

    # ── Sha'ban ─────────────────────────────────────────────
    (8,  3):  "Birthday of Imam Hussain ibn Ali (3rd Imam)",
    (8,  4):  "Birthday of Abbas ibn Ali (Son of Imam Ali)",
    (8,  5):  "Birthday of Imam Ali ibn Husayn al-Sajjad / Zayn al-Abidin (4th Imam)",
    (8,  15): "Birthday of Imam Muhammad al-Mahdi (12th Imam) / Mid-Sha'ban Night",

    # ── Ramadan ─────────────────────────────────────────────
    (9,  15): "Birthday of Imam Hasan ibn Ali (2nd Imam)",
    (9,  19): "Laylat al-Qadr — Night of Power (19th Ramadan)",
    (9,  21): "Laylat al-Qadr (21st Ramadan) & Martyrdom of Imam Ali ibn Abi Talib (1st Imam)",
    (9,  23): "Laylat al-Qadr — Night of Power (23rd Ramadan)",

    # ── Shawwal ─────────────────────────────────────────────
    (10, 1):  "Eid al-Fitr — End of Ramadan",
    (10, 25): "Martyrdom of Imam Ja'far al-Sadiq (6th Imam)",

    # ── Dhu al-Qi'da ────────────────────────────────────────
    (11, 11): "Birthday of Imam Ali al-Ridha (8th Imam)",
    (11, 29): "Martyrdom of Imam Muhammad al-Jawad (9th Imam)",

    # ── Dhu al-Hijja ────────────────────────────────────────
    (12, 7):  "Martyrdom of Imam Muhammad al-Baqir (5th Imam)",
    (12, 10): "Eid al-Adha — Feast of Sacrifice",
    (12, 15): "Birthday of Imam Ali al-Hadi (10th Imam)",
    (12, 18): "Eid al-Ghadir — Day of Imam Ali's Appointment at Ghadir Khumm",
}

# The Aladhan API endpoint — returns prayer times + Hijri date for Beirut.
ALADHAN_API_URL = (
    "https://api.aladhan.com/v1/timingsByCity"
    "?city=Beirut&country=Lebanon&method=0"
)


def get_todays_hijri():
    """
    Calls the Aladhan API and returns today's Hijri (day, month_number).

    Returns:
        (int, int)   — e.g. (10, 1) for 10 Muharram
        (None, None) — if the API call failed
    """
    print("  Fetching today's Hijri date from Aladhan API …")

    try:
        # Make an HTTP GET request; give up after 10 seconds.
        response = requests.get(ALADHAN_API_URL, timeout=10)

        # HTTP 200 = success. Any other status is an error.
        if response.status_code != 200:
            print(f"  API returned unexpected status: {response.status_code}")
            return None, None

        # Parse the JSON response into a Python dictionary.
        data = response.json()

        # Drill into the nested JSON:  data → data → date → hijri
        hijri        = data['data']['date']['hijri']
        day          = int(hijri['day'])               # e.g. 10
        month_number = int(hijri['month']['number'])   # e.g. 1  (= Muharram)
        month_name   = hijri['month']['en']            # e.g. "Muharram"

        print(f"  Today's Hijri date: {day} {month_name} ({month_number})")
        return day, month_number

    except requests.exceptions.ConnectionError:
        print("  ERROR: No internet connection. Cannot reach Aladhan API.")
    except requests.exceptions.Timeout:
        print("  ERROR: Aladhan API request timed out (10 s).")
    except (KeyError, ValueError, TypeError) as exc:
        print(f"  ERROR: Unexpected API response format — {exc}")

    return None, None


def check_todays_event():
    """
    Fetches today's Hijri date, looks it up in HIJRI_EVENTS, and prints
    any matching Islamic occasion to the console.

    Called once at startup and once per day by the scheduler.
    """
    print("\n─── Hijri Calendar Check ──────────────────────────")

    day, month = get_todays_hijri()

    if day is None or month is None:
        print("  Skipping event check (API error).")
        print("─────────────────────────────────────────────────\n")
        return

    # Look up the (day, month) tuple in the events dictionary.
    event = HIJRI_EVENTS.get((day, month))

    if event:
        print(f"  *** SPECIAL ISLAMIC DAY TODAY ***")
        print(f"  *** {event} ***")
        print("  (Sending a WhatsApp message for this will be added later.)")
    else:
        print(f"  No special event today ({day}/{month} Hijri).")

    print("─────────────────────────────────────────────────\n")
