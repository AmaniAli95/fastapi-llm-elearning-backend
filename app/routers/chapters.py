from fastapi import APIRouter, Depends
from db.supabase import get_sb
import logging

router = APIRouter(
  prefix="/chapters",
  tags=["chapters"] 
)

# Define the endpoints for Chapters
@router.get("/")
async def get_chapters():
    try:
        supabase_client = get_sb()
        chapters = supabase_client.table('chapters').select("*").execute()   
        return chapters
    except Exception as e:
        logging.error(f"Error occurred while fetching chapters: {str(e)}")
        return {"error": "Failed to fetch chapters"}

@router.get("/")
async def get_chapters():
    supabase_client = get_sb()
    chapters = supabase_client.table('chapters').select("*").execute()   
    return chapters

@router.post("/{id}/chapters")
async def add_chapter(id: int):
    pass

@router.get("/{id}")
async def get_chapter(id: int):
    supabase_client = get_sb() 
    chapters = supabase_client.table('chapters').select("*").eq('id', id).execute()
    return chapters

@router.put("/{id}")
async def update_chapter(id: int):
    pass

@router.delete("/{id}")
async def delete_chapter(id: int):
    pass
