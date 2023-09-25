import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

def get_supabase_client():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

sb = None

def get_sb():
    global sb
    if sb is None:
        sb = get_supabase_client()
    return sb
