import tempfile
import requests
from datetime import datetime
from utils.logging import send_slack_message

from db.supabase import get_sb

def download_file(input_bucket_name, file_location):
    file_url = get_sb().storage.from_(input_bucket_name).get_public_url(file_location)
    response = requests.get(file_url)
    file_content = response.text
    return file_content

def download_and_split_files(input_bucket_name, chapter_dir_path):
    file_list = get_sb().storage.from_(input_bucket_name).list(chapter_dir_path)
    temp_file_path = None
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
        for file_info in file_list:
            if file_info.get("name").endswith(".md"):
                file_name = file_info["name"]
                #send_slack_message(f"Processing the text extraction for {file_name}")
                file_location = f"{chapter_dir_path}/{file_name}"
                file_content = download_file(input_bucket_name, file_location)
                temp_file.write(file_content)
        temp_file_path = temp_file.name
    return temp_file_path, file_name

def download_and_split_files_output(output_bucket_name, chapter_dir_path):
    file_list = get_sb().storage.from_(output_bucket_name).list(chapter_dir_path)
    temp_file_path_output = None
    temp_file_path_output_list = []
    file_location_list = []
    file_name_list = []
    
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
        for file_info in file_list:
            if file_info.get("name").endswith("md"):
                file_name = file_info["name"]
                file_name_list.append(file_name)
                file_location = f"{chapter_dir_path}/{file_name}"
                file_location_list.append(file_location)
                file_content = download_file(output_bucket_name, file_location)
                # Create a temporary file and store content
                temp_file = tempfile.NamedTemporaryFile(mode="w", delete=False)
                temp_file.write(file_content)
                temp_file_path_output_list.append(temp_file.name)
                temp_file.close()
    return temp_file_path_output_list, file_name_list, file_location_list

def get_file_location(chapter_id):
    result = get_sb().table("chapters").select("file_location").eq("chapter_index", chapter_id).execute()
    return result.data[0]["file_location"]
