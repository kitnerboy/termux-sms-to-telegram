#!/bin/bash
# This script should be put in ~/.termux/boot directory and will be launched with termux-boot (installed separately from termux itself)
TOKEN="<YOUR TELEGRAM BOT TOKE>"
CHAT_ID="<YOUR TELEGRAM ID>"
URL="https://api.telegram.org/bot$TOKEN/sendMessage"
NL=$'\n'

HOME_DIR="/data/data/com.termux/files/home"
LOG_FILE="${HOME_DIR}/sms_monitor.log"
LAST_PROCESSED_ID_FILE="${HOME_DIR}/.last_sms_id"

# Function to load the last processed SMS ID
load_last_processed_id() {
  if [ -f "$LAST_PROCESSED_ID_FILE" ]; then
    last_processed_id=$(cat "$LAST_PROCESSED_ID_FILE")
  else
    last_processed_id=0 # Or the ID of the last SMS you want to consider initial
  fi
}

# Function to save the last processed SMS ID
save_last_processed_id() {
  echo "$1" > "$LAST_PROCESSED_ID_FILE"
}

echo "$(date) Started" | tee -a "$LOG_FILE"

load_last_processed_id

echo "Last id = $last_processed_id" | tee -a "$LOG_FILE"

while true; do
    all_sms=$(termux-sms-list)

    if [ -n "$all_sms" ]; then
        new_sms_json=$(echo "$all_sms" | jq -c '.[] | select(."_id" > '$last_processed_id')')
#        echo "New sms raw: \"$new_sms_json\""
	if [ ! -z "${new_sms_json}" ]; then
		echo "Found new sms"
	        while IFS= read -r new_sms_item; do
	            sender=$(echo "$new_sms_item" | jq -r '.address')
	            body=$(echo "$new_sms_item" | jq -r '.body')
	            timestamp=$(echo "$new_sms_item" | jq -r '.received')
	            sms_id=$(echo "$new_sms_item" | jq -r '."_id"')


		    CONTENT="Sender: ${sender}${NL}"
		    CONTENT="${CONTENT}Time: ${timestamp}${NL}"
		    CONTENT="${CONTENT}${body}${NL}"
		    CONTENT=${CONTENT//&/%26}
		    CONTENT=${CONTENT//</%3C}
	            CONTENT=${CONTENT//>/%3E}

		    curl -f -X POST $URL -d chat_id=$CHAT_ID -d text="${CONTENT}"
		    if [[ $? -ne 0 ]]; then
			echo "$(date) curl failed on sms $sms_id" | tee -a "$LOG_FILE"
			continue
		    fi

                    echo | tee -a "$LOG_FILE"
		    echo "$(date) Succesfully sent:"
                    echo "ID: $sms_id" | tee -a "$LOG_FILE"
                    echo "Sender: $sender" | tee -a "$LOG_FILE"
                    echo "Time: $timestamp" | tee -a "$LOG_FILE"
                    echo "Body: $body" | tee -a "$LOG_FILE"
                    echo | tee -a "$LOG_FILE"



#	            echo "$(date) - New SMS (ID: $sms_id) - From: $sender, Body: $body, Received at: $timestamp" | tee -a "$LOG_FILE"

	            # Update the last processed ID
	            if [[ "$sms_id" -gt "$last_processed_id" ]]; then
	                last_processed_id="$sms_id"
	            fi
	        done < <(echo "$new_sms_json")
	fi

        # Save the latest processed ID
        save_last_processed_id "$last_processed_id"
    fi

    sleep 5
done
