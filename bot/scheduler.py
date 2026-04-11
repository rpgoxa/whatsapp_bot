# ============================================================
# bot/scheduler.py - Daily and weekly task scheduling
# ============================================================
# Registers all timed tasks (duas, calendar check) and runs
# them in a background thread so the main bot loop is not blocked.

import time      # Built-in: time.sleep()
import threading # Built-in: daemon background thread

import schedule  # pip install schedule

# Relative import — calendar.py lives in the same bot/ package.
from .calendar import check_todays_event


# ============================================================
# Task functions
# ============================================================

def task_dua_kumayl():
    """Fires every Thursday at 20:00."""
    print("\n" + "═" * 50)
    print("  *** THURSDAY NIGHT — DUA KUMAYL REMINDER ***")
    print("  Should send Dua Kumayl to the group.")
    print("  (Actual sending will be added in a future update.)")
    print("═" * 50 + "\n")


def task_dua_tawassul():
    """Fires every Tuesday at 20:00."""
    print("\n" + "═" * 50)
    print("  *** TUESDAY NIGHT — DUA TAWASSUL REMINDER ***")
    print("  Should send Dua Tawassul to the group.")
    print("  (Actual sending will be added in a future update.)")
    print("═" * 50 + "\n")


def task_daily_hijri_check():
    """Fires every day at 00:01 — re-checks the Hijri calendar."""
    print("\n[Scheduler] Running daily Hijri calendar check …")
    check_todays_event()


# ============================================================
# Setup
# ============================================================

def setup_schedule():
    """
    Registers all scheduled jobs.
    Call this ONCE at startup before starting the background thread.
    """
    print("Setting up scheduled tasks …")

    # Daily at one minute past midnight: Hijri calendar check.
    schedule.every().day.at("00:01").do(task_daily_hijri_check)
    print("  Scheduled: daily Hijri check at 00:01")

    # Every Thursday at 8 PM: Dua Kumayl.
    schedule.every().thursday.at("20:00").do(task_dua_kumayl)
    print("  Scheduled: Thursday 20:00 — Dua Kumayl reminder")

    # Every Tuesday at 8 PM: Dua Tawassul.
    schedule.every().tuesday.at("20:00").do(task_dua_tawassul)
    print("  Scheduled: Tuesday 20:00 — Dua Tawassul reminder")

    print("All tasks registered.\n")


# ============================================================
# Background thread
# ============================================================

def _schedule_loop():
    """
    Runs in a background thread — checks every 30 seconds whether
    any scheduled job is due and fires it.
    """
    print("[Scheduler] Background thread running.")
    while True:
        schedule.run_pending()  # Fire any job whose time has come
        time.sleep(30)          # No need to check more than twice a minute


def start_schedule_thread():
    """
    Launches _schedule_loop() as a daemon thread.
    A daemon thread dies automatically when the main program exits.
    """
    thread = threading.Thread(
        target=_schedule_loop,
        name="ScheduleThread",
        daemon=True
    )
    thread.start()
    print("[Scheduler] Background thread started.\n")
    return thread
