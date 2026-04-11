# ============================================================
# get_groups.py - Helper: list all WhatsApp group names
# ============================================================
# Run this ONCE to discover your group names:
#   python get_groups.py
#
# Output example:
#   1. Family Chat
#   2. Work Team
#
# Copy the exact names you need into SOURCE_GROUP_NAME and
# DESTINATION_GROUP_NAME in config.py.

import time

from selenium.webdriver.common.by import By

from bot.forwarder import init_driver, open_whatsapp, wait_for_login


def scroll_chat_list(driver, panel_selector: str, steps: int = 20) -> None:
    """
    Scrolls the chat list downward to force WhatsApp to load more items.
    WhatsApp uses lazy / virtual scrolling, so chats only appear when visible.
    """
    try:
        panel = driver.find_element(By.CSS_SELECTOR, panel_selector)
        for i in range(steps):
            driver.execute_script("arguments[0].scrollTop += 600", panel)
            time.sleep(0.7)
            print(f"  Scrolling … ({i + 1}/{steps})", end="\r")
        print()  # Newline after progress line
    except Exception as exc:
        print(f"\n  (Could not scroll chat list: {exc})")


def collect_visible_chats(driver) -> dict:
    """
    Scrapes all currently rendered chat rows from the sidebar.
    Returns dict of chat_name → chat_name.
    (WhatsApp Web removed data-id attributes, so we can only get exact names)
    """
    chats = {}

    # WhatsApp Web chatlist items are now standard div[role="row"]
    for el in driver.find_elements(By.CSS_SELECTOR, "div[role='row']"):
        try:
            # Look for the span that holds the title string
            title_el = el.find_element(By.CSS_SELECTOR, "span[title]")
            title = title_el.get_attribute("title")
            if title:
                chats[title] = title
        except Exception:
            continue

    return chats


def print_results(chats: dict) -> None:
    """Prints a clean numbered list of discovered chats."""
    # Without data-id, we cannot filter out individual contacts from groups securely,
    # so we print all identified chats.
    groups = sorted(
        [(name, cid) for cid, name in chats.items()],
        key=lambda x: x[0].lower(),
    )

    if not groups:
        print("\n  No chats found. Try running the script again.\n")
        return

    print("\n" + "=" * 56)
    print("  Copy the EXACT names below into config.py")
    print("=" * 56)

    for idx, (name, _) in enumerate(groups, start=1):
        # Safely print names containing emojis on Windows terminals
        safe_name = name.encode('ascii', 'ignore').decode('ascii') if name else "Unknown"
        if not safe_name.strip():
            safe_name = "[Emoji Only Name]"
        print(f"  {idx:>3}. {safe_name}")
    print("=" * 56)
    print(f"\n  Total: {len(groups)} chats found\n")


def main():
    print("=" * 56)
    print("  WhatsApp Group Name Finder")
    print("=" * 56 + "\n")

    print("[1/4] Starting Chrome …")
    driver = init_driver()

    print("[2/4] Opening WhatsApp Web …")
    open_whatsapp(driver)
    try:
        wait_for_login(driver)
    except RuntimeError as exc:
        print(f"\nFATAL: {exc}")
        driver.quit()
        return

    print("[3/4] Collecting groups (scrolling through chat list) …")

    # Detect the scrollable sidebar panel.
    panel_selector = "#pane-side"
    for sel in ["#pane-side", '[data-testid="chat-list"]']:
        try:
            driver.find_element(By.CSS_SELECTOR, sel)
            panel_selector = sel
            break
        except Exception:
            continue

    # First pass — collect whatever is already loaded.
    all_chats = collect_visible_chats(driver)
    print(f"  Found {len(all_chats)} chats before scrolling …")

    # Scroll to reveal lazy-loaded chats, then collect again.
    scroll_chat_list(driver, panel_selector, steps=20)
    all_chats.update(collect_visible_chats(driver))
    print(f"  Total after scrolling: {len(all_chats)} chats")

    print("[4/4] Closing browser …")
    driver.quit()

    print_results(all_chats)


if __name__ == "__main__":
    main()
