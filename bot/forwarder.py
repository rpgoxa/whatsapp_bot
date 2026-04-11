# ============================================================
# bot/forwarder.py - WhatsApp Web automation with Selenium
# ============================================================
# Handles everything browser-related:
#   • Opening Chrome with a saved session (no QR re-scan after first run)
#   • Waiting for WhatsApp Web to finish loading
#   • Scanning the source group for the prayer-times keyword
#   • Forwarding matching messages to the destination group

import os        # Built-in: path manipulation, folder creation
import re        # Built-in: regex — used to parse MIME type from base64 header
import base64    # Built-in: decode the base64 image data returned by JavaScript
import hashlib   # Built-in: stable content-based message IDs (data-id is gone)
import tempfile  # Built-in: create a temporary file to store the downloaded image
import time      # Built-in: time.sleep()

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager  # Auto-installs ChromeDriver

# config.py lives at the project root — Python finds it because the root
# directory is on sys.path when you run "python index.py" from there.
import config

# ── Message ID tracking ─────────────────────────────────────
# Store IDs of messages we have already processed so we never
# forward the same message twice, even across multiple scans.
_seen_message_ids: set = set()


# ============================================================
# 1. Driver initialisation
# ============================================================

def init_driver() -> webdriver.Chrome:
    """
    Creates and returns a Chrome WebDriver instance.

    The --user-data-dir option saves Chrome's login state to ./session/
    so WhatsApp stays logged in between bot restarts — QR only once.
    """
    print("Starting Chrome browser …")

    # Build an absolute path to the session folder so it always resolves
    # relative to the project root, not whatever the current directory is.
    session_path = os.path.abspath(config.SESSION_FOLDER)
    os.makedirs(session_path, exist_ok=True)
    print(f"  Session folder: {session_path}")

    options = Options()
    options.add_argument(f"--user-data-dir={session_path}")   # Persist login
    options.add_argument("--profile-directory=Default")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-notifications")           # No desktop alerts
    options.add_argument("--log-level=3")                     # Quiet log output
    options.add_argument("--silent")
    # Hide the "Chrome is controlled by automated software" info bar.
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    # webdriver_manager downloads the ChromeDriver that matches your Chrome.
    service = Service(ChromeDriverManager().install())
    driver  = webdriver.Chrome(service=service, options=options)

    print("Chrome started.\n")
    return driver


# ============================================================
# 2. Loading WhatsApp Web
# ============================================================

def open_whatsapp(driver: webdriver.Chrome) -> None:
    """Navigates Chrome to WhatsApp Web."""
    print(f"Opening {config.WHATSAPP_WEB_URL} …")
    driver.get(config.WHATSAPP_WEB_URL)


def wait_for_login(driver: webdriver.Chrome) -> None:
    """
    Blocks until the WhatsApp sidebar is visible (= user is logged in).

    First run: WhatsApp shows a QR code — scan it with your phone via
               WhatsApp → Linked Devices → Link a Device.
    Later runs: the saved session restores login automatically.
    """
    print("\n" + "=" * 56)
    print("  Waiting for WhatsApp Web to load …")
    print("  FIRST TIME?  Scan the QR code with your phone.")
    print("  RETURNING?   Session will restore automatically.")
    print(f"  Timeout: {config.PAGE_LOAD_TIMEOUT} seconds")
    print("=" * 56)

    try:
        # '#side' is the left sidebar — it only appears after a successful login.
        WebDriverWait(driver, config.PAGE_LOAD_TIMEOUT).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#side"))
        )
        print("\nLogged in successfully!")
        print("Waiting 4 s for chats to finish loading …")
        time.sleep(4)

    except Exception:
        raise RuntimeError(
            f"WhatsApp Web did not load within {config.PAGE_LOAD_TIMEOUT} s. "
            "Check your internet connection and try again."
        )


# ============================================================
# 3. Chat navigation
# ============================================================

