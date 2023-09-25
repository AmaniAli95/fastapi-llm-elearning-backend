from fastapi import APIRouter, Depends
from db.supabase import get_sb
import logging

router = APIRouter(
  prefix="/courses",
  tags=["courses"] 
)

# Define the endpoints for Courses
@router.get("/")
async def get_courses():
    try:
        supabase_client = get_sb()
        courses = supabase_client.table('courses').select('*').execute()  
        return courses
    except Exception as e:
        logging.error(f"Error occurred while fetching courses: {str(e)}")
        return {"error": "Failed to fetch courses"}
    pass

@router.get("/{id}")
async def get_course(id: str):
    try:
        supabase_client = get_sb()
        course = supabase_client.table('courses').select('*').eq('id', id).execute()
        return course
    except Exception as e:
        logging.error(f"Error occurred while fetching course: {str(e)}")
        return {"error": "Failed to fetch course"}
    pass

@router.post("/")
async def add_course():
  pass

@router.put("/{id}")
async def update_course(id: int):
  pass

@router.delete("/{id}")
async def delete_course(id: int):
  pass
