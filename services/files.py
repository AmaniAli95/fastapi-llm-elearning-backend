import os
import tempfile
import requests
from datetime import datetime

from utils.logging import send_slack_message
from db.database import log_job
from db.supabase import get_sb

def upload_file(bucket_name, file_path, file_name):
    file_content = ""
    with open(file_path, "r") as file:
        file_content = file.read()
    file_location = f"{bucket_name}/{file_name}"
    get_sb().storage.from_(bucket_name).upload(file_location, file_content)
    return file_location

def delete_file(file_location):
    get_sb().storage.from_(file_location).delete()
    return

def log_job(message):
    get_sb().table("jobs").insert({"status": message}).execute()

def get_file_location(chapter_id):
    result = get_sb().table("chapters").select("file_location").eq("id", chapter_id).execute()
    return result["file_location"]