def open_chat_by_name(driver: webdriver.Chrome, chat_name: str) -> bool:
    """
    Clicks on the chat whose title matches chat_name in the sidebar.

    chat_name must be the exact display name of the group or contact
    as it appears in WhatsApp (e.g. 'Prayer Times Group').

    Returns True on success, False if the chat was not found.
    """
    if not chat_name:
        print("  open_chat_by_name: chat_name is empty — skipping.")
        return False

    print(f"  Opening chat: {chat_name}")
    try:
        # Match the sidebar span whose title attribute equals the group name.
        # WhatsApp Web renders each chat row with a <span title="Group Name">.
        el = WebDriverWait(driver, config.ELEMENT_TIMEOUT).until(
            EC.presence_of_element_located(
                (By.XPATH, f"//span[@title='{chat_name}']")
            )
        )
        el.click()
        time.sleep(2)  # Wait for the chat panel to open
        print("  Chat opened.")
        return True

    except Exception as exc:
        print(f"  Could not open chat '{chat_name}': {exc}")
        print("  Tip: verify the name matches exactly (including spaces and Arabic text).")
        return False


# ============================================================
# 4. Reading messages
# ============================================================

def get_recent_messages(driver: webdriver.Chrome, count: int = 10) -> list:
    """
    Returns the last `count` messages from the currently open chat.

    Each message is a dict:
        {
            'id'       : str         — stable content-based hash used for dedup
            'text'     : str         — plain text (empty for media-only msgs)
            'has_image': bool        — True if the message has an inline image
            'element'  : WebElement  — raw Selenium element (for future use)
        }
    """
    messages = []

    try:
        # WhatsApp Web renders each message bubble as div[role="row"].
        # data-id attributes were removed from the DOM, so we rely on
        # this ARIA role to locate message bubbles instead.
        all_els = driver.find_elements(By.CSS_SELECTOR, 'div[role="row"]')
        recent  = all_els[-count:] if len(all_els) > count else all_els

        for el in recent:
            try:
                # ── Text ─────────────────────────────────────
                text = ""
                try:
                    spans = el.find_elements(
                        By.CSS_SELECTOR, "span.selectable-text"
                    )
                    text = " ".join(s.text for s in spans if s.text).strip()
                except Exception:
                    pass

                # ── Image detection ───────────────────────────
                has_image = False
                try:
                    imgs      = el.find_elements(
                        By.CSS_SELECTOR, 'img[src^="blob:"]'
                    )
                    has_image = len(imgs) > 0
                except Exception:
                    pass

                # ── Stable ID from content ────────────────────
                # data-id is no longer present in the DOM, so we derive a
                # deduplication key from the message content.  MD5 is fast
                # and collision-free enough for a chat-bot use case.
                raw    = f"{text}|{has_image}"
                msg_id = hashlib.md5(raw.encode()).hexdigest()

                messages.append({
                    "id":        msg_id,
                    "text":      text,
                    "has_image": has_image,
                    "element":   el,
                })

            except Exception:
                continue

    except Exception as exc:
        print(f"  Error reading messages: {exc}")

    return messages


# ============================================================
# 5. Image download
# ============================================================

