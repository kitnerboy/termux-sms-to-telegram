#!/usr/bin/python3

import json
import subprocess
import time
import requests

# --- Telegram Bot Configuration ---
# IMPORTANT: Replace these with your actual Telegram Bot Token and Chat ID.
# You can get a bot token from the "BotFather" bot on Telegram.
# To find your chat ID, send a message to your new bot and then
# go to the following URL in your browser:
# https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
# Look for the "chat":{"id":...} field.
TELEGRAM_BOT_TOKEN = "<YOUT_BOT_TOKEN>"
TELEGRAM_CHAT_ID = "<CHAT_ID_TO_SEND_MESSAGES_TO>"

# --- System Command Configuration ---
CONFIG_DIR="/data/data/com.termux/files/home/.sms2tg"
# File to store the list of filtered addresses.
FILTERED_ADDRESSES_FILE = f"{CONFIG_DIR}/filtered_addresses.json"
# File to store the single last processed message ID.
LAST_PROCESSED_ID_FILE = f"{CONFIG_DIR}/last_processed_id.json"
# The command to execute to get messages.
GET_MESSAGES_COMMAND = ["termux-sms-list"]
# How often to check for new messages in seconds.
CHECK_INTERVAL_SECONDS = 5

# A variable to store the last processed message ID.
# It is loaded from the file on startup.
last_processed_id = -1

# --- Telegram API Interaction Functions ---

def send_telegram_message(text, reply_markup=None):
    """
    Sends a message to the specified Telegram chat.
    Optional `reply_markup` can be used to add inline keyboard buttons.
    """
    if TELEGRAM_BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN" or TELEGRAM_CHAT_ID == "YOUR_TELEGRAM_CHAT_ID":
        print("Error: Please configure your Telegram bot token and chat ID.")
        return None

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown",
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
        
    try:
        # Use the `json` parameter to let requests handle serialization and encoding.
        response = requests.post(url, json=payload)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error sending message to Telegram: {e}")
        return None

def get_telegram_updates(offset=None):
    """
    Gets updates from the Telegram API, which includes button presses.
    `offset` is used to get only new updates.
    """
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
    params = {"offset": offset, "timeout": 10}
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching updates from Telegram: {e}")
        return None

# --- Helper Functions ---

def load_filtered_addresses():
    """
    Loads the list of filtered addresses from a JSON file.
    If the file doesn't exist, it returns an empty list.
    """
    try:
        with open(FILTERED_ADDRESSES_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_filtered_addresses(addresses):
    """
    Saves the list of filtered addresses to a JSON file.
    """
    with open(FILTERED_ADDRESSES_FILE, "w") as f:
        json.dump(addresses, f, indent=2)
        
def load_last_processed_id():
    """
    Loads the last processed message ID from a JSON file.
    """
    try:
        with open(LAST_PROCESSED_ID_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return -1

def save_last_processed_id(id_val):
    """
    Saves the current state of the last processed message ID to a JSON file.
    """
    with open(LAST_PROCESSED_ID_FILE, "w") as f:
        json.dump(id_val, f, indent=2)

def get_last_messages():
    """
    Executes the linux command to get messages and returns them as a JSON object.
    Handles potential errors if the command fails to run.
    """
    try:
        result = subprocess.run(
            GET_MESSAGES_COMMAND,
            capture_output=True,
            text=True,
            check=True,
            shell=False
        )
        messages = json.loads(result.stdout)
        return messages
    except (FileNotFoundError, subprocess.CalledProcessError, json.JSONDecodeError) as e:
        print(f"Error executing command or parsing output: {e}")
        return []

def format_message_for_chat(message):
    """
    Formats a message dictionary into a user-friendly string for Markdown.
    Escapes special Markdown characters in the message body.
    """
    address = message.get("address", "Unknown Address")
    received = message.get("received", "Unknown Time")
    body = message.get("body", "No Message Body")

    # Escape special Markdown characters in the message body
    # TODO maybe not all those symbols are necessary to check
    # See: https://core.telegram.org/bots/api#markdownv2-style
    special_chars = ['_', '*', '~', '`', '>', '+', '=', '|']
    escaped_body = body
    for char in special_chars:
        escaped_body = escaped_body.replace(char, f'\\{char}')

    return (
        f"*From:* `{address}`\n"
        f"*Received:* `{received}`\n"
        f"*Message:* {escaped_body}"
    )

def main():
    """
    The main function of the bot. It continuously checks for new messages,
    sends them to Telegram, and listens for filter button presses.
    """
    global last_processed_id
    
    filtered_addresses = set(load_filtered_addresses())
    last_processed_id = load_last_processed_id()
    
    print("Bot started. Messages from the following addresses will be filtered:")
    print(filtered_addresses)
    print(f"\nLast processed message ID loaded: {last_processed_id}")

    telegram_update_offset = None

    while True:
        # 1. Process new system messages
        messages = get_last_messages()
        if messages:
            # Sort messages by ID to ensure we process them in chronological order
            messages.sort(key=lambda m: m.get("_id", -1))
            
            for message in messages:
                message_id = message.get("_id")
                sender_address = message.get("address")

                if not message_id or not sender_address:
                    continue

                # Check if the message is already processed or from a filtered address
                if message_id <= last_processed_id or sender_address in filtered_addresses:
                    continue

                # Process new, unfiltered messages
                formatted_msg = format_message_for_chat(message)
                
                # Create the inline keyboard button with the filter action
                reply_markup = {
                    "inline_keyboard": [
                        [{"text": "🚫 Filter this sender", "callback_data": f"filter:{sender_address}"}]
                    ]
                }
                
                # Send the message and check for success before updating the ID
                response = send_telegram_message(formatted_msg, reply_markup=reply_markup)
                
                if response and response.get("ok"):
                    last_processed_id = message_id
                    save_last_processed_id(last_processed_id)
                else:
                    print(f"Failed to send message with ID {message_id}. Halting processing for this cycle.")
                    break # Stop processing messages for this cycle if a send fails

        # 2. Process Telegram updates (like button presses)
        updates = get_telegram_updates(offset=telegram_update_offset)
        if updates and updates.get("ok"):
            for update in updates.get("result", []):
                telegram_update_offset = update["update_id"] + 1
                
                if "callback_query" in update:
                    callback_query = update["callback_query"]
                    callback_data = callback_query.get("data")
                    
                    if callback_data and callback_data.startswith("filter:"):
                        sender_to_filter = callback_data.split(":")[1]
                        
                        if sender_to_filter not in filtered_addresses:
                            filtered_addresses.add(sender_to_filter)
                            save_filtered_addresses(list(filtered_addresses))
                            print(f"Messages from '{sender_to_filter}' are now being filtered.")
                            
                            # Send a confirmation message to the chat
                            confirmation_text = f"✅ Filtered messages from `{sender_to_filter}`."
                            send_telegram_message(confirmation_text)

        # Wait for the next check cycle.
        time.sleep(CHECK_INTERVAL_SECONDS)

if __name__ == "__main__":
    main()
