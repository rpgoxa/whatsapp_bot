# ============================================================
# index.py - Main entry point  |  WhatsApp Bot Beta v1.0
# ============================================================
# Run this file to start the bot:
#   python index.py
#
# What happens on startup:
#   1. Checks today's Hijri calendar for Islamic events
#   2. Registers weekly / daily scheduled tasks
#   3. Opens Chrome (restores saved session or asks for QR scan)
#   4. Enters the main monitoring loop — forwards prayer times forever

import sys

from bot.calendar  import check_todays_event
from bot.scheduler import setup_schedule, start_schedule_thread
from bot.forwarder import init_driver, open_whatsapp, wait_for_login, monitor_loop


def main():
    print("=" * 56)
    print("  WhatsApp Bot  —  Beta v1.0")
    print("=" * 56 + "\n")

    # ── 1. Hijri calendar check ───────────────────────────────
    print("[1/4] Checking today's Islamic calendar …")
    check_todays_event()

    # ── 2. Scheduler ─────────────────────────────────────────
    print("[2/4] Setting up the scheduler …")
    setup_schedule()
    start_schedule_thread()  # Runs in background — does not block

    # ── 3. Open Chrome + WhatsApp Web ────────────────────────
    print("[3/4] Launching Chrome and opening WhatsApp Web …")
    driver = None
    try:
        driver = init_driver()
        open_whatsapp(driver)
        wait_for_login(driver)

    except RuntimeError as exc:
        print(f"\nFATAL: {exc}")
        if driver:
            driver.quit()
        sys.exit(1)

    except Exception as exc:
        print(f"\nFATAL: Could not start Chrome — {exc}")
        print("Make sure Google Chrome is installed on this computer.")
        if driver:
            driver.quit()
        sys.exit(1)

    # ── 4. Monitoring loop ────────────────────────────────────
    print("[4/4] Entering monitoring loop …")
    try:
        monitor_loop(driver)        # Runs forever until Ctrl+C

    except KeyboardInterrupt:
        print("\n\nCtrl+C — shutting down …")

    finally:
        if driver:
            print("Closing Chrome …")
            driver.quit()
        print("Bot stopped. Goodbye!")


if __name__ == "__main__":
    main()