def download_image_from_message(driver: webdriver.Chrome, msg_element) -> str | None:
    """
    Downloads the image attached to a WhatsApp message and saves it to a
    temporary file on disk.

    IMPORTANT: call this while the source group is still open in the browser.
    Once you navigate to another chat the message element becomes stale and
    the blob URL is no longer accessible.

    How it works:
        WhatsApp Web loads images as blob: URLs — short-lived in-browser URLs
        that point to raw bytes stored in memory.  We cannot fetch these with
        the requests library (they only exist inside the browser process), so
        we use JavaScript inside Chrome to read the blob and hand us back the
        raw bytes encoded as base64.  We then decode and write to a temp file.

    Returns:
        str  — absolute path to the downloaded temp file  (e.g. C:/tmp/wa_prayer_xxxx.jpg)
        None — if the image could not be downloaded for any reason
    """
    try:
        # Find the <img> element whose src starts with "blob:" inside this message bubble.
        img_el   = msg_element.find_element(By.CSS_SELECTOR, 'img[src^="blob:"]')
        blob_url = img_el.get_attribute("src")

        if not blob_url:
            print("  Image element found but src is empty — skipping image.")
            return None

        print(f"  Image blob URL found: {blob_url[:70]}…")
        print("  Downloading image via JavaScript …")

        # Give the async JavaScript up to 30 seconds to complete.
        driver.set_script_timeout(30)

        # JavaScript explanation:
        #   arguments[0]                  → the blob URL we pass in
        #   arguments[arguments.length-1] → Selenium's auto-injected async callback
        #
        #   fetch()        downloads the blob as a Blob object
        #   FileReader     converts the Blob to a base64 data-URL string
        #   callback(...)  hands the result back to Python
        js_blob_to_base64 = """
        var blobUrl  = arguments[0];
        var callback = arguments[arguments.length - 1];

        fetch(blobUrl)
            .then(function(response) { return response.blob(); })
            .then(function(blob) {
                var reader = new FileReader();
                reader.onloadend = function() { callback(reader.result); };
                reader.onerror   = function() { callback(null); };
                reader.readAsDataURL(blob);
            })
            .catch(function(err) { callback(null); });
        """

        # execute_async_script blocks Python until callback() is called in JS.
        b64_result = driver.execute_async_script(js_blob_to_base64, blob_url)

        if not b64_result:
            print("  JavaScript returned no data — image download failed.")
            return None

        # b64_result looks like:  "data:image/jpeg;base64,/9j/4AAQ..."
        # Split into the header ("data:image/jpeg;base64") and the raw base64 payload.
        if "," not in b64_result:
            print("  Unexpected base64 format — cannot parse image data.")
            return None

        header, raw_b64 = b64_result.split(",", 1)

        # Extract the image format from the MIME type in the header.
        # e.g. "data:image/jpeg;base64"  →  ext = "jpg"
        mime_match = re.search(r"data:image/(\w+);", header)
        ext = mime_match.group(1) if mime_match else "jpg"
        if ext.lower() == "jpeg":
            ext = "jpg"

        # Decode base64 string → raw bytes.
        img_bytes = base64.b64decode(raw_b64)

        # Write bytes to a named temporary file so we can pass the path to Selenium.
        # delete=False means the file stays on disk after we close it; we remove it
        # manually after the image has been sent.
        tmp = tempfile.NamedTemporaryFile(
            suffix=f".{ext}",
            prefix="wa_prayer_",
            delete=False,
        )
        tmp.write(img_bytes)
        tmp.close()

        print(f"  Image saved to temp file: {tmp.name}  ({len(img_bytes):,} bytes)")
        return tmp.name

    except Exception as exc:
        print(f"  Could not download image: {exc}")
        return None


# ============================================================
# 6. Sending an image
# ============================================================

def send_image_to_current_chat(driver: webdriver.Chrome, image_path: str) -> bool:
    """
    Attaches a local image file to the currently open chat and sends it.

    How it works:
        WhatsApp Web has a hidden <input type="file"> element in the DOM.
        Calling send_keys() on it with a file path is the standard Selenium
        way to upload files without needing to interact with the OS file dialog.
        After the file is selected, WhatsApp shows a preview — we then click
        the send button in that preview to dispatch the message.

    Returns True on success, False on failure.
    """
    abs_path = os.path.abspath(image_path)
    print(f"  Attaching image: {abs_path}")

    try:
        # ── Step 1: Find a file input that accepts images ─────────────────────
        # WhatsApp Web embeds multiple hidden <input type="file"> elements.
        # We want the one whose 'accept' attribute includes 'image'.
        file_inputs  = driver.find_elements(By.CSS_SELECTOR, 'input[type="file"]')
        target_input = None

        for inp in file_inputs:
            accept = (inp.get_attribute("accept") or "").lower()
            if "image" in accept:
                target_input = inp
                break

        # Fallback A: no image-specific input found — try clicking the attach
        # button first, which may reveal the inputs in the DOM.
        if not target_input:
            print("  No image file-input visible yet — clicking attach button …")
            for selector in [
                '[data-testid="clip"]',     # WhatsApp Web (most versions)
                '[data-testid="attach"]',   # Alternative selector
                '[title="Attach"]',         # Fallback by title attribute
            ]:
                try:
                    driver.find_element(By.CSS_SELECTOR, selector).click()
                    time.sleep(1)  # Wait for the attach menu to open
                    break
                except Exception:
                    continue

            # Search again after the menu is open.
            file_inputs = driver.find_elements(By.CSS_SELECTOR, 'input[type="file"]')
            for inp in file_inputs:
                accept = (inp.get_attribute("accept") or "").lower()
                if "image" in accept:
                    target_input = inp
                    break

        # Fallback B: accept any file input we can find.
        if not target_input and file_inputs:
            print("  Using first available file input as last resort …")
            target_input = file_inputs[0]

        if not target_input:
            print("  ERROR: No file input element found in WhatsApp Web.")
            print("  WhatsApp may have updated its layout — check bot/forwarder.py.")
            return False

        # ── Step 2: Hand the file path to the input ───────────────────────────
        # send_keys() on a file input triggers WhatsApp to load the image and
        # show a preview dialog — no OS dialog appears.
        target_input.send_keys(abs_path)
        print("  File path delivered to input. Waiting for preview dialog …")
        time.sleep(3)  # WhatsApp needs a moment to render the image preview

        # ── Step 3: Click the send button in the preview dialog ───────────────
        # The send button inside the media-preview modal has the same
        # data-testid="send" as the regular message send button.
        send_btn = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, '[data-testid="send"]')
            )
        )
        send_btn.click()
        time.sleep(2)  # Wait for the send animation / upload to complete

        print("  Image sent successfully!")
        return True

    except Exception as exc:
        print(f"  Failed to send image: {exc}")
        return False


