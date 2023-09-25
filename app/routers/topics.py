from fastapi import APIRouter, Depends
from db.supabase import get_sb
import logging

router = APIRouter(
  prefix="/topics",
  tags=["topics"] 
)

# Define the endpoints for Topics
@router.get("/{id}/topics")
def get_topics(id: int):
    try:
        supabase_client = get_sb()
        chapters = supabase_client.table('topics').select("*").eq('id', id).execute()   
        return chapters
    except Exception as e:
        logging.error(f"Error occurred while fetching topics: {str(e)}")
        return {"error": "Failed to fetch topics"}
    pass

@router.post("/{id}/topics")
def add_topic(id: int):
    pass

@router.get("/topics/{id}")
def get_topic(id: int):
    pass

@router.put("/topics/{id}")
def update_topic(id: int):
    pass

@router.delete("/topics/{id}")
def delete_topic(id: int):
    pass
