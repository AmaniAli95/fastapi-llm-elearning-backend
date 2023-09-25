import os
from slack_sdk import WebClient
from datetime import datetime

slack_client = WebClient(os.environ.get("SLACK_BOT_TOKEN"))

def send_slack_message(message: str):
    formatted_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted_message = f"{message} -- created_at: {formatted_timestamp}"
    slack_client.chat_postMessage(channel="#log", text=formatted_message)