# ============================================================
# 7. Sending a text message
# ============================================================

def send_text_message(driver: webdriver.Chrome, text: str) -> bool:
    """
    Types `text` into the compose box of the current chat and presses Enter.
    Returns True on success, False on failure.
    """
    try:
        # data-testid selectors are more stable than CSS class names because
        # WhatsApp frequently renames its internal CSS classes after updates.
        input_box = WebDriverWait(driver, config.ELEMENT_TIMEOUT).until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR,
                 '[data-testid="conversation-compose-box-input"]')
            )
        )
        input_box.click()
        time.sleep(0.3)
        input_box.send_keys(text)
        time.sleep(0.3)
        input_box.send_keys(Keys.ENTER)
        time.sleep(1)

        preview = text[:60] + ("…" if len(text) > 60 else "")
        print(f"  Sent: {preview}")
        return True

    except Exception as exc:
        print(f"  Failed to send message: {exc}")
        return False


# ============================================================
# 8. Forwarding a matched message (image first, then text)
# ============================================================

def forward_to_destination(
    driver: webdriver.Chrome,
    message: dict,
    image_path: str | None = None,
) -> bool:
    """
    Forwards a matched prayer-times message to DESTINATION_GROUP_NAME.

    Sending order — mirrors the original message layout:
        1. Image  (if one was downloaded and image_path is not None)
        2. Text

    Parameters:
        driver     — the active Chrome WebDriver
        message    — dict from get_recent_messages() with 'text', 'has_image', etc.
        image_path — absolute path to a locally saved image file, or None
    """
    dest = config.DESTINATION_GROUP_NAME
    print(f"\n  Forwarding to destination group: {dest}")

    # Open the destination group — this navigates away from the source group,
    # which is why the image must already be downloaded before calling this.
    if not open_chat_by_name(driver, dest):
        print("  ERROR: Cannot open destination group.")
        print("  Check DESTINATION_GROUP_NAME in config.py")
        return False

    time.sleep(2)

    overall_success = True

    # ── 1. Send the image first ───────────────────────────────────────────────
    if image_path:
        print("  Step 1/2: Sending image …")
        img_ok = send_image_to_current_chat(driver, image_path)
        if not img_ok:
            print("  Image send failed — will still attempt to send text.")
            overall_success = False
    else:
        if message["has_image"]:
            # has_image was True but we never got a file (download failed earlier)
            print("  Step 1/2: Image download had failed — skipping image send.")
        else:
            print("  Step 1/2: No image in this message — skipping.")

    # ── 2. Send the text ──────────────────────────────────────────────────────
    if message["text"]:
        print("  Step 2/2: Sending text …")
        txt_ok = send_text_message(driver, message["text"])
        if not txt_ok:
            overall_success = False
    else:
        print("  Step 2/2: No text content — skipping.")

    if overall_success:
        print("  Forward complete!\n")
    else:
        print("  Forward finished with one or more errors — check logs above.\n")

    return overall_success


