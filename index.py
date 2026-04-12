# ============================================================
# index.py - Main entry point  |  WhatsApp Bot Beta v2.0
# ============================================================
# Run this file to start the bot:
#   python index.py
#
# What happens on startup:
#   1. Checks today's Hijri calendar for Islamic events
#   2. Registers weekly / daily scheduled tasks
#   3. Connects to Green API to map group names to chat IDs
#   4. Enters the main monitoring loop — polls for prayer times
#
# Remember to fill config.py with your INSTANCE_ID and API_TOKEN!

import sys

from bot.calendar  import check_todays_event
from bot.scheduler import setup_schedule, start_schedule_thread
from bot.forwarder import init_green_api, monitor_loop

def main():
    print("=" * 56)
    print("  WhatsApp Bot  —  Beta v2.0")
    print("=" * 56 + "\n")

    # ── 1. Hijri calendar check ───────────────────────────────
    print("[1/4] Checking today's Islamic calendar …")
    check_todays_event()

    # ── 2. Scheduler ─────────────────────────────────────────
    print("[2/4] Setting up the scheduler …")
    setup_schedule()
    start_schedule_thread()  # Runs in background — does not block

    # ── 3. Connect to Green API & Map IDs ────────────────────────
    print("[3/4] Connecting to Green API …")
    try:
        src_id, dest_id = init_green_api()
        if not src_id or not dest_id:
            print("\nError: Could not find one or both groups.")
            print("Make sure your INSTANCE_ID and API_TOKEN are correct,")
            print("and that the exact group names are in config.py.")
            sys.exit(1)
    except Exception as exc:
        print(f"\nFATAL: API Initialization failed — {exc}")
        sys.exit(1)

    # ── 4. Monitoring loop ────────────────────────────────────
    print("[4/4] Entering polling loop …")
    try:
        monitor_loop(src_id, dest_id)        # Runs forever until Ctrl+C

    except KeyboardInterrupt:
        print("\n\nCtrl+C — shutting down …")

    finally:
        print("Bot stopped. Goodbye!")

if __name__ == "__main__":
    main()
