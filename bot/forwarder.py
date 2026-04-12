# ============================================================
# bot/forwarder.py - WhatsApp Bot using Green API
# ============================================================
# Handles all communication with WhatsApp via Green API HTTP endpoints.
# This replaces the old Selenium/Chrome implementation.

import time
import requests
import json
import config

# Track already forwarded messages to prevent duplicates.
# We store the `idMessage` strings here.
_seen_message_ids = set()

def _get_api_url(method: str) -> str:
    """Helper to construct the Green API endpoint URL."""
    if not config.INSTANCE_ID or not config.API_TOKEN:
        raise ValueError("INSTANCE_ID or API_TOKEN is missing in config.py")
    
    # Use API_URL from config if available, fallback to default
    base_url = getattr(config, "API_URL", "https://api.green-api.com").rstrip("/")
    return f"{base_url}/waInstance{config.INSTANCE_ID}/{method}/{config.API_TOKEN}"

# ============================================================
# 1. Finding Chat IDs
# ============================================================

def get_chats() -> list:
    """
    Calls GET /getChats to fetch all chats for this instance.
    Returns a list of dicts: [{"id": "...", "name": "..."}, ...]
    """
    url = _get_api_url("getChats")
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        return response.json()
    except Exception as exc:
        print(f"  [API Error] Could not fetch chats: {exc}")
        return []

def get_group_id_by_name(group_name: str) -> str:
    """
    Finds the chatId for a given exact group name.
    """
    if not group_name:
        return ""
    chats = get_chats()
    for chat in chats:
        if chat.get("name") == group_name:
            return chat.get("id")
    return ""

def init_green_api():
    """
    Called on startup. Finds and returns the source and destination chat IDs.
    Returns: (source_chat_id, dest_chat_id)
    """
    print("\nConnecting to Green API to find groups...")
    src_id = get_group_id_by_name(config.SOURCE_GROUP_NAME)
    dest_id = get_group_id_by_name(config.DESTINATION_GROUP_NAME)
    
    if not src_id:
        print(f"  [WARNING] Source group not found: {config.SOURCE_GROUP_NAME}")
    else:
        print(f"  Source group found: {config.SOURCE_GROUP_NAME}")
        
    if not dest_id:
        print(f"  [WARNING] Destination group not found: {config.DESTINATION_GROUP_NAME}")
    else:
        print(f"  Destination group found: {config.DESTINATION_GROUP_NAME}")
        
    return src_id, dest_id

# ============================================================
# 2. Reading Messages
# ============================================================

def get_recent_messages(chat_id: str, count: int = 10) -> list:
    """
    Calls POST /getChatHistory to pull the last `count` messages.
    Returns a list of messages.
    """
    if not chat_id:
        return []
        
    url = _get_api_url("getChatHistory")
    payload = {
        "chatId": chat_id,
        "count": count
    }
    headers = {'Content-Type': 'application/json'}
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as exc:
        print(f"  [API Error] Could not fetch messages: {exc}")
        return []

# ============================================================
# 3. Sending Messages & Media
# ============================================================

def send_image(chat_id: str, url_file: str, caption: str = "") -> bool:
    """
    Calls POST /sendFileByUrl to send an image.
    """
    url = _get_api_url("sendFileByUrl")
    payload = {
        "chatId": chat_id,
        "urlFile": url_file,
        "fileName": "prayer_times.jpg",
        "caption": caption
    }
    headers = {'Content-Type': 'application/json'}
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        response.raise_for_status()
        return True
    except Exception as exc:
        print(f"  [API Error] Could not send image: {exc}")
        return False

def send_text_message(chat_id: str, text: str) -> bool:
    """
    Calls POST /sendMessage to send a text message.
    """
    url = _get_api_url("sendMessage")
    payload = {
        "chatId": chat_id,
        "message": text
    }
    headers = {'Content-Type': 'application/json'}
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        response.raise_for_status()
        return True
    except Exception as exc:
        print(f"  [API Error] Could not send text message: {exc}")
        return False

# ============================================================
# 4. Polling & Forwarding Logic
# ============================================================

def check_source_group(src_id: str, dest_id: str) -> None:
    """
    Polls the source group for new prayer-times messages.
    If found, forwards the image first, then the text to the destination group.
    """
    if not src_id or not dest_id:
        return
        
    messages = get_recent_messages(src_id, count=10)
    forwarded = 0
    
    for msg in messages:
        msg_id = msg.get("idMessage")
        if not msg_id or msg_id in _seen_message_ids:
            continue
            
        # Extract text based on Green API message types
        # textMessage -> textMessage
        # extendedTextMessage -> text
        # imageMessage -> caption
        text = ""
        msg_type = msg.get("typeMessage")
        
        if msg_type == "textMessage":
            text = msg.get("textMessage", "")
        elif msg_type == "extendedTextMessage":
            text = msg.get("extendedTextMessage", {}).get("text", "")
        elif msg_type == "imageMessage":
            text = msg.get("imageMessage", {}).get("caption", "")

        # Always mark as seen once processed
        _seen_message_ids.add(msg_id)
        
        if config.PRAYER_KEYWORD not in text:
            continue
            
        print(f"  *** PRAYER TIMES FOUND (ID: {msg_id}) ***")
        
        overall_success = True
        
        # Check if the message contains an image URL we can download and forward.
        # Green API usually provides a downloadUrl for attachments.
        image_data = msg.get("imageMessage", {})
        download_url = msg.get("downloadUrl", "")
        if msg_type == "imageMessage" and image_data:
            # Note: Green API downloadUrls might be deprecated or different depending on plan, 
            # but per instructions, we check for downloadUrl on the message.
            if download_url:
                print("  Step 1/2: Sending image ...")
                img_ok = send_image(dest_id, download_url, caption="")
                if not img_ok:
                    print("  Image send failed - will still attempt to send text.")
                    overall_success = False
            else:
                print("  Step 1/2: Image found but no downloadUrl available.")
        else:
            print("  Step 1/2: No image in this message - skipping.")
            
        # Send text if it's there
        if text:
            print("  Step 2/2: Sending text ...")
            txt_ok = send_text_message(dest_id, text)
            if not txt_ok:
                overall_success = False
        else:
            print("  Step 2/2: No text content - skipping.")
            
        if overall_success:
             print("  Forward complete!\n")
        else:
             print("  Forward finished with one or more errors.\n")
             
        forwarded += 1
        
    if forwarded == 0:
        pass # Optional: print("No new target messages found")

def monitor_loop(src_id: str, dest_id: str) -> None:
    """
    Runs forever, checking the source group every POLL_INTERVAL seconds.
    """
    print("\n" + "=" * 56)
    print("  Bot is running — monitoring via Green API.")
    print(f"  Scan interval : {config.POLL_INTERVAL} s")
    print("  Press Ctrl+C to stop.")
    print("=" * 56 + "\n")

    while True:
        try:
            check_source_group(src_id, dest_id)
        except KeyboardInterrupt:
            raise
        except Exception as exc:
            print(f"\n  [monitor_loop] Error: {exc}")
            print("  Recovering — will retry on next scan …\n")
            
        time.sleep(config.POLL_INTERVAL)