# ============================================================
# 9. Core scan: check source group for the prayer keyword
# ============================================================

def check_source_group(driver: webdriver.Chrome) -> None:
    """
    Opens the source group, reads recent messages, and forwards any that
    contain PRAYER_KEYWORD to the destination group.

    Flow for each matching message:
        1. Download the image NOW — while we are still in the source group.
           The blob: URL becomes invalid as soon as we navigate away.
        2. Call forward_to_destination(), which opens the destination group
           and sends the image (step 1) then the text (step 2).
        3. Delete the temporary image file from disk.

    Already-forwarded message IDs are tracked in _seen_message_ids to
    ensure each message is forwarded at most once per bot session.
    """
    global _seen_message_ids

    src  = config.SOURCE_GROUP_NAME
    dest = config.DESTINATION_GROUP_NAME

    if not src or not dest:
        print("\n  WARNING: SOURCE_GROUP_NAME or DESTINATION_GROUP_NAME is empty in config.py")
        print("  Set both group names (exactly as they appear in WhatsApp) then restart.\n")
        return

    print(f"\nScanning source group …  ({src})")

    if not open_chat_by_name(driver, src):
        print("  Could not open source group. Skipping this scan.")
        return

    messages = get_recent_messages(driver, count=config.MESSAGES_TO_CHECK)
    print(f"  Loaded {len(messages)} messages to check.")

    forwarded = 0
    for msg in messages:
        if msg["id"] in _seen_message_ids:
            continue

        # Mark as seen immediately — whether it matches or not — so we never
        # re-process this message ID on the next scan.
        _seen_message_ids.add(msg["id"])

        if config.PRAYER_KEYWORD not in msg["text"]:
            continue  # Not the prayer-times message — move on

        print(f"  *** PRAYER TIMES FOUND (ID: {msg['id']}) ***")

        # ── Download the image BEFORE navigating away ─────────────────────
        # The blob: URL only lives in this browser tab.  If there is no image
        # (has_image is False) this returns None immediately.
        image_path = None
        if msg["has_image"]:
            print("  Message has an image — downloading it now …")
            image_path = download_image_from_message(driver, msg["element"])
        else:
            print("  Message has no image — text-only forward.")

        # ── Forward (navigates to destination group) ──────────────────────
        try:
            forward_to_destination(driver, msg, image_path=image_path)
            forwarded += 1
        finally:
            # ── Clean up the temp file regardless of success or failure ───
            if image_path and os.path.exists(image_path):
                os.remove(image_path)
                print(f"  Temp image file deleted: {image_path}")

    if forwarded == 0:
        print("  No new prayer-times messages this scan.")


# ============================================================
# 10. Main monitoring loop
# ============================================================

def monitor_loop(driver: webdriver.Chrome) -> None:
    """
    Runs forever, calling check_source_group() every CHECK_INTERVAL_SECONDS.
    Only exits when the user presses Ctrl+C.
    """
    print("\n" + "=" * 56)
    print("  Bot is running — monitoring for prayer times.")
    print(f"  Scan interval : {config.CHECK_INTERVAL_SECONDS} s")
    print(f"  Source group  : {config.SOURCE_GROUP_NAME  or '⚠  NOT SET'}")
    print(f"  Dest group    : {config.DESTINATION_GROUP_NAME or '⚠  NOT SET'}")
    print("  Press Ctrl+C to stop.")
    print("=" * 56 + "\n")

    while True:
        try:
            check_source_group(driver)
        except KeyboardInterrupt:
            raise  # Propagate so main() can exit cleanly
        except Exception as exc:
            print(f"\n  [monitor_loop] Error: {exc}")
            print("  Recovering — will retry on next scan …\n")

        print(f"  Next scan in {config.CHECK_INTERVAL_SECONDS} s …")
        time.sleep(config.CHECK_INTERVAL_SECONDS)
