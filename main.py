import os
import json
import tempfile
import logging
import orjson
import time
import random
from typing import Any

from datetime import datetime
from fastapi import FastAPI, Response
from fastapi import HTTPException
from dotenv import load_dotenv
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

from app.routers import courses, chapters, topics
from db.supabase import get_sb
from db.database import get_course_directory_name, get_chapter_directory_name
from services.storage import download_and_split_files, download_and_split_files_output
from services.text_split import split_text, generate_structure
from services.text_extract import extract_syllabus
from tasks.jobs import create_job_status, update_job_status, get_chapter_index, get_job_status
from utils.logging import send_slack_message
from utils.file_utils import create_directory_if_not_exists
from utils.embeddings import getvectorId
from tasks.jobs import get_topic_id
from services.assessment import QuestionGenerator, ProfilingEngine

app = FastAPI()

origins = ["http://127.0.0.1:3000"]

logging.basicConfig(filename='app.log', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CustomORJSONResponse(Response):
    media_type = "application/json"

    def render(self, content: Any) -> bytes:
        assert orjson is not None, "orjson must be installed"
        return orjson.dumps(content, option=orjson.OPT_INDENT_2)

@app.get("/extract_syllabus/{chapter_id}")
async def split_text_into_files(chapter_id):
    try:
        topics_exists = get_sb().table("topics").select("chapter_id").neq("chapter_id", chapter_id).execute()
        if topics_exists:
            return {"error": f"This chapter already processed"}

        chapter_index = get_chapter_index(chapter_id)
        job_id = create_job_status(chapter_id, chapter_index)
        update_job_status(job_id, "processing")
        chapter = get_sb().table("chapters").select("*").eq("id", chapter_id).execute()
        course = get_sb().table("courses").select("*").eq("id", chapter.data[0]['course_id']).execute()

        chapter_dir_name = get_chapter_directory_name(chapter)
        course_dir_name = get_course_directory_name(course)

        input_bucket_name = "corpus"
        output_bucket_name = "course-content"
        chapter_dir_path = f"{course_dir_name}/{chapter_dir_name}"
        create_directory_if_not_exists(chapter_dir_path)
        temp_file_path, file_name = download_and_split_files(input_bucket_name, chapter_dir_path)
        headers_to_split_on = [("###", "Topik")]
        split_text(temp_file_path, headers_to_split_on,output_bucket_name,chapter_dir_path)
        temp_file_path_output_list, file_name_list, file_location_list = download_and_split_files_output(output_bucket_name, chapter_dir_path)
        filename_without_extension = os.path.splitext(file_name)[0]
        timestamp = int(datetime.now().timestamp())
        new_filename = f"{filename_without_extension}-{timestamp}.json"
        df_result, vector_data_list_result = getvectorId(file_name_list, temp_file_path_output_list)
        output = extract_syllabus(temp_file_path_output_list, vector_values_list,file_location_list,file_name_list,chapter_id)
        output_file_path = os.path.join(tempfile.gettempdir(), new_filename)
        with open(output_file_path, "w") as output_json_file:
            json.dump(output[0], output_json_file, indent=2)
        with open(output_file_path, "rb") as file:
            data = get_sb().storage.from_(output_bucket_name).upload(f"{chapter_dir_path}/{new_filename}", file)
        os.remove(output_file_path)
        update_job_status(job_id, "complete")
        send_slack_message(f"Complete the text extraction for {file_name}")

        return "DONE"

    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid chapter_id")

@app.get("/extract_syllabus/{chapter_id}/status")
async def show_status(chapter_id):
    id, status = get_job_status(chapter_id)
    return {id: status}

@app.get("/assessments/init", response_class=CustomORJSONResponse)
async def init_assessment(user_id, course_id,  chapter_id):
    try:
        generator = QuestionGenerator(user_id = user_id, course_id = course_id, chapter_id = chapter_id)
        generator.init_QuestionGenerator()
        generator.save()
        questions = get_sb().table('questions').select("id").execute()
        question_ids = [question['id'] for question in questions.data]
        engine = ProfilingEngine()
        proficiency_json, user_id = engine.analyze_responses(question_ids)
        engine.save_profile(proficiency_json, user_id)
        return Response(proficiency_json)
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
@app.get("/")
def read_root():
    return {"Key": "Miss World Rapid Fire Round"}

class Course(BaseModel):
    id: str
    created_at: str
    name: str
    name_en: str
    course_code: str
    version: float
    description: str
    corpus_location: str
    language: list

class Chapter(BaseModel):
    created_at: str
    course_id: int
    name: str
    content_type: str
    chapter_index: int

class Topic(BaseModel):
    id: int
    created_at: str
    name: str
    chapter_id: int
    parent_id: int
    metadata: dict
    weight: int
    significance: int
    corpus_location: str
    vector_id: str


app.include_router(courses.router)
app.include_router(chapters.router) 
app.include_router(topics.router)
