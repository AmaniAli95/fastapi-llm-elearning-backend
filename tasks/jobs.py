from db.supabase import get_sb

def get_chapter_index(task_id):
    chapter = get_sb().table("chapters").select("chapter_index").eq("id", task_id).execute()
    return chapter.data[0]['chapter_index']

def create_job_status(task_id,chapter_index):
    job = get_sb().table("jobs").insert({"task_id": task_id, "chapter_index": chapter_index, "status": "pending"}).execute()
    job_id = job.data[0]['id']
    return job_id

def update_job_status(job_id, status):
    get_sb().table("jobs").update({"status": status}).eq("id", job_id).execute()

def get_job_status(task_id):
    job = get_sb().table("jobs").select("id, status").eq("task_id", task_id).execute()
    return job.data[0]['id'], job.data[0]['status']

def get_topic_id(topicName):
    job = get_sb().table("topics").select("id").eq("name", topicName).execute()
    return job.data[0]['id']