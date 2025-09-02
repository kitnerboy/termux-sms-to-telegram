# Termux SMS to Telegram

Readme is written with google gemini, sorry.

## Description

This shell script (`sms2tg.sh`) is designed to run on Termux, an Android terminal emulator, and forward incoming SMS messages to a Telegram chat.  It is intended to be placed in the `~/.termux/boot` directory so that it starts automatically when Termux is launched (specifically, when launched via termux-boot, which is a separate add-on).

## Prerequisites

* **Termux:** Install Termux from F-Droid (recommended) or the Google Play Store.
* **Termux-boot:** Install the Termux-boot add-on from the Termux repository.  This add-on allows scripts in `~/.termux/boot` to be executed on device boot.
* **Termux Permissions:** Grant Termux the necessary permissions to access SMS messages.  You'll likely need to run `termux-setup-storage` and then grant SMS permissions.
* **Telegram Bot:**
    * Create a Telegram bot using BotFather.  You will need the bot's token.
    * Obtain the chat ID of the Telegram chat where you want to receive the SMS messages.  You can use a bot like [@userinfobot](https://t.me/userinfobot) to get this ID.

## Installation

1.  **Install Prerequisites:** Follow the steps above to install Termux and Termux-boot.  Ensure Termux has SMS permissions.
2.  **Create the Script Directory:** If it doesn't exist, create the `~/.termux/boot` directory:

    ```bash
    mkdir -p ~/.termux/boot
    ```

3.  **Save the Script:**
    * Copy the `sms2tg.py` script to the `~/.termux/boot` directory.  You can use a text editor like `nano` within Termux:
        ```bash
        nano ~/.termux/boot/sms2tg.py
        ```
    * Paste the script content into the editor.
    * Save the file.  In `nano`, you would press `Ctrl+O`, then `Enter`, then `Ctrl+X`.

4.  **Make the Script Executable:** Make the script executable:

    ```bash
    chmod +x ~/.termux/boot/sms2tg.py
    ```

5.  **Configure the Script:**
    * Edit the `sms2tg.py` script:
        ```bash
        nano ~/.termux/boot/sms2tg.py
        ```
    * Replace the following placeholders with your actual values:
        * `TOKEN="<YOUR TELEGRAM BOT TOKE>"`:  Replace with your Telegram bot's token.
        * `CHAT_ID="<YOUR TELEGRAM ID>"`: Replace with the chat ID of the Telegram chat.
    * Save the changes.

## Usage

The script will automatically start sending new SMS messages to your Telegram chat whenever Termux is started via Termux-boot (e.g., after a device reboot).

* **Important:** For this to work automatically on device boot, you *must* have Termux-boot installed and configured correctly.  Simply starting Termux manually will *not* trigger the script if Termux-boot is not set up.
* **Logging:** The script logs its activity to `/data/data/com.termux/files/home/sms_monitor.log`.
* **Last Processed ID:** The script stores the ID of the last processed SMS in `/data/data/com.termux/files/home/.last_sms_id` to avoid sending duplicate messages after a restart.

## How it Works

1.  **Initialization:**
    * It loads the ID of the last processed SMS from `~/.sms2tg/last_processed_id.json`.  If the file doesn't exist, it defaults to -1 (or you can change it to the last SMS ID you want to be processed as the first message after the script starts).
    * It loads filtere sender names from `~/.sms2tg/filtered_addresses.json`.  If the file doesn't exist, filtered list will be empty. Filter list is used to filter unwanted sender from being redirected in telegram.
2.  **SMS Polling Loop:**
    * The script enters an infinite loop that runs every 5 seconds.
    * It uses `termux-sms-list` to get a list of all SMS messages on the device in JSON format.
3.  **Sending to Telegram:**
    * For each new SMS:
        * It extracts the sender's phone number, the message body, the timestamp and the SMS ID.
        * It formats the message content, masking &, <, > and other special characters to prevent issues with the Telegram API.
    * It updates the last processed SMS ID.
4.  **Saving Last Processed ID:**
    * The script saves the ID of the latest processed SMS to `~/.sms2tg/last_processed_id.json` to ensure that only new messages are sent after a restart.
5.  **Sleeping:**
    * The script pauses for 5 seconds before checking for new SMS messages again.

## Important Notes

* **Security:** This script involves handling sensitive data (SMS messages) and your Telegram bot token.  Ensure your Termux environment is secure and that you keep your bot token confidential.  Anyone with your bot token can send messages from your bot.
* **Termux-boot Reliability:** Termux-boot's reliability can vary depending on the Android version and device.  If the script doesn't start automatically on boot, you may need to consult the Termux documentation or community for troubleshooting tips.  Make sure Termux is excluded from any battery optimizations.
* **Error Handling:** The script includes very basic error handling. You may want to enhance the error handling to make it more robust.
* **Resource Usage:** The script runs in an infinite loop, which may consume some battery and system resources.  Consider adjusting the sleep interval if necessary.
* **Customization:** You can customize the message format, add more information from the SMS data, or modify the script to suit your specific needs.
* **SMS Ordering:** SMS messages are not guaranteed to arrive in order.  This script processes them based on their internal ID, which *usually* corresponds to the order of arrival, but there might be edge cases where the order is not strictly preserved.
* **Large SMS:** Very large SMS messages might cause issues.  Telegram has limits on message size.

## Disclaimer

Use this script at your own risk.  The author is not responsible for any issues or damages caused by the use of this script.  Always review and understand the code before running it on your device.
